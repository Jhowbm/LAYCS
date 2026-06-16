"""
debug_selecoes.py — Inspeciona a estrutura H2H de jogos de seleções nacionais.

Abre o Firefox visível, busca o jogo EUA vs Paraguai (ou o primeiro jogo
internacional disponível) e inspeciona todos os seletores CSS do H2H.
"""
import re
import sys
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

from scraper import setup_driver, _aceitar_cookies, coletar_jogos_do_dia

TIMES_SELECAO = [
    "EUA", "Paraguai", "Brasil", "Argentina", "Uruguai", "Colombia",
    "Chile", "Peru", "Venezuela", "Bolivia", "Equador", "Mexico",
    "Portugal", "Espanha", "Franca", "Alemanha", "Italia", "Ingla",
    "Copa", "Nations", "Eliminatoria",
]

driver = setup_driver(headless=False)

print("Coletando jogos do dia...")
jogos = coletar_jogos_do_dia(driver)

if not jogos:
    print("ERRO: Nenhum jogo encontrado hoje.")
    driver.quit()
    sys.exit(1)

print(f"{len(jogos)} jogos encontrados:")
for i, j in enumerate(jogos):
    print(f"  [{i}] {j['hora']} {j['time_casa']} vs {j['time_fora']}")

# Tenta achar jogo de seleção
jogo_alvo = None
for j in jogos:
    nomes = f"{j['time_casa']} {j['time_fora']}".upper()
    if any(s.upper() in nomes for s in TIMES_SELECAO):
        jogo_alvo = j
        print(f"\nJogo de selecao encontrado: {j['time_casa']} vs {j['time_fora']}")
        break

if not jogo_alvo:
    jogo_alvo = jogos[0]
    print(f"\nNenhum jogo de selecao identificado. Usando: {jogo_alvo['time_casa']} vs {jogo_alvo['time_fora']}")

url_h2h = jogo_alvo["url"]
print(f"URL: {url_h2h}")

# Navega para a aba H2H
print("\nAbrindo aba H2H...")
driver.get(url_h2h)
_aceitar_cookies(driver)

# Aguarda skeleton aparecer
print("Aguardando elementos h2h no DOM...")
try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='h2h']"))
    )
    print("  Elemento h2h presente no DOM.")
except TimeoutException:
    print("  TIMEOUT: nenhum elemento h2h encontrado em 20s — pode ser que o H2H nao exista para esse jogo.")

# Aguarda skeleton desaparecer
print("Aguardando skeleton desaparecer...")
try:
    WebDriverWait(driver, 20).until_not(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__skeleton"))
    )
    print("  Skeleton desapareceu — dados carregados.")
except TimeoutException:
    print("  Skeleton ainda presente ou nao existia.")

time.sleep(2)

soup = BeautifulSoup(driver.page_source, "html.parser")

# ── 1. Classes com 'h2h' ──────────────────────────────────────────────
print("\n" + "="*60)
print("1. CLASSES COM 'h2h' NO HTML")
print("="*60)
classes_h2h = {}
for tag in soup.find_all(True):
    for cls in tag.get("class", []):
        if "h2h" in cls.lower() and cls not in classes_h2h:
            classes_h2h[cls] = {"tag": tag.name, "texto": tag.get_text(strip=True)[:60]}

if classes_h2h:
    for cls, info in sorted(classes_h2h.items()):
        print(f"  .{cls:40s} tag={info['tag']:6s} '{info['texto']}'")
else:
    print("  NENHUMA classe com 'h2h' encontrada na pagina!")
    print("  Isso confirma que jogos de selecao usam estrutura diferente.")

# ── 2. data-testid com 'h2h' ou 'score' ──────────────────────────────
print("\n" + "="*60)
print("2. data-testid COM 'h2h' OU 'score'")
print("="*60)
encontrou_testid = False
for tag in soup.find_all(attrs={"data-testid": True}):
    tid = tag.get("data-testid", "")
    if "h2h" in tid.lower() or "score" in tid.lower() or "table" in tid.lower():
        print(f"  [{tid}] tag={tag.name} text='{tag.get_text(strip=True)[:60]}'")
        encontrou_testid = True
