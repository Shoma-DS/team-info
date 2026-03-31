#!/bin/bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 24

cd /Users/deguchishouma/team-info/outputs/web-clones/bytech-lp
npm i playwright --save-dev
npx playwright install chromium

node scripts/download-assets.mjs
