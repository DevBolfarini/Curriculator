#!/bin/bash

# 🚀 Script de Push para GitHub
# 
# Uso: bash push_to_github.sh
# 
# Este script:
# 1. Verifica .gitignore
# 2. Valida que não há arquivos sensíveis
# 3. Faz commit e push

set -e

echo "🔍 Validando projeto antes do push..."
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se .env existe e está em .gitignore
if [ -f ".env" ]; then
    if ! grep -q "\.env" .gitignore; then
        echo -e "${RED}❌ Erro: .env existe mas não está em .gitignore!${NC}"
        echo "Adicione a seguinte linha ao .gitignore:"
        echo "  .env"
        exit 1
    else
        echo -e "${GREEN}✅ .env está em .gitignore${NC}"
    fi
fi

# Verificar se há segredos (API Keys) em arquivos trackeados
echo ""
echo "🔐 Verificando por possíveis vazamentos de chaves..."

# Arquivos que DEVEM ser verificados (excluir exemplos e docs)
FILES_TO_CHECK=$(git ls-files --cached 2>/dev/null | grep -v "\.example$" | grep -v "\.md$" | grep -v "\.sh$" | grep -v "\.toml$")

if [ ! -z "$FILES_TO_CHECK" ]; then
    FOUND_SECRETS=false
    
    # Padrões reais de chaves (mais específicos para evitar falsos positivos)
    # Procura por chaves que parecem reais, não por templates
    if echo "$FILES_TO_CHECK" | xargs grep -E "(GOOGLE_API_KEY\s*=\s*['\"][a-zA-Z0-9_-]{20,}|sk-[a-zA-Z0-9]{20,}|Bearer\s+[a-zA-Z0-9_-]{20,})" 2>/dev/null | grep -v "sua_chave\|your_key\|placeholder\|example"; then
        echo -e "${RED}⚠️  Possível chave real detectada!${NC}"
        FOUND_SECRETS=true
    fi
    
    if [ "$FOUND_SECRETS" = true ]; then
        echo ""
        echo -e "${RED}❌ Possíveis vazamentos de segurança detectados!${NC}"
        echo "Resolva antes de fazer push."
        exit 1
    else
        echo -e "${GREEN}✅ Nenhum vazamento de segurança detectado${NC}"
    fi
else
    echo -e "${GREEN}✅ Nenhum vazamento de segurança detectado${NC}"
fi

echo -e "${GREEN}✅ Nenhum vazamento de segurança detectado${NC}"

# Verificar status do git
echo ""
echo "📋 Status do repositório:"
git status --short

# Solicitar confirmação
echo ""
echo -e "${YELLOW}Deseja prosseguir com o push? (s/n)${NC}"
read -r -n 1 REPLY
echo

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Push cancelado."
    exit 1
fi

# Fazer commit
echo ""
echo "📝 Fazendo commit..."
git add -A
git commit -m "🚀 Prepare for Streamlit Cloud deployment" || echo "ℹ️  Nenhuma mudança para commitar"

# Fazer push
echo ""
echo "📤 Enviando para GitHub..."
git push origin main

echo ""
echo -e "${GREEN}✅ Push concluído com sucesso!${NC}"
echo ""
echo "Próximo passo:"
echo "  1. Vá para: https://share.streamlit.io/"
echo "  2. Clique em 'New app'"
echo "  3. Selecione seu repositório"
echo ""
