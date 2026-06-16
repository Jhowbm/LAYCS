#!/usr/bin/env python3
# =============================================================================
# ciclos_manager.py — Sistema de Gestão do Método de Ciclos do Netuno
# =============================================================================

import json
import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class PerfilRisco(Enum):
    """Perfil de risco para o Método de Ciclos"""
    CONSERVADOR = "conservador"  # 4-5% por entrada
    MODERADO = "moderado"        # 4-5% por entrada  
    AGRESSIVO = "agressivo"      # 8% por entrada


class Estrategia(Enum):
    """Estratégias disponíveis para o Método de Ciclos"""
    LAY_FAVORITO_1T = "Lay Favorito (1º Tempo)"
    LAY_FAVORITO_2T = "Lay Favorito (2º Tempo)"
    LAY_ZEBRA_1T = "Lay Zebra (1º Tempo)"
    LAY_ZEBRA_2T = "Lay Zebra (2º Tempo)"
    BACK_FAVORITO_VENCENDO = "Back Favorito vencendo"
    BACK_ZEBRA_VENCENDO = "Back Zebra vencendo"
    LAY_FAVORITO_PERDENDO = "Lay Favorito perdendo"


@dataclass
class Entrada:
    """Representa uma entrada individual no ciclo"""
    jogo_numero: int
    time_casa: str
    time_fora: str
    campeonato: str
    estrategia: str
    stake_inicial: float
    banca_trabalho: float
    banca_teorica: float
    objetivo_porcentagem: float
    objetivo_valor: float
    lucro_real: float
    resultado: str  # "OK" ou "NOK"
    residuo: float
    data_hora: str
    odds: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Ciclo:
    """Representa um ciclo completo do Método de Ciclos"""
    ciclo_numero: int
    perfil: PerfilRisco
    banca_inicial: float
    stake_inicial: float
    objetivo_porcentagem: float
    objetivo_final: float
    entradas: List[Entrada]
    lucro_acumulado: float
    residuo_acumulado: float
    banca_atual: float
    status: str  # "em_andamento", "concluido", "parado"
    data_inicio: str
    data_fim: Optional[str] = None
    saque_teorico: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['perfil'] = self.perfil.value
        return data


