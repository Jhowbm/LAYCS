# Método de Ciclos do Netuno - Documentação

## 📋 Visão Geral

O **Método de Ciclos do Netuno** é um sistema avançado de gestão de banca para apostas esportivas em exchanges (como Betfair), focado em Lay betting no correct score. Este sistema foi implementado no Flashscore Lay Analyzer para proporcionar uma gestão profissional e matemática de banca.

## 🎯 Características Principais

### **Estrutura de Ciclos**
- **5 ciclos progressivos** com gestão de banca automática
- **10 entradas obrigatórias** por ciclo
- **Progressão matemática** baseada na planilha original do Netuno

### **Perfis de Risco**
- **🛡️ Conservador**: 4% de lucro por entrada (objetivo final: 5x a banca inicial)
- **⚖️ Moderado**: 4-5% de lucro por entrada (objetivo final: 5x a banca inicial)
- **🚀 Agressivo**: 8% de lucro por entrada (objetivo final: 10x a banca inicial)

### **Gestão de Resíduos**
- Cálculo automático da diferença entre lucro real e meta
- Resíduos são acumulados sem afetar a obrigatoriedade das 10 entradas
- Sistema inteligente de gestão de banca

### **Estratégias Disponíveis**
1. **Lay Favorito (1º Tempo)**
2. **Lay Favorito (2º Tempo)**
3. **Lay Zebra (1º Tempo)**
4. **Lay Zebra (2º Tempo)**
5. **Back Favorito vencendo** ⚠️ (com alerta de risco)
6. **Back Zebra vencendo**
7. **Lay Favorito perdendo**

## 🚀 Como Usar

### **1. Iniciar a Aplicação Web**

```bash
# Ativar ambiente virtual (se necessário)
venv\Scripts\activate

# Iniciar a aplicação Flask
python app.py
```

A aplicação estará disponível em: `http://localhost:5000`

### **2. Navegar para o Método de Ciclos**

1. Abra o navegador e acesse `http://localhost:5000`
2. Clique na aba **"Método de Ciclos"**
3. Leia o aviso importante sobre operar em dinheiro real

### **3. Criar um Novo Ciclo**

1. Se não houver ciclo ativo, clique em **"Criar Ciclo"**
2. Escolha o **Perfil de Risco**:
   - Conservador para operação segura
   - Moderado para equilíbrio
   - Agressivo para maior retorno (maior risco)
3. Defina a **Banca Inicial** (padrão: R$ 100)
4. Clique em **"Criar Ciclo"**

### **4. Adicionar Entradas**

1. Preencha os dados do jogo:
   - Time Casa
   - Time Fora
   - Campeonato
2. Selecione a **Estratégia** utilizada
3. Informe o **Lucro Real** obtido
4. Selecione o **Resultado** (OK/NOK)
5. Clique em **"Adicionar Entrada"**

### **5. Acompanhar o Progresso**

- **Barra de progresso** mostra quantas entradas foram realizadas
- **Estatísticas em tempo real** de banca, lucro e ROI
- **Histórico completo** de todas as entradas
- **Gestão automática** de resíduos

### **6. Finalizar Ciclo e Avançar**

- Ao completar 10 entradas, o ciclo é finalizado automaticamente
- O sistema calcula o saque teórico
- Clique em **"Criar Próximo Ciclo"** para continuar

## 📊 Funcionalidades da Interface

### **Dashboard Principal**
- **Resumo Geral**: Total de ciclos, lucro total, ROI, banca atual
- **Ciclo Atual**: Status, progresso, estatísticas detalhadas
- **Formulário de Entrada**: Adição rápida de novas operações
- **Tabela de Histórico**: Registro completo de todas as entradas

### **Alertas e Avisos**
- **Aviso de operação real**: Recomendação de usar dinheiro real
- **Alerta de estratégia perigosa**: Aviso para "Back Favorito vencendo"
- **Validação de campos**: Impede entradas incompletas

### **Planilha Oficial**
- Link para planilha do Google Sheets
- Instruções claras de cópia (sem solicitar edição)
- Integração com o sistema web

## 🔧 Configuração e Personalização

### **Ajustar Metas por Perfil**

No arquivo `ciclos_manager.py`, você pode ajustar:

