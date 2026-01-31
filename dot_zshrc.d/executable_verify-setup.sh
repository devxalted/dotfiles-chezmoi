#!/bin/bash
# Verification script for Zsh enhancement setup

echo "🔍 Zsh Setup Verification"
echo "========================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
  if [ -f "$1" ]; then
    echo -e "${GREEN}✓${NC} $1 exists"
    return 0
  else
    echo -e "${RED}✗${NC} $1 missing"
    return 1
  fi
}

check_dir() {
  if [ -d "$1" ]; then
    echo -e "${GREEN}✓${NC} $1 exists"
    return 0
  else
    echo -e "${RED}✗${NC} $1 missing"
    return 1
  fi
}

echo "📁 Checking file structure..."
check_file "$HOME/.zshrc"
check_file "$HOME/.config/starship.toml"
check_file "$HOME/.zshrc.d/aliases.zsh"
check_file "$HOME/.zshrc.d/functions.zsh"
echo ""

echo "📦 Checking zinit installation..."
check_dir "$HOME/.local/share/zinit/zinit.git"
echo ""

echo "🔧 Checking available commands..."
commands=("zsh" "git" "starship" "eza" "bat" "fd" "rg" "btm" "dust" "duf" "procs" "fnm" "zoxide" "fzf")
for cmd in "${commands[@]}"; do
  if command -v "$cmd" &> /dev/null; then
    echo -e "${GREEN}✓${NC} $cmd is installed"
  else
    echo -e "${YELLOW}⚠${NC} $cmd is not installed (optional)"
  fi
done
echo ""

echo "🎨 Testing aliases..."
if [ -f "$HOME/.zshrc.d/aliases.zsh" ]; then
  alias_count=$(grep -c "^alias" "$HOME/.zshrc.d/aliases.zsh")
  echo -e "${GREEN}✓${NC} $alias_count aliases defined"
fi
echo ""

echo "⚡ Testing functions..."
if [ -f "$HOME/.zshrc.d/functions.zsh" ]; then
  function_count=$(grep -c "^[a-z_]*() {" "$HOME/.zshrc.d/functions.zsh")
  echo -e "${GREEN}✓${NC} $function_count functions defined"
fi
echo ""

echo "📝 Next steps:"
echo "1. Restart your shell or run: source ~/.zshrc"
echo "2. Test startup time: time zsh -i -c exit"
echo "3. Try typing a command and press ↑ for history search"
echo "4. Try typing 'git' and press Tab for completions"
echo "5. Run 'gs' to test git status alias"
echo "6. Run 'mkcd testdir' to test custom functions"
echo ""

echo "💡 Useful commands:"
echo "   reload     - Reload zsh configuration"
echo "   zshconfig  - Edit .zshrc"
echo "   gs         - Git status"
echo "   glog       - Pretty git log"
echo "   mkcd DIR   - Create and enter directory"
echo "   up N       - Go up N directories"
echo ""
