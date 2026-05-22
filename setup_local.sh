#!/bin/bash

# 🚀 Script de Setup para Desenvolvimento Local

echo "🔧 Configurando Curriculator para desenvolvimento local..."
echo ""

# Criar diretório de secrets do Streamlit
mkdir -p ~/.streamlit

# Verificar se secrets.toml já existe
if [ -f ~/.streamlit/secrets.toml ]; then
    echo "⚠️  ~/.streamlit/secrets.toml já existe"
    read -p "Deseja sobrescrever? (s/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "❌ Setup cancelado"
        exit 1
    fi
fi

# Solicitar API Key
echo ""
echo "Insira sua GOOGLE_API_KEY:"
read -s API_KEY

if [ -z "$API_KEY" ]; then
    echo "❌ API Key vazia!"
    exit 1
fi

# Criar arquivo de secrets
cat > ~/.streamlit/secrets.toml << EOF
GOOGLE_API_KEY = "$API_KEY"
EOF

echo ""
echo "✅ Secrets configurados em ~/.streamlit/secrets.toml"
echo ""
echo "Você pode agora executar:"
echo "  streamlit run app.py"
echo ""
