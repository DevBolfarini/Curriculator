# 🚀 MASTER PLAN - Curriculator Evolution (Radar de Vagas)

> [!IMPORTANT]
> **INSTRUÇÃO PARA A IA (GEMINI PRO):** Você está recebendo um projeto Python/Streamlit que automatiza a criação de currículos. Sua missão é implementar o módulo "Radar de Vagas". Sinta-se incentivado a analisar o código atual e sugerir melhorias de performance, UX ou arquitetura antes de iniciar, pedindo a aprovação do usuário para as mudanças sugeridas.

## 1. Contexto Atual
- **Tecnologias:** Python, Streamlit, SQLite, Google GenAI (Gemini).
- **Estrutura:**
  - `app.py`: Interface principal.
  - `database.py`: Gerenciamento do SQLite.
  - `services.py`: Lógica de extração de PDF, prompts e geração de PDFs.
- **Segurança:** O projeto usa Git para versionamento. O arquivo `.env` gerencia chaves de API.

---

## 2. Próxima Grande Implementação: RADAR DE VAGAS

### 2.1 Banco de Dados (`database.py`)
- **Implementar:** Tabela `vagas_radar`.
- **Campos sugeridos:** `id`, `data_descoberta`, `empresa`, `cargo`, `link`, `status` ('pendente', 'aplicado', 'descartado') e `match_score`.

### 2.2 Inteligência de Busca (`services.py`)
- **Meta-Prompt:** Criar uma função que analise o currículo mestre e retorne 3 frases de busca inteligentes (ex: "Desenvolvedor Backend Python Remoto").
- **API de Busca:** Uso da **SerpApi** (Google Jobs API).
  - Integrar o retorno JSON com a tabela `vagas_radar`.
  - Diferencial: Limitar a busca por data (ex: vagas das últimas 24h).

### 2.3 Interface do Usuário (`app.py`)
- **Nova Aba "Radar de Vagas":**
  - Botão de sincronização diária.
  - Visualização em Cards das vagas encontradas.
  - Ações rápidas:
    - **[Aplicar]:** Abre o link da vaga e já preenche os campos de candidatura na outra aba.
    - **[Lembrar depois]:** Muda o status no banco.
    - **[Descartar]:** Remove da vista.

---

## 3. Diretriz Analítica (Para o Gemini Pro)

**Analise as seguintes áreas e proponha melhorias:**
1. **Performance:** O processamento de PDF e as chamadas de API podem ser assíncronas?
2. **UX/UI:** O dashboard em Streamlit pode ser mais elegante ou intuitivo?
3. **Prompt Engineering:** Os prompts atuais em `services.py` podem ser otimizados para gastar menos tokens ou serem mais precisos?
4. **Erro Handling:** Como melhorar a robustez contra erros de cota (429) ou falhas na leitura de URLs complexas?

---

## 4. Como Executar
1. Leia todos os arquivos do repositório.
2. Proponha sua visão de melhoria baseada nos itens acima.
3. Aguarde a aprovação do usuário.
4. Codifique as funções de busca e integração de banco de dados por partes.

---
*Documento gerado por Antigravity em 17/04/2026.*
