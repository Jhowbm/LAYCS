# Sistema de Comunicação Local ↔ Nuvem

Este documento explica como configurar e usar o sistema de comunicação entre o sistema local (com scraping) e o sistema em nuvem (https://laycs.onrender.com).

## Visão Geral

O sistema funciona da seguinte forma:
1. **Sistema Local**: Executa o scraping do Flashscore (requer Firefox/Selenium)
2. **Sistema Nuvem**: Interface web acessível de qualquer lugar
3. **Comunicação**: A nuvem solicita análise ao local quando necessário

## Configuração

### 1. Configurar o Sistema Local

O sistema local já está configurado automaticamente com:
- API endpoints em `/api/local/analizar` e `/api/local/status`
- Autenticação via chave de API
- Configuração padrão: `http://localhost:5000`

Para iniciar o sistema local:
```bash
# Execute o script
INICIAR.bat
```

### 2. Configurar o Sistema Nuvem

No painel do Render (https://dashboard.render.com):

1. Acesse seu serviço LAYCS
2. Vá em "Environment"
3. Adicione as seguintes variáveis de ambiente:

#### Variável LOCAL_API_URL
- **Descrição**: URL onde o sistema local pode ser acessado
- **Valor padrão**: `http://localhost:5000`
- **Para acesso remoto**: Use uma URL pública (ngrok ou IP público)

#### Variável LOCAL_API_KEY
- **Descrição**: Chave de autenticação para comunicação segura
- **Valor padrão**: `flashscore-lay-2024-secret`
- **Recomendação**: Mantenha o valor padrão ou altere para uma chave segura

4. Clique em "Save Changes"
5. O serviço reiniciará automaticamente

## Opções de Acesso Remoto

### Opção 1: Ngrok (Recomendado)

Ngrok cria um túnel seguro que expõe seu servidor local para a internet.

#### Instalação:
1. Baixe ngrok em https://ngrok.com/download
2. Crie uma conta gratuita
3. Autentique: `ngrok authtoken SEU_TOKEN`

#### Uso:
```bash
# Iniciar túnel na porta 5000
ngrok http 5000
```

O ngrok vai gerar uma URL como: `https://a1b2-c3d4.ngrok-free.app`

#### Configuração no Render:
- `LOCAL_API_URL` = `https://a1b2-c3d4.ngrok-free.app`

#### Script Automático:
Execute `ACESSO_REMOTO_NGROK.bat` para iniciar automaticamente.

### Opção 2: IP Público com Port Forwarding

Se você tem IP público estático:

1. Configure o roteador para redirecionar a porta 5000 para seu computador
2. Execute `MOSTRAR_IP.bat` para descobrir seu IP público
3. Configure no Render: `LOCAL_API_URL` = `http://SEU_IP_PUBLICO:5000`

### Opção 3: Uso Local Apenas

Se você só usa o sistema na mesma rede:
- Execute `MOSTRAR_IP.bat` para descobrir seu IP local
- Configure no Render: `LOCAL_API_URL` = `http://SEU_IP_LOCAL:5000`

**Nota**: Esta opção geralmente não funciona com o Render, pois ele está na nuvem.

## Como Usar

### Cenário 1: Uso Local (Padrão)

1. Execute `INICIAR.bat`
2. Acesse http://localhost:5000
3. Use normalmente - scraping funciona localmente

### Cenário 2: Acesso Remoto via Nuvem

1. **Inicie o sistema local**:
   ```bash
   INICIAR.bat
   ```

2. **Configure o túnel remoto** (se usando ngrok):
   ```bash
   ngrok http 5000
   ```

3. **Acesse a nuvem**:
   - Vá para https://laycs.onrender.com
   - Clique na aba "Análise"
   - Clique em "Analisar Jogos"
   - O sistema vai chamar o sistema local automaticamente

4. **Acompanhe o progresso**:
   - O sistema local mostrará logs no console
   - A nuvem mostrará os resultados quando disponíveis

## Testes

### Testar API Local

```bash
# Testar status (com autenticação)
curl -H "X-API-Key: flashscore-lay-2024-secret" http://localhost:5000/api/local/status

# Testar análise (com autenticação)
curl -X POST -H "Content-Type: application/json" -H "X-API-Key: flashscore-lay-2024-secret" -d '{"dias": 0}' http://localhost:5000/api/local/analizar
```

### Testar Comunicação Nuvem → Local

1. Certifique-se de que o sistema local está rodando
2. Acesse https://laycs.onrender.com
3. Tente fazer uma análise
4. Verifique se funciona

## Solução de Problemas

### Erro: "Não autorizado - chave de API inválida"
- Verifique se `LOCAL_API_KEY` é igual no local e na nuvem
- O valor padrão é `flashscore-lay-2024-secret`

### Erro: "Não foi possível conectar ao sistema local"
- Verifique se o sistema local está rodando (INICIAR.bat)
- Verifique se o ngrok está ativo (se usando ngrok)
- Verifique se `LOCAL_API_URL` está correta no Render
- Verifique se o firewall não está bloqueando

### Erro: "Tempo esgotado ao conectar ao sistema local"
- O scraping demorou mais que 5 minutos
- Tente analisar menos dias
- Verifique sua conexão com a internet

### Erro: "Sistema local não respondeu"
- O sistema local pode ter caído durante a análise
- Reinicie o sistema local
- Verifique os logs para identificar o erro

## Segurança

### Autenticação
- Todas as requisições requerem a chave de API correta
- A chave é enviada via header `X-API-Key`
- Nunca compartilhe sua chave de API

### Recomendações
- Use ngrok para acesso remoto (mais seguro que IP público)
- Altere a chave de API padrão para algo único
- Mantenha o sistema local atualizado
- Use apenas em redes confiáveis

## Alternativa: Método de Ciclos

Se a comunicação remota não funcionar, lembre-se que:
- O **Método de Ciclos** funciona 100% na nuvem
- Não requer comunicação com o sistema local
- Pode ser usado independentemente da análise de jogos

## Manutenção

### Atualizar o Sistema

1. Faça pull das alterações no GitHub
2. O Render fará deploy automático
3. Localmente, execute `git pull` e reinicie o sistema

### Verificar Logs

**Local**: Os logs aparecem no console quando você executa `INICIAR.bat`

**Nuvem**: 
1. Acesse https://dashboard.render.com
2. Selecione seu serviço LAYCS
3. Vá em "Logs"

### Monitoramento

Monitore regularmente:
- Se o sistema local está rodando
- Se o ngrok está ativo (se usando)
- Se a comunicação está funcionando
- Os logs de erros

## Suporte

Para problemas:
1. Verifique este documento
2. Verifique os logs (local e nuvem)
3. Consulte `CONFIGURAR_IP_NUVEM.md` para configuração de IP
4. Consulte `DEPLOY_NUVEM.md` para informações de deploy

## Resumo Rápido

**Para usar o sistema remotamente:**
1. Execute `INICIAR.bat`
2. Execute `ngrok http 5000` (ou configure IP público)
3. Configure `LOCAL_API_URL` no Render com a URL do ngrok
4. Acesse https://laycs.onrender.com
5. Use a aba "Análise" normalmente

**Para usar localmente:**
1. Execute `INICIAR.bat`
2. Acesse http://localhost:5000
3. Use normalmente