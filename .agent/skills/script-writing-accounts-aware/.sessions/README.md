# セッション管理フォルダ

このフォルダには、台本作成セッションの進行状況が保存されます。

## 目的

- 段階的な台本作成の進行状況を保存
- 構成の見本要約を保存
- ネタの台本要約を保存
- 章構成を保存
- 各章の草稿を保存
- セッション中断・再開を可能にする

## フォルダ構造

```
.sessions/
├── README.md （このファイル）
├── 20260211_143000_norse_mythology/  # セッションフォルダ（例）
│   ├── session_info.json            # セッション情報
│   ├── structure_summary.md         # 構成の見本要約
│   ├── content_summary.md           # ネタの台本要約
│   ├── chapter_plan.md              # 章構成
│   ├── draft_chapter_01.md          # 第1章の草稿
│   ├── draft_chapter_02.md          # 第2章の草稿
│   ├── draft_chapter_03.md          # 第3章の草稿
│   ├── draft_chapter_04.md          # 第4章の草稿
│   └── final_script.md              # 最終統合版（完成時）
└── 20260212_100000_universe/        # 別のセッション（例）
    └── ...
```

## セッションIDの命名規則

```
YYYYMMDD_HHMMSS_theme
```

### 例
- `20260211_143000_norse_mythology` - 2026年2月11日 14:30:00開始、テーマは北欧神話
- `20260212_100000_universe` - 2026年2月12日 10:00:00開始、テーマは宇宙

## セッション情報ファイル（session_info.json）

各セッションには `session_info.json` が含まれ、以下の情報が記録されます：

```json
{
  "session_id": "20260211_143000_norse_mythology",
  "created_at": "2026-02-11T14:30:00",
  "updated_at": "2026-02-11T15:45:30",
  "account": "sleep_travel",
  "format": "long",
  "structure_sample_script": "sleep_travel_greek_mythology.md",
  "content_sample_script": "sleep_travel_universe_01.md",
  "theme": "北欧神話",
  "total_chapters": 5,
  "completed_chapters": 2,
  "current_chapter": 3,
  "status": "in_progress",
  "chapter_plan": [
    "オープニング",
    "第1話: ギンヌンガガップ",
    "第2話: ユミルと霜の巨人",
    "第3話: オーディンと世界の創造",
    "第4話: 世界樹ユグドラシル"
  ]
}
```

### ステータス
- `in_progress`: 執筆中
- `completed`: 完成
- `paused`: 一時停止
- `abandoned`: 中止

## セッションのライフサイクル

### 1. セッション開始
- 新しいセッションフォルダを作成
- `session_info.json` を作成し、status を `in_progress` に設定

### 2. 台本の要約作成
- 構成の見本となる台本を読み込んで要約を作成
- `structure_summary.md` として保存
- ネタとなる台本を読み込んで要約を作成
- `content_summary.md` として保存

### 3. 章構成の作成
- 全体の章構成を決定
- `chapter_plan.md` として保存
- `session_info.json` の `chapter_plan` に記録

### 4. 各章の執筆
- 一章ずつ執筆
- `draft_chapter_XX.md` として保存（XXは章番号）
- 完了したら `session_info.json` の `completed_chapters` を更新

### 5. 最終統合
- 全ての章を統合
- `final_script.md` として保存
- 生成された台本を `Remotion/script_resources/generated_scripts/[日本語タイトル].md` として保存
- `session_info.json` の status を `completed` に更新

### 6. 要約ファイルの統合
- `structure_summary.md` と `content_summary.md` を1つのファイルに統合
- `Remotion/script_resources/generated_scripts/【要約】[日本語タイトル].md` として保存
- 台本と同じフォルダに保存されるため、後から参照しやすい

### 7. 一時ファイルの削除
- セッションフォルダ内の章ファイル（`draft_chapter_XX.md`）を削除
- セッションフォルダ内の元の要約ファイル（`structure_summary.md`, `content_summary.md`）を削除
- 理由: 統合版が `generated_scripts/` に保存されているため、セッション内の個別ファイルは不要
- 保持: `session_info.json`, `chapter_plan.md`, `final_script.md`

### 8. セッション完了
- 完成した台本のパスを報告
- 統合要約ファイルのパスを報告
- セッションフォルダは保持（記録として）

## セッションの再開

ユーザーが「前回の続きから」と言った場合：

1. 最新のセッションフォルダを検索（status が `in_progress` のもの）
2. `session_info.json` を読み込む
3. `current_chapter` を確認
4. 該当する章から執筆を再開

## セッションの管理

### アクティブなセッションの確認
```bash
# status が in_progress のセッションを探す
find .sessions -name "session_info.json" -exec grep -l '"status": "in_progress"' {} \;
```

### 古いセッションの削除
```bash
# 30日以上前のセッションを削除する場合
find .sessions -type d -mtime +30 -exec rm -rf {} \;
```

### セッションのバックアップ
定期的に `.sessions` フォルダ全体をバックアップすることを推奨します。

## 注意事項

### Gitignore
このフォルダはセッション作業用の一時ファイルを含むため、必要に応じて `.gitignore` に追加してください。

ただし、完成した台本のテンプレートやサンプルとして残したい場合は、個別にGitに追加してもよいでしょう。

### ディスク容量
セッションが増えるとディスク容量を消費します。定期的に不要なセッションを削除してください。

### 個人情報
セッション情報には個人的なメモやテーマが含まれる可能性があります。公開リポジトリの場合は注意してください。

## トラブルシューティング

### セッションが見つからない
- セッションIDが正しいか確認
- `.sessions/` フォルダのパーミッションを確認

### session_info.json が破損している
- 手動でファイルを編集して修正
- または、新しいセッションを開始

### 途中で章構成を変更したい
- `chapter_plan.md` を手動で編集
- `session_info.json` の `chapter_plan` も更新
- 次の章からは新しい構成に従う

---

**最終更新**: 2026-02-11
