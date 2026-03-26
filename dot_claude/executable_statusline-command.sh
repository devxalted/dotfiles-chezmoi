#!/bin/bash

# Get JSON input
input=$(cat)

# Extract data from JSON
current_dir=$(echo "$input" | jq -r '.workspace.current_dir')
model_name=$(echo "$input" | jq -r '.model.display_name')
context_pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
context_info="${context_pct}%"

# Get machine name
hostname=$(hostname -s)

# Get current time
time=$(date +%H:%M:%S)

# Get just the directory name
dir_name=$(basename "$current_dir")

# Get git branch and status if in a git repo
git_info=""
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    branch=$(git branch --show-current 2>/dev/null)
    if [ -n "$branch" ]; then
        status_symbols=""
        if ! git diff --quiet 2>/dev/null; then
            status_symbols=" ✗"
        fi
        if ! git diff --cached --quiet 2>/dev/null; then
            status_symbols="${status_symbols} ✓"
        fi
        git_info=" ($branch$status_symbols)"
    fi
fi

# Output with colors
# Format: [hostname] [time] dir (branch) | Model | ctx% ❯
printf "\033[2m\033[38;5;141m%s\033[0m \033[2m\033[38;5;242m[\033[0m\033[2m%s\033[0m\033[2m\033[38;5;242m]\033[0m \033[2m\033[38;5;75m%s\033[0m\033[2m\033[38;5;141m%s\033[0m \033[2m\033[38;5;242m|\033[0m \033[2m\033[38;5;208m%s\033[0m \033[2m\033[38;5;242m|\033[0m \033[2m\033[38;5;82m%s\033[0m \033[2m\033[38;5;242m❯\033[0m" "$hostname" "$time" "$dir_name" "$git_info" "$model_name" "$context_info"