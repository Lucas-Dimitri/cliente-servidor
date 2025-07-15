#!/bin/bash

echo "🚀 Abrindo todos os gráficos da pasta analysis_results_interactive..."

GRAPHS_DIR="/home/dimitri/Documents/cliente-servidor/analysis_results_interactive"

# Verificar se a pasta existe
if [ ! -d "$GRAPHS_DIR" ]; then
    echo "❌ Pasta não encontrada: $GRAPHS_DIR"
    exit 1
fi

echo "📂 Abrindo gerenciador de arquivos na pasta dos gráficos..."

# Tentar diferentes gerenciadores de arquivos
if command -v nautilus >/dev/null 2>&1; then
    nautilus "$GRAPHS_DIR" &
    echo "✅ Nautilus aberto!"
elif command -v thunar >/dev/null 2>&1; then
    thunar "$GRAPHS_DIR" &
    echo "✅ Thunar aberto!"
elif command -v pcmanfm >/dev/null 2>&1; then
    pcmanfm "$GRAPHS_DIR" &
    echo "✅ PCManFM aberto!"
elif command -v dolphin >/dev/null 2>&1; then
    dolphin "$GRAPHS_DIR" &
    echo "✅ Dolphin aberto!"
else
    echo "⚠️  Nenhum gerenciador de arquivos encontrado. Tentando xdg-open..."
    xdg-open "$GRAPHS_DIR" &
fi

echo ""
echo "📋 INSTRUÇÕES:"
echo "1. No gerenciador de arquivos que abriu, você verá todos os arquivos .html"
echo "2. Clique duas vezes em qualquer arquivo .html para abrir no navegador"
echo "3. Ou selecione múltiplos arquivos (Ctrl+clique) e abra todos de uma vez"
echo ""
echo "🎯 PRINCIPAIS GRÁFICOS RECOMENDADOS:"
echo "   • comparison_3d_interactive.html - Comparação lado a lado completa"
echo "   • overlapped_3d_general.html - Gráficos sobrepostos (melhor para comparação)"
echo "   • interactive_3d_final.html - Análise final consolidada"
echo ""
echo "📊 GRÁFICOS POR NÚMERO DE MENSAGENS:"
echo "   • interactive_3d_messages_*.html - Gráficos interativos por cenário"
echo "   • overlapped_3d_messages_*.html - Gráficos sobrepostos por cenário"
echo ""
echo "💡 DICA: Use Ctrl+clique para selecionar múltiplos arquivos e abrir todos de uma vez!"

# Listar todos os arquivos disponíveis
echo ""
echo "📁 Arquivos disponíveis:"
ls -1 "$GRAPHS_DIR"/*.html | sed 's|.*/||' | sort
