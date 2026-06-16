# Flashscore Lay Analyzer

Extrai dados de jogos do dia no Flashscore, analisa histórico H2H e identifica
oportunidades de aposta **Lay 1x0** e **Lay 0x1** com base na frequência histórica
desses placares.

---

## Requisitos

- Python 3.11+
- Firefox instalado
- Geckodriver compatível com a versão do Firefox

---

## 1. Instalar o Geckodriver

O Geckodriver é o driver que o Selenium usa para controlar o Firefox.

### Opção A — Automático via webdriver-manager (recomendado)
O `webdriver-manager` já está no `requirements.txt` e baixa o geckodriver automaticamente
na primeira execução. Nenhuma configuração extra necessária.

### Opção B — Manual
1. Descubra a versão do seu Firefox: Menu → Ajuda → Sobre o Firefox
2. Baixe o geckodriver correspondente em: https://github.com/mozilla/geckodriver/releases
3. Extraia o executável (`geckodriver.exe` no Windows)
4. Coloque em uma pasta do PATH **ou** defina a variável de ambiente:

```bat
set GECKODRIVER_PATH=C:\caminho\para\geckodriver.exe
```

---

## 2. Configurar o ambiente virtual

```bat
# Criar ambiente virtual
python -m venv venv

# Ativar (Windows)
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

---

## 3. Rodar

```bat
# Execução padrão (headless, limiar 10%)
python main.py

# Com Firefox visível (útil para depurar seletores)
python main.py --no-headless

# Limiar personalizado (ex: 8%)
python main.py --limiar 0.08

# Delay maior entre requisições (evitar bloqueio)
python main.py --delay 4

