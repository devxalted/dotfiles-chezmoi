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
  echo "Original: $(numfmt --to=iec-i --suffix=B $origsize)"
  echo "Gzipped: $(numfmt --to=iec-i --suffix=B $gzipsize)"
  echo "Ratio: ${ratio}%"
}

# Smart extract function
extract() {
  if [ -f "$1" ]; then
    case "$1" in
      *.tar.bz2)   tar xjf "$1"     ;;
      *.tar.gz)    tar xzf "$1"     ;;
      *.bz2)       bunzip2 "$1"     ;;
      *.rar)       unrar x "$1"     ;;
      *.gz)        gunzip "$1"      ;;
      *.tar)       tar xf "$1"      ;;
      *.tbz2)      tar xjf "$1"     ;;
      *.tgz)       tar xzf "$1"     ;;
      *.zip)       unzip "$1"       ;;
      *.Z)         uncompress "$1"  ;;
      *.7z)        7z x "$1"        ;;
      *.tar.xz)    tar xf "$1"      ;;
      *.txz)       tar xf "$1"      ;;
      *)           echo "'$1' cannot be extracted via extract()" ;;
    esac
  else
    echo "'$1' is not a valid file"
  fi
}

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
