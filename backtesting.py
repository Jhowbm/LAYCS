#!/usr/bin/env python3
# =============================================================================
# backtesting.py — Sistema de Backtesting de Previsões Lay
# =============================================================================

import json
import os
from datetime import date, datetime, timedelta
from typing import List, Dict, Any

class BacktestingSystem:
    """Sistema para salvar previsões e comparar com resultados reais."""
    
    def __init__(self, arquivo_historico='previsoes_historico.json'):
        self.arquivo_historico = arquivo_historico
        self.previsoes = self._carregar_historico()
    
    def _carregar_historico(self) -> List[Dict]:
        """Carrega histórico de previsões do arquivo JSON."""
        if os.path.exists(self.arquivo_historico):
            try:
                with open(self.arquivo_historico, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erro ao carregar histórico: {e}")
                return []
        return []
    
    def _salvar_historico(self):
        """Salva o histórico de previsões no arquivo JSON."""
        try:
            with open(self.arquivo_historico, 'w', encoding='utf-8') as f:
                json.dump(self.previsoes, f, ensure_ascii=False, indent=2)
            print(f"Histórico salvo: {len(self.previsoes)} previsões")
        except Exception as e:
            print(f"Erro ao salvar histórico: {e}")
    
    def adicionar_previsao(self, jogo: Dict, analise: Dict):
        """Adiciona uma previsão ao histórico."""
        previsao = {
            'data': date.today().isoformat(),
            'data_hora': datetime.now().isoformat(),
            'time_casa': jogo.get('time_casa'),
            'time_fora': jogo.get('time_fora'),
            'hora': jogo.get('hora'),
            'tipo_lay': analise.get('tipo_lay'),
            'classificacao': analise.get('classificacao'),
            'ev_1x0': analise.get('freqs', {}).get('ev_1x0', 0.0),
            'ev_0x1': analise.get('freqs', {}).get('ev_0x1', 0.0),
            'retorno_1x0': analise.get('freqs', {}).get('retorno_1x0', 0.0),
            'retorno_0x1': analise.get('freqs', {}).get('retorno_0x1', 0.0),
            'prob_estimada_1x0': analise.get('freqs', {}).get('prob_estimada_1x0', 0.0),
            'prob_estimada_0x1': analise.get('freqs', {}).get('prob_estimada_0x1', 0.0),
            'media_gols': analise.get('freqs', {}).get('media_gols_confronto', 0.0),
            'is_copa_do_mundo': analise.get('is_copa_do_mundo', False),
            'resultado_real': None,  # Preenchido depois
            'placar_real': None,      # Preenchido depois
            'lucro': None            # Calculado depois
        }
        
        self.previsoes.append(previsao)
        self._salvar_historico()
        print(f"Previsão adicionada: {jogo['time_casa']} vs {jogo['time_fora']} - {analise['tipo_lay']}")
    
    def adicionar_resultado_real(self, time_casa: str, time_fora: str, placar_real: str):
        """
        Adiciona o resultado real de um jogo.
        placar_real: formato "1x0", "0x1", "2x1", etc.
        """
        for prev in self.previsoes:
            if (prev['time_casa'] == time_casa and 
                prev['time_fora'] == time_fora and 
                prev['resultado_real'] is None):
                
                prev['resultado_real'] = placar_real
                prev['placar_real'] = placar_real
                
                # Calcular resultado do Lay
                tipo_lay = prev['tipo_lay']
                
                if tipo_lay == 'LAY_1X0':
                    # Lay 1x0: ganha se placar NÃO for 1x0
                    ganhou = placar_real != '1x0'
                elif tipo_lay == 'LAY_0X1':
                    # Lay 0x1: ganha se placar NÃO for 0x1
                    ganhou = placar_real != '0x1'
                else:
                    ganhou = None  # Não aplicável
                
                if ganhou is not None:
                    # Calcular lucro (retorno% stake - liability% se perder)
                    if tipo_lay == 'LAY_1X0':
                        retorno = prev['retorno_1x0']
                    else:
                        retorno = prev['retorno_0x1']
                    
                    if ganhou:
                        prev['lucro'] = retorno  # Ganhou o retorno
                    else:
                        # Perdeu: liability = odd - 1
                        if tipo_lay == 'LAY_1X0':
                            odd = prev.get('odd_cs_1x0', 10)
                        else:
                            odd = prev.get('odd_cs_0x1', 10)
                        liability = odd - 1 if odd else 9
                        prev['lucro'] = -liability
                
                print(f"Resultado adicionado: {time_casa} vs {time_fora} - {placar_real} -> Lucro: {prev['lucro']}")
        
        self._salvar_historico()
    
    def calcular_metricas_backtesting(self) -> Dict[str, Any]:
        """Calcula métricas de desempenho do backtesting."""
        if not self.previsoes:
            return {}
        
        # Filtrar apenas previsões com resultado real
        analisados = [p for p in self.previsoes if p['resultado_real'] is not None]
        
        if not analisados:
            return {'erro': 'Nenhum resultado real registrado para análise'}
        
        total = len(analisados)
        acertos = sum(1 for p in analisados if p['lucro'] is not None and p['lucro'] > 0)
        erros = total - acertos
        
        # Calcular lucro total
        lucro_total = sum(p['lucro'] for p in analisados if p['lucro'] is not None)
        
        # ROI
        stake_total = total  # 1 unidade por aposta
        roi = (lucro_total / stake_total) * 100 if stake_total > 0 else 0
        
        # Análise por tipo de Lay
        lay_1x0_analises = [p for p in analisados if p['tipo_lay'] == 'LAY_1X0']
        lay_0x1_analises = [p for p in analisados if p['tipo_lay'] == 'LAY_0X1']
        
        def calcular_stats_grupo(grupo):
            if not grupo:
                return {}
            total_g = len(grupo)
            acertos_g = sum(1 for p in grupo if p['lucro'] and p['lucro'] > 0)
            lucro_g = sum(p['lucro'] for p in grupo if p['lucro'] is not None)
            return {
                'total': total_g,
                'acertos': acertos_g,
                'taxa_acerto': (acertos_g / total_g * 100) if total_g > 0 else 0,
                'lucro_total': lucro_g,
                'roi': (lucro_g / total_g * 100) if total_g > 0 else 0
            }
        
        return {
            'total_previsoes': len(self.previsoes),
            'com_resultado': total,
            'acertos': acertos,
            'erros': erros,
            'taxa_acerto_geral': (acertos / total * 100) if total > 0 else 0,
            'lucro_total': lucro_total,
            'roi_total': roi,
            'lay_1x0_stats': calcular_stats_grupo(lay_1x0_analises),
            'lay_0x1_stats': calcular_stats_grupo(lay_0x1_analises),
            'copa_do_mundo_stats': calcular_stats_grupo([p for p in analisados if p['is_copa_do_mundo']])
        }
    
    def gerar_relatorio_backtesting(self):
        """Gera um relatório detalhado de backtesting."""
        metricas = self.calcular_metricas_backtesting()
        
        print("\n" + "=" * 70)
        print(" RELATORIO DE BACKTESTING - FLASHSCORE LAY ANALYZER")
        print("=" * 70)
        
        if 'erro' in metricas:
            print(f"\nERRO: {metricas['erro']}")
            return
        
        print(f"\nESTATISTICAS GERAIS:")
        print(f"  Total de previsoes:     {metricas['total_previsoes']}")
        print(f"  Com resultado real:     {metricas['com_resultado']}")
        print(f"  Acertos:                {metricas['acertos']} ({metricas['taxa_acerto_geral']:.1f}%)")
        print(f"  Erros:                  {metricas['erros']} ({100-metricas['taxa_acerto_geral']:.1f}%)")
        print(f"  Lucro total:            {metricas['lucro_total']:.1f}%")
        print(f"  ROI total:               {metricas['roi_total']:.1f}%")
        
        if 'lay_1x0_stats' in metricas and metricas['lay_1x0_stats']:
            print(f"\nLAY 1X0:")
            stats = metricas['lay_1x0_stats']
            print(f"  Total:                  {stats['total']}")
            print(f"  Acertos:                {stats['acertos']} ({stats['taxa_acerto']:.1f}%)")
            print(f"  Lucro:                  {stats['lucro_total']:.1f}%")
            print(f"  ROI:                    {stats['roi']:.1f}%")
        
        if 'lay_0x1_stats' in metricas and metricas['lay_0x1_stats']:
            print(f"\nLAY 0X1:")
            stats = metricas['lay_0x1_stats']
            print(f"  Total:                  {stats['total']}")
            print(f"  Acertos:                {stats['acertos']} ({stats['taxa_acerto']:.1f}%)")
            print(f"  Lucro:                  {stats['lucro_total']:.1f}%")
            print(f"  ROI:                    {stats['roi']:.1f}%")
        
        if 'copa_do_mundo_stats' in metricas and metricas['copa_do_mundo_stats']:
            print(f"\nCOPA DO MUNDO:")
            stats = metricas['copa_do_mundo_stats']
            print(f"  Total:                  {stats['total']}")
            print(f"  Acertos:                {stats['acertos']} ({stats['taxa_acerto']:.1f}%)")
            print(f"  Lucro:                  {stats['lucro_total']:.1f}%")
            print(f"  ROI:                    {stats['roi']:.1f}%")
        
        print("\n" + "=" * 70)
        
        return metricas
    
    def exportar_para_csv(self, arquivo='backtesting_resultados.csv'):
        """Exporta dados de backtesting para CSV."""
        if not self.previsoes:
            print("Nenhum dado para exportar")
            return
        
        df = pd.DataFrame(self.previsoes)
        df.to_csv(arquivo, index=False, encoding='utf-8-sig')
        print(f"Dados exportados para: {arquivo}")


# Funções de integração com o sistema principal
def salvar_previsoes_analise(jogos_processados):
    """Salva todas as previsões de uma análise no sistema de backtesting."""
    bt = BacktestingSystem()
    
    for item in jogos_processados:
        jogo = item.get('jogo', {})
        analise = {
            'tipo_lay': item.get('tipo_lay'),
            'classificacao': item.get('classificacao'),
            'freqs': item.get('freqs', {}),
            'is_copa_do_mundo': item.get('is_copa_do_mundo', False)
        }
        bt.adicionar_previsao(jogo, analise)
    
    print(f"{len(jogos_processados)} previsoes salvas no sistema de backtesting")
    return bt


if __name__ == "__main__":
    import sys
    
    # Exemplo de uso
    bt = BacktestingSystem()
    
    print("Sistema de Backtesting - Flashscore Lay Analyzer")
    print("=" * 70)
    
    # Se passar argumentos, interpretar como comando
    if len(sys.argv) > 1:
        comando = sys.argv[1]
        
        if comando == "relatorio":
            # Gerar relatório atual
            bt.gerar_relatorio_backtesting()
        
        elif comando == "adicionar":
            # Adicionar resultado manual: python backtesting.py adicionar "Time Casa" "Time Fora" "1x0"
            if len(sys.argv) >= 5:
                time_casa = sys.argv[2]
                time_fora = sys.argv[3]
                placar = sys.argv[4]
                bt.adicionar_resultado_real(time_casa, time_fora, placar)
                print("\nRelatório atualizado:")
                bt.gerar_relatorio_backtesting()
            else:
                print("Uso: python backtesting.py adicionar <time_casa> <time_fora> <placar>")
        
        elif comando == "exportar":
            arquivo_saida = sys.argv[2] if len(sys.argv) > 2 else 'backtesting_resultados.csv'
            bt.exportar_para_csv(arquivo_saida)
        
        else:
            print(f"Comando desconhecido: {comando}")
    else:
        # Sem argumentos: mostrar relatório atual
        bt.gerar_relatorio_backtesting()
        
        print("\n💡 Comandos disponíveis:")
        print("  python backtesting.py relatorio       - Mostrar relatório")
        print("  python backtesting.py adicionar <Casa> <Fora> <Placar> - Adicionar resultado")
        print("  python backtesting.py exportar [arquivo]  - Exportar para CSV")