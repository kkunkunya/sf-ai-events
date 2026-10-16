#!/bin/zsh
# Daily: for each city, ask Codex / Claude / Gemini (whichever are installed) -> merge -> push (GitHub Pages serves docs/).
export PATH=/opt/homebrew/bin:$HOME/.local/bin:/usr/local/bin:$PATH
cd "$(dirname "$0")/.." || exit 1
CITIES=("San Francisco Bay Area" Beijing Shanghai)
rm -f raw/*.json
ask() {  # $1 = city
  local P=$(sed -e "s/DATE_PLACEHOLDER/$(date +%F)/" -e "s/CITY_PLACEHOLDER/$1/" scripts/prompt.txt) f="raw/${1// /_}"
  command -v codex  >/dev/null && timeout 900 codex --search exec --skip-git-repo-check -s read-only "$P" > "$f.codex.json" 2>/dev/null &
  command -v claude >/dev/null && timeout 900 claude -p "$P" --allowedTools WebSearch WebFetch > "$f.claude.json" 2>/dev/null &
  command -v gemini >/dev/null && timeout 900 gemini -p "$P" > "$f.gemini.json" 2>/dev/null &
  wait
}
for c in "${CITIES[@]}"; do ask "$c" & done; wait
python3 scripts/merge.py . || exit 1
git add -A && git commit -qm "events $(date +%F)" && git push -q