# Prefixo personalizado para os arquivos de saída
python main.py --saida resultado_hoje
```

---

## 4. Saída

- `flashscore_lay_YYYY-MM-DD.csv` — planilha com todos os jogos analisados
- `flashscore_lay_YYYY-MM-DD.json` — mesmo conteúdo em JSON
- `erros.log` — jogos que falharam (timeout, seletor não encontrado, etc.)

### Colunas do CSV/JSON

| Coluna | Descrição |
|--------|-----------|
| data | Data da análise |
| hora | Horário do jogo |
| time_casa | Nome do mandante |
| time_fora | Nome do visitante |
| freq_1x0_h2h | Frequência do placar 1x0 nos confrontos diretos |
| freq_0x1_h2h | Frequência do placar 0x1 nos confrontos diretos |
| freq_1x0_casa | Freq. 1x0 nos últimos jogos do mandante |
| freq_0x1_fora | Freq. 0x1 nos últimos jogos do visitante |
| freq_combinada_total | Soma das frequências combinadas 1x0 + 0x1 |
| odd_1 / odd_x / odd_2 | Odds 1x2 |
| odd_cs_1x0 / odd_cs_0x1 | Odds de placar exato (se disponível) |
| classificacao | LAY_OPORTUNIDADE / MONITORAR / DESCARTAR |

### Classificação

| Valor | Significado |
|-------|-------------|
| `LAY_OPORTUNIDADE` | freq_combinada_total < limiar → placar raro → bom para Lay |
| `MONITORAR` | entre limiar e limiar × 1,5 → analisar com mais cautela |
| `DESCARTAR` | placar ocorre com frequência → risco elevado para Lay |

---

## 5. Atualizar seletores CSS

O Flashscore ocasionalmente altera as classes CSS do site. Se o scraper parar de funcionar:

1. Abra o Flashscore no Firefox
2. Pressione F12 → inspecione o elemento desejado
3. Copie a nova classe CSS
4. Atualize o arquivo **`config.py`** — todos os seletores estão centralizados lá

---

## Estrutura do projeto

```
flashscore-lay/
├── config.py        # Seletores CSS e parâmetros (edite aqui se o site mudar)
├── scraper.py       # Coleta de dados com Selenium + BeautifulSoup
├── analyzer.py      # Análise estatística e exportação
├── main.py          # Orquestrador — ponto de entrada
├── requirements.txt
└── README.md
```

---

## Aviso

Este projeto é apenas para fins educacionais e de estudo de dados.
Aposte com responsabilidade.


considerações do criador 


Crie um projeto Python completo para extração e análise de dados pré-live do Flashscore (flashscore.com.br), 
com o objetivo de identificar oportunidades de aposta "Lay 1x0" e "Lay 0x1" (apostar contra esses placares exatos).

ESTRUTURA DO PROJETO:
- scraper.py: módulo de coleta de dados (Selenium + BeautifulSoup)
- analyzer.py: módulo de cálculo das métricas e classificação de oportunidades
- config.py: seletores CSS, limiares e parâmetros configuráveis
- main.py: orquestração geral
- requirements.txt
- README.md com instruções de instalação (Geckodriver, Firefox, dependências)

1. SETUP DO SELENIUM
- Firefox + Geckodriver (caminho configurável via variável de ambiente)
- WebDriverWait em todas as esperas (nunca apenas time.sleep)
- Modo headless opcional via flag

2. COLETA DE JOGOS DO DIA
- Acessar a aba "Próximos" (pre-live, não "Ao Vivo")
- Capturar a "div mãe" da lista de jogos via .event__match
- Extrair pares mandante/visitante com .event__participant--home e .event__participant--away
- Parsear via BeautifulSoup (outerHTML) e limpar texto com .get_text()

3. COLETA DE HISTÓRICO (H2H E FORMA RECENTE)
Para cada time (mandante e visitante), navegar até a aba H2H/Form e extrair os últimos 10-15 jogos:
- Placares via .event__score--home e .event__score--away
- Para cada jogo histórico, armazenar: gols marcados pelo time, gols sofridos, e o placar final completo

4. MÓDULO DE MÉTRICAS (analyzer.py)
Implemente as seguintes métricas para cada time, com base no histórico coletado:

a) Frequência de placar exato:
   - % dos últimos N jogos do mandante que terminaram em 1x0 (a favor do mandante)
   - % dos últimos N jogos do visitante que terminaram em 0x1 (a favor do visitante)
   - Frequência combinada = média ponderada dessas duas

b) Média de gols:
   - Média de gols marcados + sofridos por jogo de cada time (média combinada do confronto)
   - Clean sheets: % de jogos em que o time não sofreu gols

c) Cruzamento ofensivo x defensivo:
   - Sinalizar como "cenário ideal" quando o mandante tem média de gols marcados alta 
     E o visitante tem média de gols sofridos alta (defesa fraca), e vice-versa

d) Odds (se disponíveis no scraping):
   - Capturar odds 1x2 e, se possível, odds de "Over 1.5 gols" e mercado de placar exato
   - Calcular probabilidade implícita a partir das odds (1 / odd)
   - Definir teto configurável para odds do Lay (padrão: não recomendar Lay com odd acima de 8.0)

5. REGRA DE CLASSIFICAÇÃO ("Aprovado para Lay")
Um jogo é classificado como oportunidade quando:
   - Frequência combinada de 1x0/0x1 < limiar configurável (padrão 10%)
   - E média de gols do confronto > limiar configurável (padrão 2.0)
   - (Opcional, se odds disponíveis) E odd implícita de Over 1.5 < limiar configurável (padrão 1.40)

Tornar todos esses limiares parâmetros de linha de comando ou de config.py.

6. SAÍDA DE DADOS
Exportar para CSV e JSON com as colunas:
   data, time_casa, time_fora, freq_1x0_casa, freq_0x1_fora, freq_combinada, 
   media_gols_confronto, clean_sheets_casa, clean_sheets_fora, 
   odd_1x2, odd_over_1_5, prob_implicita_over_1_5, 
   classificacao ("Oportunidade Lay" / "Risco Alto" / "Sem dados suficientes")

7. TRATAMENTO DE ERROS E RESILIÊNCIA
- Try/except em cada etapa, registrando falhas em erros.log
- Retry automático (até 3 tentativas) em timeouts
- Delay configurável entre requisições (para não sobrecarregar o site/evitar bloqueio)
- Se um time não tiver histórico suficiente (menos de N jogos), marcar como "Sem dados suficientes" 
  em vez de descartar silenciosamente

8. DOCUMENTAÇÃO
- README explicando instalação (Geckodriver, venv, requirements: selenium, beautifulsoup4, 
  pandas, webdriver-manager)
- Comentar bem o código, especialmente os seletores CSS e a lógica das métricas, 
  já que o Flashscore pode alterar a estrutura HTML com o tempo

Comece pela estrutura de pastas e requirements.txt, depois implemente scraper.py com coleta básica 
(testar antes de avançar), depois a coleta de H2H, e por fim o analyzer.py com as métricas e regra de classificação.
