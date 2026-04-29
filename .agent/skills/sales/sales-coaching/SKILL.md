# sales-coaching スキル

## 概要
ジモティー営業（1S・面接）の文字起こしを Loom MCP で取得し、
ローカル保存と Supabase 登録まで進める。
担当者名は Loom アカウント所有者ではなく、文字起こし冒頭の自己紹介から抽出する。
また、在宅ワーク面談・その他面談・セミナーなどを動的に判定してタグを付ける。
その後の分析・スクリプト生成・比較レポートは Claude Code / Codex が担当する。

## 担当者
- 出口（deguchi）
- 菅下（sugashita）

## 対応種別
- **1S**：ジモティーの求職者への初回アプローチ
- **面接**：応募者との採用面接

---

## フォルダ構成

```text
personal/deguchishouma/sales/coaching/
├── transcripts/
│   ├── 1s/          # 1S文字起こし原本
│   └── interview/   # 面接文字起こし原本
├── analysis/
│   ├── 1s/          # 1S分析レポート（Claude Codeが生成）
│   └── interview/   # 面接分析レポート（Claude Codeが生成）
├── scripts/
│   ├── 1s/          # 1S改善トークスクリプト（Claude Codeが生成）
│   └── interview/   # 面接改善トークスクリプト（Claude Codeが生成）
└── reports/
    ├── comparison/  # 出口vs菅下比較レポート（Claude Codeが生成）
    └── progress/    # 改善推移レポート
```

---

## 役割分担

| 処理 | 担当 | 理由 |
|-----|------|------|
| Loom動画情報・文字起こし取得 | Loom MCP | OAuth実装なしで安定して取得できる |
| Loom MCP export の整形・保存 | Python（run_all.py） | 分類・保存・DB登録をまとめて行う |
| Supabase upsert | Python（run_all.py） | 既存分類結果とまとめて登録できる |
| 種別・話者の簡易判別 | Python（キーワード） | APIコストゼロ |
| 種別・話者の精度確認 | Claude Code | 信頼度が低い場合に目視修正 |
| フェーズ別詳細分析 | Claude Code | 従量課金なし |
| 改善トークスクリプト生成 | Claude Code | 従量課金なし |
| 比較レポート生成 | Claude Code | 従量課金なし |

---

## STEP 1: Loom MCP で export を保存する

Codex / Claude Code から Loom MCP を使い、対象動画を export する。
`get_video_details` か `get_transcript` に `save_dir` を渡すと、次のようなファイルが保存される。

```text
/tmp/loom-mcp/<video_id>/
├── metadata.json
├── transcript.txt
├── summary.txt
├── chapters.txt
├── tasks.txt
└── comments.txt
```

`run_all.py` が必須で読むのは `metadata.json` と `transcript.txt`。
他のファイルはあれば一緒に Supabase へ入る。

---

## STEP 2: export を分類・保存・Supabase 登録する

### 前提：`.env` に Supabase の接続情報を入れる

```bash
echo 'SUPABASE_URL=https://<project-ref>.supabase.co' >> "$TEAM_INFO_ROOT/.env"
echo 'SUPABASE_SERVICE_ROLE_KEY=ここにservice_role_key' >> "$TEAM_INFO_ROOT/.env"
echo 'SUPABASE_TABLE=sales_coaching_transcripts' >> "$TEAM_INFO_ROOT/.env"
```

`SUPABASE_ACCESS_TOKEN` だけでは行データの insert / upsert はできない。
`SUPABASE_SERVICE_ROLE_KEY` を使う。

### 実行コマンド

```bash
"$TEAM_INFO_ROOT/Remotion/.venv/bin/python3.11" \
  "$TEAM_INFO_ROOT/.agent/skills/sales/sales-coaching/scripts/run_all.py" \
  --loom-export-dir "/tmp/loom-mcp/<video_id>" \
  --sync-supabase
```

複数件ある場合は `--loom-export-dir` を複数回付ける。

```bash
"$TEAM_INFO_ROOT/Remotion/.venv/bin/python3.11" \
  "$TEAM_INFO_ROOT/.agent/skills/sales/sales-coaching/scripts/run_all.py" \
  --loom-export-dir "/tmp/loom-mcp/<video_id_1>" \
  --loom-export-dir "/tmp/loom-mcp/<video_id_2>" \
  --sync-supabase
```