```python
# Linhas 53-56
META_CONSERVADOR = 0.04  # 4% - ajuste conforme necessário
META_AGRESSIVO = 0.08    # 8% - ajuste conforme necessário

MULTIPLICADOR_CONSERVADOR = 5.0  # 5x - multiplicador final
MULTIPLICADOR_AGRESSIVO = 10.0   # 10x - multiplicador final
```

### **Progressão de Banca**

A progressão segue a planilha original:

```python
# Linha 51
PROGRESSAO_BANCA = [100.0, 100.0, 125.0, 137.5, 156.25]
```

### **Limite de Entradas por Ciclo**

```python
# Linha 58
MAX_ENTRADAS_POR_CICLO = 10
```

## 📈 Integração com Sistema de Análise

O Método de Ciclos está integrado com o sistema de análise existente:

### **Uso Combinado**
1. **Análise de Jogos**: Use a aba "Análise de Jogos" para identificar oportunidades
2. **Método de Ciclos**: Registre as operações no Método de Ciclos
3. **Backtracking**: Acompanhe a performance das estratégias

### **Indicação de Lay**
O sistema de análise indica qual Lay (1x0 ou 0x1) é mais recomendado baseado em:
- Valor Esperado (EV+)
- Frequência histórica
- Probabilidade estimada
- Odds disponíveis

## ⚠️ Avisos Importantes

### **Operação em Dinheiro Real**
> Recomendamos operar o método em dinheiro real (mesmo com stakes mínimas), pois o modo treino não simula o peso emocional necessário para este método.

### **Estratégia "Back Favorito vencendo"**
> Aviso: Esta é a estratégia mais perigosa para o método. Exige muito tempo de exposição para bater a meta de lucro. Use apenas na iminência de um 2 a 0 ou feche a posição se o time recuar.

### **Exchange vs Casa de Apostas**
> O método deve ser aplicado em Exchange, para você poder utilizar o lay. Não é possível fazer o Método de Ciclos em casas de apostas tradicionais.

## 🔗 API Endpoints

O sistema oferece endpoints REST para integração:

### **Obter Dados dos Ciclos**
```
GET /api/ciclos/dados
```

### **Criar Novo Ciclo**
```
POST /api/ciclos/criar
Content-Type: application/json

{
  "perfil": "conservador",
  "banca_inicial": 100.0
}
```

### **Adicionar Entrada**
```
POST /api/ciclos/adicionar-entrada
Content-Type: application/json

{
  "time_casa": "Brasil",
  "time_fora": "Argentina",
  "campeonato": "Copa do Mundo",
  "estrategia": "Lay Favorito (1º Tempo)",
  "lucro_real": 4.50,
  "resultado": "OK"
}
```

### **Estatísticas de Ciclo**
```
GET /api/ciclos/estatisticas/<ciclo_numero>
```

### **Resumo Geral**
```
GET /api/ciclos/resumo
```

## 📁 Arquivos do Sistema

### **Novos Arquivos**
- `ciclos_manager.py`: Módulo principal do Método de Ciclos
- `ciclos_dados.json`: Banco de dados dos ciclos (criado automaticamente)
- `METODO_CICLOS_README.md`: Esta documentação

### **Arquivos Modificados**
- `app.py`: Interface web atualizada com Método de Ciclos
- `metodo_ciclos.xlsx`: Planilha original do Netuno (renomeada)

## 🛠️ Solução de Problemas

### **Erro ao criar ciclo**
- Verifique se já existem 5 ciclos concluídos
- Reinicie o sistema para começar novos ciclos

### **Entrada não adicionada**
- Verifique se o ciclo está "em_andamento"
- Confirme que não atingiu o limite de 10 entradas
- Valide todos os campos obrigatórios

### **Dados não salvos**
- Verifique permissões de escrita no diretório
- Confirme que o arquivo `ciclos_dados.json` não está corrompido

## 📞 Suporte e Melhorias

### **Próximas Funcionalidades Planejadas**
- [ ] Integração direta com APIs de exchanges
- [ ] Alertas automáticos de oportunidades
- [ ] Gráficos de desempenho avançados
- [ ] Exportação de dados para Excel/CSV
- [ ] Sistema de notificações push

### **Feedback e Sugestões**
Para reportar bugs ou sugerir melhorias, consulte a documentação principal do projeto.

---

**Versão**: 1.0  
**Data**: 16/06/2026  
**Status**: ✅ Funcional e pronto para uso