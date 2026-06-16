# =============================================================================
# server.py — Serviço web do Flashscore Lay Analyzer
#
# Uso:
#   python server.py
#   Acesse http://localhost:5001
#
# Comportamento:
#   - Run automático às 09:00 analisa jogos de HOJE
#   - Run automático às 22:00 analisa jogos de AMANHÃ (pré-live)
#   - Cache dual: slots "hoje" e "amanha" independentes
#   - Dashboard com toggle Hoje/Amanhã
# =============================================================================

import glob
import json
import logging
import threading
import time
from datetime import datetime, date, timedelta

from flask import Flask, jsonify, render_template_string, request

import config
from analyzer import (calcular_frequencias_jogo, classificar_oportunidade,
                      construir_dataframe, exportar_dados)
from scraper import coletar_h2h, coletar_jogos_do_dia, coletar_odds, setup_driver

app = Flask(__name__)
logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger("server")
logger.setLevel(logging.INFO)
_ch = logging.StreamHandler()
_ch.setFormatter(logging.Formatter("%(asctime)s [server] %(message)s", datefmt="%H:%M:%S"))
logger.addHandler(_ch)


# =============================================================================
# Estado global (thread-safe)
# =============================================================================
_lock = threading.Lock()

_state = {
    "status":    "idle",   # idle | running | done | error
    "progress":  0,
    "total":     0,
    "current":   "",
    "log":       [],
    "last_run":  None,
    "last_slot": None,     # "hoje" ou "amanha"
}

# Cache dual: slots independentes para hoje e amanhã
_cache = {
    "hoje":   {"data": [], "source": None, "date": None},
    "amanha": {"data": [], "source": None, "date": None},
}


def _upd(**kw):
    with _lock:
        _state.update(kw)


def _log(msg: str):
    with _lock:
        _state["log"].append(msg)
        _state["log"] = _state["log"][-80:]


# =============================================================================
# Cache — carrega resultados existentes na inicialização
# =============================================================================
def _carregar_cache():
    hoje_str   = date.today().isoformat()
    amanha_str = (date.today() + timedelta(days=1)).isoformat()

    for slot, data_str in [("hoje", hoje_str), ("amanha", amanha_str)]:
        path = f"flashscore_lay_{data_str}.json"
        try:
            with open(path, encoding="utf-8") as f:
                dados = json.load(f)
            with _lock:
                _cache[slot]["data"]   = dados
                _cache[slot]["source"] = path
                _cache[slot]["date"]   = data_str
            logger.info(f"Cache [{slot}] carregado: {path} ({len(dados)} jogos)")
        except FileNotFoundError:
            logger.info(f"Cache [{slot}] vazio — arquivo {path} não encontrado.")
        except Exception as ex:
            logger.warning(f"Falha ao carregar cache [{slot}]: {ex}")


def _atualizar_cache(df, slot: str, data_str: str):
    try:
        dados = json.loads(df.to_json(orient="records", force_ascii=False))
        with _lock:
            _cache[slot]["data"]   = dados
            _cache[slot]["source"] = f"flashscore_lay_{data_str}.json"
            _cache[slot]["date"]   = data_str
    except Exception as ex:
        logger.warning(f"Falha ao atualizar cache [{slot}]: {ex}")


