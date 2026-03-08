# Remotion/ — 動画制作環境

Remotion（React ベースの動画レンダリングフレームワーク）を使った
チャンネル動画制作の作業ディレクトリ。

## サブフォルダ構造

| フォルダ | 用途 |
|---|---|
| `my-video/` | メイン Remotion プロジェクト（npm プロジェクトルート） |
| `my-video/src/` | React コンポーネント（チャンネル別テンプレート） |
| `my-video/public/` | 静的アセット（音声・画像・動画素材） |
| `my-video/public/assets/songs/` | 楽曲ごとのフォルダ（audio.mp3, lyrics.lrc, lyric_animation_data.json） |
| `my-video/public/assets/channels/` | チャンネル別素材（背景動画・エフェクト等） |
| `scripts/` | Python 補助スクリプト（LRC生成・解析等） |
| `scripts/lyrics/` | Whisper 生成 + 手修正済み LRC ファイル |
| `script_resources/` | 台本サンプル・参考素材 |
| `configs/` | チャンネル設定ファイル |
| `.venv/` | Python 仮想環境（Git 管理外） |

## よく使うコマンド

```bash
# Remotion Studio（プレビュー）
npm --prefix "$TEAM_INFO_ROOT/Remotion/my-video" run dev

# TypeScript 型チェック
npm --prefix "$TEAM_INFO_ROOT/Remotion/my-video" run typecheck

# レンダリング
npm --prefix "$TEAM_INFO_ROOT/Remotion/my-video" run render -- --composition={CompositionID}
```

## Composition 命名規則

| チャンネル | パターン | 例 |
|---|---|---|
| アコリエル | `AcoRiel-{曲名}-{バリアント}` | `AcoRiel-Diamond-Princess-MultiBG` |
| 寝ながらトラベル | `SleepTravel-{種別}-{日付}` | `SleepTravel-Long-20260308` |

## 楽曲フォルダ構成（アコリエル）

```
my-video/public/assets/songs/{曲名}/
├── audio.mp3                  楽曲音源
├── lyrics.lrc                 タイミング付き歌詞（LRC形式）
└── lyric_animation_data.json  Remotion アニメーション用 JSON（48エントリ等）
```

## 使用チャンネル

- **acoriel（アコリエル）**: アコースティックカバー動画。MultiBG テンプレート使用。
- **sleep_travel（寝ながらトラベル）**: 知識系・旅行系ショート/長尺動画。

## Python 仮想環境

```
Remotion/.venv/bin/python3.11
```

Whisper（faster-whisper）・OpenCV・mediapipe 等がインストール済み。
