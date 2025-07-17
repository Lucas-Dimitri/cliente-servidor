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
    echo "🚀 Abrindo gráficos no Firefox (mantendo abas existentes)..."
    
    # NÃO matar processos Firefox existentes para preservar suas abas
    # Verificar se Firefox já está rodando
    if pgrep firefox >/dev/null; then
        echo "✅ Firefox já está rodando - abrindo em nova janela..."
        # Usar --new-window para abrir em nova janela sem fechar abas existentes
        DISPLAY=:0 GDK_BACKEND=x11 MOZ_ENABLE_WAYLAND=0 \
        firefox --new-window "$GRAPHS_DIR"/*.html &
    else
        echo "🚀 Iniciando nova instância do Firefox..."
        # Abrir Firefox com todos os gráficos da pasta
        DISPLAY=:0 GDK_BACKEND=x11 MOZ_ENABLE_WAYLAND=0 \
        firefox "$GRAPHS_DIR"/*.html &
    fi
    
    echo "✅ Gráficos sendo abertos no Firefox! Aguarde alguns segundos..."
    sleep 3
    
    echo "🎯 Se os gráficos não abriram, tente:"
    echo "   1. Verificar se o Firefox abriu (pode estar minimizado)"
    echo "   2. Navegar manualmente para: file://$GRAPHS_DIR/"
    echo "   3. Clicar duas vezes no arquivo .html no gerenciador de arquivos"
    echo "   4. Os gráficos devem abrir em abas/janela nova"
    
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
echo "🎯 Principais gráficos que devem abrir:"
echo "   • comparison_3d_interactive.html - Comparação completa"
echo "   • overlapped_3d_general.html - Gráficos sobrepostos"
echo "   • interactive_3d_final.html - Análise final"
echo "   • overlapped_3d_final.html - Análise sobreposta final"
echo "   • interactive_3d_messages_*.html - Gráficos por número de mensagens (1, 10, 100, 500, 1000, 10000)"
echo "   • overlapped_3d_messages_*.html - Gráficos sobrepostos por número de mensagens"
echo ""
echo "📊 Total: 16 gráficos interativos em abas separadas"
