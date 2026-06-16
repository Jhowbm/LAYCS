# =============================================================================
# analyzer.py — Módulo de análise estatística
# =============================================================================

import logging
from datetime import date
import re

import pandas as pd

import config

logger = logging.getLogger(__name__)

# Cores ANSI para destaque visual
class Cores:
    AMARELO = "\033[93m"      # Amarelo brilhante
    VERDE = "\033[92m"       # Verde brilhante
    VERMELHO = "\033[91m"    # Vermelho brilhante
    AZUL = "\033[94m"        # Azul brilhante
    RESET = "\033[0m"        # Reset cor
    BOLD = "\033[1m"         # Negrito

# Times/Campeonatos da Copa do Mundo para identificação
COPA_DO_MUNDO_PALAVRAS = [
    "copa do mundo", "world cup", "copa mundial",
    "seleção", "national team", "nationalelf",
    "argentina", "brasil", "france", "alemanha", "espanha",
    "inglaterra", "portugal", "holanda", "bélgica", "croácia",
    "marrocos", "japão", "coreia", "uruguai", "colômbia",
    "méxico", "eua", "usa", "estados unidos"
]

def é_copa_do_mundo(time_casa: str, time_fora: str) -> bool:
    """
    Identifica se é um jogo da Copa do Mundo baseado nos nomes dos times.
    """
    texto_completo = f"{time_casa.lower()} {time_fora.lower()}"
    
    for palavra in COPA_DO_MUNDO_PALAVRAS:
        if palavra.lower() in texto_completo:
            return True
    
    return False


# =============================================================================
# CÁLCULO DE VALOR ESPERADO (EV)
# =============================================================================
def calcular_probabilidade_estimada(freq_historica, odd_placar, media_gols, fator_contexto=1.0):
    """
    Calcula probabilidade estimada combinando:
    - Frequência histórica (peso 0.4)
    - Probabilidade implícita das odds (peso 0.4) 
    - Contexto do jogo (peso 0.2)
    
    fator_contexto: >1.0 aumenta prob (jogo fechado), <1.0 diminui (jogo aberto)
    """
    # Probabilidade implícita das odds (se disponível)
    prob_odds = (1 / odd_placar) if odd_placar and odd_placar > 0 else None
    
    # Probabilidade baseada em média de gols
    # Mais gols = menor prob de placar exato baixo
    prob_gols = max(0.01, min(0.15, 0.10 / (media_gols / 2))) if media_gols > 0 else 0.08
    
    # Combinação ponderada
    pesos = []
    valores = []
    
    if freq_historica is not None:
        pesos.append(0.4)
        valores.append(freq_historica)
    
    if prob_odds is not None:
        pesos.append(0.4)
        valores.append(prob_odds)
    else:
        pesos.append(0.4)
        valores.append(prob_gols)
    
    pesos.append(0.2)
    valores.append(prob_gols * fator_contexto)
    
    # Média ponderada
    prob_estimada = sum(p * v for p, v in zip(pesos, valores)) / sum(pesos)
    
    return round(min(max(prob_estimada, 0.01), 0.30), 4)  # Limita entre 1% e 30%


def calcular_fator_contexto(freqs: dict) -> float:
    """
    Calcula fator de contexto baseado em características do jogo:
    - Defesas fortes aumentam prob de placar baixo (>1.0)
    - Média de gols alta diminui prob de placar baixo (<1.0)
    - Cenário ideal (aberto) diminui prob (<1.0)
    """
    media_gols = freqs.get("media_gols_confronto", 2.0)
    clean_sheets_casa = freqs.get("clean_sheets_casa", 0.0)
    clean_sheets_fora = freqs.get("clean_sheets_fora", 0.0)
    cenario_ideal = freqs.get("cenario_ideal", False)
    
    # Fator base
    fator = 1.0
    
    # Defesas fortes aumentam prob de placar baixo
    if clean_sheets_casa > 0.5:
        fator += 0.2
    if clean_sheets_fora > 0.5:
        fator += 0.1
    
    # Média de gols alta diminui prob
    if media_gols > 2.5:
        fator -= 0.3
    elif media_gols < 1.5:
        fator += 0.3
    
    # Cenário ideal (jogo aberto) diminui prob
    if cenario_ideal:
        fator -= 0.2
    
    return round(max(0.5, min(fator, 1.5)), 2)


