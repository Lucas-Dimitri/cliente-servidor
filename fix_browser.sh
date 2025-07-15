#!/bin/bash
# Script melhorado para abrir gráficos com resolução de problemas de display

echo "🔧 Configurando ambiente para abrir gráficos..."

# Configurar variáveis de ambiente para forçar X11
export DISPLAY=:0
export GDK_BACKEND=x11
export MOZ_ENABLE_WAYLAND=0
export XDG_SESSION_TYPE=x11

# Verificar se X11 está rodando
if ! xset q &>/dev/null; then
    echo "⚠️  X11 não está rodando. Tentando iniciar..."
    startx &
    sleep 3
fi

# Caminho para os gráficos
GRAPHS_DIR="/home/dimitri/Documents/cliente-servidor/analysis_results_interactive"

echo "📂 Abrindo gráfico principal..."

# Tentar abrir com Firefox forçando X11
if command -v firefox >/dev/null 2>&1; then
    echo "🚀 Iniciando Firefox com suporte X11..."
    
    # Matar processos Firefox existentes para evitar conflitos
    pkill firefox 2>/dev/null
    sleep 1
    
    # Abrir Firefox com configurações específicas
    DISPLAY=:0 GDK_BACKEND=x11 MOZ_ENABLE_WAYLAND=0 \
    firefox --new-instance --no-remote \
    "$GRAPHS_DIR/comparison_3d_interactive.html" \
    "$GRAPHS_DIR/overlapped_3d_general.html" &
    
    echo "✅ Firefox iniciado! Aguarde alguns segundos..."
    sleep 3
    
    echo "🎯 Se os gráficos não abriram, tente:"
    echo "   1. Verificar se o Firefox abriu (pode estar minimizado)"
    echo "   2. Navegar manualmente para: file://$GRAPHS_DIR/"
    echo "   3. Clicar duas vezes no arquivo .html no gerenciador de arquivos"
    
else
    echo "❌ Firefox não encontrado. Tentando instalar..."
    sudo apt update && sudo apt install firefox-esr -y
fi

# Alternativa: abrir gerenciador de arquivos
echo ""
echo "💡 Alternativa: Abrindo gerenciador de arquivos na pasta dos gráficos..."
if command -v nautilus >/dev/null 2>&1; then
    nautilus "$GRAPHS_DIR" 2>/dev/null &
elif command -v thunar >/dev/null 2>&1; then
    thunar "$GRAPHS_DIR" 2>/dev/null &
elif command -v pcmanfm >/dev/null 2>&1; then
    pcmanfm "$GRAPHS_DIR" 2>/dev/null &
fi

echo ""
echo "📋 Instruções manuais:"
echo "   1. Abra o gerenciador de arquivos"
echo "   2. Navegue para: $GRAPHS_DIR"
echo "   3. Clique duas vezes em qualquer arquivo .html"
echo "   4. Escolha 'Abrir com Firefox' se perguntado"
echo ""
echo "🎯 Principais gráficos:"
echo "   • comparison_3d_interactive.html - Comparação completa"
echo "   • overlapped_3d_general.html - Gráficos sobrepostos"
echo "   • interactive_3d_final.html - Análise final"
