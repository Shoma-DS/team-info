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

# 単発レンダリング（出力先を自分で指定）
npm --prefix "$TEAM_INFO_ROOT/Remotion/my-video" run render -- SleepTravelLong "$TEAM_INFO_ROOT/outputs/common/renders/sample.mp4"

# 固定テンプレート + JSON 差し替えで量産レンダリング
npm --prefix "$TEAM_INFO_ROOT/Remotion/my-video" run render:outputs -- Viral-Studio-Template viral-variant.mp4 --props "$TEAM_INFO_ROOT/path/to/viral-props.json"
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

## 量産向けの基本導線

記事の「AI で量産する」という話のうち、この repo でそのまま使いやすいのは
**勝てる型を固定し、素材と文言だけを JSON で差し替える運用**です。

1. `Viral-Clip-Editor` で既存プリセットを調整する
2. `JSON 書き出し` で設定を保存する
3. `Viral-Studio-Template` に `--props` で JSON を渡してレンダリングする

`Viral-Studio-Template` は、シーン終端と字幕終端から尺を自動計算するため、
JSON 側のタイムラインが変わっても毎回コードを増やさずに縦動画を書き出せる。
「テンプレを固定して中身だけ差し替える」量産導線として使う。

## Python ランタイム

```
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" run-remotion-python -- ...
```

標準は Docker ランタイム `team-info/python-skill-runtime:3.11.9`。Whisper（faster-whisper）・OpenCV・mediapipe 等はそこに固定される。
