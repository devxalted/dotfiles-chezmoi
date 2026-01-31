#!/bin/bash

# Get JSON input
input=$(cat)

# Extract current directory and model from JSON
current_dir=$(echo "$input" | jq -r '.workspace.current_dir')
model_name=$(echo "$input" | jq -r '.model.display_name')

# Get current time
time=$(date +%H:%M:%S)

# Get just the directory name (equivalent to %1~ in zsh)
dir_name=$(basename "$current_dir")

# Get git branch and status if in a git repo
git_info=""
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    branch=$(git branch --show-current 2>/dev/null)
    if [ -n "$branch" ]; then
        # Check for changes (equivalent to zsh vcs_info)
        status_symbols=""
        if ! git diff --quiet 2>/dev/null; then
            status_symbols=" ✗"  # unstaged changes
        fi
        if ! git diff --cached --quiet 2>/dev/null; then
            status_symbols="${status_symbols} ✓"  # staged changes
        fi
        git_info=" ($branch$status_symbols)"
    fi
fi

# Output with colors using printf (dimmed colors for status line)
# Format: [time] dir (branch) | Model ❯
printf "\033[2m\033[38;5;242m[\033[0m\033[2m%s\033[0m\033[2m\033[38;5;242m]\033[0m \033[2m\033[38;5;75m%s\033[0m\033[2m\033[38;5;141m%s\033[0m \033[2m\033[38;5;242m|\033[0m \033[2m\033[38;5;208m%s\033[0m \033[2m\033[38;5;242m❯\033[0m" "$time" "$dir_name" "$git_info" "$model_name"