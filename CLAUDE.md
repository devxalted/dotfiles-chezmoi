# Home Directory Instructions

## Dotfiles & Chezmoi

When I ask you to modify any config files (anything in `~/.config/`, `~/.zshrc`, etc.):

1. **Always check if the file is managed by chezmoi** - look for it in `~/.local/share/chezmoi/`
2. **Ask me before adding to chezmoi**: "Is this change for Linux only, or for all systems?"
3. **Based on my answer**:
   - **Linux only**: Edit the chezmoi source file directly (no template needed for Linux-only files like Hyprland)
   - **All systems**: Edit the chezmoi source, using `.tmpl` extension and `{{ if eq .chezmoi.os "..." }}` conditionals if OS-specific behavior is needed
   - **This machine only**: Edit only the live config, not chezmoi source

## Chezmoi File Naming

- Regular files: `dot_config/app/config` -> `~/.config/app/config`
- Templates: `dot_config/app/config.tmpl` -> `~/.config/app/config`
- Executable scripts: `executable_script.sh`

## Common Paths

- Chezmoi source: `~/.local/share/chezmoi/`
- Hyprland (Linux only): `dot_config/hypr/hyprland.conf`
- Zsh: `dot_zshrc.tmpl`, `dot_zshrc.d/`
- Wezterm: `dot_config/wezterm/wezterm.lua.tmpl`
