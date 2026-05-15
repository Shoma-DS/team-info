# HyperFrames Tenshoku Short 20260416

Remotion の `TenshokuShort-20260416` を HyperFrames で再現する比較用プロジェクトです。Remotion 側は変更せず、画像・音声素材は `remotion-public` symlink から既存の `Remotion/my-video/public/` を参照します。

## 対象

- 元 Composition: `Remotion/my-video/src/viral/TenshokuShort20260416.tsx`
- 元テンプレート: `Remotion/my-video/src/viral/components/ViralTemplate.tsx`
- サイズ: `1080x1920`
- FPS: `30`
- 尺: `2394f` / `79.8s`

## 実行

```bash
npm --prefix "$TEAM_INFO_ROOT/HyperFrames/tenshoku-short-20260416" install
npm --prefix "$TEAM_INFO_ROOT/HyperFrames/tenshoku-short-20260416" run doctor
npm --prefix "$TEAM_INFO_ROOT/HyperFrames/tenshoku-short-20260416" run lint
npm --prefix "$TEAM_INFO_ROOT/HyperFrames/tenshoku-short-20260416" run inspect
npm --prefix "$TEAM_INFO_ROOT/HyperFrames/tenshoku-short-20260416" run preview
```

Ask agent から Codex / Claude を呼ぶ拡張付き preview:

```bash
npm --prefix "$TEAM_INFO_ROOT/HyperFrames/tenshoku-short-20260416" run preview:agents
```

起動後は `http://127.0.0.1:3102` を開きます。通常の `hyperframes preview` を `3002` で再利用し、Studio shell に `ask-agents-overlay.js` を注入します。既存の `Copy prompt` が作るプロンプトを使い、チェックボックスで `Codex App Server` / `Claude Code` を選んで実行できます。

Ask agent の流れ:

1. Studio 上で対象要素を選んで Ask agent を開く
2. 指示文を書き、provider を選んで `Run selected`
3. 実行モーダルで進捗バー、provider 別ステータス、ライブログを確認
4. 完了後、AI agent report、変更ファイル、diff stat、git status を確認
5. `確認してリロード` を押して Studio を再読み込みし、反映結果を見る

レンダー:

```bash
npm --prefix "$TEAM_INFO_ROOT/HyperFrames/tenshoku-short-20260416" run render
```

出力先:

```text
$TEAM_INFO_ROOT/outputs/hyperframes/tenshoku-short-20260416.mp4
```

## 比較対象

Remotion 版:

```text
$TEAM_INFO_ROOT/outputs/viral/renders/TenshokuShort-20260416.mp4
```

HyperFrames draft 版:

```text
$TEAM_INFO_ROOT/outputs/hyperframes/tenshoku-short-20260416.mp4
```

2026-05-14 の検証結果:

| 項目 | Remotion | HyperFrames |
|---|---:|---:|
| サイズ | 1080x1920 | 1080x1920 |
| FPS | 30 | 30 |
| 映像尺 | 79.8s | 79.8s |
| 音声 | AAC 48kHz stereo | AAC 48kHz stereo |
| ファイルサイズ | 9.2MB | 6.9MB |
| HyperFrames render | - | draft / workers 1 / 4m40.1s |

## 比較メモ

この版は HyperFrames の HTML composition と `window.__hf.seek()` で、Remotion のフレームベースの表示切替に近づけています。GSAP などの外部ランタイムは使わず、フレーム番号から DOM 状態を決定する構成です。

HyperFrames 0.6.6 では音声ミックス用の要素に `data-end` を明示しています。`data-duration` だけでは今回の構成で音声ストリームが出ないためです。

低メモリ環境で `sharp` が source build に落ちたため、`node-addon-api` と `node-gyp` を devDependency に明示しています。

## Ask Agents 拡張

- `scripts/ask_agents_bridge.py`: HyperFrames preview へのローカル proxy と agent 実行 API。
- `ask-agents-overlay.js`: Studio の `Ask agent` モーダルに provider 選択 UI を追加。
- Codex は `codex app-server --listen stdio://` を使い、`thread/start` から `turn/start` を実行します。
- Claude は `claude -p --permission-mode acceptEdits` を使います。
- 複数 provider を選んだ場合は、同じファイルを同時編集しないよう順番に実行します。
- 実行前後のプロジェクトファイルスナップショットを比較し、変更されたファイルを結果モーダルに表示します。

環境変数で挙動を変えられます。

```bash
ASK_AGENTS_CODEX_MODEL=gpt-5.5
ASK_AGENTS_CODEX_APPROVAL=never
ASK_AGENTS_CODEX_SANDBOX=workspace-write
ASK_AGENTS_CLAUDE_PERMISSION_MODE=acceptEdits
ASK_AGENTS_CLAUDE_MODEL=sonnet
```
