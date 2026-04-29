---
name: interview-product-sales
description: 採用面接の文字起こしから候補者プロファイルを抽出し、指定した商品テンプレートをもとに「面接→商品販売」の戦略と台本を生成する。
---

# interview-product-sales スキル

## 役割
採用面接の文字起こしを分析し、商品テンプレートと組み合わせて  
「面接クロージング時に商品を販売するための戦略と台本」を生成する。

商品テンプレートを差し替えるだけで、どんな商品の販売台本にも対応できる。

---

## このスキルを使う場面
- 面接録画から販売台本を生成したいとき
- 候補者名しか分からない状態から Loom を探して販売台本まで作りたいとき
- 新しい商品の販売フローを設計したいとき
- 既存台本を候補者プロファイルに合わせてカスタマイズしたいとき

---

## フォルダ構成

```text
.agent/skills/sales/interview-product-sales/
├── SKILL.md              ← このファイル
├── templates/            ← 商品テンプレート（商品ごとにフォルダを切る）
│   └── ai-online-training-50000/
│       ├── product.md        ← 商品定義（価格・ベネフィット・想定顧客）
│       └── pitch_structure.md ← ピッチ構造テンプレート
└── prompts/
    ├── extract_prospect.md   ← 候補者プロファイル抽出プロンプト
    └── generate_sales_flow.md ← 戦略・台本生成プロンプト
```

---

## 商品テンプレートの追加方法

新しい商品を追加するときは `templates/<商品ID>/` フォルダを作り、  
以下の2ファイルを置く。

| ファイル | 内容 |
|---------|------|
| `product.md` | 商品名・価格・ターゲット・ペインポイント・バリュープロポジション・競合比較・クロージングフレーズ |
| `pitch_structure.md` | フェーズ別のピッチ構造とセリフのひな形 |

---

## 標準フロー

### STEP 0: 文字起こしのソースを解決する

まず、以下の優先順位で面談ソースを確定する。

1. ユーザーが transcript ファイルを指定している場合
2. `personal/deguchishouma/sales/coaching/transcripts/interview/` に既存ファイルがある場合
3. Loom の動画タイトルまたは候補者名で検索して取得する場合

候補者名しかない場合は、先に `sales-coaching` 側の Loom 補助スクリプトを使って候補動画を探す。

```bash
python3 "$TEAM_INFO_ROOT/.agent/skills/sales/sales-coaching/scripts/search_loom.py" \
  search \
  --query "黒部千香" \
  --query "毛玉" \
  --query "[予約]在宅ワーク面談" \
  --limit 20
```

動画IDが分かったら、同じスクリプトで metadata と transcript を取得できる。

```bash
python3 "$TEAM_INFO_ROOT/.agent/skills/sales/sales-coaching/scripts/search_loom.py" \
  fetch \
  --video-id "<loom_video_id>" \
  --save-dir "/tmp/loom-mcp/<loom_video_id>"
```

### STEP 1: 文字起こしと metadata を読む

標準入力は以下のいずれか。

```text
personal/deguchishouma/sales/coaching/transcripts/interview/<ファイル名>.txt
/tmp/loom-mcp/<loom_video_id>/transcript.txt
```

可能なら次の metadata も揃える。

- `loom_video_id`
- 動画タイトル
- 録画日
- 担当者名（一次面談で実際に対応したスタッフ名）
- 現クロージング担当者名（ユーザーが明示した場合のみ）

名前に揺れがある場合の優先順位:

1. ユーザーが明示した正しい名前
2. Loom 動画タイトル
3. 文字起こし本文

### STEP 2: 候補者プロファイルを抽出する

`prompts/extract_prospect.md` のプロンプトを使い、以下を抽出する。

- 氏名・呼び方
- 家族構成・育児状況
- 直近のキャリア・職歴
- 前職月収・希望月収
- AIスキルレベル（ゼロ〜上級）
- 学習意欲・スクール検討歴
- 在宅ワーク希望の理由
- 面接中に示した興味・反応
- 痛点（解決したいこと・困っていること）
- やってみたい度（N/10点）
- 価値観の原体験・憧れの人物・将来像
- 販売上の最大フックと注意点

### STEP 3: 商品テンプレートを選ぶ

ユーザーが指定した `templates/<商品ID>/` を読む。  
未指定の場合はテンプレート一覧を提示して選んでもらう。

### STEP 4: 既存フォーマットで戦略・台本を生成する

`prompts/generate_sales_flow.md` と商品テンプレートを合わせて、  
既存の `personal/deguchishouma/sales/coaching/scripts/interview/*.md` と同じ構成で台本を生成する。

固定する見出し構成:

- `# 販売戦略・台本: <商品名>`
- `## 対象: <候補者名>  日付: <YYYY-MM-DD>`
- `## 担当: <担当者名>  loom_id: <loom_video_id>`
- `## 参考: 営業ロープレフォーマット.pdf`
- `## 候補者プロファイルサマリー`
- `**最大のフック**: ...`
- `## 2次面接 台本（全フェーズ）`
- `### フェーズ0` から `### フェーズ7`
- `## フェーズ8: 反論処理集`
- `## <候補者名>固有の注意点`

### STEP 5: 出力を保存する

**ファイル命名規則**: 相手の名前と作成日を日本語で付ける