def calcular_ev_lay(odd_placar, prob_ocorrencia):
    """
    Calcula Valor Esperado (EV) de uma aposta Lay:
    
    EV = (Prob_Não_Ocorrencia * Lucro) - (Prob_Ocorrencia * Liability)
    
    odd_placar: Odd do placar exato (ex: 10.0)
    prob_ocorrencia: Probabilidade do placar ocorrer (ex: 0.08)
    
    Retorna: (EV, retorno_porcentagem, liability)
    """
    if not odd_placar or odd_placar <= 1 or not prob_ocorrencia:
        return (0.0, 0.0, 0.0)
    
    liability = odd_placar - 1  # Quanto pode perder
    prob_nao_ocorrencia = 1 - prob_ocorrencia
    lucro = 1.0  # Stake unitário
    
    ev = (prob_nao_ocorrencia * lucro) - (prob_ocorrencia * liability)
    retorno_porcentagem = (1 / odd_placar) * 100
    
    return (round(ev, 4), round(retorno_porcentagem, 2), liability)


# =============================================================================
# FREQUÊNCIA DE PLACAR EXATO
# =============================================================================
def calcular_frequencia_placar(resultados: list[tuple], placar_alvo: tuple) -> float:
    """Proporção de vezes que um placar específico ocorreu. Retorna 0.0 se vazio."""
    if not resultados:
        return 0.0
    ocorrencias = sum(1 for r in resultados if r == placar_alvo)
    return round(ocorrencias / len(resultados), 4)


