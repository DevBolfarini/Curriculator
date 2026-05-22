# ✅ PRÉ-DEPLOYMENT CHECKLIST

**Antes de fazer push para GitHub e deploy no Streamlit Cloud, verifique:**

## 🔐 Segurança

- [ ] `.env` **NÃO** está versionado (está em `.gitignore`?)
- [ ] `.streamlit/secrets.toml` **NÃO** está versionado
- [ ] Nenhum arquivo contém GOOGLE_API_KEY em texto plano
- [ ] Executar: `git status` e verificar arquivos não versionados

## 📦 Dependências

- [ ] `requirements.txt` está atualizado
  ```bash
  pip freeze > requirements.txt
  ```
- [ ] Testou instalação limpa:
  ```bash
  python -m venv test_venv
  source test_venv/bin/activate  # Windows: test_venv\Scripts\activate
  pip install -r requirements.txt
  ```
- [ ] Todas as dependências estão no arquivo

## 🧪 Testes Locais

- [ ] App rodando sem erros:
  ```bash
  streamlit run app.py
  ```
- [ ] Upload de PDF funciona
- [ ] Geração de currículo funciona
- [ ] Dashboard mostra dados
- [ ] Nenhum erro no console

## 📁 Estrutura de Pastas

- [ ] Pasta `controle_dados/` existe (será criada automaticamente?)
- [ ] Pasta `temp/` pode ser criada automaticamente
- [ ] Pasta `curriculos_gerados/` existe

## 🔄 Git

- [ ] Todos os arquivos necessários foram adicionados:
  ```bash
  git add -A
  ```
- [ ] Commit descritivo:
  ```bash
  git commit -m "🚀 Prepare for Streamlit Cloud deployment"
  ```
- [ ] Pronto para push:
  ```bash
  git push origin main
  ```

## 📝 Documentação

- [ ] Leu [QUICK_START_CLOUD.md](QUICK_START_CLOUD.md)
- [ ] Entendeu sobre persistência de dados (SQLite ephemeral)
- [ ] Sabe como configurar secrets no Streamlit Cloud

## 🔑 API Key

- [ ] Google API Key está pronta para colar
- [ ] Sabe que vai colar em: Settings ⚙️ → Secrets

---

## 📋 Checklist para o Deploy

Após fazer push para GitHub:

1. [ ] Vá para: https://share.streamlit.io/
2. [ ] Clique em "New app"
3. [ ] Preencheu corretamente:
   - Repository: `seu_usuario/Curriculator-main`
   - Branch: `main`
   - Main file path: `app.py`
4. [ ] Deploy foi iniciado
5. [ ] Aguardou ~3-5 minutos pela build
6. [ ] App ficou online (status "Your app is running")
7. [ ] Clicou em ⚙️ Settings
8. [ ] Adicionou Secret: `GOOGLE_API_KEY = "sua_chave"`
9. [ ] App reiniciou automaticamente
10. [ ] Testou: Upload PDF, Nova candidatura

---

## 🎉 Sucesso!

Se chegou aqui, sua app está **ONLINE E FUNCIONAL** 🚀

URL: `https://seu_usuario-curriculator-main-xxxxx.streamlit.app`

Compartilhe com:
- Amigos
- Familiares
- Colegas que fazem seleção

---

**Alguma dúvida?** Consulte:
- [QUICK_START_CLOUD.md](QUICK_START_CLOUD.md) — Guia rápido
- [DEPLOY_STREAMLIT_CLOUD.md](DEPLOY_STREAMLIT_CLOUD.md) — Guia completo
- [Documentação Streamlit](https://docs.streamlit.io/deploy/streamlit-cloud)
