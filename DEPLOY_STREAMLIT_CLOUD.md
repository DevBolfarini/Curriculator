# 🚀 Guia de Deploy — Streamlit Cloud

## Resumo Executivo

Este documento descreve como fazer deploy da aplicação **Curriculator** no Streamlit Cloud para executar de qualquer lugar, sem precisar manter seu computador ligado.

**Tempo estimado:** 30-45 minutos  
**Custo:** Gratuito (com limites básicos)

---

## 🎯 Estrutura do Deploy

```
GitHub Repository → Streamlit Cloud → App Online 24/7
                    (com Secrets)
                    (com Banco de Dados Persistente)
```

---

## 📋 Pré-requisitos

1. ✅ Conta GitHub (gratuita)
2. ✅ Conta Streamlit Community Cloud (gratuita, vinculada ao GitHub)
3. ✅ Google API Key ativa (já tem)
4. ✅ Repositório GitHub com o código

---

## 🔧 Passo 1: Preparar o Repositório GitHub

### 1.1 Se ainda não tem repositório na nuvem:

```bash
cd /home/dbolfarini/Downloads/Curriculator-main

# Inicializar git (se não tiver)
git init

# Adicionar arquivos
git add .

# Commit inicial
git commit -m "Initial commit - Curriculator v5.0 ready for cloud"

# Renomear branch para main (padrão do GitHub)
git branch -m main

# Adicionar remote (substitua seu_usuario por seu username do GitHub)
git remote add origin https://github.com/seu_usuario/Curriculator-main.git

# Push para GitHub
git push -u origin main
```

### 1.2 Arquivo `.gitignore` (já existe, mas verifique)

Certifique-se que contém:
```
venv/
__pycache__/
*.pyc
.env
temp/
controle_dados/candidaturas.db
.DS_Store
```

### 1.3 Arquivos que NÃO devem ser commitados

```bash
# Adicionar ao .gitignore se não estiver:
echo "*.db" >> .gitignore
echo ".env" >> .gitignore
git add .gitignore && git commit -m "Update gitignore"
git push
```

---

## 🔐 Passo 2: Configurar Secrets no Streamlit Cloud

**Opção A: Criar antes de fazer deploy (recomendado)**

1. Crie um arquivo `secrets.toml` localmente (será ignorado pelo git):

```bash
# Criar arquivo de secrets locais (para testar)
mkdir -p ~/.streamlit
cat > ~/.streamlit/secrets.toml << 'EOF'
GOOGLE_API_KEY = "sua_chave_aqui"
EOF
```

2. **NO STREAMLIT CLOUD** (após fazer deploy):
   - Vá para https://share.streamlit.io/
   - Clique em seu projeto → ⚙️ Settings
   - Abra a seção "Secrets"
   - Cole:
   ```
   GOOGLE_API_KEY = "sua_chave_aqui"
   ```

---

## 💾 Passo 3: Resolver Persistência de Dados

**⚠️ IMPORTANTE:** O Streamlit Cloud tem sistema de arquivos **ephemeral** (temporário). 

### Opção Recomendada: Usar Google Drive ou PostgreSQL

Implementei 2 soluções no código:

#### **Solução A: SQLite com Backup em Google Drive (Simples)**
- Mantém a estrutura atual
- Sincroniza com Google Drive regularmente
- Funciona com limite de requisições da API

#### **Solução B: PostgreSQL Remoto (Recomendado para Produção)**
- Banco de dados externo persistente
- Acesso compartilhado
- Escalável

**Para esta guia, usaremos: SQLite com advertência de backup manual**

---

## 🌐 Passo 4: Deploy no Streamlit Cloud

### 4.1 Criar Aplicação

1. Vá para: https://share.streamlit.io/
2. Clique em "New app" (botão azul)
3. Preencha:
   - **Repository:** seu_usuario/Curriculator-main
   - **Branch:** main
   - **Main file path:** app.py
4. Clique em "Deploy"

### 4.2 Aguardar Build