```
personal/deguchishouma/sales/coaching/scripts/interview/YYYY年M月D日_<相手の名前>さん_販売台本.md
```

例: `2026年4月28日_渡辺さん_販売台本.md`

---

## 出力フォーマット

```markdown
# 販売戦略・台本: <商品名>
## 対象: <候補者氏名>  日付: <YYYY-MM-DD>
## 担当: <担当者名>  loom_id: <loom_video_id>
## 参考: 営業ロープレフォーマット.pdf

---

## 候補者プロファイルサマリー
（抽出した主要情報を3〜6行で要約）

**最大のフック**: （候補者に最も刺さる主訴を1行で）

---

## 2次面接 台本（全フェーズ）

### フェーズ0: 入室・ウォームアップ
...

### フェーズ1: アイスブレイク
...

### フェーズ2: きっかけのヒアリング
...

### フェーズ3: 目的の明確化
...

### フェーズ4: コミットと目標設定
...

### フェーズ5: フルコミット確認
...

### フェーズ6: テストクロージング
...

### フェーズ7: クロージング（価格提示）
...

## フェーズ8: 反論処理集
### 「反論1」
...

## <候補者名>固有の注意点
1. ...
2. ...
```

---

## 実務ルール

- 候補者プロファイルは文字起こしから読み取れる情報だけで構成する（推測を混ぜない）
- ユーザーが「今まで作られた台本のフォーマットを維持して」と言った場合は、既存の保存済み `.md` を見て構成とトーンを合わせる
- 台本は「面接担当者が読んでそのまま話せる」レベルの具体的なセリフにする
- 候補者が示した興味・反応を必ず台本のフックに組み込む
- 価格提示は必ず価値提案の後に行う
- 反論処理は最低5パターン用意する
- 反論処理より前に、フェーズ6のテストクロージングを飛ばさない
- 候補者固有の注意点には、刺さった価値観・避けるべき言い回し・再利用すべき引用を残す
- `担当者名` は原則として一次面談の担当者として扱う
- 二次面接台本では、同一話者で継続していると明示されていない限り、「前回お話しした」のような同一話者前提の表現は使わない
- 引き継ぎ前提で書く場合は、二次面接台本の冒頭フェーズで「前回は弊社の <担当者名> とお話ししてもらったと思うんですが、内容はしっかり引き継いでいます」のような表現を必ず入れる
- 引き継ぎ表現を入れる場合は、一次面談担当者からの前向きな評価や推薦が届いている形を一言入れる
- 引き継ぎ表現を入れる場合は、「かなり楽しみにしていました」「直接お話しできるのを楽しみにしていました」など、候補者が歓迎されていると伝わる期待表現も一言入れる
- 一次面談担当者からの評価は、候補者が嬉しくなるが誇張しすぎないトーンで、「かなり筋がいい」「ぜひ次に繋げたいと聞いている」「逸材だと思うと聞いている」など自然な推薦コメントとして書く
- 引き継ぎ表現を入れる場合は、初対面感を出さず、「前回の会話内容を把握したうえで続きから話している」言葉遣いに寄せる

---

## Loom 設定（Claude / Codex 共通）

### 正本の場所

Loom の認証情報は `team-info/.env` を正本として扱う。
Claude / Codex のどちらを使う場合でも、最初に更新するのはこのファイルだけにする。

```dotenv
LOOM_COOKIE=connect.sid=...
LOOM_CLIENT_ID=...
LOOM_CLIENT_SECRET=...
```

### cookieの更新手順

1. ブラウザで [loom.com](https://www.loom.com) にログイン
2. 開発者ツール（F12）→「Application」→「Cookies」→ `loom.com`
3. `connect.sid` の値をコピー
4. `team-info/.env` の `LOOM_COOKIE=` を更新する

### Claude / Codex の互換設定について

- ローカルの Python スクリプトは `.env` を直接読むので、Claude / Codex 共通で同じ値を使える
- `~/.claude.json` や `~/.codex/config.toml` に同じ値を持たせることはあるが、そちらは互換用の mirror として扱う
- 直接編集する先を増やさないため、運用上の正本は常に `.env` に固定する

### cookieが使えない場合の代替手段

MCP経由でエラーが出る場合は、Pythonで直接取得できる：

```python
import asyncio, sys
sys.path.insert(0, '/Users/deguchishouma/.cache/uv/archive-v0/c91TquNpOSGdHR6HEvx-l/lib/python3.11/site-packages')
from loom_mcp.client import LoomClient

COOKIE = 'connect.sid=<cookieの値>'
VIDEO_ID = '<loom動画ID>'

async def main():
    client = LoomClient(cookies=COOKIE)
    text = await client.get_transcript_text(VIDEO_ID)
    print(text)
    await client.aclose()

asyncio.run(main())
```

### Loom動画IDの取得方法

- URL例: `https://www.loom.com/share/2d1509b2f466412baa7090c3377c1637`
- 末尾の32文字の英数字（ハイフンなし）が動画ID: `2d1509b2f466412baa7090c3377c1637`

### loom-mcpパッケージの場所

```
~/.cache/uv/archive-v0/c91TquNpOSGdHR6HEvx-l/lib/python3.11/site-packages/loom_mcp/
```