実行後、文字起こしは `personal/deguchishouma/sales/coaching/transcripts/1s/` または `personal/deguchishouma/sales/coaching/transcripts/interview/` に保存され、
同じ内容が Supabase に upsert される。

Supabase へ入る主な項目:
- `facilitator_name` / `facilitator_slug` / `facilitator_role`
- `session_kind` / `session_tags` / `work_domain`
- `conversation_type`（従来の `1s` / `interview`）
- `loom_owner_name` は共有 Loom アカウントの補助情報としてのみ保持

---

## STEP 3: Supabase の最小テーブル例

`on_conflict=loom_video_id` で upsert するので、`loom_video_id` に unique 制約が必要。

```sql
create table if not exists public.sales_coaching_transcripts (
  id bigint generated always as identity primary key,
  loom_video_id text not null unique,
  source text not null default 'loom_mcp',
  video_name text,
  recorded_at timestamptz,
  processed_date date,
  loom_owner_name text,
  organization_name text,
  duration_seconds numeric,
  views_total integer,
  speaker text,
  speaker_confidence integer,
  speaker_reason text,
  facilitator_name text,
  facilitator_slug text,
  facilitator_role text,
  facilitator_confidence integer,
  conversation_type text,
  type_confidence integer,
  type_reason text,
  session_kind text,
  session_confidence integer,
  session_reason text,
  session_tags jsonb not null default '[]'::jsonb,
  work_domain text,
  calendar_meeting_guid text,
  transcript text not null,
  summary_text text,
  chapters_text text,
  tasks_text text,
  comments_text text,
  transcript_local_path text,
  loom_export_dir text,
  raw_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
```

---

## STEP 4: 詳細分析（Claude Code担当）

ユーザーが以下のように指示する：
```text
personal/deguchishouma/sales/coaching/transcripts/ の新しいファイルを分析して
```

### Claude Codeが実行する手順

1. **ファイルを読み込む**
   - メタデータ（speaker, type, date, loom_id）を確認
   - 種別・話者の信頼度が低ければ内容から再判定して修正

2. **フェーズ別詳細分析**
   - `prompts/analyze_1s.md` または `prompts/analyze_interview.md` を読み込む
   - プロンプトに従ってフェーズ別スコアリング・改善点を分析
   - 結果を `personal/deguchishouma/sales/coaching/analysis/{1s|interview}/{date}_{speaker}_analysis.md` に保存

3. **改善トークスクリプト生成**
   - `prompts/generate_script.md` を読み込む
   - 分析レポートをもとに改善版スクリプトを生成
   - `personal/deguchishouma/sales/coaching/scripts/{1s|interview}/{date}_{speaker}_script.md` に保存

---

## STEP 5: 比較レポート（Claude Code担当）

ユーザーが以下のように指示する：
```text
出口と菅下の1S営業を比較レポートにして
```

### Claude Codeが実行する手順

1. `personal/deguchishouma/sales/coaching/analysis/1s/` または `analysis/interview/` の全ファイルを読む
2. `prompts/compare_speakers.md` を読み込む
3. プロンプトに従って比較レポートを生成
4. `personal/deguchishouma/sales/coaching/reports/comparison/{date}_comparison_{type}.md` に保存

---

## スクリプト構成

| ファイル | 役割 | AI使用 |
|---------|-----|--------|
| `fetch_loom.py` | Loom API 取得の旧経路。必要時のみ使う | なし |
| `classify.py` | キーワードベースで種別・話者を簡易判別 | なし |
| `save_transcript.py` | Loom export の読込、文字起こし保存、Supabase payload 作成 | なし |
| `run_all.py` | Loom MCP export の取り込みと Supabase upsert の実行 | なし |

---

## 旧 Loom API 経路（必要時のみ）

MCP が使えない場合だけ、従来の Loom OAuth ルートを使う。
この場合は `LOOM_CLIENT_ID` と `LOOM_CLIENT_SECRET` が必要。

```bash
"$TEAM_INFO_ROOT/Remotion/.venv/bin/python3.11" \
  "$TEAM_INFO_ROOT/.agent/skills/sales/sales-coaching/scripts/run_all.py" \
  --url "https://www.loom.com/share/動画ID"
```
