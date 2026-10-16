#!/bin/zsh
# Daily: ask Codex / Claude / Gemini (whichever are installed) -> merge -> commit -> deploy.
export PATH=/opt/homebrew/bin:$HOME/.local/bin:/usr/local/bin:$PATH
cd "$(dirname "$0")/.." || exit 1
P=$(sed "s/DATE_PLACEHOLDER/$(date +%F)/" scripts/prompt.txt)
rm -f raw/*.json
command -v codex  >/dev/null && codex --search exec --skip-git-repo-check -s read-only "$P" > raw/codex.json 2>/dev/null
command -v claude >/dev/null && claude -p "$P" --allowedTools WebSearch WebFetch > raw/claude.json 2>/dev/null
command -v gemini >/dev/null && gemini -p "$P" > raw/gemini.json 2>/dev/null
python3 scripts/merge.py . || exit 1
git add -A && git commit -qm "events $(date +%F)" && git push -q 2>/dev/null
# Cloudflare auth lives in the Mac's wrangler login / env, never in this repo.
wrangler pages deploy site --project-name sf-ai-events --commit-dirty=true