def calcular_frequencias_jogo(dados_jogo: dict, odds: dict = None) -> dict:
    """
    Calcula todas as métricas para um jogo a partir dos dados H2H coletados.

    Retorna dict com frequências de placar, médias de gols, clean sheets,
    indicadores de cenário ideal para Lay e métricas de Valor Esperado.
    """
    h2h  = dados_jogo.get("h2h_confrontos", [])
    casa = dados_jogo.get("h2h_casa", [])
    fora = dados_jogo.get("h2h_fora", [])
    
    if odds is None:
        odds = {}

    # ── Frequências de placar ──────────────────────────────────────────────
    f_1x0_h2h  = calcular_frequencia_placar(h2h,  (1, 0))
    f_1x0_casa = calcular_frequencia_placar(casa, (1, 0))
    f_1x0_fora = calcular_frequencia_placar(fora, (1, 0))
    f_0x1_h2h  = calcular_frequencia_placar(h2h,  (0, 1))
    f_0x1_casa = calcular_frequencia_placar(casa, (0, 1))
    f_0x1_fora = calcular_frequencia_placar(fora, (0, 1))

    def media_grupos(*grupos):
        """Média ignorando grupos vazios."""
        valores = [v for v, src in grupos if src]
        return round(sum(valores) / len(valores), 4) if valores else 0.0

    freq_comb_1x0 = media_grupos(
        (f_1x0_h2h, h2h), (f_1x0_casa, casa), (f_1x0_fora, fora)
    )
    freq_comb_0x1 = media_grupos(
        (f_0x1_h2h, h2h), (f_0x1_casa, casa), (f_0x1_fora, fora)
    )
    freq_total = round(freq_comb_1x0 + freq_comb_0x1, 4)

    # ── Média de gols e clean sheets (confrontos H2H diretos) ──────────────
    if h2h:
        media_gols      = round(sum(g1 + g2 for g1, g2 in h2h) / len(h2h), 2)
        media_gols_casa = round(sum(g1       for g1, g2 in h2h) / len(h2h), 2)
        media_gols_fora = round(sum(g2       for g1, g2 in h2h) / len(h2h), 2)
        clean_sheets_casa = round(sum(1 for _, g2 in h2h if g2 == 0) / len(h2h), 4)
        clean_sheets_fora = round(sum(1 for g1, _ in h2h if g1 == 0) / len(h2h), 4)
    else:
        media_gols = media_gols_casa = media_gols_fora = 0.0
        clean_sheets_casa = clean_sheets_fora = 0.0

    # Cenário ideal: ambos times marcam historicamente e o jogo tende a ter gols
    cenario_ideal = (
        media_gols_casa >= 1.0
        and media_gols_fora >= 1.0
        and media_gols >= 2.5
    )
    
    # ── Cálculos de Valor Esperado (EV) ─────────────────────────────────────
    # Criar dict temporário com as métricas para calcular fator de contexto
    freqs_temp = {
        "media_gols_confronto": media_gols,
        "clean_sheets_casa": clean_sheets_casa,
        "clean_sheets_fora": clean_sheets_fora,
        "cenario_ideal": cenario_ideal,
    }
    fator_contexto = calcular_fator_contexto(freqs_temp)
    
    # Odds do placar exato
    odd_cs_1x0 = odds.get("odd_cs_1x0")
    odd_cs_0x1 = odds.get("odd_cs_0x1")
    
    # Probabilidades estimadas para cada placar
    prob_est_1x0 = calcular_probabilidade_estimada(freq_comb_1x0, odd_cs_1x0, media_gols, fator_contexto)
    prob_est_0x1 = calcular_probabilidade_estimada(freq_comb_0x1, odd_cs_0x1, media_gols, fator_contexto)
    
    # Valor Esperado para cada Lay
    ev_1x0, retorno_1x0, liability_1x0 = calcular_ev_lay(odd_cs_1x0, prob_est_1x0)
    ev_0x1, retorno_0x1, liability_0x1 = calcular_ev_lay(odd_cs_0x1, prob_est_0x1)

    return {
        "n_jogos_h2h":           len(h2h),
        "freq_1x0_h2h":          f_1x0_h2h,
        "freq_0x1_h2h":          f_0x1_h2h,
        "freq_1x0_casa":         f_1x0_casa,
        "freq_0x1_casa":         f_0x1_casa,
        "freq_1x0_fora":         f_1x0_fora,
        "freq_0x1_fora":         f_0x1_fora,
        "freq_combinada_1x0":    freq_comb_1x0,
        "freq_combinada_0x1":    freq_comb_0x1,
        "freq_combinada_total":  freq_total,
        "media_gols_confronto":  media_gols,
        "media_gols_casa_h2h":   media_gols_casa,
        "media_gols_fora_h2h":   media_gols_fora,
        "clean_sheets_casa":     clean_sheets_casa,
        "clean_sheets_fora":     clean_sheets_fora,
        "cenario_ideal":         cenario_ideal,
        # Métricas de Valor Esperado
        "fator_contexto":        fator_contexto,
        "prob_estimada_1x0":     prob_est_1x0,
        "prob_estimada_0x1":     prob_est_0x1,
        "ev_1x0":                ev_1x0,
        "ev_0x1":                ev_0x1,
        "retorno_1x0":           retorno_1x0,
        "retorno_0x1":           retorno_0x1,
        "liability_1x0":         liability_1x0,
        "liability_0x1":         liability_0x1,
    }


