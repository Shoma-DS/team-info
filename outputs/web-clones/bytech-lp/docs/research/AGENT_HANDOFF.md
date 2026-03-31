# Bytech LP クローン・エージェント引き継ぎ資料 (Agent Handoff)

## プロジェクト概要
- **ターゲットURL**: `https://ah-c.bytech.jp/?uid=01KM8AJKHWVPCE85EYCHP6BRKH`
- **作業ディレクトリ**: `"$TEAM_INFO_ROOT/outputs/web-clones/bytech-lp"`
- **ベーススキル**: `/clone-website` (参考: `.agent/skills/web-design/clone-website/references/upstream-clone-workflow.md`)
- **技術スタック**: Next.js 16, Tailwind v4, Node 24

## 現在の進捗状況 (Progress)
- [x] **Phase 1: Reconnaissance (調査) & Workspace Setup**
  - Next.js Workspaceの初期化完了（`npm install`, `npm run build` 通過済み）
  - ブラウザ自動化によるページ構成・アニメーション調査完了
  - `PAGE_TOPOLOGY.md` と `BEHAVIORS.md` 作成済み
- [x] **Phase 2: Foundation Build (基盤構築) - アセット抽出（自動化実行中・完了確認待ち）**
  - アセットとSVG、フォント、カラートークンを抽出してダウンロードするためのPlaywrightのスクリプト（`scripts/download-assets.mjs` および `install-and-run.sh`）を作成し、バックグラウンドで実行状態に入りました。
- [ ] **Phase 2: Foundation Build (基盤構築) - 👈 次はここから！**
  - （ここからの担当です）ダウンロードされた `DESIGN_TOKENS.json` や `RAW_SVGS.json` を確認し、抽出された色やフォントを `src/app/globals.css` と `layout.tsx` に反映してください。
  - 抽出されたSVGを綺麗に整形し、 `src/components/icons.tsx` にコンポーネント化してください。
- [ ] **Phase 3 & 4: Component Dispatch & Assembly (セクション実装)**
- [ ] **Phase 5: Visual QA Diff**

## 次のエージェントへの指示 (Next Steps)
1. まだ `public/` 内へ元サイトの画像・動画・SVGアセットの抽出が行われていません。「Phase 2: Foundation Build」として、LPのグローバルアセットをダウンロードし、`public/images/` などに保存してください。
2. LPの基調カラー（緑、背景色など）とフォント設定を抽出し、`src/app/globals.css` と `src/app/layout.tsx` に反映してください。
3. 基盤が整い次第、「Phase 3: Component Specification & Dispatch」へと進み、`docs/research/components/` に各セクションごとの `.spec.md` を作成しながら、Reactコンポーネントを逐次構築してください。

## 特記事項
- **必須確認事項**: `/clone-website` スキルのルール上、必ず各セクションの `.spec.md` に抽出したCSS（`getComputedStyle` ベース）と挙動を先に記述してから、コンポーネントの実装(`tsx`)を行う必要があります。
- ** Node 24環境**: 必ず作業前に Node 24 (`nvm use 24`) を使用してください。
