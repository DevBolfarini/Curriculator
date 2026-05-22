# 🎯 Guia Rápido: 7 Passos para Deploy no Streamlit Cloud

## Passo 1️⃣: Prepare seu Repositório GitHub

Se ainda não tem repositório:

```bash
cd /home/dbolfarini/Downloads/Curriculator-main

# Verifique se git já está inicializado
git status

# Se não, inicialize
git init

# Adicione todos os arquivos
git add -A

# Commit inicial
git commit -m "🚀 Curriculator ready for cloud deployment"

# Crie o repositório no GitHub e adicione como remote
# Depois execute:
git remote add origin https://github.com/SEU_USUARIO/Curriculator-main.git
git branch -M main
git push -u origin main
```

---

## Passo 2️⃣: Verifique o `.gitignore`

Certifique-se que o arquivo `.gitignore` contém:

```
.env
.streamlit/secrets.toml
venv/
__pycache__/
*.pyc
temp/
controle_dados/candidaturas.db
*.db
.DS_Store
*.xlsx
.git/
```

Se fizer alterações, execute:

```bash
git add .gitignore
git commit -m "✅ Update gitignore for cloud deployment"
git push
```

---

## Passo 3️⃣: Prepare Sua API Key

⚠️ **NÃO coloque a chave no `.env` ou commitar no GitHub!**

### A. Testando Localmente

```bash
# Crie arquivo local de secrets (será ignorado pelo git)
mkdir -p ~/.streamlit

cat > ~/.streamlit/secrets.toml << 'EOF'
GOOGLE_API_KEY = "sua_chave_aqui"
EOF

# Teste rodando a app localmente
streamlit run app.py
```

### B. Produção (Streamlit Cloud)

Você configurará isso **APÓS** fazer o deploy (próximos passos)

---

## Passo 4️⃣: Crie Conta no Streamlit Cloud

1. Vá para: https://streamlit.io/cloud
2. Clique em **"Sign up"** ou **"Sign in"**
3. Conecte com sua conta GitHub
4. Autorize Streamlit a acessar seus repositórios

---

## Passo 5️⃣: Deploy a Aplicação

1. Na dashboard do Streamlit Cloud (https://share.streamlit.io/), clique em **"New app"**

2. Preencha os campos:
   - **Repository:** `seu_usuario/Curriculator-main`
   - **Branch:** `main`
   - **Main file path:** `app.py`

3. Clique em **"Deploy"**

4. **Aguarde 3-5 minutos** enquanto a aplicação é construída e iniciada

   - Você verá: "Your app is in development mode"
   - Isso é normal - significa que está rodando

---

## Passo 6️⃣: Configure Secrets (API Key)

Depois que a app estiver online:

1. Procure pela **engrenagem ⚙️** no canto superior direito
2. Clique em **"Settings"**
3. Abra a aba **"Secrets"**
4. Cole seu GOOGLE_API_KEY:

```toml
GOOGLE_API_KEY = "cole_sua_chave_aqui"
```

5. Clique em **"Save"**
6. A aplicação vai reiniciar automaticamente ✨

---

## Passo 7️⃣: Teste sua App

1. Verifique se aparece a mensagem de erro sobre API Key (se desapareceu, está funcionando! ✅)
2. Tente fazer upload de um PDF
3. Teste uma candidatura para confirmar que está tudo funcionando

---

## ✅ Pronto! Sua App está ONLINE!

URL de acesso: `https://seu_usuario-curriculator-main-xxxxx.streamlit.app`

Compartilhe esse link com qualquer pessoa que precisar usar a aplicação!

---

## 🔄 Como Atualizar o Código

Sempre que fizer mudanças no código:

```bash
git add .
git commit -m "📝 Descrição da mudança"
git push
```

O Streamlit Cloud vai detectar o push e fazer redeploy automaticamente em segundos!

---

## ⚠️ Importante: Persistência de Dados

### O Problema
O Streamlit Cloud usa um sistema de arquivos **temporário**. Isso significa:
- Cada reinicialização da app (a cada 24h ou com novo deploy) limpa os arquivos
- Seu banco SQLite será perdido!

### Soluções

**Opção 1: Backup Manual (Simples)**
- Baixe o arquivo `controle_dados/candidaturas.db` regularmente
- Re-upload quando precisar recuperar dados

**Opção 2: Integração Google Drive (Intermediária)**
- A app pode fazer backup automático em Google Drive
- Restaura dados de forma automática

**Opção 3: PostgreSQL Remoto (Profissional)**
- Use um serviço como Render.com, ElephantSQL ou Railway
- Banco de dados persistente na nuvem
- Melhor para múltiplos usuários

### Recomendação Imediata
Use **Opção 1** (backup manual) enquanto aprende. Depois migre para Opção 2 ou 3.

---

## 🆘 Solução de Problemas

### ❌ Erro: "GOOGLE_API_KEY não encontrada"
```
Solução: Vá em Settings ⚙️ → Secrets e adicione sua chave
```

### ❌ Erro: "Arquivo não encontrado"
```
Solução: A app foi reiniciada e perdeu o arquivo temporário.
Use backup/persistência (ver seção acima)
```

### ❌ Erro: "Permissão negada"
```
Solução: Clique em "Rerun" (botão no canto superior direito)
```

### ❌ App muito lenta ou com timeout
```
Solução: Google Gemini API com rate limiting.
Aguarde alguns minutos e tente novamente.
O fallback automático tentará outros modelos.
```

---

## 📞 Precisa de Ajuda?

- **Documentação Streamlit:** https://docs.streamlit.io/deploy/streamlit-cloud
- **GitHub Actions:** Para CI/CD automático
- **Suporte:** Comunidade Streamlit no Discord

---

**Versão:** 1.0  
**Atualizado:** 22 de maio de 2026  
**Stack:** Streamlit + Google Gemini + SQLite
