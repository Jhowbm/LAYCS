# =============================================================================
# config.py — Configurações centralizadas
#
# ATENÇÃO: O Flashscore pode alterar seus seletores CSS a qualquer momento.
# Se o scraper parar de funcionar, este é o primeiro arquivo a revisar.
# Inspecione o site com F12 (DevTools) e atualize as constantes abaixo.
# =============================================================================

# --- URLs ---
BASE_URL       = "https://www.flashscore.com.br/"
GAME_BASE_URL  = "https://www.flashscore.com.br/jogo/"   # + ID do jogo + "/#/h2h/h2h-geral"

# --- Navegação de data (botão "próximo dia" na lista de jogos) ---
# Tentados em ordem — o primeiro que for clicável é usado
SEL_NAV_PROXIMO_DIA = [
    "[data-testid='wcl-calendar-navigation-next']",
    ".calendar__navigation--next",
    "button[class*='navigation--next']",
    "[class*='calendarNavigation'][class*='next']",
    "[aria-label='Próximo dia']",
    "[aria-label='Next day']",
]

# --- Seletores da lista de jogos (página principal) ---
# Cada jogo agendado aparece como um div com essa classe
SEL_JOGO_ROW       = ".event__match"
# ATUALIZADO 2026-06 — Flashscore migrou para componentes wcl-*
# Seletores antigos (.event__participant--home/away) foram removidos do HTML
SEL_TIME_CASA      = ".event__homeParticipant [data-testid='wcl-scores-simple-text-01']"
SEL_TIME_FORA      = ".event__awayParticipant [data-testid='wcl-scores-simple-text-01']"
# Link para a página de detalhes — o href já contém a URL completa do jogo
SEL_JOGO_LINK      = "a.eventRowLink"
# Classe que identifica jogos AGENDADOS (não iniciados)
SEL_JOGO_SCHEDULED = "event__match--scheduled"

# --- Seletores da página de detalhes ---
# Aba H2H (clique para ativar)
SEL_ABA_H2H        = "a[href*='h2h']"
# Seção "Confrontos Diretos" dentro da aba H2H
SEL_H2H_SECAO      = ".h2h__section"
# Cada linha de resultado H2H
SEL_H2H_ROW        = ".h2h__row"
# Placar dentro de cada linha H2H — dois spans wcl-tableScore dentro de .h2h__result
# .h2h__result exibe "21" como concatenação de dois spans filhos; usar data-testid para extrair
SEL_H2H_SCORE      = "[data-testid='wcl-tableScore']"

# --- Seletores de odds ---
# Aba de odds (1x2)
SEL_ABA_ODDS       = "a[href*='odds-comparacao']"
# Células de odds 1x2 (Betfair ou primeira casa listada) - seletores alternativos
SEL_ODDS_LINHA     = ".ui-table__row"
SEL_ODDS_LINHA_ALT = "[class*='table__row']"
SEL_ODD_1          = ".oddsCell__odd:nth-child(1)"
SEL_ODD_X          = ".oddsCell__odd:nth-child(2)"
SEL_ODD_2          = ".oddsCell__odd:nth-child(3)"
# Odds de placar exato (correct score) — seção específica
SEL_ABA_CS         = "a[href*='placar-exato']"
SEL_CS_LINHA       = ".ui-table__row"
SEL_CS_LINHA_ALT   = "[class*='table__row']"
SEL_CS_PLACAR      = ".oddsCell__noOddsCell"
SEL_CS_PLACAR_ALT  = "[class*='noOddsCell'], [class*='placar']"
SEL_CS_ODD         = ".oddsCell__odd"

# --- Parâmetros de comportamento ---
TIMEOUT_PADRAO     = 8        # segundos para WebDriverWait (reduzido)
TIMEOUT_ODDS       = 10       # segundos específicos para odds (reduzido)
MAX_TENTATIVAS     = 2        # retry automático por elemento/página (reduzido)
DELAY_ENTRE_JOGOS  = 0.5      # segundos entre abertura de páginas de jogos (reduzido drasticamente)
MAX_H2H_RESULTADOS = 10       # últimos N resultados H2H a considerar
MAX_WORKERS        = 3        # número de workers para processamento paralelo

# --- Placares-alvo para análise Lay ---
PLACARES_ALVO = ["1:0", "0:1"]   # formato Flashscore usa ":" como separador

# --- Limiar padrão de oportunidade (sobreescrito via CLI) ---
LIMIAR_OPORTUNIDADE = 0.10   # 10% — freq combinada abaixo disso → oportunidade (método antigo)

# --- Classificação multi-critério (Valor Esperado) ---
MIN_H2H_JOGOS       = 3     # confrontos mínimos para não classificar como SEM_DADOS
MEDIA_GOLS_MINIMA   = 2.0   # média de gols totais por jogo no H2H para ser LAY (método antigo)
LIMIAR_ODD_OVER15   = 1.40  # odd de Over 1.5 abaixo disso → mercado espera gols → favorável ao Lay (método antigo)
TETO_ODD_LAY        = 8.0   # odd máxima do placar exato 1x0/0x1 — acima disso a liability é alta (método antigo)
RETORNO_MINIMO      = 5.0   # retorno mínimo % stake para considerar LAY_VALOR (novo método EV)

# --- Agendamento automático (server.py) ---
AUTO_RUN_HORA     = 9     # hora para análise dos jogos de HOJE (formato 24h, horário local)
AUTO_RUN_MINUTO   = 0
AUTO_RUN_AMANHA_HORA   = 22   # hora para análise prévia dos jogos de AMANHÃ
AUTO_RUN_AMANHA_MINUTO = 0
AUTO_RUN_HEADLESS = True  # rodar sem janela visível no modo automático
