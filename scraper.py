# =============================================================================
# scraper.py — Módulo de coleta de dados do Flashscore
#
# Responsável por:
#   - Inicializar o WebDriver Firefox
#   - Coletar jogos agendados do dia
#   - Navegar até cada jogo e extrair H2H e odds
# =============================================================================

import os
import re
import time
import logging
from functools import wraps

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup

import config

# Logger deste módulo — saída vai para erros.log (configurado em main.py)
logger = logging.getLogger(__name__)


# =============================================================================
# RETRY — decorador que tenta novamente em caso de falha
# =============================================================================
def com_retry(max_tentativas=config.MAX_TENTATIVAS, delay=1.5):
    """Decora uma função para retentar automaticamente em caso de exceção."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for tentativa in range(1, max_tentativas + 1):
                try:
                    return func(*args, **kwargs)
                except (TimeoutException, WebDriverException, Exception) as e:
                    logger.warning(f"[retry {tentativa}/{max_tentativas}] {func.__name__}: {e}")
                    if tentativa == max_tentativas:
                        raise
                    time.sleep(delay * tentativa)
        return wrapper
    return decorator


# =============================================================================
# SETUP DO DRIVER
# =============================================================================
def setup_driver(headless: bool = True) -> webdriver.Firefox:
    """
    Cria e retorna um WebDriver Firefox configurado (otimizado para velocidade).

    Usa webdriver-manager para baixar automaticamente o geckodriver compatível.
    
    headless=True: roda sem janela visível (recomendado para automação)
    headless=False: abre o Firefox visível (útil para depuração)
    """
    opcoes = Options()

    if headless:
        opcoes.add_argument("--headless")

    # Evita detecção de bot — define user-agent realista
    opcoes.set_preference(
        "general.useragent.override",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
    )
    # Desabilita notificações e popups
    opcoes.set_preference("dom.webnotifications.enabled", False)
    opcoes.set_preference("geo.enabled", False)
    # Eager: para de aguardar quando o DOM está pronto (não espera imagens/ads externos)
    # Evita timeout por recursos de terceiros lentos (anúncios, rastreadores, etc.)
    opcoes.page_load_strategy = "eager"
    
    # Otimizações de velocidade
    opcoes.set_preference("network.http.pipelining", True)
    opcoes.set_preference("content.notify.interval", 500)
    
    # Timeout de página
    page_load_timeout = 45

    # Usa webdriver-manager para download automático do geckodriver
    geckodriver_path = os.environ.get("GECKODRIVER_PATH")
    if geckodriver_path:
        service = Service(executable_path=geckodriver_path)
    else:
        logger.info("Baixando geckodriver automaticamente...")
        service = Service(GeckoDriverManager().install())
        logger.info("Geckodriver baixado com sucesso!")

    driver = webdriver.Firefox(service=service, options=opcoes)
    driver.set_page_load_timeout(page_load_timeout)
    driver.set_script_timeout(30)
    return driver


def _esperar_elemento(driver, seletor_css: str, timeout: int = config.TIMEOUT_PADRAO):
    """Aguarda até que um elemento CSS esteja presente no DOM e o retorna."""
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, seletor_css))
    )


def _esperar_elementos(driver, seletor_css: str, timeout: int = config.TIMEOUT_PADRAO):
    """Aguarda e retorna uma lista de elementos CSS."""
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, seletor_css))
    )


def _aceitar_cookies(driver):
    """Tenta fechar o banner de cookies, se presente."""
    try:
        btn = WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button#onetrust-accept-btn-handler"))
        )
        btn.click()
        logger.info("Banner de cookies aceito.")
    except TimeoutException:
        pass  # Sem banner — sem problema


def _navegar_proximo_dia(driver):
    """Clica no botão de navegação para o próximo dia na lista de jogos."""
    for sel in config.SEL_NAV_PROXIMO_DIA:
        try:
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
            )
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(2.0)  # aguarda a lista recarregar
            logger.info(f"Navegou para o próximo dia (selector: {sel}).")
            return True
        except TimeoutException:
            continue
    logger.warning("Botão de próximo dia não encontrado — usando jogos da data atual.")
    return False


# =============================================================================
# COLETA DE JOGOS DO DIA
# =============================================================================
@com_retry()
def coletar_jogos_do_dia(driver, dias_frente: int = 0) -> list[dict]:
    """
    Acessa o Flashscore e retorna todos os jogos AGENDADOS do dia.

    dias_frente=0: jogos de hoje
    dias_frente=1: jogos de amanhã (clica no botão "próximo dia")

    Retorna uma lista de dicts com:
        {id, time_casa, time_fora, url, hora}
    """
    logger.info(f"Acessando {config.BASE_URL} ...")
    driver.get(config.BASE_URL)
    _aceitar_cookies(driver)

    for i in range(dias_frente):
        logger.info(f"Navegando para o próximo dia ({i+1}/{dias_frente})...")
        _navegar_proximo_dia(driver)

    # Aguarda a lista de jogos carregar — o seletor principal é .event__match
    # Nota: o Flashscore carrega via JS; WebDriverWait é essencial aqui
    try:
        _esperar_elemento(driver, config.SEL_JOGO_ROW, timeout=20)
    except TimeoutException:
        logger.error("Timeout aguardando lista de jogos. Verifique SEL_JOGO_ROW em config.py.")
        return []

    # Parseia o HTML atual com BeautifulSoup para extração eficiente
    soup = BeautifulSoup(driver.page_source, "html.parser")
    linhas = soup.select(config.SEL_JOGO_ROW)
    logger.info(f"{len(linhas)} partidas encontradas na página principal.")

    jogos = []
    for linha in linhas:
        try:
            # Filtro confiável: apenas jogos com classe event__match--scheduled
            # (ao vivo = event__match--live, encerrados não têm essa classe)
            classes = linha.get("class", [])
            if config.SEL_JOGO_SCHEDULED not in classes:
                continue

            # Extrai nomes dos times — seletores wcl-* (atualizados jun/2026)
            time_casa = linha.select_one(config.SEL_TIME_CASA)
            time_fora = linha.select_one(config.SEL_TIME_FORA)
            if not time_casa or not time_fora:
                continue

            nome_casa = time_casa.get_text(strip=True)
            nome_fora = time_fora.get_text(strip=True)
            if not nome_casa or not nome_fora:
                continue

            # Hora — pode vir com sufixo como "19:00SRF"; extrai só HH:MM
            hora_el  = linha.select_one(".event__time")
            hora_raw = hora_el.get_text(strip=True) if hora_el else ""
            match_hora = re.match(r"(\d{1,2}:\d{2})", hora_raw)
            hora_txt = match_hora.group(1) if match_hora else hora_raw

            # URL do jogo vem diretamente do href de a.eventRowLink
            link_el = linha.select_one(config.SEL_JOGO_LINK)
            if not link_el or not link_el.get("href"):
                continue
            url_base = link_el["href"].split("?")[0].rstrip("/")
            url_jogo = f"{url_base}/#/h2h/h2h-geral"

            # ID para logging — último segmento do id HTML (ex: g_1_EwWaFBeL → EwWaFBeL)
            jogo_id = linha.get("id", "").rsplit("_", 1)[-1]

            jogos.append({
                "id":        jogo_id,
                "time_casa": nome_casa,
                "time_fora": nome_fora,
                "hora":      hora_txt,
                "url":       url_jogo,
            })
        except Exception as e:
            logger.warning(f"Erro ao parsear linha de jogo: {e}")
            continue

    logger.info(f"{len(jogos)} jogos agendados extraídos.")
    return jogos


# =============================================================================
# COLETA DE DADOS H2H
# =============================================================================
@com_retry()
def coletar_h2h(driver, url_jogo: str, id_jogo: str) -> dict:
    """
    Navega até a aba H2H de um jogo e extrai os últimos resultados.

    Retorna dict com:
        {
          h2h_confrontos: [(gols_casa, gols_fora), ...],   # confrontos diretos
          h2h_casa:       [(gols_casa, gols_fora), ...],   # últimos jogos time da casa
          h2h_fora:       [(gols_casa, gols_fora), ...],   # últimos jogos time de fora
        }
    """
    logger.info(f"[{id_jogo}] Abrindo H2H: {url_jogo}")
    driver.get(url_jogo)

    resultado = {
        "h2h_confrontos": [],
        "h2h_casa":       [],
        "h2h_fora":       [],
    }

    # 1. Aguarda qualquer elemento h2h aparecer no DOM (skeleton ou dados reais)
    # 2. Depois aguarda o skeleton desaparecer — isso indica que os dados reais foram carregados
    # O Flashscore carrega H2H via API assíncrona; o skeleton é exibido enquanto aguarda
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='h2h']"))
        )
        WebDriverWait(driver, 15).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__skeleton"))
        )
    except TimeoutException:
        # Tenta clicar na aba H2H manualmente (alguns layouts não abrem direto)
        try:
            aba = _esperar_elemento(driver, config.SEL_ABA_H2H, timeout=8)
            driver.execute_script("arguments[0].click();", aba)
            WebDriverWait(driver, 15).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__skeleton"))
            )
        except TimeoutException:
            logger.warning(f"[{id_jogo}] H2H não carregou após skeleton wait.")
            return resultado

    soup = BeautifulSoup(driver.page_source, "html.parser")
    secoes = soup.select(config.SEL_H2H_SECAO)

    # O Flashscore normalmente retorna 3 seções na aba H2H:
    #   [0] = confrontos diretos entre os dois times
    #   [1] = últimos jogos do time da casa
    #   [2] = últimos jogos do time visitante
    chaves = ["h2h_confrontos", "h2h_casa", "h2h_fora"]

    for idx, (chave, secao) in enumerate(zip(chaves, secoes)):
        linhas = secao.select(config.SEL_H2H_ROW)
        placar_lista = []

        for linha in linhas[:config.MAX_H2H_RESULTADOS]:
            placar = _extrair_placar_h2h(linha)
            if placar:
                placar_lista.append(placar)

        resultado[chave] = placar_lista
        logger.debug(f"[{id_jogo}] H2H seção '{chave}': {len(placar_lista)} resultados")

    return resultado


def _extrair_placar_h2h(linha) -> tuple | None:
    """
    Extrai o placar (gols_casa, gols_fora) de uma linha H2H.

    O Flashscore (pós-2026) exibe o placar como dois spans [data-testid='wcl-tableScore']
    dentro de .h2h__result — o texto concatenado (ex: "21") não contém dois pontos.
    """
    try:
        resultado_el = linha.select_one(".h2h__result")
        if resultado_el:
            scores = resultado_el.find_all(attrs={"data-testid": "wcl-tableScore"})
            if len(scores) >= 2:
                return (int(scores[0].get_text(strip=True)), int(scores[1].get_text(strip=True)))
    except (ValueError, IndexError, AttributeError):
        pass

    return None


# =============================================================================
# COLETA DE ODDS
# =============================================================================
@com_retry()
def coletar_odds(driver, id_jogo: str, url_jogo: str = "") -> dict:
    """
    Navega até a aba de odds de um jogo e extrai:
      - Odds 1x2 (vitória casa / empate / vitória fora)
      - Odds de placar exato 1:0 e 0:1 (se disponíveis)
      - Odds Over/Under 1.5 (se disponíveis)

    url_jogo: URL base do jogo (ex: https://www.flashscore.com.br/jogo/futebol/a/b/)
              Se fornecida, usa ela; caso contrário, reconstrói só com o ID (fallback).
    Retorna dict com: {odd_1, odd_x, odd_2, odd_cs_1x0, odd_cs_0x1, odd_over_1_5}
    """
    # Usa a URL completa do jogo — remove qualquer fragmento (#...) e monta as odds
    if url_jogo:
        base = url_jogo.split("#")[0].rstrip("/")
    else:
        base = f"{config.GAME_BASE_URL}{id_jogo}"
    url_odds = f"{base}/#/comparacao-odds/1x2"
    logger.info(f"[{id_jogo}] Coletando odds: {url_odds}")
    driver.get(url_odds)

    resultado = {
        "odd_1":        None,
        "odd_x":        None,
        "odd_2":        None,
        "odd_cs_1x0":   None,
        "odd_cs_0x1":   None,
        "odd_over_1_5": None,
    }

    # --- Odds 1x2 ---
    try:
        # Tenta com seletor principal
        _esperar_elemento(driver, config.SEL_ODDS_LINHA, timeout=config.TIMEOUT_ODDS)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        linhas = soup.select(config.SEL_ODDS_LINHA)
        
        # Se não encontrou, tenta seletor alternativo
        if not linhas:
            linhas = soup.select(config.SEL_ODDS_LINHA_ALT)
            logger.debug(f"[{id_jogo}] Usando seletor alternativo para odds 1x2")

        # Pega a primeira linha (geralmente a casa de apostas principal / média)
        for linha in linhas:
            celulas = linha.select(".oddsCell__odd")
            if len(celulas) >= 3:
                try:
                    resultado["odd_1"] = float(celulas[0].get_text(strip=True).replace(",", "."))
                    resultado["odd_x"] = float(celulas[1].get_text(strip=True).replace(",", "."))
                    resultado["odd_2"] = float(celulas[2].get_text(strip=True).replace(",", "."))
                    logger.info(f"[{id_jogo}] Odds 1x2 coletadas: {resultado['odd_1']}/{resultado['odd_x']}/{resultado['odd_2']}")
                    break
                except ValueError:
                    continue
            else:
                # Tenta encontrar odds em formato diferente
                odds_text = linha.get_text(strip=True)
                logger.debug(f"[{id_jogo}] Tentando parser alternativo, texto: {odds_text[:100]}")

    except TimeoutException:
        logger.warning(f"[{id_jogo}] Timeout nas odds 1x2.")

    # --- Odds de placar exato (correct score) ---
    url_cs = f"{base}/#/comparacao-odds/placar-exato"
    try:
        driver.get(url_cs)
        _esperar_elemento(driver, config.SEL_CS_LINHA, timeout=config.TIMEOUT_ODDS)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        linhas_cs = soup.select(config.SEL_CS_LINHA)
        if not linhas_cs:
            linhas_cs = soup.select(config.SEL_CS_LINHA_ALT)
            
        for linha in linhas_cs:
            # Tenta diferentes seletores para o placar
            placar_el = linha.select_one(config.SEL_CS_PLACAR)
            if not placar_el:
                placar_el = linha.select_one(config.SEL_CS_PLACAR_ALT)
            
            odd_el = linha.select_one(config.SEL_CS_ODD)
            if not placar_el or not odd_el:
                continue

            placar_texto = placar_el.get_text(strip=True)  # ex: "1:0"
            try:
                odd_val = float(odd_el.get_text(strip=True).replace(",", "."))
            except ValueError:
                continue

            if placar_texto == "1:0":
                resultado["odd_cs_1x0"] = odd_val
                logger.info(f"[{id_jogo}] Odd CS 1x0: {odd_val}")
            elif placar_texto == "0:1":
                resultado["odd_cs_0x1"] = odd_val
                logger.info(f"[{id_jogo}] Odd CS 0x1: {odd_val}")

    except TimeoutException:
        logger.debug(f"[{id_jogo}] Mercado de placar exato não disponível.")

    # --- Odds Over/Under 1.5 ---
    url_ou = f"{base}/#/comparacao-odds/over-under"
    try:
        driver.get(url_ou)
        _esperar_elemento(driver, config.SEL_ODDS_LINHA, timeout=config.TIMEOUT_ODDS)
        soup_ou = BeautifulSoup(driver.page_source, "html.parser")
        
        linhas_ou = soup_ou.select(config.SEL_ODDS_LINHA)
        if not linhas_ou:
            linhas_ou = soup_ou.select(config.SEL_ODDS_LINHA_ALT)
            
        for linha in linhas_ou:
            label_el = linha.select_one(config.SEL_CS_PLACAR)
            if not label_el:
                label_el = linha.select_one(config.SEL_CS_PLACAR_ALT)
                
            if label_el and "1.5" in label_el.get_text(strip=True):
                celulas = linha.select(config.SEL_CS_ODD)
                if celulas:
                    try:
                        resultado["odd_over_1_5"] = float(
                            celulas[0].get_text(strip=True).replace(",", ".")
                        )
                        logger.info(f"[{id_jogo}] Odd Over 1.5: {resultado['odd_over_1_5']}")
                        break
                    except ValueError:
                        continue
    except TimeoutException:
        logger.debug(f"[{id_jogo}] Odds Over/Under não disponíveis.")

    return resultado
