# Useful functions

# Create directory and cd into it
mkcd() {
  mkdir -p "$1" && cd "$1"
}

# Go up N directories
up() {
  local count=${1:-1}
  local path=""
  for ((i=0; i<count; i++)); do
    path="../$path"
  done
  cd "$path" || return
}

# Get gzipped size of file
gz() {
  local origsize=$(wc -c < "$1")
  local gzipsize=$(gzip -c "$1" | wc -c)
  local ratio=$(echo "scale=2; $gzipsize * 100 / $origsize" | bc)
  echo "Original: $origsize bytes"
  echo "Gzipped: $gzipsize bytes"
  echo "Ratio: ${ratio}%"
}

# extract() provided by OMZ extract plugin via zinit

# Quick find in files
fif() {
  if [ -z "$1" ]; then
    echo "Usage: fif <search-term>"
    return 1
  fi
  rg --files-with-matches --no-messages "$1" | fzf --preview "rg --ignore-case --pretty --context 10 '$1' {}"
}

# Git clone and cd
gcl() {
  git clone "$1" && cd "$(basename "$1" .git)"
}

# Create a backup of a file
backup() {
  cp "$1" "$1.backup-$(date +%Y%m%d-%H%M%S)"
}

# Show disk usage of current directory
ducks() {
  dust -d 1 -r
}
