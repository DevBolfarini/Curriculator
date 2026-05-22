#!/bin/bash
# Script simples de push para GitHub

cd /home/dbolfarini/Downloads/Curriculator-main

echo "📝 Fazendo commit das mudanças..."
git add -A
git commit -m "🚀 Prepare for Streamlit Cloud deployment" || echo "Nenhuma mudança para commitar"

echo ""
echo "📤 Enviando para GitHub..."
echo "Será solicitado suas credenciais do GitHub..."
echo ""

# Fazer push
git push origin main

echo ""
echo "✅ Push concluído!"