class CiclosManager:
    """Gerenciador principal do Método de Ciclos do Netuno"""
    
    # Progressão de banca baseada na planilha original
    PROGRESSAO_BANCA = [100.0, 100.0, 125.0, 137.5, 156.25]
    
    # Metas de lucro por entrada
    META_CONSERVADOR = 0.04  # 4%
    META_AGRESSIVO = 0.08    # 8%
    
    # Objetivos finais (multiplicador da banca inicial)
    MULTIPLICADOR_CONSERVADOR = 5.0  # 5x
    MULTIPLICADOR_AGRESSIVO = 10.0   # 10x
    
    # Máximo de entradas por ciclo
    MAX_ENTRADAS_POR_CICLO = 10
    
    def __init__(self, arquivo_dados='ciclos_dados.json'):
        self.arquivo_dados = arquivo_dados
        self.ciclos: List[Ciclo] = []
        self.ciclo_atual: Optional[Ciclo] = None
        self._carregar_dados()
    
    def _carregar_dados(self):
        """Carrega dados dos ciclos do arquivo JSON"""
        if os.path.exists(self.arquivo_dados):
            try:
                with open(self.arquivo_dados, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    self.ciclos = [self._dict_to_ciclo(ciclo_dict) for ciclo_dict in dados]
                    
                    # Define o ciclo atual (último ciclo não concluído)
                    for ciclo in reversed(self.ciclos):
                        if ciclo.status == "em_andamento":
                            self.ciclo_atual = ciclo
                            break
            except Exception as e:
                print(f"Erro ao carregar dados dos ciclos: {e}")
                self.ciclos = []
    
    def _salvar_dados(self):
        """Salva dados dos ciclos no arquivo JSON"""
        try:
            dados = [ciclo.to_dict() for ciclo in self.ciclos]
            with open(self.arquivo_dados, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar dados dos ciclos: {e}")
    
    def _dict_to_ciclo(self, ciclo_dict: Dict[str, Any]) -> Ciclo:
        """Converte dicionário para objeto Ciclo"""
        # Converter perfil de string para enum
        if isinstance(ciclo_dict.get('perfil'), str):
            ciclo_dict['perfil'] = PerfilRisco(ciclo_dict['perfil'])
        
        # Converter entradas
        entradas = [Entrada(**ent) for ent in ciclo_dict.get('entradas', [])]
        ciclo_dict['entradas'] = entradas
        
        return Ciclo(**ciclo_dict)
    
    def criar_novo_ciclo(self, perfil: PerfilRisco, banca_inicial: float = 100.0) -> Ciclo:
        """Cria um novo ciclo com as configurações especificadas"""
        
        # Determina o número do ciclo
        ciclo_numero = len(self.ciclos) + 1
        
        # Verifica se já atingiu o limite de 5 ciclos
        if ciclo_numero > 5:
            raise ValueError("Limite de 5 ciclos atingido. Reinicie o sistema para começar novamente.")
        
        # Define stake inicial baseado na progressão
        if ciclo_numero <= len(self.PROGRESSAO_BANCA):
            stake_inicial = self.PROGRESSAO_BANCA[ciclo_numero - 1]
        else:
            stake_inicial = banca_inicial
        
        # Define objetivo porcentagem baseado no perfil
        if perfil == PerfilRisco.AGRESSIVO:
            objetivo_porcentagem = self.META_AGRESSIVO
            multiplicador = self.MULTIPLICADOR_AGRESSIVO
        else:
            objetivo_porcentagem = self.META_CONSERVADOR
            multiplicador = self.MULTIPLICADOR_CONSERVADOR
        
        # Calcula objetivo final
        objetivo_final = banca_inicial * multiplicador
        
        # Cria o ciclo
        novo_ciclo = Ciclo(
            ciclo_numero=ciclo_numero,
            perfil=perfil,
            banca_inicial=banca_inicial,
            stake_inicial=stake_inicial,
            objetivo_porcentagem=objetivo_porcentagem,
            objetivo_final=objetivo_final,
            entradas=[],
            lucro_acumulado=0.0,
            residuo_acumulado=0.0,
            banca_atual=banca_inicial,
            status="em_andamento",
            data_inicio=datetime.now().isoformat(),
            saque_teorico=0.0
        )
        
        self.ciclos.append(novo_ciclo)
        self.ciclo_atual = novo_ciclo
        self._salvar_dados()
        
        return novo_ciclo
    
    def adicionar_entrada(self, 
                         time_casa: str, 
                         time_fora: str, 
                         campeonato: str,
                         estrategia: str,
                         lucro_real: float,
                         resultado: str,
                         odds: Optional[Dict[str, float]] = None) -> Entrada:
        """Adiciona uma entrada ao ciclo atual"""
        
        if not self.ciclo_atual:
            raise ValueError("Não há ciclo em andamento. Crie um novo ciclo primeiro.")
        
        if self.ciclo_atual.status != "em_andamento":
            raise ValueError("O ciclo atual não está em andamento.")
        
        if len(self.ciclo_atual.entradas) >= self.MAX_ENTRADAS_POR_CICLO:
            raise ValueError(f"Limite de {self.MAX_ENTRADAS_POR_CICLO} entradas atingido para este ciclo.")
        
        # Número da entrada
        jogo_numero = len(self.ciclo_atual.entradas) + 1
        
        # Calcula banca de trabalho e teórica
        banca_trabalho = self.ciclo_atual.banca_atual
        banca_teorica = self.ciclo_atual.stake_inicial * (1 + self.ciclo_atual.objetivo_porcentagem) ** jogo_numero
        
        # Calcula objetivo valor
        objetivo_valor = banca_trabalho * self.ciclo_atual.objetivo_porcentagem
        
        # Calcula resíduo
        residuo = lucro_real - objetivo_valor
        
        # Cria a entrada
        entrada = Entrada(
            jogo_numero=jogo_numero,
            time_casa=time_casa,
            time_fora=time_fora,
            campeonato=campeonato,
            estrategia=estrategia,
            stake_inicial=self.ciclo_atual.stake_inicial,
            banca_trabalho=banca_trabalho,
            banca_teorica=banca_teorica,
            objetivo_porcentagem=self.ciclo_atual.objetivo_porcentagem,
            objetivo_valor=objetivo_valor,
            lucro_real=lucro_real,
            resultado=resultado,
            residuo=residuo,
            data_hora=datetime.now().isoformat(),
            odds=odds
        )
        
        # Adiciona ao ciclo
        self.ciclo_atual.entradas.append(entrada)
        
        # Atualiza ciclo
        self.ciclo_atual.lucro_acumulado += lucro_real
        self.ciclo_atual.residuo_acumulado += residuo
        self.ciclo_atual.banca_atual += lucro_real
        
        # Verifica se completou as 10 entradas
        if len(self.ciclo_atual.entradas) >= self.MAX_ENTRADAS_POR_CICLO:
            self._finalizar_ciclo()
        
        self._salvar_dados()
        
        return entrada
    
    def _finalizar_ciclo(self):
        """Finaliza o ciclo atual e calcula saque teórico"""
        if not self.ciclo_atual:
            return
        
        self.ciclo_atual.status = "concluido"
        self.ciclo_atual.data_fim = datetime.now().isoformat()
        
        # Calcula saque teórico (baseado na planilha)
        if self.ciclo_atual.lucro_acumulado > 0:
            # Saque de 50% do lucro para ciclos iniciais, ajustando para ciclos posteriores
            if self.ciclo_atual.ciclo_numero <= 2:
                self.ciclo_atual.saque_teorico = self.ciclo_atual.lucro_acumulado * 0.5
            else:
                self.ciclo_atual.saque_teorico = self.ciclo_atual.lucro_acumulado * 0.4
        
        self.ciclo_atual = None
    
    def obter_estatisticas_ciclo(self, ciclo_numero: int) -> Dict[str, Any]:
        """Obtém estatísticas detalhadas de um ciclo específico"""
        ciclo = next((c for c in self.ciclos if c.ciclo_numero == ciclo_numero), None)
        
        if not ciclo:
            return {}
        
        # Estatísticas por estratégia
        stats_estrategia = {}
        for entrada in ciclo.entradas:
            if entrada.estrategia not in stats_estrategia:
                stats_estrategia[entrada.estrategia] = {
                    'quantidade': 0,
                    'lucro_total': 0.0,
                    'acertos': 0,
                    'erros': 0
                }
            
            stats_estrategia[entrada.estrategia]['quantidade'] += 1
            stats_estrategia[entrada.estrategia]['lucro_total'] += entrada.lucro_real
            
            if entrada.resultado == "OK":
                stats_estrategia[entrada.estrategia]['acertos'] += 1
            else:
                stats_estrategia[entrada.estrategia]['erros'] += 1
        
        # Estatísticas por campeonato
        stats_campeonato = {}
        for entrada in ciclo.entradas:
            if entrada.campeonato not in stats_campeonato:
                stats_campeonato[entrada.campeonato] = {
                    'quantidade': 0,
                    'lucro_total': 0.0
                }
            
            stats_campeonato[entrada.campeonato]['quantidade'] += 1
            stats_campeonato[entrada.campeonato]['lucro_total'] += entrada.lucro_real
        
        return {
            'ciclo': ciclo.to_dict(),
            'stats_estrategia': stats_estrategia,
            'stats_campeonato': stats_campeonato,
            'progresso': len(ciclo.entradas) / self.MAX_ENTRADAS_POR_CICLO * 100
        }
    
    def obter_resumo_geral(self) -> Dict[str, Any]:
        """Obtém resumo geral de todos os ciclos"""
        total_ciclos = len(self.ciclos)
        ciclos_concluidos = len([c for c in self.ciclos if c.status == "concluido"])
        
        lucro_total = sum(c.lucro_acumulado for c in self.ciclos)
        residuo_total = sum(c.residuo_acumulado for c in self.ciclos)
        
        # Cálculo de ROI total
        banca_total_investida = sum(c.banca_inicial for c in self.ciclos)
        roi_total = (lucro_total / banca_total_investida * 100) if banca_total_investida > 0 else 0
        
        return {
            'total_ciclos': total_ciclos,
            'ciclos_concluidos': ciclos_concluidos,
            'ciclo_atual': self.ciclo_atual.to_dict() if self.ciclo_atual else None,
            'lucro_total': lucro_total,
            'residuo_total': residuo_total,
            'roi_total': roi_total,
            'banca_atual': self.ciclo_atual.banca_atual if self.ciclo_atual else 0
        }
    
    def verificar_pode_avancar(self) -> Tuple[bool, str]:
        """Verifica se pode avançar para o próximo ciclo"""
        if not self.ciclo_atual:
            return True, "Crie um novo ciclo para começar"
        
        if len(self.ciclo_atual.entradas) < self.MAX_ENTRADAS_POR_CICLO:
            return False, f"Complete as {self.MAX_ENTRADAS_POR_CICLO} entradas do ciclo atual primeiro"
        
        if self.ciclo_atual.status == "concluido":
            return True, "Ciclo concluído. Pode criar um novo ciclo"
        
        return False, "Complete o ciclo atual primeiro"
    
    def obter_estrategias_disponiveis(self) -> List[str]:
        """Obtém lista de estratégias disponíveis"""
        return [e.value for e in Estrategia]
    
    def verificar_alerta_estrategia(self, estrategia: str) -> Optional[str]:
        """Verifica se a estratégia requer alerta especial"""
        if estrategia == Estrategia.BACK_FAVORITO_VENCENDO.value:
            return "Aviso: Esta é a estratégia mais perigosa para o método. Exige muito tempo de exposição para bater a meta de lucro. Use apenas na iminência de um 2 a 0 ou feche a posição se o time recuar"
        return None


# Funções auxiliares para integração com Flask
def inicializar_sistema_ciclos():
    """Inicializa o sistema de ciclos para uso na aplicação web"""
    return CiclosManager()


def obter_dados_para_interface(manager: CiclosManager) -> Dict[str, Any]:
    """Obtém dados formatados para a interface web"""
    resumo = manager.obter_resumo_geral()
    
    # Dados do ciclo atual
    ciclo_atual_dados = None
    if manager.ciclo_atual:
        ciclo_atual_dados = manager.obter_estatisticas_ciclo(manager.ciclo_atual.ciclo_numero)
    
    return {
        'resumo_geral': resumo,
        'ciclo_atual': ciclo_atual_dados,
        'pode_avancar': manager.verificar_pode_avancar(),
        'estrategias': manager.obter_estrategias_disponiveis(),
        'max_entradas': manager.MAX_ENTRADAS_POR_CICLO
    }


if __name__ == "__main__":
    # Teste do sistema
    print("Sistema de Método de Ciclos - Teste")
    print("=" * 70)
    
    manager = CiclosManager()
    
    # Criar novo ciclo conservador
    print("\nCriando novo ciclo conservador...")
    ciclo = manager.criar_novo_ciclo(PerfilRisco.CONSERVADOR, 100.0)
    print(f"Ciclo {ciclo.ciclo_numero} criado com sucesso!")
    print(f"Banca inicial: R$ {ciclo.banca_inicial:.2f}")
    print(f"Stake inicial: R$ {ciclo.stake_inicial:.2f}")
    print(f"Objetivo por entrada: {ciclo.objetivo_porcentagem * 100:.1f}%")
    print(f"Objetivo final: R$ {ciclo.objetivo_final:.2f}")
    
    # Adicionar algumas entradas de teste
    print("\nAdicionando entradas de teste...")
    entrada1 = manager.adicionar_entrada(
        time_casa="Brasil",
        time_fora="Argentina",
        campeonato="Copa do Mundo",
        estrategia="Lay Favorito (1º Tempo)",
        lucro_real=4.5,
        resultado="OK"
    )
    print(f"Entrada 1: Lucro R$ {entrada1.lucro_real:.2f}, Resíduo R$ {entrada1.residuo:.2f}")
    
    # Mostrar resumo
    resumo = manager.obter_resumo_geral()
    print(f"\nResumo geral:")
    print(f"Total de ciclos: {resumo['total_ciclos']}")
    print(f"Lucro total: R$ {resumo['lucro_total']:.2f}")
    print(f"ROI total: {resumo['roi_total']:.1f}%")