# =============================================================================
# Lógica de análise (roda em thread separada)
# =============================================================================
def _run(headless: bool, limiar: float, slot: str = "hoje", dias_frente: int = 0):
    data_alvo = (date.today() + timedelta(days=dias_frente)).isoformat()

    _upd(status="running", progress=0, total=0,
         current="Iniciando Firefox...", log=[],
         last_run=datetime.now().strftime("%H:%M:%S"),
         last_slot=slot)
    driver = None
    try:
        driver = setup_driver(headless=headless)

        label_slot = "Amanhã" if slot == "amanha" else "Hoje"
        _upd(current=f"Coletando jogos de {label_slot} ({data_alvo})...")
        jogos = coletar_jogos_do_dia(driver, dias_frente=dias_frente)

        if not jogos:
            _upd(status="error", current="Nenhum jogo agendado encontrado.")
            return

        _upd(total=len(jogos))
        _log(f"Encontrados {len(jogos)} jogos ({label_slot} — {data_alvo}).")
        processados = []

        for i, jogo in enumerate(jogos, 1):
            desc = f"{jogo['time_casa']} vs {jogo['time_fora']}"
            _upd(progress=i, current=f"[{i}/{len(jogos)}] {desc}")
            _log(f"[{i}/{len(jogos)}] {desc}")

            try:
                h2h  = coletar_h2h(driver, jogo["url"], jogo["id"])
                time.sleep(config.DELAY_ENTRE_JOGOS)
                odds = coletar_odds(driver, jogo["id"], url_jogo=jogo["url"])
                time.sleep(config.DELAY_ENTRE_JOGOS)

                freqs   = calcular_frequencias_jogo(h2h)
                classif = classificar_oportunidade(freqs, odds, limiar)

                _log(f"  -> {classif}  freq={freqs['freq_combinada_total']:.1%}")
                processados.append({
                    "jogo": jogo, "h2h": h2h, "odds": odds,
                    "freqs": freqs, "classificacao": classif,
                })
            except Exception as ex:
                _log(f"  -> ERRO: {ex}")

        if processados:
            df = construir_dataframe(processados, data_override=data_alvo)
            exportar_dados(df, "flashscore_lay", data_override=data_alvo)
            _atualizar_cache(df, slot, data_alvo)
            _upd(status="done",
                 current=f"Concluido — {len(processados)}/{len(jogos)} jogos ({label_slot}).")
            _log(f"Analise concluida. {len(processados)} jogos no cache [{slot}].")
        else:
            _upd(status="error", current="Nenhum jogo processado com sucesso.")

    except Exception as ex:
        _upd(status="error", current=f"Erro fatal: {ex}")
        _log(f"ERRO FATAL: {ex}")
    finally:
        if driver:
            driver.quit()


def _iniciar_run(headless: bool, limiar: float, slot: str = "hoje", dias_frente: int = 0):
    with _lock:
        if _state["status"] == "running":
            return False
    threading.Thread(target=_run, args=(headless, limiar, slot, dias_frente), daemon=True).start()
    return True


# =============================================================================
# Scheduler automático
# =============================================================================
def _scheduler():
    logger.info(
        f"Scheduler ativo — Hoje às {config.AUTO_RUN_HORA:02d}:{config.AUTO_RUN_MINUTO:02d} | "
        f"Amanhã às {config.AUTO_RUN_AMANHA_HORA:02d}:{config.AUTO_RUN_AMANHA_MINUTO:02d}"
    )
    ultimo_hoje   = None
    ultimo_amanha = None

    while True:
        now   = datetime.now()
        chave = (now.date(), now.hour, now.minute)

        if (now.hour == config.AUTO_RUN_HORA
                and now.minute == config.AUTO_RUN_MINUTO
                and chave != ultimo_hoje):
            ultimo_hoje = chave
            logger.info(f"Run automático HOJE ({now.strftime('%H:%M')})...")
            _iniciar_run(config.AUTO_RUN_HEADLESS, config.LIMIAR_OPORTUNIDADE,
                         slot="hoje", dias_frente=0)

        elif (now.hour == config.AUTO_RUN_AMANHA_HORA
                and now.minute == config.AUTO_RUN_AMANHA_MINUTO
                and chave != ultimo_amanha):
            ultimo_amanha = chave
            logger.info(f"Run automático AMANHÃ ({now.strftime('%H:%M')})...")
            _iniciar_run(config.AUTO_RUN_HEADLESS, config.LIMIAR_OPORTUNIDADE,
                         slot="amanha", dias_frente=1)

        time.sleep(30)


# =============================================================================
# Rotas da API
# =============================================================================
@app.route("/api/status")
def api_status():
    with _lock:
        st = dict(_state)

    now  = datetime.now()

    # Próximo run hoje
    prox_hoje = now.replace(hour=config.AUTO_RUN_HORA, minute=config.AUTO_RUN_MINUTO,
                            second=0, microsecond=0)
    if prox_hoje <= now:
        prox_hoje += timedelta(days=1)

    # Próximo run amanhã
    prox_amanha = now.replace(hour=config.AUTO_RUN_AMANHA_HORA,
                              minute=config.AUTO_RUN_AMANHA_MINUTO,
                              second=0, microsecond=0)
    if prox_amanha <= now:
        prox_amanha += timedelta(days=1)

    st["next_run_hoje"]   = prox_hoje.strftime("%d/%m %H:%M")
    st["next_run_amanha"] = prox_amanha.strftime("%d/%m %H:%M")

    with _lock:
        st["cache"] = {
            slot: {"date": _cache[slot]["date"], "count": len(_cache[slot]["data"])}
            for slot in ("hoje", "amanha")
        }
    return jsonify(st)


