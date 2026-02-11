# プロジェクト構造マニュアル

## 各フォルダの役割
- `.agent/`:
  - エージェント用の設定とスキルを管理するフォルダ
  - `skills/` 配下に各スキル定義（`SKILL.md`）や個別マニュアルを配置
- `Remotion/`:
  - 台本作成・音声化・動画制作関連の実作業フォルダ
  - `scripts/voice_scripts/` は音声化で参照する台本置き場
  - `script_resources/` は台本作成時の素材（アカウント情報・見本台本）
- `manuals/`:
  - マニュアル集約フォルダ（このフォルダ）
  - プロジェクト構造説明と、各スキル説明へのショートカットを配置
- `.venv/`, `Remotion/.venv/`:
  - Python仮想環境
- `my-video/`, `Remotion/my-video/`:
  - Remotionプロジェクト本体や生成物

## ツリー構造（主要部）
```text
team-info/
├── .agent/
│   └── skills/
│       ├── git-workflow/
│       ├── macos-intel-compatibility/
│       ├── script-writing-accounts-aware/
│       └── voice-script-launcher/
├── Remotion/
│   ├── configs/
│   ├── scripts/
│   │   └── voice_scripts/
│   ├── script_resources/
│   │   ├── account_profiles/
│   │   └── script_samples/
│   └── output/
├── manuals/
│   ├── README.md
│   ├── PROJECT_STRUCTURE.md
│   └── skills/
└── Agent.md
```

## 運用ルール（マニュアル関連）
- 新しいスキルを作成したら、`manuals/skills/` にショートカットを追加する
- 可能なら「利用者向けのMANUAL」を優先してリンクし、なければ `SKILL.md` をリンクする