# =============================================================================
# CLASSIFICAÇÃO MULTI-CRITÉRIO
# =============================================================================
def classificar_oportunidade(
    freqs: dict,
    odds:  dict,
    limiar: float = config.LIMIAR_OPORTUNIDADE,
    retorno_minimo: float = 5.0,
) -> tuple[str, str]:
    """
    Classifica um jogo como oportunidade de Lay com base em Valor Esperado (EV):

      1. Histórico H2H suficiente (>= MIN_H2H_JOGOS)
      2. Valor Esperado (EV) positivo para pelo menos um placar
      3. Retorno % stake > retorno_minimo (padrão: 5%)
      4. Odds disponíveis para cálculo de EV

    Retorna:
        tuple (classificacao, tipo_lay)
        
        classificacao:
            "LAY_VALOR"       — EV positivo + retorno >5% (melhor oportunidade)
            "LAY_MONITORAR"   — EV positivo mas retorno baixo ou risco moderado
            "DESCARTAR"       — EV negativo ou sem odds
            "SEM_DADOS"       — histórico H2H insuficiente
            
        tipo_lay:
            "LAY_1X0"   — melhor valor no Lay 1x0
            "LAY_0X1"   — melhor valor no Lay 0x1
            "LAY_AMBOS" — ambos com valor positivo
            "NENHUM"    — nenhum com valor positivo
    """
    n_jogos = freqs.get("n_jogos_h2h", 0)
    
    # Métricas de EV
    ev_1x0 = freqs.get("ev_1x0", 0.0)
    ev_0x1 = freqs.get("ev_0x1", 0.0)
    retorno_1x0 = freqs.get("retorno_1x0", 0.0)
    retorno_0x1 = freqs.get("retorno_0x1", 0.0)
    
    # Critério 0 — dados suficientes
    if n_jogos < config.MIN_H2H_JOGOS:
        return "SEM_DADOS", "NENHUM"
    
    # Verificar qual Lay tem melhor valor
    ev_1x0_positivo = ev_1x0 > 0 and retorno_1x0 > retorno_minimo
    ev_0x1_positivo = ev_0x1 > 0 and retorno_0x1 > retorno_minimo
    
    # Escolher o melhor Lay
    if ev_1x0_positivo and ev_0x1_positivo:
        # Ambos têm valor positivo - escolher o maior EV
        if ev_1x0 >= ev_0x1:
            tipo_lay = "LAY_1X0"
        else:
            tipo_lay = "LAY_0X1"
        classificacao = "LAY_VALOR"
    elif ev_1x0_positivo:
        tipo_lay = "LAY_1X0"
        classificacao = "LAY_VALOR"
    elif ev_0x1_positivo:
        tipo_lay = "LAY_0X1"
        classificacao = "LAY_VALOR"
    elif ev_1x0 > 0 or ev_0x1 > 0:
        # EV positivo mas retorno abaixo do mínimo
        if ev_1x0 >= ev_0x1:
            tipo_lay = "LAY_1X0"
        else:
            tipo_lay = "LAY_0X1"
        classificacao = "LAY_MONITORAR"
    else:
        tipo_lay = "NENHUM"
        classificacao = "DESCARTAR"
    
    return classificacao, tipo_lay


# =============================================================================
# CONSTRUÇÃO DO DATAFRAME
# =============================================================================
def construir_dataframe(lista_jogos: list[dict], data_override: str = None) -> pd.DataFrame:
    """Monta DataFrame padronizado com todos os dados coletados e métricas.

    data_override: data dos jogos no formato YYYY-MM-DD (ex: amanhã).
                   Se None, usa date.today().
    """
    data_str = data_override or date.today().isoformat()
    linhas = []

    for item in lista_jogos:
        jogo    = item.get("jogo", {})
        odds    = item.get("odds", {})
        freqs   = item.get("freqs", {})
        classif = item.get("classificacao", "N/A")
        tipo_lay = item.get("tipo_lay", "NENHUM")

        odd_over = odds.get("odd_over_1_5")
        prob_over = round(1 / odd_over, 4) if odd_over else None
        
        # Identificar se é jogo da Copa do Mundo
        time_casa = jogo.get("time_casa", "")
        time_fora = jogo.get("time_fora", "")
        is_copa = é_copa_do_mundo(time_casa, time_fora)

        linhas.append({
            # Identificação
            "data":       data_str,
            "hora":       jogo.get("hora", ""),
            "time_casa":  jogo.get("time_casa", ""),
            "time_fora":  jogo.get("time_fora", ""),
            "is_copa_do_mundo": is_copa,

            # H2H — confrontos diretos
            "n_jogos_h2h":           freqs.get("n_jogos_h2h", 0),
            "freq_1x0_h2h":          freqs.get("freq_1x0_h2h", 0.0),
            "freq_0x1_h2h":          freqs.get("freq_0x1_h2h", 0.0),
            "freq_combinada_1x0":    freqs.get("freq_combinada_1x0", 0.0),
            "freq_combinada_0x1":    freqs.get("freq_combinada_0x1", 0.0),
            "freq_combinada_total":  freqs.get("freq_combinada_total", 0.0),

            # Gols e clean sheets
            "media_gols_confronto":  freqs.get("media_gols_confronto", 0.0),
            "media_gols_casa_h2h":   freqs.get("media_gols_casa_h2h", 0.0),
            "media_gols_fora_h2h":   freqs.get("media_gols_fora_h2h", 0.0),
            "clean_sheets_casa":     freqs.get("clean_sheets_casa", 0.0),
            "clean_sheets_fora":     freqs.get("clean_sheets_fora", 0.0),
            "cenario_ideal":         freqs.get("cenario_ideal", False),

            # Odds 1x2
            "odd_1": odds.get("odd_1"),
            "odd_x": odds.get("odd_x"),
            "odd_2": odds.get("odd_2"),

            # Odds placar exato
            "odd_cs_1x0": odds.get("odd_cs_1x0"),
            "odd_cs_0x1": odds.get("odd_cs_0x1"),

            # Over 1.5
            "odd_over_1_5":           odd_over,
            "prob_implicita_over_1_5": prob_over,

            # Métricas de Valor Esperado
            "fator_contexto":        freqs.get("fator_contexto", 1.0),
            "prob_estimada_1x0":     freqs.get("prob_estimada_1x0", 0.0),
            "prob_estimada_0x1":     freqs.get("prob_estimada_0x1", 0.0),
            "ev_1x0":                freqs.get("ev_1x0", 0.0),
            "ev_0x1":                freqs.get("ev_0x1", 0.0),
            "retorno_1x0":           freqs.get("retorno_1x0", 0.0),
            "retorno_0x1":           freqs.get("retorno_0x1", 0.0),
            "liability_1x0":         freqs.get("liability_1x0", 0.0),
            "liability_0x1":         freqs.get("liability_0x1", 0.0),

            # Classificação final
            "classificacao": classif,
            "tipo_lay":      tipo_lay,
        })

    df = pd.DataFrame(linhas)

    ordem = {"LAY_VALOR": 0, "LAY_MONITORAR": 1, "LAY_OPORTUNIDADE": 2, "MONITORAR": 3, "DESCARTAR": 4, "SEM_DADOS": 5, "N/A": 6}
    df["_ord"] = df["classificacao"].map(ordem).fillna(6)
    df = df.sort_values(["_ord", "freq_combinada_total"]).drop(columns=["_ord"])
    df = df.reset_index(drop=True)

    return df


