# 🚀 Guia Completo de Deploy na Railway

## 📋 Pré-requisitos

- Conta no GitHub
- Projeto commitado no GitHub
- Conta na Railway (gratuita)

## 🎯 Etapa 1: Configuração da Conta Railway

### 1.1 Criar Conta na Railway
1. Acesse [railway.app](https://railway.app)
2. Clique em "Start a New Project"
3. Faça login com sua conta GitHub
4. Autorize o Railway a acessar seus repositórios

### 1.2 Conectar Repositório
1. No dashboard da Railway, clique em "New Project"
2. Selecione "Deploy from GitHub repo"
3. Escolha o repositório do projeto
4. Clique em "Deploy Now"

## 🔧 Etapa 2: Configuração do Projeto

### 2.1 Verificar Arquivos de Configuração
Certifique-se de que os seguintes arquivos estão no repositório:

```
📁 Projeto/
├── 📄 requirements.txt     # Dependências Python
├── 📄 Procfile            # Comando de inicialização
├── 📄 railway.json        # Configurações Railway
├── 📄 .env.example        # Template de variáveis
├── 📄 .gitignore          # Arquivos ignorados
└── 📄 app_mapa_interativo.py  # Aplicação principal
```

### 2.2 Configurar Variáveis de Ambiente
1. No dashboard Railway, clique no seu projeto
2. Vá para a aba "Variables"
3. Adicione as seguintes variáveis:

```env
FLASK_ENV=production
FLASK_APP=app_mapa_interativo.py
SECRET_KEY=sua_chave_secreta_aqui_mude_isso
PYTHONPATH=.
```

### 2.3 Configurar Domínio (Opcional)
1. Na aba "Settings" do projeto
2. Em "Domains", clique em "Generate Domain"
3. Ou adicione um domínio customizado

## 🚀 Etapa 3: Deploy Automático

### 3.1 Primeiro Deploy
1. O Railway detectará automaticamente o `requirements.txt`
2. Instalará as dependências Python
3. Executará o comando definido no `Procfile`
4. O deploy será concluído em 2-5 minutos

### 3.2 Monitorar Deploy
1. Acompanhe os logs na aba "Deployments"
2. Verifique se não há erros de dependências
3. Confirme que o servidor iniciou corretamente

## 🔍 Etapa 4: Verificação e Testes

### 4.1 Testar Aplicação
1. Acesse a URL fornecida pela Railway
2. Verifique se o mapa carrega corretamente
3. Teste as funcionalidades de edição
4. Confirme que os WebSockets funcionam

### 4.2 Verificar Logs
```bash
# Logs em tempo real
railway logs

# Logs específicos
railway logs --tail 100
```

## 🛠️ Etapa 5: Configurações Avançadas

### 5.1 Configurar Banco de Dados (Se Necessário)
1. No dashboard, clique em "New"
2. Selecione "Database" → "PostgreSQL"
3. Configure as variáveis de conexão

### 5.2 Configurar Armazenamento Persistente
```json
// railway.json
{
  "deploy": {
    "startCommand": "gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app_mapa_interativo:app",
    "healthcheckPath": "/"
  }
}
```

## 🔄 Etapa 6: Deploy Contínuo

### 6.1 Configurar Auto-Deploy
1. Vá para "Settings" → "Service"
2. Em "Source Repo", configure:
   - Branch: `main` ou `master`
   - Auto-deploy: `Enabled`

### 6.2 Deploy Manual
```bash
# Via CLI Railway
npm install -g @railway/cli
railway login
railway deploy
```

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. Erro de Dependências
```bash
# Verificar requirements.txt
pip freeze > requirements.txt
```

#### 2. Erro de Porta
```python
# Usar variável PORT do Railway
port = int(os.getenv('PORT', 5001))
```

#### 3. Arquivos Não Encontrados
```python
# Usar caminhos relativos
with open('./zona_cores_mapping.json', 'r') as f:
    data = json.load(f)
```

#### 4. WebSockets Não Funcionam
```python
# Verificar configuração do gunicorn
# Procfile deve usar: --worker-class eventlet
```

### Logs de Debug
```bash
# Verificar logs detalhados
railway logs --tail 200

# Conectar ao container
railway shell
```

## 📊 Monitoramento

### 6.1 Métricas da Railway
- CPU Usage
- Memory Usage
- Network I/O
- Response Time

### 6.2 Logs Personalizados
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Aplicação iniciada com sucesso")
```

## 💰 Custos e Limites

### Plano Gratuito
- $5 de crédito mensal
- 500 horas de execução
- 1GB RAM
- 1GB armazenamento

### Otimização de Custos
- Use sleep mode para aplicações de desenvolvimento
- Configure auto-scaling adequadamente
- Monitore uso de recursos

## 🔐 Segurança

### Variáveis Sensíveis
```env
# Nunca commitar no código
SECRET_KEY=chave_super_secreta
DATABASE_URL=postgresql://...
API_KEY=sua_api_key
```

### HTTPS
- Railway fornece HTTPS automaticamente
- Certificados SSL renovados automaticamente

## 📚 Recursos Adicionais

- [Documentação Railway](https://docs.railway.app)
- [CLI Railway](https://docs.railway.app/develop/cli)
- [Templates Railway](https://railway.app/templates)
- [Comunidade Discord](https://discord.gg/railway)

## ✅ Checklist Final

- [ ] Conta Railway criada e conectada ao GitHub
- [ ] Repositório com todos os arquivos de configuração
- [ ] Variáveis de ambiente configuradas
- [ ] Deploy realizado com sucesso
- [ ] Aplicação funcionando na URL da Railway
- [ ] WebSockets operacionais
- [ ] Logs sem erros críticos
- [ ] Funcionalidades testadas

## 🆘 Suporte

Em caso de problemas:
1. Verifique os logs da Railway
2. Consulte a documentação oficial
3. Verifique issues no GitHub do projeto
4. Entre em contato com o suporte Railway

---

**🎉 Parabéns! Sua aplicação está no ar!**

Acesse sua aplicação em: `https://seu-projeto.railway.app`