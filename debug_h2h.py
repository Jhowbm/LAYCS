"""
debug_h2h.py — Inspeciona a estrutura HTML da aba H2H de um jogo de hoje.

Coleta o primeiro jogo agendado do dia, navega até a aba H2H e espera
o skeleton desaparecer antes de inspecionar os seletores.
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

driver = setup_driver(headless=False)

print("Coletando jogos do dia...")
jogos = coletar_jogos_do_dia(driver)

if not jogos:
    print("ERRO: Nenhum jogo encontrado hoje. Abortando.")
    driver.quit()
    sys.exit(1)

jogo = jogos[0]
url_h2h = jogo["url"]
print(f"Jogo: {jogo['time_casa']} vs {jogo['time_fora']}")
print(f"URL H2H: {url_h2h}")

_aceitar_cookies(driver)
driver.get(url_h2h)
_aceitar_cookies(driver)

print("Aguardando skeleton H2H aparecer...")
try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='h2h']"))
    )
    print("Skeleton encontrado. Aguardando dados carregarem...")
except TimeoutException:
    print("Nenhum elemento h2h encontrado em 20s.")

# Aguarda skeleton desaparecer (dados reais carregados)
try:
    WebDriverWait(driver, 20).until_not(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__skeleton"))
    )
    print("Skeleton desapareceu — dados reais carregados.")
except TimeoutException:
    print("Skeleton ainda presente após 20s — tentando inspecionar mesmo assim.")

# Pausa extra para garantir renderização completa
time.sleep(2)

soup = BeautifulSoup(driver.page_source, "html.parser")

# Testa seletores candidatos
print("\n=== Testando seletores H2H ===")
candidatos = [
    ".h2h__section", ".h2h__row", ".h2h__result",
    "[class*='h2h']", "[data-testid*='h2h']",
    ".h2h", "[class*='H2H']",
]
for sel in candidatos:
    els = soup.select(sel)
    print(f"  '{sel}' -> {len(els)} elementos")
    if els and len(els) <= 5:
        for el in els[:3]:
            print(f"    tag={el.name} class={el.get('class',[])} text={el.get_text(strip=True)[:60]}")

# Mostra TODAS as classes que contêm 'h2h'
print("\n=== Todas as classes com 'h2h' no HTML ===")
classes_h2h = {}
for tag in soup.find_all(True):
    for cls in tag.get("class", []):
        if "h2h" in cls.lower():
            if cls not in classes_h2h:
                classes_h2h[cls] = {"tag": tag.name, "texto": tag.get_text(strip=True)[:50]}
for cls, info in sorted(classes_h2h.items()):
    print(f"  .{cls} (tag={info['tag']}) '{info['texto']}'")

# Mostra data-testid com 'h2h' ou 'score'
print("\n=== data-testid com 'h2h' ou 'score' ===")
for tag in soup.find_all(attrs={"data-testid": True}):
    tid = tag.get("data-testid", "")
    if "h2h" in tid.lower() or "score" in tid.lower():
        print(f"  [{tid}] tag={tag.name} text='{tag.get_text(strip=True)[:50]}'")

# Procura placares no formato X:Y ou X - Y
print("\n=== Placares encontrados (X:Y) ===")
placares = soup.find_all(string=re.compile(r"^\d:\d$"))
print(f"  {len(placares)} encontrados:")
for p in placares[:15]:
    parent = p.parent
    gp = parent.parent if parent else None
    print(f"    '{p.strip()}' — tag={parent.name} class={parent.get('class',[])} | parent-class={gp.get('class',[]) if gp else []}")

# Dump das primeiras 60 classes únicas na página (para encontrar padrão)
print("\n=== Primeiras 60 classes únicas na página ===")
todas_classes = set()
for tag in soup.find_all(True):
    for cls in tag.get("class", []):
        todas_classes.add(cls)
h2h_classes = sorted(c for c in todas_classes if "h2h" in c.lower())
outras = sorted(c for c in todas_classes if "h2h" not in c.lower())[:60 - len(h2h_classes)]
print("  [H2H]:", h2h_classes)
print("  [outras]:", outras)

driver.quit()
print("\nDebug concluido.")