# =============================================================================
# EXPORTAÇÃO
# =============================================================================
def exportar_dados(df: pd.DataFrame, prefixo: str = "flashscore_lay",
                   data_override: str = None) -> tuple[str, str]:
    """Exporta para CSV e JSON. Retorna (caminho_csv, caminho_json)."""
    hoje         = data_override or date.today().isoformat()
    caminho_csv  = f"{prefixo}_{hoje}.csv"
    caminho_json = f"{prefixo}_{hoje}.json"

    df.to_csv(caminho_csv, index=False, encoding="utf-8-sig")
    df.to_json(caminho_json, orient="records", force_ascii=False, indent=2)

    logger.info(f"Exportado: {caminho_csv} | {caminho_json}")
    return caminho_csv, caminho_json


# =============================================================================
# RESUMO NO TERMINAL
# =============================================================================
def exibir_resumo(df: pd.DataFrame, limiar: float) -> None:
    lay_valor = df[df["classificacao"] == "LAY_VALOR"]
    lay_monitorar = df[df["classificacao"] == "LAY_MONITORAR"]
    oportunidades = df[df["classificacao"] == "LAY_OPORTUNIDADE"]
    monitorar = df[df["classificacao"] == "MONITORAR"]
    sem_dados = df[df["classificacao"] == "SEM_DADOS"]

    print("\n" + "=" * 78)
    print(f"  ANÁLISE LAY 1x0 / 0x1 — VALOR ESPERADO (EV+) — {date.today().isoformat()}")
    print(f"  Retorno mínimo: 5.0%  |  Mín. H2H: {config.MIN_H2H_JOGOS} jogos")
    print("=" * 78)
    print(f"\n  Total analisados  : {len(df)}")
    print(f"  LAY_VALOR         : {len(lay_valor)} ✅ (EV+ + retorno >5%)")
    print(f"  LAY_MONITORAR     : {len(lay_monitorar)} ⚠️  (EV+ mas retorno baixo)")
    print(f"  LAY_OPORTUNIDADE  : {len(oportunidades)} (método antigo)")
    print(f"  MONITORAR         : {len(monitorar)} (método antigo)")
    print(f"  SEM_DADOS         : {len(sem_dados)}")

    if not lay_valor.empty:
        print("\n  " + Cores.BOLD + Cores.AMARELO + "🏆 JOGOS DA COPA DO MUNDO - LAY VALOR 🏆" + Cores.RESET)
        print("  ──────────────────────────────────────────────────────────────────")
        
        # Separar jogos da Copa do Mundo
        copa_games = []
        outros_games = []
        
        for _, r in lay_valor.iterrows():
            if é_copa_do_mundo(r['time_casa'], r['time_fora']):
                copa_games.append(r)
            else:
                outros_games.append(r)
        
        # Mostrar jogos da Copa do Mundo primeiro em amarelo
        if copa_games:
            print("\n  " + Cores.BOLD + Cores.AMARELO + "⭐ COPA DO MUNDO ⭐" + Cores.RESET)
            for r in copa_games:
                tipo_lay = r.get('tipo_lay', 'NENHUM')
                ev = r.get(f'ev_{tipo_lay.lower().replace("lay_", "")}', 0.0)
                retorno = r.get(f'retorno_{tipo_lay.lower().replace("lay_", "")}', 0.0)
                prob = r.get(f'prob_estimada_{tipo_lay.lower().replace("lay_", "")}', 0.0)
                
                # Indicação clara do Lay
                if tipo_lay == "LAY_1X0":
                    indicacao = Cores.VERDE + "► LAY 1X0 RECOMENDADO" + Cores.RESET
                elif tipo_lay == "LAY_0X1":
                    indicacao = Cores.VERDE + "► LAY 0X1 RECOMENDADO" + Cores.RESET
                else:
                    indicacao = f"► {tipo_lay}"
                
                print(
                    f"  {Cores.AMARELO}{r['hora']:5s}  {r['time_casa'][:15]:<15s} vs {r['time_fora'][:15]:<15s}{Cores.RESET}"
                    f"  {indicacao}"
                    f"  EV={ev:+.3f}"
                    f"  Retorno={retorno:.1f}%"
                    f"  Prob={prob:.1%}"
                )
        
        # Mostrar outros jogos
        if outros_games:
            print("\n  OUTROS JOGOS:")
            for r in outros_games:
                tipo_lay = r.get('tipo_lay', 'NENHUM')
                ev = r.get(f'ev_{tipo_lay.lower().replace("lay_", "")}', 0.0)
                retorno = r.get(f'retorno_{tipo_lay.lower().replace("lay_", "")}', 0.0)
                prob = r.get(f'prob_estimada_{tipo_lay.lower().replace("lay_", "")}', 0.0)
                
                # Indicação clara do Lay
                if tipo_lay == "LAY_1X0":
                    indicacao = Cores.VERDE + "► LAY 1X0" + Cores.RESET
                elif tipo_lay == "LAY_0X1":
                    indicacao = Cores.VERDE + "► LAY 0X1" + Cores.RESET
                else:
                    indicacao = f"► {tipo_lay}"
                
                print(
                    f"  {r['hora']:5s}  {r['time_casa'][:15]:<15s} vs {r['time_fora'][:15]:<15s}"
                    f"  {indicacao}"
                    f"  EV={ev:+.3f}"
                    f"  Retorno={retorno:.1f}%"
                    f"  Prob={prob:.1%}"
                )

    if not lay_monitorar.empty:
        print("\n  ── LAY MONITORAR (EV+ mas Retorno <5%) ───────────────────────────────────")
        for _, r in lay_monitorar.iterrows():
            tipo_lay = r.get('tipo_lay', 'NENHUM')
            ev = r.get(f'ev_{tipo_lay.lower().replace("lay_", "")}', 0.0)
            retorno = r.get(f'retorno_{tipo_lay.lower().replace("lay_", "")}', 0.0)
            
            # Indicação do Lay
            if tipo_lay == "LAY_1X0":
                indicacao = "► LAY 1X0"
            elif tipo_lay == "LAY_0X1":
                indicacao = "► LAY 0X1"
            else:
                indicacao = f"► {tipo_lay}"
            
            print(
                f"  {r['hora']:5s}  {r['time_casa'][:15]:<15s} vs {r['time_fora'][:15]:<15s}"
                f"  {indicacao}"
                f"  EV={ev:+.3f}"
                f"  Retorno={retorno:.1f}%"
            )

    print("=" * 78 + "\n")
