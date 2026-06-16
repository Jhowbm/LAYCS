"""
debug_rows.py — Inspeciona as primeiras 15 linhas .event__match do Flashscore.
Mostra: hora_txt, classes, nome dos times e id do elemento.
Útil para ajustar seletores e filtros de status.
"""
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

from scraper import setup_driver, _aceitar_cookies
import config

driver = setup_driver(headless=False)
driver.get(config.BASE_URL)
_aceitar_cookies(driver)

WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, config.SEL_JOGO_ROW))
)

soup = BeautifulSoup(driver.page_source, "html.parser")
linhas = soup.select(config.SEL_JOGO_ROW)

print(f"\n=== {len(linhas)} linhas .event__match encontradas ===\n")
for i, linha in enumerate(linhas[:20]):
    hora_el  = linha.select_one(".event__time")
    hora_txt = hora_el.get_text(strip=True) if hora_el else "(sem .event__time)"
    classes  = " ".join(linha.get("class", []))
    elem_id  = linha.get("id", "(sem id)")
    casa_el  = linha.select_one(config.SEL_TIME_CASA)
    fora_el  = linha.select_one(config.SEL_TIME_FORA)
    casa     = casa_el.get_text(strip=True) if casa_el else "?"
    fora     = fora_el.get_text(strip=True) if fora_el else "?"

    is_hhmm = bool(re.match(r"^\d{1,2}:\d{2}$", hora_txt))
    print(f"[{i:02d}] hora='{hora_txt}' | hhmm={is_hhmm} | {casa} vs {fora}")
    print(f"      classes: {classes}")
    print(f"      id: {elem_id}\n")

driver.quit()
