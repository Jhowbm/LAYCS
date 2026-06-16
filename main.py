# =============================================================================
# main.py — Orquestrador principal
#
# Uso:
#   python main.py [--limiar 0.10] [--headless] [--delay 2.5] [--saida flashscore_lay]
#
# Exemplos:
#   python main.py                        # padrões do config.py
#   python main.py --limiar 0.08          # oportunidade abaixo de 8%
#   python main.py --headless --delay 3   # sem janela, delay de 3s
# =============================================================================

import argparse
import logging
import sys
import time
from pathlib import Path
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from scraper import setup_driver, coletar_jogos_do_dia, coletar_h2h, coletar_odds
from analyzer import (
    calcular_frequencias_jogo,
    classificar_oportunidade,
    construir_dataframe,
    exportar_dados,
    exibir_resumo,
    é_copa_do_mundo,
)
from backtesting import salvar_previsoes_analise, BacktestingSystem


# =============================================================================
# LOGGING
# =============================================================================
def configurar_logging():
    """
    Configura logging básico para evitar problemas de encoding.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler()]
    )


# =============================================================================
# ARGUMENTOS DE LINHA DE COMANDO
# =============================================================================
def parse_args():
    parser = argparse.ArgumentParser(
        description="Extrai dados do Flashscore e identifica oportunidades Lay 1x0/0x1."
    )
    parser.add_argument(
        "--limiar", type=float, default=config.LIMIAR_OPORTUNIDADE,
        help=f"Frequência máxima para classificar como oportunidade (padrão: {config.LIMIAR_OPORTUNIDADE})"
    )
    parser.add_argument(
        "--headless", action="store_true", default=True,
        help="Roda o Firefox sem janela visível (padrão: ativado)"
    )
    parser.add_argument(
        "--no-headless", dest="headless", action="store_false",
        help="Abre o Firefox de forma visível (útil para depuração)"
    )
    parser.add_argument(
        "--delay", type=float, default=config.DELAY_ENTRE_JOGOS,
        help=f"Delay em segundos entre requisições (padrão: {config.DELAY_ENTRE_JOGOS})"
    )
    parser.add_argument(
        "--saida", type=str, default="flashscore_lay",
        help="Prefixo dos arquivos de saída CSV e JSON (padrão: flashscore_lay)"
    )
    parser.add_argument(
        "--dias", type=int, default=0,
        help="Dias à frente (0=hoje, 1=amanhã, 2=depois de amanhã, etc.)"
    )
    parser.add_argument(
        "--salvar-previsoes", action="store_true",
        help="Salvar previsões no sistema de backtesting"
    )
    parser.add_argument(
        "--backtesting", action="store_true",
        help="Mostrar relatório de backtesting"
    )
    return parser.parse_args()


# =============================================================================
# PROCESSAMENTO DE UM JOGO
# =============================================================================
def processar_jogo(jogo: dict, limiar: float, delay: float, headless: bool) -> dict | None:
    """
    Coleta H2H e odds de um jogo, calcula frequências e classifica.
    Versão paralela: cria seu próprio driver.

    Retorna None se ocorrer falha irrecuperável (será registrado em erros.log).
    """
    logger = logging.getLogger(__name__)
    id_jogo = jogo["id"]
    descricao = f"{jogo['time_casa']} vs {jogo['time_fora']}"
    driver = None

    try:
        driver = setup_driver(headless=headless)

        # --- H2H ---
        h2h = coletar_h2h(driver, jogo["url"], id_jogo)
        time.sleep(delay)

        # --- Odds ---
        odds = coletar_odds(driver, id_jogo, url_jogo=jogo["url"])
        time.sleep(delay)

        # --- Análise ---
        freqs = calcular_frequencias_jogo(h2h, odds)
        classif, tipo_lay = classificar_oportunidade(freqs, odds, limiar)

        ev_1x0 = freqs.get('ev_1x0', 0.0)
        ev_0x1 = freqs.get('ev_0x1', 0.0)
        retorno_1x0 = freqs.get('retorno_1x0', 0.0)
        retorno_0x1 = freqs.get('retorno_0x1', 0.0)

        logger.info(
            f"[{id_jogo}] {descricao} -> {classif} | {tipo_lay} | "
            f"EV_1x0={ev_1x0:.3f} ({retorno_1x0:.1f}%) | EV_0x1={ev_0x1:.3f} ({retorno_0x1:.1f}%)"
        )

        return {
            "jogo":         jogo,
            "h2h":          h2h,
            "odds":         odds,
            "freqs":        freqs,
            "classificacao": classif,
            "tipo_lay":     tipo_lay,
            "is_copa_do_mundo": é_copa_do_mundo(jogo.get('time_casa', ''), jogo.get('time_fora', '')),
        }

    except Exception as e:
        logger.warning(f"FALHA [{id_jogo}] {descricao}: {e}")
        return None
    finally:
        if driver:
            driver.quit()


# =============================================================================
# MAIN
# =============================================================================
def main():
    configurar_logging()
    args = parse_args()
    logger = logging.getLogger(__name__)

    logger.info("=" * 55)
    logger.info("  Flashscore Lay Analyzer — iniciando")
    logger.info(f"  Limiar: {args.limiar:.0%} | Delay: {args.delay}s | Headless: {args.headless}")
    logger.info(f"  Workers: {config.MAX_WORKERS} (processamento paralelo)")
    logger.info(f"  Dias à frente: {args.dias} (0=hoje, 1=amanhã)")
    logger.info(f"  Salvar previsões: {args.salvar_previsoes}")
    logger.info(f"  Backtesting: {args.backtesting}")
    logger.info("=" * 55)

    # Se solicitado apenas backtesting, mostrar relatório e sair
    if args.backtesting:
        bt = BacktestingSystem()
        bt.gerar_relatorio_backtesting()
        return

    driver = None
    jogos_processados = []

    try:
        driver = setup_driver(headless=args.headless)

        # 1. Coleta lista de jogos do dia
        jogos = coletar_jogos_do_dia(driver, dias_frente=args.dias)
        if not jogos:
            logger.error("Nenhum jogo encontrado. Encerrando.")
            return

        logger.info(f"Processando {len(jogos)} jogos em paralelo...")

        # 2. Processa jogos em paralelo
        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            # Submete todos os jogos para processamento
            future_to_jogo = {
                executor.submit(
                    processar_jogo, 
                    jogo, 
                    args.limiar, 
                    args.delay, 
                    args.headless
                ): jogo for jogo in jogos
            }

            # Coleta resultados conforme completam
            for i, future in enumerate(as_completed(future_to_jogo), 1):
                jogo = future_to_jogo[future]
                logger.info(f"[{i}/{len(jogos)}] {jogo['time_casa']} vs {jogo['time_fora']}")
                try:
                    resultado = future.result()
                    if resultado:
                        jogos_processados.append(resultado)
                except Exception as e:
                    logger.warning(f"Erro ao processar jogo {jogo['id']}: {e}")

        if not jogos_processados:
            logger.error("Nenhum jogo processado com sucesso. Verifique erros.log.")
            return

        # 3. Monta DataFrame e exporta
        # Calcula a data correta baseada nos dias à frente
        data_alvo = date.today() + timedelta(days=args.dias)
        df = construir_dataframe(jogos_processados, data_override=data_alvo.isoformat())
        csv_path, json_path = exportar_dados(df, args.saida)

        # 4. Exibe resumo no terminal
        exibir_resumo(df, args.limiar)

        logger.info(f"Arquivos gerados: {csv_path} | {json_path}")

        # 5. Salvar previsões no sistema de backtesting
        if args.salvar_previsoes:
            logger.info("Salvando previsões no sistema de backtesting...")
            bt = salvar_previsoes_analise(jogos_processados)
            logger.info(f"Previsões salvas: {len(jogos_processados)} jogos")

    except KeyboardInterrupt:
        logger.info("Interrompido pelo usuário.")
    except Exception as e:
        logger.exception(f"Erro fatal: {e}")
    finally:
        if driver:
            driver.quit()
            logger.info("Driver principal encerrado.")


if __name__ == "__main__":
    main()
