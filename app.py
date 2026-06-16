#!/usr/bin/env python3
# =============================================================================
# app.py — Aplicação Web Flask para Flashscore Lay Analyzer
# =============================================================================

from flask import Flask, render_template_string, request, jsonify
from datetime import date, timedelta, datetime
import sys
import os
import requests

# Adiciona o diretório atual ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import setup_driver, coletar_jogos_do_dia, coletar_h2h, coletar_odds
from analyzer import (
    calcular_frequencias_jogo,
    classificar_oportunidade,
    construir_dataframe,
    é_copa_do_mundo,
    Cores
)
from ciclos_manager import (
    CiclosManager, 
    PerfilRisco, 
    obter_dados_para_interface,
    inicializar_sistema_ciclos
)
import config
import os

app = Flask(__name__)

# Inicializar sistema de ciclos
ciclos_manager = inicializar_sistema_ciclos()

# Template HTML expandido com Método de Ciclos
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flashscore Lay Analyzer - Método de Ciclos</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 20px;
        }
        
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #ddd;
        }
        
        .tab {
            padding: 15px 20px;
            cursor: pointer;
            background: #f5f5f5;
            border: none;
            border-bottom: 3px solid transparent;
            font-weight: bold;
            transition: all 0.3s;
        }
        
        .tab:hover {
            background: #e0e0e0;
        }
        
        .tab.active {
            background: white;
            border-bottom: 3px solid #667eea;
            color: #667eea;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #555;
        }
        
        select, input, button {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
        }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: bold;
            transition: transform 0.2s;
        }
        
        button:hover {
            transform: scale(1.02);
        }
        
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .loading {
            text-align: center;
            margin: 20px 0;
            display: none;
        }
        
        .loading.active {
            display: block;
        }
        
        .results {
            margin-top: 30px;
            display: none;
        }
        
        .results.active {
            display: block;
        }
        
        .game-card {
            border: 2px solid #eee;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            transition: all 0.3s;
        }
        
        .game-card:hover {
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .game-copa {
            background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
            border: 2px solid #ff9800;
        }
        
        .game-header {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .lay-indicator {
            font-size: 16px;
            font-weight: bold;
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
        
        .lay-1x0 {
            background: #4CAF50;
            color: white;
        }
        
        .lay-0x1 {
            background: #2196F3;
            color: white;
        }
        
        .metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 10px;
        }
        
        .metric {
            background: #f5f5f5;
            padding: 8px;
            border-radius: 5px;
            text-align: center;
        }
        
        .metric-label {
            font-size: 12px;
            color: #666;
        }
        
        .metric-value {
            font-size: 16px;
            font-weight: bold;
            color: #333;
        }
        
        .no-results {
            text-align: center;
            padding: 20px;
            color: #666;
            font-style: italic;
        }
        
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            display: none;
        }
        
        .error.active {
            display: block;
        }
        
        /* Estilos do Método de Ciclos */
        .ciclo-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .ciclo-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }
        
        .entradas-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .entradas-table th,
        .entradas-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        .entradas-table th {
            background: #667eea;
            color: white;
        }
        
        .entradas-table tr:hover {
            background: #f5f5f5;
        }
        
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        
        .alert-box {
            background: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }
        
        .warning-box {
            background: #d4edda;
            border: 1px solid #28a745;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }
        
        .planilha-section {
            background: #e3f2fd;
            padding: 20px;
            border-radius: 10px;
            margin-top: 30px;
            border: 2px solid #2196F3;
        }
        
        .tooltip {
            position: relative;
            display: inline-block;
        }
        
        .tooltip .tooltip-text {
            visibility: hidden;
            width: 300px;
            background-color: #555;
            color: white;
            text-align: center;
            border-radius: 6px;
            padding: 10px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -150px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 12px;
        }
        
        .tooltip:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        
        .modal.active {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .modal-content {
            background: white;
            padding: 30px;
            border-radius: 15px;
            max-width: 500px;
            width: 90%;
            position: relative;
        }
        
        .close-btn {
            position: absolute;
            top: 10px;
            right: 15px;
            font-size: 28px;
            cursor: pointer;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 Flashscore Lay Analyzer</h1>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('analise')">Análise de Jogos</button>
            <button class="tab" onclick="switchTab('ciclos')">Método de Ciclos</button>
        </div>
        
        <!-- Tab: Análise de Jogos -->
        <div id="tab-analise" class="tab-content active">
            <div class="warning-box" id="cloud-warning" style="display: none;">
                <strong>⚠️ Modo Nuvem Detectado:</strong> A análise de jogos em tempo real não está disponível na versão em nuvem, pois requer Firefox/Selenium que não funcionam em ambiente de nuvem gratuito. Use o <strong>Método de Ciclos</strong> para gerenciar suas operações ou execute a análise localmente.
            </div>
            
            <div class="form-group">
                <label for="dias">Selecione o dia:</label>
                <select id="dias">
                    <option value="0">Hoje</option>
                    <option value="1">Amanhã</option>
                    <option value="2">Depois de amanhã</option>
                </select>
            </div>
            
            <button onclick="analisar()" id="btn-analisar">🔍 Analisar Jogos</button>
            
            <div class="loading" id="loading">
                <p>⏳ Analisando jogos... Isso pode levar alguns minutos...</p>
            </div>
            
            <div class="error" id="error"></div>
            
            <div class="results" id="results">
                <div id="games-container"></div>
            </div>
        </div>
        
        <!-- Tab: Método de Ciclos -->
        <div id="tab-ciclos" class="tab-content">
            <div class="warning-box">
                <strong>⚠️ Aviso Importante:</strong> Recomendamos operar o método em dinheiro real (mesmo com stakes mínimas), pois o modo treino não simula o peso emocional necessário para este método.
            </div>
            
            <div id="ciclo-conteudo">
                <!-- Conteúdo será carregado via JavaScript -->
            </div>
            
            <div class="planilha-section">
                <h3>📊 Planilha Oficial de Ciclos</h3>
                <p style="margin: 15px 0; font-weight: bold; color: #c62828;">
                    ⚠️ Para utilizar a planilha, você NÃO deve solicitar acesso de edição. Ao abrir o link, clique em 'Arquivo > Fazer uma cópia' (ou 'File > Make a copy') para salvá-la no seu computador ou Google Drive
                </p>
                <button onclick="abrirPlanilha()">📋 Abrir Planilha Oficial</button>
            </div>
        </div>
    </div>
    
    <!-- Modal para alerta de estratégia -->
    <div id="modal-alerta" class="modal">
        <div class="modal-content">
            <span class="close-btn" onclick="fecharModal()">&times;</span>
            <h3 style="color: #c62828; margin-bottom: 15px;">⚠️ Alerta de Estratégia</h3>
            <p id="modal-texto"></p>
        </div>
    </div>
    
    <script>
        // Alternar abas
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
            document.getElementById(`tab-${tabName}`).classList.add('active');
            
            if (tabName === 'ciclos') {
                carregarDadosCiclos();
            }
        }
        
        // Análise de jogos (função existente)
        function analisar() {
            const dias = document.getElementById('dias').value;
            const btn = document.getElementById('btn-analisar');
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');
            const error = document.getElementById('error');
            
            loading.classList.add('active');
            results.classList.remove('active');
            error.classList.remove('active');
            btn.disabled = true;
            
            fetch('/api/analizar?dias=' + dias)
                .then(response => response.json())
                .then(data => {
                    loading.classList.remove('active');
                    btn.disabled = false;
                    
                    // Verificar se está em modo nuvem
                    if (data.cloud_mode) {
                        document.getElementById('cloud-warning').style.display = 'block';
                        error.textContent = '⚠️ ' + data.message;
                        error.classList.add('active');
                        return;
                    }
                    
                    if (data.error) {
                        error.textContent = '❌ ' + data.error;
                        error.classList.add('active');
                        return;
                    }
                    
                    if (data.jogos.length === 0) {
                        document.getElementById('games-container').innerHTML = 
                            '<div class="no-results">Nenhum jogo encontrado para análise.</div>';
                        results.classList.add('active');
                        return;
                    }
                    
                    let html = '';
                    data.jogos.forEach(jogo => {
                        const isCopa = jogo.is_copa_do_mundo;
                        const copaClass = isCopa ? 'game-copa' : '';
                        const copaIcon = isCopa ? '🏆 ' : '';
                        
                        let layClass = '';
                        let layText = jogo.tipo_lay;
                        if (jogo.tipo_lay === 'LAY_1X0') {
                            layClass = 'lay-1x0';
                            layText = '✓ LAY 1X0 RECOMENDADO';
                        } else if (jogo.tipo_lay === 'LAY_0X1') {
                            layClass = 'lay-0x1';
                            layText = '✓ LAY 0X1 RECOMENDADO';
                        }
                        
                        html += `
                            <div class="game-card ${copaClass}">
                                <div class="game-header">
                                    ${copaIcon}${jogo.hora} - ${jogo.time_casa} vs ${jogo.time_fora}
                                </div>
                                <div class="lay-indicator ${layClass}">
                                    ${layText}
                                </div>
                                <div class="metrics">
                                    <div class="metric">
                                        <div class="metric-label">EV</div>
                                        <div class="metric-value">${jogo.ev?.toFixed(3) || 'N/A'}</div>
                                    </div>
                                    <div class="metric">
                                        <div class="metric-label">Retorno</div>
                                        <div class="metric-value">${jogo.retorno?.toFixed(1) || 'N/A'}%</div>
                                    </div>
                                    <div class="metric">
                                        <div class="metric-label">Probabilidade</div>
                                        <div class="metric-value">${(jogo.probabilidade * 100).toFixed(1)}%</div>
                                    </div>
                                    <div class="metric">
                                        <div class="metric-label">Média Gols</div>
                                        <div class="metric-value">${jogo.media_gols?.toFixed(1) || 'N/A'}</div>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    
                    document.getElementById('games-container').innerHTML = html;
                    results.classList.add('active');
                })
                .catch(err => {
                    loading.classList.remove('active');
                    btn.disabled = false;
                    error.textContent = '❌ Erro ao analisar: ' + err.message;
                    error.classList.add('active');
                });
        }
        
        // Funções do Método de Ciclos
        function carregarDadosCiclos() {
            fetch('/api/ciclos/dados')
                .then(response => response.json())
                .then(data => {
                    renderizarCiclos(data);
                })
                .catch(err => {
                    document.getElementById('ciclo-conteudo').innerHTML = 
                        '<div class="error">Erro ao carregar dados dos ciclos: ' + err.message + '</div>';
                });
        }
        
        function renderizarCiclos(data) {
            const container = document.getElementById('ciclo-conteudo');
            const resumo = data.resumo_geral;
            const cicloAtual = data.ciclo_atual;
            
            let html = '';
            
            // Resumo geral
            html += `
                <div class="ciclo-stats">
                    <div class="stat-card">
                        <div class="stat-value">${resumo.total_ciclos}</div>
                        <div class="stat-label">Ciclos Totais</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">R$ ${resumo.lucro_total.toFixed(2)}</div>
                        <div class="stat-label">Lucro Total</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${resumo.roi_total.toFixed(1)}%</div>
                        <div class="stat-label">ROI Total</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">R$ ${resumo.banca_atual.toFixed(2)}</div>
                        <div class="stat-label">Banca Atual</div>
                    </div>
                </div>
            `;
            
            // Ciclo atual ou criar novo
            if (resumo.ciclo_atual) {
                html += renderizarCicloAtual(resumo.ciclo_atual, data.pode_avancar, data.estrategias);
            } else {
                html += renderizarCriarCiclo();
            }
            
            container.innerHTML = html;
        }
        
        function renderizarCicloAtual(ciclo, podeAvancar, estrategias) {
            const cicloData = ciclo.ciclo;
            const progresso = ciclo.progresso;
            const entradas = cicloData.entradas;
            
            let html = `
                <div class="ciclo-header">
                    <h2>🔄 Ciclo ${cicloData.ciclo_numero} - ${cicloData.perfil.toUpperCase()}</h2>
                    <p>Status: ${cicloData.status === 'em_andamento' ? '🔄 Em Andamento' : '✅ Concluído'}</p>
                </div>
                
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${progresso}%">
                        ${Math.round(progresso)}% (${entradas.length}/10 entradas)
                    </div>
                </div>
                
                <div class="ciclo-stats">
                    <div class="stat-card">
                        <div class="stat-value">R$ ${cicloData.banca_inicial.toFixed(2)}</div>
                        <div class="stat-label">Banca Inicial</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">R$ ${cicloData.banca_atual.toFixed(2)}</div>
                        <div class="stat-label">Banca Atual</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">R$ ${cicloData.lucro_acumulado.toFixed(2)}</div>
                        <div class="stat-label">Lucro Acumulado</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${(cicloData.objetivo_porcentagem * 100).toFixed(1)}%</div>
                        <div class="stat-label">Meta por Entrada</div>
                    </div>
                </div>
            `;
            
            // Formulário para adicionar entrada (se ciclo em andamento)
            if (cicloData.status === 'em_andamento' && entradas.length < 10) {
                html += `
                    <div style="background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <h3>➕ Adicionar Nova Entrada</h3>
                        <div class="form-group">
                            <label>Time Casa:</label>
                            <input type="text" id="entrada-time-casa" placeholder="Ex: Brasil">
                        </div>
                        <div class="form-group">
                            <label>Time Fora:</label>
                            <input type="text" id="entrada-time-fora" placeholder="Ex: Argentina">
                        </div>
                        <div class="form-group">
                            <label>Campeonato:</label>
                            <input type="text" id="entrada-campeonato" placeholder="Ex: Copa do Mundo">
                        </div>
                        <div class="form-group">
                            <label>Estratégia:</label>
                            <select id="entrada-estrategia" onchange="verificarAlertaEstrategia(this.value)">
                                <option value="">Selecione...</option>
                                ${estrategias.map(e => `<option value="${e}">${e}</option>`).join('')}
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Lucro Real (R$):</label>
                            <input type="number" id="entrada-lucro" step="0.01" placeholder="Ex: 4.50">
                        </div>
                        <div class="form-group">
                            <label>Resultado:</label>
                            <select id="entrada-resultado">
                                <option value="OK">✅ OK (Acerto)</option>
                                <option value="NOK">❌ NOK (Erro)</option>
                            </select>
                        </div>
                        <button onclick="adicionarEntrada()">➕ Adicionar Entrada</button>
                    </div>
                `;
            }
            
            // Tabela de entradas
            if (entradas.length > 0) {
                html += `
                    <h3>📋 Histórico de Entradas</h3>
                    <table class="entradas-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Jogo</th>
                                <th>Estratégia</th>
                                <th>Lucro</th>
                                <th>Resíduo</th>
                                <th>Resultado</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${entradas.map(e => `
                                <tr>
                                    <td>${e.jogo_numero}</td>
                                    <td>${e.time_casa} vs ${e.time_fora}</td>
                                    <td>${e.estrategia}</td>
                                    <td style="color: ${e.lucro_real >= 0 ? 'green' : 'red'}">R$ ${e.lucro_real.toFixed(2)}</td>
                                    <td>R$ ${e.residuo.toFixed(2)}</td>
                                    <td>${e.resultado === 'OK' ? '✅' : '❌'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            }
            
            // Botão para criar próximo ciclo (se atual concluído)
            if (cicloData.status === 'concluido' && podeAvancar[0]) {
                html += `
                    <div style="margin-top: 20px;">
                        <button onclick="mostrarCriarProximoCiclo()">🔄 Criar Próximo Ciclo</button>
                    </div>
                `;
            }
            
            return html;
        }
        
        function renderizarCriarCiclo() {
            return `
                <div style="text-align: center; padding: 40px;">
                    <h2>🚀 Começar Novo Ciclo</h2>
                    <p style="margin: 20px 0; color: #666;">Inicie sua jornada no Método de Ciclos do Netuno</p>
                    
                    <div style="max-width: 400px; margin: 20px auto; text-align: left;">
                        <div class="form-group">
                            <label>Perfil de Risco:</label>
                            <select id="novo-ciclo-perfil">
                                <option value="conservador">🛡️ Conservador (4% por entrada)</option>
                                <option value="moderado">⚖️ Moderado (4-5% por entrada)</option>
                                <option value="agressivo">🚀 Agressivo (8% por entrada)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Banca Inicial (R$):</label>
                            <input type="number" id="novo-ciclo-banca" value="100" step="0.01">
                        </div>
                        <button onclick="criarNovoCiclo()">🚀 Criar Ciclo</button>
                    </div>
                </div>
            `;
        }
        
        function verificarAlertaEstrategia(estrategia) {
            if (estrategia === 'Back Favorito vencendo') {
                document.getElementById('modal-texto').textContent = 
                    'Aviso: Esta é a estratégia mais perigosa para o método. Exige muito tempo de exposição para bater a meta de lucro. Use apenas na iminência de um 2 a 0 ou feche a posição se o time recuar';
                document.getElementById('modal-alerta').classList.add('active');
            }
        }
        
        function fecharModal() {
            document.getElementById('modal-alerta').classList.remove('active');
        }
        
        function criarNovoCiclo() {
            const perfil = document.getElementById('novo-ciclo-perfil').value;
            const banca = parseFloat(document.getElementById('novo-ciclo-banca').value);
            
            fetch('/api/ciclos/criar', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({perfil, banca_inicial: banca})
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Erro: ' + data.error);
                } else {
                    carregarDadosCiclos();
                }
            })
            .catch(err => alert('Erro: ' + err.message));
        }
        
        function adicionarEntrada() {
            const entrada = {
                time_casa: document.getElementById('entrada-time-casa').value,
                time_fora: document.getElementById('entrada-time-fora').value,
                campeonato: document.getElementById('entrada-campeonato').value,
                estrategia: document.getElementById('entrada-estrategia').value,
                lucro_real: parseFloat(document.getElementById('entrada-lucro').value),
                resultado: document.getElementById('entrada-resultado').value
            };
            
            fetch('/api/ciclos/adicionar-entrada', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(entrada)
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Erro: ' + data.error);
                } else {
                    carregarDadosCiclos();
                }
            })
            .catch(err => alert('Erro: ' + err.message));
        }
        
        function mostrarCriarProximoCiclo() {
            document.getElementById('ciclo-conteudo').innerHTML = renderizarCriarCiclo();
        }
        
        function abrirPlanilha() {
            // Substitua com o link real da planilha do Google Sheets
            window.open('https://docs.google.com/spreadsheets/d/SUA_PLANILHA_AQUI', '_blank');
        }
        
        // Carregar dados iniciais
        document.addEventListener('DOMContentLoaded', function() {
            // Carrega dados de ciclos se a aba estiver ativa
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/analizar')
def analisar():
    """API para analisar jogos - consume API local se estiver em nuvem."""
    # Verificar se está em ambiente de nuvem
    is_cloud = os.environ.get('RENDER', 'false').lower() == 'true'
    
    if is_cloud:
        # Em nuvem, tentar consumir API local
        try:
            dias = int(request.args.get('dias', 0))
            
            # Chamar API local
            local_api_url = config.LOCAL_API_URL
            
            print(f"[NUVEM] Tentando conectar ao sistema local: {local_api_url}")
            
            response = requests.post(
                f"{local_api_url}/api/local/analizar",
                json={'dias': dias},
                headers={'X-API-Key': config.LOCAL_API_KEY},
                timeout=config.LOCAL_API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return jsonify({
                        'error': None,
                        'jogos': data.get('jogos', []),
                        'total': data.get('total', 0),
                        'source': 'local_api',
                        'timestamp': data.get('timestamp')
                    })
                else:
                    return jsonify({
                        'error': data.get('error', 'Erro na análise local'),
                        'jogos': [],
                        'source': 'local_api_error'
                    })
            elif response.status_code == 401:
                return jsonify({
                    'error': 'Erro de autenticação com sistema local',
                    'jogos': [],
                    'cloud_mode': True,
                    'message': 'A chave de API não corresponde. Verifique a configuração LOCAL_API_KEY no Render.'
                })
            else:
                return jsonify({
                    'error': f'Sistema local não respondeu (Status: {response.status_code})',
                    'jogos': [],
                    'cloud_mode': True,
                    'message': 'Verifique se o sistema local está rodando (INICIAR.bat) e se o IP está configurado corretamente.'
                })
                
        except requests.exceptions.Timeout:
            return jsonify({
                'error': 'Tempo esgotado ao conectar ao sistema local',
                'jogos': [],
                'cloud_mode': True,
                'message': 'O scraping demorou mais que 5 minutos. Verifique sua conexão ou execute a análise localmente.'
            })
        except requests.exceptions.ConnectionError:
            return jsonify({
                'error': 'Não foi possível conectar ao sistema local',
                'jogos': [],
                'cloud_mode': True,
                'message': 'Verifique se o sistema local está rodando (execute INICIAR.bat) e se o IP está configurado corretamente no ambiente de variáveis LOCAL_API_URL.'
            })
        except Exception as e:
            return jsonify({
                'error': f'Erro ao conectar ao sistema local: {str(e)}',
                'jogos': [],
                'cloud_mode': True,
                'message': 'Verifique a configuração do sistema local.'
            })
    
    # Execução local normal
    try:
        dias = int(request.args.get('dias', 0))
        
        # Iniciar driver
        driver = setup_driver(headless=True)
        
        # Coletar jogos
        jogos = coletar_jogos_do_dia(driver, dias_frente=dias)
        
        if not jogos:
            driver.quit()
            return jsonify({'error': 'Nenhum jogo encontrado', 'jogos': []})
        
        # Processar jogos (sequencial para simplificar)
        jogos_processados = []
        for jogo in jogos:
            try:
                # Coletar H2H
                h2h = coletar_h2h(driver, jogo["url"], jogo["id"])
                
                # Coletar odds
                odds = coletar_odds(driver, jogo["id"], url_jogo=jogo["url"])
                
                # Analisar
                freqs = calcular_frequencias_jogo(h2h, odds)
                classif, tipo_lay = classificar_oportunidade(freqs, odds, config.LIMIAR_OPORTUNIDADE)
                
                # Extrair métricas para exibição
                ev_key = f'ev_{tipo_lay.lower().replace("lay_", "")}'
                retorno_key = f'retorno_{tipo_lay.lower().replace("lay_", "")}'
                prob_key = f'prob_estimada_{tipo_lay.lower().replace("lay_", "")}'
                
                jogos_processados.append({
                    'hora': jogo['hora'],
                    'time_casa': jogo['time_casa'],
                    'time_fora': jogo['time_fora'],
                    'is_copa_do_mundo': é_copa_do_mundo(jogo['time_casa'], jogo['time_fora']),
                    'tipo_lay': tipo_lay,
                    'classificacao': classif,
                    'ev': freqs.get(ev_key, 0.0),
                    'retorno': freqs.get(retorno_key, 0.0),
                    'probabilidade': freqs.get(prob_key, 0.0),
                    'media_gols': freqs.get('media_gols_confronto', 0.0)
                })
            except Exception as e:
                print(f"Erro ao processar jogo {jogo['id']}: {e}")
                continue
        
        driver.quit()
        
        return jsonify({
            'error': None,
            'jogos': jogos_processados,
            'total': len(jogos_processados),
            'source': 'local'
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'jogos': []})


# =============================================================================
# ROTAS DO MÉTODO DE CICLOS
# =============================================================================

@app.route('/api/ciclos/dados')
def ciclos_dados():
    """API para obter dados do sistema de ciclos."""
    try:
        dados = obter_dados_para_interface(ciclos_manager)
        return jsonify(dados)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/ciclos/criar', methods=['POST'])
def criar_ciclo():
    """API para criar um novo ciclo."""
    try:
        data = request.json
        perfil = data.get('perfil', 'conservador')
        banca_inicial = data.get('banca_inicial', 100.0)
        
        # Converter string de perfil para enum
        try:
            perfil_enum = PerfilRisco(perfil)
        except ValueError:
            return jsonify({'error': 'Perfil inválido. Use: conservador, moderado ou agressivo'})
        
        ciclo = ciclos_manager.criar_novo_ciclo(perfil_enum, banca_inicial)
        return jsonify({'success': True, 'ciclo': ciclo.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/ciclos/adicionar-entrada', methods=['POST'])
def adicionar_entrada_ciclo():
    """API para adicionar uma entrada ao ciclo atual."""
    try:
        data = request.json
        
        entrada = ciclos_manager.adicionar_entrada(
            time_casa=data.get('time_casa'),
            time_fora=data.get('time_fora'),
            campeonato=data.get('campeonato'),
            estrategia=data.get('estrategia'),
            lucro_real=data.get('lucro_real', 0.0),
            resultado=data.get('resultado', 'NOK'),
            odds=data.get('odds')
        )
        
        return jsonify({'success': True, 'entrada': entrada.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/ciclos/estatisticas/<int:ciclo_numero>')
def estatisticas_ciclo(ciclo_numero):
    """API para obter estatísticas detalhadas de um ciclo."""
    try:
        stats = ciclos_manager.obter_estatisticas_ciclo(ciclo_numero)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/ciclos/resumo')
def resumo_ciclos():
    """API para obter resumo geral de todos os ciclos."""
    try:
        resumo = ciclos_manager.obter_resumo_geral()
        return jsonify(resumo)
    except Exception as e:
        return jsonify({'error': str(e)})


# =============================================================================
# API PARA COMUNICAÇÃO LOCAL → NUVEM
# =============================================================================

def verificar_autenticacao():
    """Verifica se a requisição tem a chave de API correta."""
    api_key = request.headers.get('X-API-Key')
    return api_key == config.LOCAL_API_KEY


@app.route('/api/local/analizar', methods=['POST'])
def analisar_local_para_nuvem():
    """
    API para sistema local executar análise e enviar para nuvem.
    Chamado pela nuvem quando precisa de dados de análise.
    """
    # Verificar autenticação
    if not verificar_autenticacao():
        return jsonify({
            'success': False,
            'error': 'Não autorizado - chave de API inválida'
        }), 401
    
    try:
        data = request.json
        dias = data.get('dias', 0)
        
        print(f"[API LOCAL] Recebida requisição de análise da nuvem - dias: {dias}")
        
        # Verificar se não está em modo nuvem
        if os.environ.get('RENDER', 'false').lower() == 'true':
            return jsonify({
                'success': False,
                'error': 'Esta API não deve ser chamada na nuvem',
                'message': 'Use a API local para executar análise'
            })
        
        # Executar análise completa (com scraping)
        driver = setup_driver(headless=True)
        
        # Coletar jogos
        jogos = coletar_jogos_do_dia(driver, dias_frente=dias)
        
        if not jogos:
            driver.quit()
            print(f"[API LOCAL] Nenhum jogo encontrado")
            return jsonify({
                'success': False,
                'error': 'Nenhum jogo encontrado',
                'jogos': []
            })
        
        print(f"[API LOCAL] Encontrados {len(jogos)} jogos para analisar")
        
        # Processar jogos
        jogos_processados = []
        for i, jogo in enumerate(jogos):
            try:
                print(f"[API LOCAL] Processando jogo {i+1}/{len(jogos)}: {jogo['time_casa']} vs {jogo['time_fora']}")
                
                # Coletar H2H
                h2h = coletar_h2h(driver, jogo["url"], jogo["id"])
                
                # Coletar odds
                odds = coletar_odds(driver, jogo["id"], url_jogo=jogo["url"])
                
                # Analisar
                freqs = calcular_frequencias_jogo(h2h, odds)
                classif, tipo_lay = classificar_oportunidade(freqs, odds, config.LIMIAR_OPORTUNIDADE)
                
                # Extrair métricas para exibição
                ev_key = f'ev_{tipo_lay.lower().replace("lay_", "")}'
                retorno_key = f'retorno_{tipo_lay.lower().replace("lay_", "")}'
                prob_key = f'prob_estimada_{tipo_lay.lower().replace("lay_", "")}'
                
                jogos_processados.append({
                    'hora': jogo['hora'],
                    'time_casa': jogo['time_casa'],
                    'time_fora': jogo['time_fora'],
                    'is_copa_do_mundo': é_copa_do_mundo(jogo['time_casa'], jogo['time_fora']),
                    'tipo_lay': tipo_lay,
                    'classificacao': classif,
                    'ev': freqs.get(ev_key, 0.0),
                    'retorno': freqs.get(retorno_key, 0.0),
                    'probabilidade': freqs.get(prob_key, 0.0),
                    'media_gols': freqs.get('media_gols_confronto', 0.0)
                })
            except Exception as e:
                print(f"[API LOCAL] Erro ao processar jogo {jogo['id']}: {e}")
                continue
        
        driver.quit()
        
        print(f"[API LOCAL] Análise concluída - {len(jogos_processados)} jogos processados")
        
        return jsonify({
            'success': True,
            'jogos': jogos_processados,
            'total': len(jogos_processados),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"[API LOCAL] Erro na análise: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'jogos': []
        })


@app.route('/api/local/status')
def status_sistema_local():
    """API para verificar se sistema local está ativo."""
    # Verificar autenticação
    if not verificar_autenticacao():
        return jsonify({
            'success': False,
            'error': 'Não autorizado - chave de API inválida'
        }), 401
    
    try:
        return jsonify({
            'success': True,
            'status': 'online',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0',
            'modo': 'local'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


if __name__ == '__main__':
    # Configuração para produção e desenvolvimento
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Em produção, usar 0.0.0.0 para aceitar conexões externas
    host = '0.0.0.0' if not debug else '127.0.0.1'
    
    if debug:
        print("=" * 60)
        print("FLASHSCORE LAY ANALYZER - MODO DESENVOLVIMENTO")
        print("=" * 60)
        print("Acesso LOCAL: http://localhost:5000")
        print("Acesso REDE: http://SEU_IP_LOCAL:5000")
        print("=" * 60)
        print()
        print("Para descobrir seu IP local:")
        print("  Windows: ipconfig | findstr IPv4")
        print("  Linux/Mac: ifconfig ou ip addr")
        print()
        print("Para acessar remotamente, use seu IP local:")
        print("  Exemplo: http://192.168.1.100:5000")
        print("=" * 60)
    else:
        print("=" * 60)
        print("FLASHSCORE LAY ANALYZER - MODO PRODUÇÃO")
        print("=" * 60)
        print(f"Servidor iniciado na porta: {port}")
        print("=" * 60)
    
    app.run(host=host, port=port, debug=debug)