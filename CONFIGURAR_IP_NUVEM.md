# Configurar IP do Sistema Local para Acesso Remoto

Este documento explica como configurar o sistema em nuvem para acessar o sistema local de análise.

## O que é necessário

Para que o sistema em nuvem (https://laycs.onrender.com) possa acessar o sistema local:

1. O sistema local deve estar rodando (execute `INICIAR.bat`)
2. O sistema local deve ter um IP público acessível pela nuvem
3. A variável de ambiente `LOCAL_API_URL` no Render deve apontar para o IP público do sistema local

## Opção 1: Usando Ngrok (Recomendado)

Ngrok cria um túnel seguro que expõe seu servidor local para a internet.

### Passos:

1. Baixe e instale o ngrok em https://ngrok.com/download
2. Crie uma conta gratuita no ngrok
3. Execute o comando para criar o túnel:
   ```
   ngrok http 5000
   ```
4. Copie a URL gerada (exemplo: `https://a1b2-c3d4.ngrok-free.app`)
5. Configure a variável de ambiente no Render:
   - Acesse https://dashboard.render.com
   - Selecione seu serviço LAYCS
   - Vá em "Environment"
   - Adicione variável: `LOCAL_API_URL` = `https://a1b2-c3d4.ngrok-free.app`
6. Reinicie o serviço no Render

### Script Automático

Execute o arquivo `ACESSO_REMOTO_NGROK.bat` para iniciar o ngrok automaticamente.

## Opção 2: IP Público com Port Forwarding

Se você tem um IP público estático e pode configurar port forwarding no roteador:

### Passos:

1. Execute `MOSTRAR_IP.bat` para ver seu IP público
2. Configure o roteador para redirecionar a porta 5000 para seu computador local
3. Configure a variável de ambiente no Render:
   - `LOCAL_API_URL` = `http://SEU_IP_PUBLICO:5000`
4. Reinicie o serviço no Render

### Limitações:
- Requer IP público estático
- Requer acesso ao roteador
- Requer configuração de firewall
- Menos seguro que ngrok

## Opção 3: IP Local (Apenas na mesma rede)

Se você está acessando a nuvem apenas da mesma rede local:

### Passos:

1. Execute `MOSTRAR_IP.bat` para ver seu IP local
2. Configure a variável de ambiente no Render:
   - `LOCAL_API_URL` = `http://SEU_IP_LOCAL:5000`
3. Reinicie o serviço no Render

### Limitações:
- Só funciona na mesma rede local
- Não funciona de fora da rede
- O Render está na nuvem, então esta opção geralmente não funciona

## Testar Conexão

Depois de configurar:

1. Certifique-se de que o sistema local está rodando (execute `INICIAR.bat`)
2. Acesse https://laycs.onrender.com
3. Clique na aba "Análise"
4. Clique em "Analisar Jogos"
5. Verifique se a análise funciona

Se aparecer erro de conexão:
- Verifique se o sistema local está rodando
- Verifique se o ngrok está ativo (se usando ngrok)
- Verifique se a URL está correta no Render
- Verifique o log do sistema local para ver se recebeu a requisição

## Solução de Problemas

### Erro: "Tempo esgotado ao conectar ao sistema local"
- O scraping demorou mais que 5 minutos
- Tente analisar menos dias
- Verifique sua conexão com a internet

### Erro: "Não foi possível conectar ao sistema local"
- O sistema local não está rodando
- O ngrok não está ativo
- A URL está incorreta
- O firewall está bloqueando a conexão

### Erro: "Sistema local não respondeu"
- O sistema local caiu durante a análise
- Reinicie o sistema local
- Verifique o log para identificar o erro

## Alternativa: Análise Local

Se a conexão remota não funcionar, você sempre pode:
1. Executar o sistema localmente (INICIAR.bat)
2. Acessar http://localhost:5000
3. Fazer a análise localmente
4. Usar apenas o Método de Ciclos na nuvem

O Método de Ciclos funciona 100% na nuvem sem necessidade de conexão local.