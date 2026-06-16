#!/usr/bin/env python3
"""
Script para criar dados de teste para o sistema de backtesting
"""
import json
from datetime import datetime
from backtesting import BacktestingSystem

def criar_dados_teste():
    """Cria dados de teste simulados para o backtesting"""
    
    bs = BacktestingSystem()
    
    # Dados de teste - Previsões simuladas
    previsoes_teste = [
        {
            "time_casa": "Brasil",
            "time_fora": "Croácia",
            "data": "2026-06-13",
            "tipo_lay": "LAY_1X0",
            "ev_1x0": 0.15,
            "ev_0x1": 0.0,
            "retorno_1x0": 12.5,
            "retorno_0x1": 0.0,
            "prob_estimada_1x0": 0.65,
            "prob_estimada_0x1": 0.0,
            "classificacao": "LAY_VALOR",
            "is_copa_do_mundo": True
        },
        {
            "time_casa": "Argentina",
            "time_fora": "México",
            "data": "2026-06-13",
            "tipo_lay": "LAY_0X1",
            "ev_1x0": 0.0,
            "ev_0x1": 0.22,
            "retorno_1x0": 0.0,
            "retorno_0x1": 18.0,
            "prob_estimada_1x0": 0.0,
            "prob_estimada_0x1": 0.72,
            "classificacao": "LAY_VALOR",
            "is_copa_do_mundo": True
        },
        {
            "time_casa": "Flamengo",
            "time_fora": "Palmeiras",
            "data": "2026-06-13",
            "tipo_lay": "LAY_1X0",
            "ev_1x0": 0.08,
            "ev_0x1": 0.0,
            "retorno_1x0": 8.5,
            "retorno_0x1": 0.0,
            "prob_estimada_1x0": 0.58,
            "prob_estimada_0x1": 0.0,
            "classificacao": "LAY_VALOR",
            "is_copa_do_mundo": False
        },
        {
            "time_casa": "Real Madrid",
            "time_fora": "Barcelona",
            "data": "2026-06-13",
            "tipo_lay": "LAY_0X1",
            "ev_1x0": 0.0,
            "ev_0x1": 0.12,
            "retorno_1x0": 0.0,
            "retorno_0x1": 10.0,
            "prob_estimada_1x0": 0.0,
            "prob_estimada_0x1": 0.62,
            "classificacao": "LAY_VALOR",
            "is_copa_do_mundo": False
        },
        {
            "time_casa": "Corinthians",
            "time_fora": "São Paulo",
            "data": "2026-06-13",
            "tipo_lay": "LAY_1X0",
            "ev_1x0": 0.18,
            "ev_0x1": 0.0,
            "retorno_1x0": 15.0,
            "retorno_0x1": 0.0,
            "prob_estimada_1x0": 0.68,
            "prob_estimada_0x1": 0.0,
            "classificacao": "LAY_VALOR",
            "is_copa_do_mundo": False
        }
    ]
    
    # Adicionar previsões ao sistema
    for prev in previsoes_teste:
        jogo = {
            "time_casa": prev["time_casa"],
            "time_fora": prev["time_fora"],
            "hora": "15:00"
        }
        
        tipo_lay_lower = prev["tipo_lay"].lower()
        analise = {
            "tipo_lay": prev["tipo_lay"],
            "classificacao": prev["classificacao"],
            "is_copa_do_mundo": prev["is_copa_do_mundo"],
            "freqs": {
                "ev_1x0": prev["ev_1x0"] if "ev_1x0" in prev else 0.0,
                "ev_0x1": prev["ev_0x1"] if "ev_0x1" in prev else 0.0,
                "retorno_1x0": prev["retorno_1x0"] if "retorno_1x0" in prev else 0.0,
                "retorno_0x1": prev["retorno_0x1"] if "retorno_0x1" in prev else 0.0,
                "prob_estimada_1x0": prev["prob_estimada_1x0"] if "prob_estimada_1x0" in prev else 0.0,
                "prob_estimada_0x1": prev["prob_estimada_0x1"] if "prob_estimada_0x1" in prev else 0.0
            }
        }
        
        bs.adicionar_previsao(jogo, analise)
    
    print("Dados de teste criados com sucesso!")
    print(f"   {len(previsoes_teste)} previsoes adicionadas")
    
    # Adicionar alguns resultados reais simulados
    resultados_teste = [
        ("Brasil", "Croácia", "2x1"),  # Acerto LAY 1X0 (placar não foi 1x0)
        ("Argentina", "México", "2x0"),  # Erro LAY 0X1 (placar foi 2x0, não 0x1)
        ("Flamengo", "Palmeiras", "1x1"),  # Acerto LAY 1X0 (placar não foi 1x0)
        ("Real Madrid", "Barcelona", "3x2"),  # Acerto LAY 0X1 (placar não foi 0x1)
        # Corinthians vs São Paulo - sem resultado ainda
    ]
    
    for casa, fora, placar in resultados_teste:
        bs.adicionar_resultado_real(casa, fora, placar)
    
    print("Resultados reais adicionados com sucesso!")
    print(f"   {len(resultados_teste)} resultados adicionados")

if __name__ == "__main__":
    criar_dados_teste()