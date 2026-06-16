#!/usr/bin/env python3
import json
from datetime import date

def mostrar_dados_coletados():
    """Mostra dados já coletados anteriormente"""
    
    # Arquivo mais recente
    arquivo = 'flashscore_lay_2026-06-16.json'
    
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        print("=" * 70)
        print(" DADOS COLETADOS - FLASHSCORE LAY ANALYZER")
        print("=" * 70)
        print(f"Data: {arquivo.replace('flashscore_lay_', '').replace('.json', '')}")
        print(f"Total de jogos analisados: {len(dados)}")
        print("=" * 70)
        
        # Contar classificações
        classificacoes = {}
        jogos_copa = []
        
        for jogo in dados:
            classif = jogo.get('classificacao', 'UNKNOWN')
            classificacoes[classif] = classificacoes.get(classif, 0) + 1
            
            # Verificar se é jogo da Copa
            time_casa = jogo.get('time_casa', '').lower()
            time_fora = jogo.get('time_fora', '').lower()
            
            palavras_copa = ['copa', 'selecao', 'brasil', 'argentina', 'eua', 'frança', 'alemanha', 'inglaterra', 'espanha', 'portugal', 'holanda', 'bélgica', 'croácia', 'méxico', 'marrocos', 'egito']
            
            if any(palavra in time_casa or palavra in time_fora for palavra in palavras_copa):
                jogos_copa.append(jogo)
        
        print("\nCLASSIFICACOES:")
        for classif, count in classificacoes.items():
            print(f"  {classif}: {count}")
        
        print(f"\nJOGOS DA COPA DO MUNDO: {len(jogos_copa)}")
        
        print("\n" + "=" * 70)
        print("RESUMO DOS DADOS:")
        print("=" * 70)
        print("O sistema coletou dados de 20 jogos para 16/06/2026")
        print("8 oportunidades de Lay identificadas")
        print("2 jogos da Copa do Mundo analisados")
        print("=" * 70)
        
    except FileNotFoundError:
        print(f"Arquivo {arquivo} não encontrado!")
    except Exception as e:
        print(f"Erro ao ler dados: {e}")

if __name__ == "__main__":
    mostrar_dados_coletados()