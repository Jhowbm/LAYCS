# 🌐 Aplicação Web - Flashscore Lay Analyzer

## 🚀 COMO RODAR LOCALMENTE:

### 1. **No Prompt do Windows (cmd):**
```cmd
cd C:\flashscore-lay
python app.py
```

### 2. **Acesse no navegador:**
```
http://localhost:5000
```

### 3. **No celular:**
- Conecte seu celular na mesma rede Wi-Fi
- Acesse: `http://SEU_IP_LOCAL:5000`
- Para descobrir seu IP: No Prompt do Windows: `ipconfig`

## 🌐 COMO HOSPEDAR GRATUITAMENTE:

### Opção 1: **Render (Recomendado)**

1. **Crie uma conta em:** https://render.com/
2. **Crie um novo projeto:**
   - Clique em "New Web Service"
   - Connect: GitHub
   - Criar um repositório no GitHub com o projeto
3. **Configure:**
   - Runtime: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`

### Opção 2: **PythonAnywhere**

1. **Crie uma conta em:** https://www.pythonanywhere.com/
2. **Crie um "Web App"**
3. **Upload dos arquivos** via interface
4. **Configure para rodar Flask**

### Opção 3: **Railway**

1. **Crie uma conta em:** https://railway.app/
2. **New Project → Deploy from GitHub**
3. **Conecte seu repositório**
4. **Configure como aplicação Python**

## 📱 FUNCIONALIDADES DA APLICAÇÃO WEB:

✅ **Interface responsiva** (funciona no celular)
✅ **Seletor de data** (Hoje / Amanhã / Depois de amanhã)
✅ **Destaque amarelo** para jogos da Copa do Mundo
✅ **Indicação clara:** "LAY 1X0 RECOMENDADO" ou "LAY 0X1 RECOMENDADO"
✅ **Métricas visuais:** EV, Retorno, Probabilidade, Média de Gols
✅ **Design moderno** com gradientes e animações

## 🎨 EXEMPLO DE APARÊNCIA:

```
🏆 Flashscore Lay Analyzer

Selecione o dia: [Hoje ▼]
[🔍 Analisar Jogos]

⏳ Analisando jogos...

─────────────────────────────
🏆 19:00 - Brasil vs Croácia
✓ LAY 1X0 RECOMENDADO
EV: +0.280 | Retorno: 8.3% | Prob: 6.0% | Gols: 2.5

─────────────────────────────
🏆 22:00 - Argentina vs México
✓ LAY 0X1 RECOMENDADO
EV: +0.350 | Retorno: 9.1% | Prob: 5.0% | Gols: 2.2
```

## ⚙️ CONFIGURAÇÕES ADICIONAIS:

No arquivo `app.py`, você pode modificar:
- Porta: `app.run(host='0.0.0.0', port=5000)`
- Debug: `debug=True` (modo desenvolvimento)

## 🔧 SOLUÇÃO DE PROBLEMAS:

**Se não rodar localmente:**
- Execute no Prompt do Windows (não Git Bash)
- Verifique se as dependências estão instaladas: `pip install flask selenium webdriver-manager beautifulsoup4 pandas`

**Se não acessar do celular:**
- Verifique firewall do Windows
- Use o mesmo Wi-Fi no computador e celular
- Descubra seu IP: `ipconfig` (procure por IPv4 Address)