@app.route("/api/results")
def api_results():
    slot = request.args.get("slot", "hoje")
    if slot not in ("hoje", "amanha"):
        slot = "hoje"
    with _lock:
        data   = list(_cache[slot]["data"])
        source = _cache[slot]["source"]
        dt     = _cache[slot]["date"]
    return jsonify({"slot": slot, "source": source, "date": dt, "count": len(data), "data": data})


@app.route("/api/run", methods=["POST"])
def api_run():
    body        = request.get_json(silent=True) or {}
    headless    = body.get("headless", True)
    limiar      = float(body.get("limiar", config.LIMIAR_OPORTUNIDADE))
    slot        = body.get("slot", "hoje")
    dias_frente = 1 if slot == "amanha" else 0

    if slot not in ("hoje", "amanha"):
        slot = "hoje"

    ok = _iniciar_run(headless, limiar, slot=slot, dias_frente=dias_frente)
    if not ok:
        return jsonify({"error": "Análise já em andamento."}), 409
    return jsonify({"ok": True, "slot": slot})


@app.route("/")
def index():
    from datetime import date as _date, timedelta as _td
    return render_template_string(
        DASHBOARD_HTML,
        auto_hora=config.AUTO_RUN_HORA,
        auto_min=config.AUTO_RUN_MINUTO,
        auto_amanha_hora=config.AUTO_RUN_AMANHA_HORA,
        auto_amanha_min=config.AUTO_RUN_AMANHA_MINUTO,
        hoje_str=_date.today().isoformat(),
        amanha_str=(_date.today() + _td(days=1)).isoformat(),
    )