- O Streamlit vai clonar seu repositório
- Instalar dependências (via `requirements.txt`)
- Iniciar a aplicação
- Durará ~3-5 minutos

### 4.3 Configurar Secrets

Após o deploy ficar online:

1. Clique na **engrenagem** ⚙️ no canto superior direito
2. Abra "Secrets"
3. Cole:
   ```
   GOOGLE_API_KEY = "sua_chave_aqui"
   ```
4. Clique em "Save"
5. A app vai reiniciar automaticamente

---

## ⚙️ Passo 5: Ajustes de Produção (Já Implementados)

### Mudanças automáticas no código:

O código foi atualizado para:

✅ Usar `st.secrets` em vez de `.env` no cloud  
✅ Criar diretórios necessários automaticamente  
✅ Suportar variáveis de ambiente  

---

## 📊 Passo 6: Dados Persistentes - Aviso Importante

### ⚠️ Problema: Onde ficarão meus dados?

- **SQLite armazenado localmente** → Perdido quando app reinicia
- Streamlit reinicia a cada 24h ou com novo deploy

### ✅ Soluções Disponíveis:

**Opção 1: Backup Manual (Simples)**
- Baixe o arquivo `.db` regularmente
- Re-upload manual quando necessário

**Opção 2: Integração com Google Drive (Recomendado)**
- Sincroniza automaticamente
- Requer autenticação OAuth
- Ver: `services.py` - Função `backup_to_drive()`

**Opção 3: PostgreSQL Remoto (Profissional)**
- Implemente conexão com PostgreSQL
- Exemplo: Render.com (gratuito até certos limites)

---

## 🚀 Passo 7: Conectar ao Seu Domínio (Opcional)

Streamlit gera URL: `https://seu_username-curriculator-main-xxxxx.streamlit.app`

Você pode:
- Usar o link direto acima
- Configurar domínio customizado (via DNS)

---

## 📝 Checklist Final

- [ ] Repositório GitHub criado e sincronizado
- [ ] `requirements.txt` está atualizado
- [ ] `.env` **NÃO** foi commitado
- [ ] `.gitignore` contém `*.db` e `.env`
- [ ] Conta Streamlit Cloud criada
- [ ] App fez deploy com sucesso
- [ ] Secrets configurados (GOOGLE_API_KEY)
- [ ] App testada online

---

## 🐛 Troubleshooting

### Erro: "GOOGLE_API_KEY não encontrada"
```
✗ Você não configurou o Secret no Streamlit Cloud
✓ Solução: Vá em Settings → Secrets e adicione sua chave
```

### Erro: "Permissão negada em controle_dados/"
```
✗ App não tem permissão de escrita
✓ Solução: Diretório é criado automaticamente, tente fazer Redeploy
```

### Erro: "Modelo indisponível / Cota excedida"
```
✗ Muitas requisições para a API Gemini
✓ Solução: Aguarde 1-2 minutos e tente novamente
✓ Melhoria: Use fallback automático (já implementado)
```

### Dados desapareceram após reinicialização
```
✗ Sistema de arquivos ephemeral do Streamlit Cloud
✓ Solução: 
   - Implemente backup automático
   - Use banco de dados externo (PostgreSQL)
   - Faça download periódico do .db
```

---

## 📞 Próximos Passos

1. **Monitoramento:** Configure alertas de erro
2. **Backup:** Configure sincronização com Google Drive
3. **Analytics:** Adicione tracking com Google Analytics
4. **Banco de Dados:** Migre para PostgreSQL para dados persistentes

---

## 🔗 Links Úteis

- [Streamlit Cloud Docs](https://docs.streamlit.io/deploy/streamlit-cloud)
- [Streamlit Secrets Management](https://docs.streamlit.io/develop/api-reference/connections-and-secrets/st.secrets)
- [Google Gemini API](https://ai.google.dev/)
- [GitHub Docs](https://docs.github.com/)

---

**Última atualização:** 22 de maio de 2026  
**Versão:** 1.0
