#!/bin/bash
# Script para abrir os gráficos HTML no navegador corretamente
# Resolve problemas de display Wayland/X11

echo "🌐 Abrindo gráficos de análise no navegador..."
echo ""

# Definir diretório dos gráficos
RESULTS_DIR="/home/dimitri/Documents/cliente-servidor/analysis_results_interactive"

# Verificar se o diretório existe
if [ ! -d "$RESULTS_DIR" ]; then
    echo "❌ Erro: Diretório $RESULTS_DIR não encontrado"
    echo "Execute primeiro: python3 analyze.py interactive"
    exit 1
fi

# Configurar variáveis de ambiente para resolver problemas de display
export DISPLAY=:0
export WAYLAND_DISPLAY=""
export GDK_BACKEND=x11
export QT_QPA_PLATFORM=xcb

# Listar arquivos HTML disponíveis
echo "📊 Gráficos disponíveis:"
echo "1. comparison_3d_interactive.html - Comparação 3D completa"
echo "2. interactive_3d_final.html - Análise final clientes vs mensagens"
echo "3. interactive_3d_messages_1.html - Análise com 1 mensagem"
echo "4. interactive_3d_messages_10.html - Análise com 10 mensagens"
echo "5. interactive_3d_messages_100.html - Análise com 100 mensagens"
echo "6. interactive_3d_messages_500.html - Análise com 500 mensagens"
echo "7. overlapped_3d_general.html - Comparação sobreposta geral"
echo "8. overlapped_3d_final.html - Comparação sobreposta final"
echo "9. Todos os gráficos"
echo ""

# Função para abrir arquivo no navegador
open_browser() {
    local file="$1"
    local filepath="$RESULTS_DIR/$file"
    
    if [ -f "$filepath" ]; then
        echo "🔗 Abrindo: $file"
        
        # Tentar diferentes navegadores em ordem de preferência
        if command -v firefox >/dev/null 2>&1; then
            GDK_BACKEND=x11 DISPLAY=:0 firefox --new-tab "file://$filepath" 2>/dev/null &
        elif command -v google-chrome >/dev/null 2>&1; then
            GDK_BACKEND=x11 DISPLAY=:0 google-chrome "file://$filepath" 2>/dev/null &
        elif command -v chromium >/dev/null 2>&1; then
            GDK_BACKEND=x11 DISPLAY=:0 chromium "file://$filepath" 2>/dev/null &
        elif command -v xdg-open >/dev/null 2>&1; then
            GDK_BACKEND=x11 DISPLAY=:0 xdg-open "$filepath" 2>/dev/null &
        else
            echo "❌ Nenhum navegador encontrado. Instale firefox, chrome ou chromium"
            return 1
        fi
        
        sleep 1
        echo "✅ Arquivo aberto no navegador"
    else
        echo "❌ Arquivo não encontrado: $file"
        return 1
    fi
}

# Ler escolha do usuário
read -p "Escolha um gráfico (1-9): " choice

case $choice in
    1)
        open_browser "comparison_3d_interactive.html"
        ;;
    2)
        open_browser "interactive_3d_final.html"
        ;;
    3)
        open_browser "interactive_3d_messages_1.html"
        ;;
    4)
        open_browser "interactive_3d_messages_10.html"
        ;;
    5)
        open_browser "interactive_3d_messages_100.html"
        ;;
    6)
        open_browser "interactive_3d_messages_500.html"
        ;;
    7)
        open_browser "overlapped_3d_general.html"
        ;;
    8)
        open_browser "overlapped_3d_final.html"
        ;;
    9)
        echo "🚀 Abrindo todos os gráficos..."
        for file in "$RESULTS_DIR"/*.html; do
            if [ -f "$file" ]; then
                filename=$(basename "$file")
                echo "🔗 Abrindo: $filename"
                GDK_BACKEND=x11 DISPLAY=:0 firefox --new-tab "file://$file" 2>/dev/null &
                sleep 0.5
            fi
        done
        echo "✅ Todos os gráficos foram abertos em abas separadas"
        ;;
    *)
        echo "❌ Opção inválida. Use 1-9"
        exit 1
        ;;
esac

echo ""
echo "🎯 Dicas para usar os gráficos 3D:"
echo "   • Arrastar: Rotacionar o gráfico"
echo "   • Scroll: Zoom in/out"
echo "   • Shift+Arrastar: Mover (pan)"
echo "   • Hover: Ver valores detalhados"
echo "   • Use os controles no canto superior direito"
echo ""
echo "📊 Se ainda tiver problemas, tente:"
echo "   1. Reiniciar o navegador"
echo "   2. Usar modo privado/incógnito"
echo "   3. Verificar se JavaScript está habilitado"
