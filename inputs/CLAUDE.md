# inputs/ — 素材インボックス

ここはすべての **入力素材・解析対象ファイルの置き場**。
生成・出力物は `outputs/` へ。このフォルダに出力ファイルを置かないこと。

## サブフォルダ構造

| フォルダ | 用途 | 対応スキル |
|---|---|---|
| `viral-analysis/` | バズ動画解析インボックス（.mp4 を置く） | `viral-template-generator` |

## viral-analysis インボックスの使い方

```
inputs/viral-analysis/
└── （解析したい動画ファイルを .mp4 / .mov 形式で置く）
```

解析スクリプトを引数なしで起動すると、このフォルダの動画一覧が表示され、
インタラクティブに選択できる。選択時は OS ネイティブ通知が鳴る。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/viral-template-generator/scripts/analyze_video.py"
```

## 注意

- バイナリファイル（.mp4 等）は Git 管理外（.gitignore 参照）
- フォルダ名は kebab-case（英語）で統一