if not encontrou_testid:
    print("  Nenhum data-testid relevante encontrado.")

# ── 3. Seletores candidatos testados ─────────────────────────────────
print("\n" + "="*60)
print("3. SELETORES CANDIDATOS")
print("="*60)
candidatos = [
    ".h2h__section", ".h2h__row", ".h2h__result", ".h2h__event",
    "[class*='h2h']",
    "[class*='H2H']",
    "[data-testid*='h2h']",
    "[data-testid*='H2H']",
    # Possíveis seletores para seleções
    ".headToHead",
    "[class*='headToHead']",
    "[class*='head-to-head']",
    "[class*='standings']",
    ".matchHistoryRow",
    "[class*='matchHistory']",
    "[class*='teamHistory']",
    "[class*='history']",
    "[class*='lastMatches']",
]
for sel in candidatos:
    els = soup.select(sel)
    status = f"{len(els)} elemento(s)"
    print(f"  '{sel:45s}' -> {status}")
    if els and len(els) <= 4:
        for el in els[:2]:
            print(f"      tag={el.name} class={el.get('class',[])} text='{el.get_text(strip=True)[:50]}'")

# ── 4. Placares no HTML ───────────────────────────────────────────────
print("\n" + "="*60)
print("4. PLACARES ENCONTRADOS (formato X:Y ou X-Y)")
print("="*60)
placares_colon = soup.find_all(string=re.compile(r"^\d+:\d+$"))
placares_dash  = soup.find_all(string=re.compile(r"^\d+ - \d+$"))
todos_placares = placares_colon + placares_dash

if todos_placares:
    for p in todos_placares[:20]:
        parent = p.parent
        gp = parent.parent if parent else None
        print(f"  '{p.strip()}' em tag={parent.name} class={parent.get('class',[])} | pai={gp.get('class',[]) if gp else []}")
else:
    print("  Nenhum placar no formato X:Y encontrado.")
    # Tenta wcl-tableScore
    scores = soup.find_all(attrs={"data-testid": "wcl-tableScore"})
    print(f"  wcl-tableScore: {len(scores)} spans encontrados")
    for s in scores[:10]:
        print(f"    texto='{s.get_text(strip=True)}' pai-class={s.parent.get('class',[])} avo-class={s.parent.parent.get('class',[]) if s.parent.parent else []}")

# ── 5. Estrutura geral da aba H2H (primeiros 30 divs) ─────────────────
print("\n" + "="*60)
print("5. PRIMEIROS 30 DIVs/SECTIONs COM CLASSES NA AREA H2H")
print("="*60)
# Tenta encontrar o container do H2H pelo URL da página
container = (
    soup.find(class_=re.compile(r"h2h", re.I)) or
    soup.find(attrs={"data-testid": re.compile(r"h2h", re.I)}) or
    soup.find("main") or
    soup.find("body")
)
if container:
    print(f"  Container: tag={container.name} class={container.get('class', [])}")
    filhos = container.find_all(["div", "section", "article", "ul", "li"], limit=30)
    for el in filhos[:30]:
        classes = el.get("class", [])
        tid = el.get("data-testid", "")
        texto = el.get_text(strip=True)[:40]
        if classes or tid:
            print(f"  tag={el.name:8s} class={str(classes):50s} testid={tid:30s} '{texto}'")

# ── 6. URL atual (pode ter redirecionado) ─────────────────────────────
print("\n" + "="*60)
print("6. URL FINAL APÓS NAVEGACAO")
print("="*60)
print(f"  {driver.current_url}")

print("\n" + "="*60)
print("NAVEGADOR ABERTO — inspecione com F12 para confirmar seletores.")
print("Pressione ENTER para fechar.")
print("="*60)
input()

driver.quit()
print("Debug concluido.")
