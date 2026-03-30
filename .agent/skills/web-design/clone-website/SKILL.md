---
name: clone-website
description: 1つ以上のWebサイトを pixel-perfect に再構築したいときの起点スキル。bundled Next.js 16 テンプレを初期化し、browser automation を使って調査・資産取得・section 単位の再構築へ進める。
---

# clone-website スキル

## 目的
- Web サイト複製用の Next.js 16 workspace を、team-info 内ですぐ作れるようにする。
- upstream の `ai-website-cloner-template` を、そのままではなく team-info 向けの template asset として再利用する。
- 実際の複製作業に入るときは、upstream の長いワークフローを reference として読む。

## 使う場面
- 「このサイトを真似して作りたい」
- 「LP を pixel-perfect で作り直したい」
- 「既存サイトを Next.js に起こしたい」
- 「/clone-website で複製の土台を作りたい」

## 前提
- browser automation が必須
- Node.js 24 系が必須
- 出力先は、特に指定がなければ `"$TEAM_INFO_ROOT/outputs/web-clones/<slug>"` を優先する

## 初期化フロー
1. 複製したい URL と出力先の絶対パスを確認する。
2. 次で workspace を初期化する。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/web-design/clone-website/scripts/init_clone_website_template.py" "$TEAM_INFO_ROOT/outputs/web-clones/<slug>"
```

3. Node 24 に切り替えて依存を入れる。

```bash
source "$HOME/.nvm/nvm.sh"
nvm use 24
cd "$TEAM_INFO_ROOT/outputs/web-clones/<slug>"
npm install
npm run build
```

4. 実際の複製作業に入る前に `references/upstream-clone-workflow.md` を読む。

## 実作業ルール
- 最初に foundation を整え、そのあと section ごとに細かく分けて進める。
- `docs/research/` を調査の正本にする。
- 実画像、実テキスト、実 SVG を優先して取る。
- まず 1:1 再現し、装飾や改善はそのあとにやる。
- 生成先の local `AGENTS.md` は、その workspace 専用の補助文脈として扱う。

## 読む reference
- 実際の複製フロー: `references/upstream-clone-workflow.md`
- 調査チェックリスト: `references/inspection-guide.md`

## ガードレール
- browser MCP が無いなら止まって確認する。
- 既存ディレクトリを上書きするときは確認する。
- cookie や認証情報は generated project に保存しない。
- upstream の agent-specific フォルダは template に戻さない。正本はこの repo の skill 側に置く。

## 検証
- 初期化スクリプトが完走する
- `npm run build` が Node 24 で通る
- `src/`, `public/`, `docs/research/`, `docs/design-references/` がそろう
- `docs/research/INSPECTION_GUIDE.md` と local `AGENTS.md` が入っている