# =============================================================================
# Dashboard HTML / CSS / JS
# =============================================================================
DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lay Analyzer</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg:     #1a1b2e;
    --card:   #1f2040;
    --border: rgba(255,255,255,0.08);
    --text:   #e2e8f0;
    --muted:  #94a3b8;
    --green:  #22d97a;
    --yellow: #f5c842;
    --red:    #f85149;
    --blue:   #58a6ff;
    --radius: 10px;
  }
  body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: linear-gradient(135deg, #1a1b2e 0%, #252641 100%);
    color: var(--text);
    min-height: 100vh;
    padding: 20px;
  }

  /* ─── Header ─────────────────────────────────────────── */
  .header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 18px 24px; gap: 16px; flex-wrap: wrap;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 20px;
  }
  .header h1 {
    font-size: 1.4rem;
    background: linear-gradient(135deg, #f5c842, #22d97a);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  }
  .header-sub { display: flex; flex-direction: column; gap: 3px; }
  .header-sub small { color: var(--muted); font-size: .76rem; }
  .header-right { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }

  /* ─── Date toggle ─────────────────────────────────────── */
  .date-toggle {
    display: flex; border-radius: 8px; overflow: hidden;
    border: 1px solid var(--border);
  }
  .dtog {
    padding: 7px 16px; background: transparent;
    border: none; color: var(--muted); font-size: .82rem; font-weight: 600;
    cursor: pointer; transition: all .15s; white-space: nowrap;
  }
  .dtog:first-child { border-right: 1px solid var(--border); }
  .dtog.active { background: rgba(88,166,255,.15); color: var(--blue); }
  .dtog:hover:not(.active) { background: rgba(255,255,255,0.06); color: var(--text); }

  /* ─── Pill de status do serviço ───────────────────────── */
  .service-pill {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 12px; border-radius: 99px;
    font-size: .74rem; font-weight: 600;
    border: 1px solid;
  }
  .service-pill.idle    { border-color: rgba(88,166,255,.3);  color: var(--blue);   background: rgba(88,166,255,.08); }
  .service-pill.running { border-color: rgba(245,200,66,.35); color: var(--yellow); background: rgba(245,200,66,.1); }
  .service-pill.done    { border-color: rgba(34,217,122,.3);  color: var(--green);  background: rgba(34,217,122,.08); }
  .service-pill.error   { border-color: rgba(248,81,73,.3);   color: var(--red);    background: rgba(248,81,73,.08); }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
  .dot.pulse { animation: pulse 1.4s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }

  .btn {
    padding: 8px 18px; border: none; border-radius: 8px;
    font-size: .85rem; font-weight: 600; cursor: pointer;
    transition: opacity .15s, transform .1s; white-space: nowrap;
  }
  .btn:hover:not(:disabled) { opacity: .85; transform: translateY(-1px); }
  .btn-primary { background: linear-gradient(135deg, #22d97a, #16a05a); color: #fff; }
  .btn-blue    { background: linear-gradient(135deg, #58a6ff, #3b82f6); color: #fff; }
  .btn:disabled { background: #2a2c50; color: #555; cursor: default; transform: none; }

  /* ─── Info bar de data ────────────────────────────────── */
  .date-info {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 16px; margin-bottom: 16px;
    background: rgba(88,166,255,.07);
    border: 1px solid rgba(88,166,255,.2);
    border-radius: 8px; font-size: .82rem; color: var(--blue);
  }
  .date-info span { margin-left: auto; color: var(--muted); font-size: .76rem; }

  /* ─── Stats ───────────────────────────────────────────── */
  .stats { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; margin-bottom: 20px; }
  .stat-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 16px 18px; text-align: center;
  }
  .stat-card .num { font-size: 1.9rem; font-weight: 700; }
  .stat-card .lbl { font-size: .7rem; color: var(--muted); margin-top: 4px; text-transform: uppercase; letter-spacing: .05em; }
  .green .num  { color: var(--green); }
  .yellow .num { color: var(--yellow); }
  .blue .num   { color: var(--blue); }
  .muted .num  { color: var(--muted); }

  /* ─── Progress ────────────────────────────────────────── */
  .progress-box {
    background: var(--card); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 16px 20px;
    margin-bottom: 20px; display: none;
  }
  .progress-box.visible { display: block; }
  .progress-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
  .progress-label { font-size: .82rem; color: var(--muted); }
  .progress-track { background: rgba(255,255,255,0.07); border-radius: 99px; height: 6px; }
  .progress-fill  { background: linear-gradient(90deg, #22d97a, #f5c842); height: 6px; border-radius: 99px; transition: width .4s; }
  .log-area {
    font-size: .72rem; color: var(--muted);
    font-family: 'Consolas', 'Cascadia Code', monospace;
    max-height: 100px; overflow-y: auto; margin-top: 10px;
    padding: 8px 10px; background: rgba(0,0,0,0.25); border-radius: 6px; line-height: 1.55;
  }

  /* ─── Filters ─────────────────────────────────────────── */
  .filter-bar { display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; align-items: center; }
  .tab {
    padding: 5px 14px; border-radius: 99px;
    border: 1px solid var(--border); background: transparent;
    color: var(--muted); font-size: .77rem; cursor: pointer; transition: all .15s;
  }
  .tab.active, .tab:hover { background: rgba(255,255,255,0.09); color: var(--text); border-color: rgba(255,255,255,0.2); }
  .tab.active { font-weight: 600; }
  .spacer { flex: 1; }
  .search-inp {
    padding: 5px 12px; border-radius: 8px;
    border: 1px solid var(--border); background: rgba(255,255,255,0.05);
    color: var(--text); font-size: .82rem; outline: none; width: 185px;
    transition: border-color .15s;
  }
  .search-inp:focus { border-color: rgba(255,255,255,0.25); }

  /* ─── Table ───────────────────────────────────────────── */
  .table-wrap { overflow-x: auto; border-radius: var(--radius); border: 1px solid var(--border); }
  table { width: 100%; border-collapse: collapse; font-size: .83rem; }
  th {
    padding: 10px 14px; text-align: left;
    font-size: .67rem; text-transform: uppercase; letter-spacing: .06em;
    color: var(--muted); background: rgba(0,0,0,0.25);
    border-bottom: 1px solid var(--border); white-space: nowrap;
  }
  td { padding: 10px 14px; border-bottom: 1px solid rgba(255,255,255,0.04); vertical-align: middle; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,255,255,0.03); }

  tr.lay td:first-child       { border-left: 3px solid var(--green); }
  tr.monitorar td:first-child { border-left: 3px solid var(--yellow); }
  tr.descartar td:first-child { border-left: 3px solid var(--red); }
  tr.sem-dados td:first-child { border-left: 3px solid #444; }
  tr.sem-dados td             { opacity: .55; }

  .badge { display: inline-block; padding: 3px 9px; border-radius: 99px; font-size: .7rem; font-weight: 700; }
  .badge-green  { background: rgba(34,217,122,.14); color: var(--green); }
  .badge-yellow { background: rgba(245,200,66,.14);  color: var(--yellow); }
  .badge-red    { background: rgba(248,81,73,.14);   color: var(--red); }
  .badge-gray   { background: rgba(148,163,184,.1);  color: var(--muted); }

  .odd-cell { font-variant-numeric: tabular-nums; }
  .freq-bar { display: inline-block; width: 48px; height: 4px; background: rgba(255,255,255,0.1); border-radius: 99px; vertical-align: middle; margin-left: 6px; }
  .freq-fill { height: 100%; border-radius: 99px; }

  .empty-msg { text-align: center; padding: 48px; color: var(--muted); font-size: .88rem; }
  label.chk { display: flex; align-items: center; gap: 6px; font-size: .8rem; color: var(--muted); cursor: pointer; }
  input[type=checkbox] { accent-color: var(--green); width: 14px; height: 14px; }

  @media (max-width: 700px) {
    .stats { grid-template-columns: repeat(2,1fr); }
    .hide-sm { display: none !important; }
    .search-inp { width: 140px; }
  }
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div class="header-sub">
    <h1>Lay Analyzer — Flashscore</h1>
    <small id="lastUpdate">Carregando...</small>
    <small id="nextRun" style="color:var(--blue)"></small>
  </div>
  <div class="header-right">
    <div class="service-pill idle" id="servicePill">
      <div class="dot" id="pillDot"></div>
      <span id="pillLabel">Aguardando</span>
    </div>
    <!-- Toggle Hoje / Amanhã -->
    <div class="date-toggle">
      <button class="dtog active" id="dtog-hoje" onclick="setSlot('hoje',this)">Hoje</button>
      <button class="dtog" id="dtog-amanha" onclick="setSlot('amanha',this)">Amanhã</button>
    </div>
    <label class="chk">
      <input type="checkbox" id="chkHeadless" checked>Headless
    </label>
    <button class="btn btn-primary" id="btnRun" onclick="startRun()">Rodar Agora</button>
  </div>
</div>

<!-- Barra de data ativa -->
<div class="date-info" id="dateInfo">
  <strong id="dateLabel">Carregando...</strong>
  <span id="dateSubLabel"></span>
</div>

<!-- Stats -->
<div class="stats">
  <div class="stat-card green"><div class="num" id="cntLay">—</div><div class="lbl">LAY</div></div>
  <div class="stat-card yellow"><div class="num" id="cntMon">—</div><div class="lbl">Monitorar</div></div>
  <div class="stat-card muted"><div class="num" id="cntDes">—</div><div class="lbl">Descartar</div></div>
  <div class="stat-card blue"><div class="num" id="cntTotal">—</div><div class="lbl">Total Jogos</div></div>
</div>

<!-- Progress (visível só durante run) -->
<div class="progress-box" id="progressBox">
  <div class="progress-head">
    <span class="progress-label" id="progLabel">Aguardando...</span>
    <span class="progress-label" id="progPct">0%</span>
  </div>
  <div class="progress-track"><div class="progress-fill" id="progBar" style="width:0%"></div></div>
  <div class="log-area" id="logArea"></div>
</div>

<!-- Filters -->
<div class="filter-bar">
  <button class="tab active" onclick="setFilter('todos',this)">Todos</button>
  <button class="tab" onclick="setFilter('lay',this)">LAY</button>
  <button class="tab" onclick="setFilter('monitorar',this)">Monitorar</button>
  <button class="tab" onclick="setFilter('descartar',this)">Descartar</button>
  <button class="tab" onclick="setFilter('sem_dados',this)">Sem dados</button>
  <div class="spacer"></div>
  <input class="search-inp" id="searchInp" placeholder="Buscar time..." oninput="renderTable()">
</div>

<!-- Table -->
<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th>Hora</th>
        <th>Partida</th>
        <th>H2H</th>
        <th>Freq</th>
        <th>Média Gols</th>
        <th class="hide-sm">Over 1.5</th>
        <th class="hide-sm">Odd 1</th>
        <th class="hide-sm">Odd X</th>
        <th class="hide-sm">Odd 2</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody id="tBody">
      <tr><td colspan="9" class="empty-msg">Carregando resultados...</td></tr>
    </tbody>
  </table>
</div>

<script>
const AUTO_HORA        = {{ auto_hora }};
const AUTO_MIN         = {{ auto_min }};
const AUTO_AMANHA_HORA = {{ auto_amanha_hora }};
const AUTO_AMANHA_MIN  = {{ auto_amanha_min }};
const HOJE_STR         = "{{ hoje_str }}";
const AMANHA_STR       = "{{ amanha_str }}";

let _data      = [];
let _filter    = 'todos';
let _poll      = null;
let _isRunning = false;
let _slot      = 'hoje';   // "hoje" | "amanha"

// ── Slot de data (Hoje / Amanhã) ──────────────────────────
function setSlot(s, el) {
  _slot = s;
  document.querySelectorAll('.dtog').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  updateDateInfo();
  loadResults();
}

function updateDateInfo() {
  const isAmanha = _slot === 'amanha';
  const label    = isAmanha ? `Amanhã — ${AMANHA_STR}` : `Hoje — ${HOJE_STR}`;
  const sub      = isAmanha
    ? `Run automático às ${String(AUTO_AMANHA_HORA).padStart(2,'0')}:${String(AUTO_AMANHA_MIN).padStart(2,'0')}`
    : `Run automático às ${String(AUTO_HORA).padStart(2,'0')}:${String(AUTO_MIN).padStart(2,'0')}`;
  document.getElementById('dateLabel').textContent    = label;
  document.getElementById('dateSubLabel').textContent = sub;
  document.getElementById('btnRun').textContent = isAmanha ? 'Rodar Amanhã' : 'Rodar Agora';
}

// ── Filtro ────────────────────────────────────────────────
function setFilter(f, el) {
  _filter = f;
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  renderTable();
}

// ── Helpers ───────────────────────────────────────────────
function fPct(v) { return (v == null) ? '—' : (v*100).toFixed(1)+'%'; }
function fOdd(v) { return (v != null) ? Number(v).toFixed(2) : '—'; }
function freqBar(v) {
  const p = Math.min((v||0)*100,100);
  const c = p<10 ? '#22d97a' : p<20 ? '#f5c842' : '#f85149';
  return `<span class="freq-bar"><span class="freq-fill" style="width:${p}%;background:${c}"></span></span>`;
}

// ── Render tabela ─────────────────────────────────────────
function renderTable() {
  const q = document.getElementById('searchInp').value.toLowerCase();
  const rows = _data.filter(r => {
    if (_filter==='lay'       && r.classificacao!=='LAY_OPORTUNIDADE') return false;
    if (_filter==='monitorar' && r.classificacao!=='MONITORAR')        return false;
    if (_filter==='descartar' && r.classificacao!=='DESCARTAR')        return false;
    if (_filter==='sem_dados' && r.classificacao!=='SEM_DADOS')        return false;
    if (q && !`${r.time_casa} ${r.time_fora}`.toLowerCase().includes(q)) return false;
    return true;
  });

  const tbody = document.getElementById('tBody');
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="9" class="empty-msg">Nenhum jogo encontrado.</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map(r => {
    const cls = r.classificacao==='LAY_OPORTUNIDADE' ? 'lay'
              : r.classificacao==='MONITORAR'        ? 'monitorar'
              : r.classificacao==='DESCARTAR'        ? 'descartar'
              : r.classificacao==='SEM_DADOS'        ? 'sem-dados' : '';
    const badge = r.classificacao==='LAY_OPORTUNIDADE'
      ? `<span class="badge badge-green">${r.cenario_ideal ? '★ LAY' : 'LAY'}</span>`
      : r.classificacao==='MONITORAR'
      ? `<span class="badge badge-yellow">Monitorar</span>`
      : r.classificacao==='SEM_DADOS'
      ? `<span class="badge badge-gray">Sem dados</span>`
      : `<span class="badge badge-red">Descartar</span>`;

    const gols    = r.media_gols_confronto;
    const golsCor = gols >= 2.5 ? 'var(--green)' : gols >= 2.0 ? 'var(--yellow)' : 'var(--muted)';
    const overTxt = r.odd_over_1_5 ? fOdd(r.odd_over_1_5) : '—';

    return `<tr class="${cls}">
      <td>${r.hora||'—'}</td>
      <td>
        <strong>${r.time_casa}</strong>
        <span style="color:var(--muted);margin:0 6px;font-size:.74rem">vs</span>
        <strong>${r.time_fora}</strong>
      </td>
      <td class="odd-cell" style="color:var(--muted);font-size:.75rem">${r.n_jogos_h2h||0} j.</td>
      <td class="odd-cell">${fPct(r.freq_combinada_total)}${freqBar(r.freq_combinada_total)}</td>
      <td class="odd-cell" style="color:${golsCor};font-weight:600">${gols!=null ? gols.toFixed(1) : '—'}</td>
      <td class="odd-cell hide-sm">${overTxt}</td>
      <td class="odd-cell hide-sm">${fOdd(r.odd_1)}</td>
      <td class="odd-cell hide-sm">${fOdd(r.odd_x)}</td>
      <td class="odd-cell hide-sm">${fOdd(r.odd_2)}</td>
      <td>${badge}</td>
    </tr>`;
  }).join('');
}

function updateStats() {
  const lay = _data.filter(r=>r.classificacao==='LAY_OPORTUNIDADE').length;
  const mon = _data.filter(r=>r.classificacao==='MONITORAR').length;
  const des = _data.filter(r=>r.classificacao==='DESCARTAR').length;
  const sd  = _data.filter(r=>r.classificacao==='SEM_DADOS').length;
  document.getElementById('cntLay').textContent   = lay;
  document.getElementById('cntMon').textContent   = mon;
  document.getElementById('cntDes').textContent   = sd > 0 ? `${des} (${sd} s/d)` : des;
  document.getElementById('cntTotal').textContent = _data.length;
}

// ── Pill de status ────────────────────────────────────────
function setPill(status, label) {
  const pill = document.getElementById('servicePill');
  const dot  = document.getElementById('pillDot');
  const lbl  = document.getElementById('pillLabel');
  pill.className = `service-pill ${status}`;
  dot.className  = `dot${status==='running' ? ' pulse' : ''}`;
  lbl.textContent = label;
}

// ── Próximo run automático ────────────────────────────────
function nextRunLabel() {
  const now    = new Date();
  const isAm   = _slot === 'amanha';
  const h      = isAm ? AUTO_AMANHA_HORA : AUTO_HORA;
  const m      = isAm ? AUTO_AMANHA_MIN  : AUTO_MIN;
  const prox   = new Date(now);
  prox.setHours(h, m, 0, 0);
  if (prox <= now) prox.setDate(prox.getDate()+1);
  const diff   = Math.round((prox-now)/60000);
  const hm     = `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`;
  if (diff < 60) return `Auto-run ${isAm?'amanhã':'hoje'} às ${hm} (em ${diff} min)`;
  const hrs    = Math.floor(diff/60);
  return `Auto-run ${isAm?'amanhã':'hoje'} às ${hm} (em ${hrs}h${diff%60>0?` ${diff%60}min`:''})`;
}

// ── Carregar resultados do servidor ───────────────────────
async function loadResults() {
  try {
    const r = await fetch(`/api/results?slot=${_slot}`);
    const j = await r.json();
    if (j.data && j.data.length) {
      _data = j.data;
      const dt = j.date ? ` — ${j.date}` : '';
      document.getElementById('lastUpdate').textContent =
        `Cache ${_slot}${dt}  •  ${j.count} jogos`;
      updateStats();
      renderTable();
    } else {
      _data = [];
      updateStats();
      const slotLabel = _slot === 'amanha' ? 'amanhã' : 'hoje';
      document.getElementById('lastUpdate').textContent =
        `Sem dados para ${slotLabel}. Clique "Rodar ${_slot==='amanha'?'Amanhã':'Agora'}" para analisar.`;
      document.getElementById('tBody').innerHTML =
        `<tr><td colspan="9" class="empty-msg">Clique em "${_slot==='amanha'?'Rodar Amanhã':'Rodar Agora'}" para analisar os jogos de ${slotLabel}.</td></tr>`;
      document.getElementById('cntLay').textContent   = '—';
      document.getElementById('cntMon').textContent   = '—';
      document.getElementById('cntDes').textContent   = '—';
      document.getElementById('cntTotal').textContent = '—';
    }
  } catch(e) { console.warn('loadResults:', e); }
}

// ── Disparar análise manual ───────────────────────────────
async function startRun() {
  const headless = document.getElementById('chkHeadless').checked;
  const btn      = document.getElementById('btnRun');
  btn.disabled   = true;
  btn.textContent = 'Iniciando...';

  try {
    const r = await fetch('/api/run', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({headless, limiar: 0.10, slot: _slot}),
    });
    const j = await r.json();
    if (j.error) { alert(j.error); btn.disabled=false; updateDateInfo(); return; }
  } catch(e) { alert('Erro: '+e); btn.disabled=false; updateDateInfo(); return; }

  document.getElementById('progressBox').classList.add('visible');
  startPolling();
}

// ── Polling de status ─────────────────────────────────────
function startPolling() {
  if (_poll) clearInterval(_poll);
  _poll = setInterval(pollStatus, 2000);
}

async function pollStatus() {
  try {
    const r = await fetch('/api/status');
    const s = await r.json();

    document.getElementById('nextRun').textContent = nextRunLabel();

    const running  = s.status === 'running';
    _isRunning     = running;

    document.getElementById('progLabel').textContent = s.current || '...';
    const p = s.total>0 ? Math.round((s.progress/s.total)*100) : 0;
    document.getElementById('progPct').textContent = p+'%';
    document.getElementById('progBar').style.width = p+'%';

    if (s.log && s.log.length) {
      const el = document.getElementById('logArea');
      el.innerHTML = s.log.map(l=>`<div>${l}</div>`).join('');
      el.scrollTop = el.scrollHeight;
    }

    if (running) {
      const runSlot = s.last_slot || 'hoje';
      setPill('running', `Analisando ${runSlot === 'amanha' ? 'Amanhã' : 'Hoje'}...`);
    } else if (s.status === 'done') {
      setPill('done', `Concluido ${s.last_run||''}`);
    } else if (s.status === 'error') {
      setPill('error', 'Erro');
    } else {
      setPill('idle', `Aguardando`);
    }

    if (s.status==='done' || s.status==='error') {
      clearInterval(_poll); _poll=null;
      const btn = document.getElementById('btnRun');
      btn.disabled = false;
      updateDateInfo();

      if (s.status==='done') {
        await loadResults();
        document.getElementById('progressBox').classList.remove('visible');
      }
    }
  } catch(e) { console.warn('pollStatus:', e); }
}

// ── Init ──────────────────────────────────────────────────
updateDateInfo();
document.getElementById('nextRun').textContent = nextRunLabel();
loadResults();

// Polling leve a cada 30s
setInterval(() => {
  if (!_isRunning) {
    fetch('/api/status').then(r=>r.json()).then(s=>{
      if (s.status==='running') { startPolling(); return; }
      document.getElementById('nextRun').textContent = nextRunLabel();
      if (s.status==='done') setPill('done', `Concluido ${s.last_run||''}`);
      else setPill('idle', 'Aguardando');
    }).catch(()=>{});
  }
}, 30000);
</script>
</body>
</html>"""


# =============================================================================
# Entry point
# =============================================================================
if __name__ == "__main__":
    _carregar_cache()
    threading.Thread(target=_scheduler, daemon=True).start()
    print(f"\n  Lay Analyzer — http://localhost:5001")
    print(f"  Auto-run Hoje:  {config.AUTO_RUN_HORA:02d}:{config.AUTO_RUN_MINUTO:02d}")
    print(f"  Auto-run Amanha: {config.AUTO_RUN_AMANHA_HORA:02d}:{config.AUTO_RUN_AMANHA_MINUTO:02d}\n")
    app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False, threaded=True)
