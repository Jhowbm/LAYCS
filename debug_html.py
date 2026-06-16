"""
debug_html.py — Imprime o HTML interno de um jogo agendado para identificar seletores corretos.
"""
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

# Pega o primeiro jogo com event__match--scheduled
for linha in linhas:
    classes = linha.get("class", [])
    if "event__match--scheduled" in classes:
        print("=== HTML bruto do primeiro jogo agendado ===\n")
        print(linha.prettify())
        break

driver.quit()
