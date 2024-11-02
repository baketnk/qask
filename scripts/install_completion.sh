#!/usr/bin/env bash

PIPX_BIN=$(pipx environment --value PIPX_BIN_DIR)/qask

# Detect shells
SHELLS=()
if [ -f "$HOME/.bashrc" ]; then
  SHELLS+=("bash")
fi
if [ -f "$HOME/.zshrc" ]; then
  SHELLS+=("zsh")
fi
if [ -f "$HOME/.config/fish/config.fish" ]; then
  SHELLS+=("fish")
fi

# Install completions for each shell
for shell in "${SHELLS[@]}"; do
  echo "Installing completions for $shell..."

  case $shell in
  "bash")
    qask --install-completion bash >>"$HOME/.bashrc"
    ;;
  "zsh")
    qask --install-completion zsh >>"$HOME/.zshrc"
    ;;
  "fish")
    qask --install-completion fish >>"$HOME/.config/fish/completions/qask.fish"
    ;;
  esac
done

echo "Completion installation finished!"
