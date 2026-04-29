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

### STEP 1: 文字起こしを読み込む

```
personal/deguchishouma/sales/coaching/transcripts/interview/<ファイル名>.txt
```
または Supabase から `loom_video_id` で取得する。

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

### STEP 3: 商品テンプレートを選ぶ

ユーザーが指定した `templates/<商品ID>/` を読む。  
未指定の場合はテンプレート一覧を提示して選んでもらう。

### STEP 4: 戦略・台本を生成する

`prompts/generate_sales_flow.md` と商品テンプレートを合わせて、  
以下の台本を生成する。

| フェーズ | 内容 |
|---------|------|
| 0. 面接クロージング直前のチェック | 候補者の温度感・ラポール状態の確認 |
| 1. ニーズの言語化 | 候補者の痛点を本人に言葉にさせる問いかけ |
| 2. 価値提案 | 商品が痛点を解決することの説明 |
| 3. 社会的証明 | 実績・事例・デモの紹介 |
| 4. 価格提示 | 価格の伝え方・正当化 |
| 5. クロージング | 申し込みへの誘導 |
| 6. 反論処理 | 想定される断り文句への返し |

### STEP 5: 出力を保存する

**ファイル命名規則**: 相手の名前と作成日を日本語で付ける

```
personal/deguchishouma/sales/coaching/scripts/interview/YYYY年M月D日_<相手の名前>さん_販売台本.md
```

例: `2026年4月28日_渡辺さん_販売台本.md`

---

## 出力フォーマット

```markdown
# 販売戦略・台本
## 候補者プロファイル
...

## 商品: <商品名>

## 販売戦略サマリー
- 最大のフック: ...
- 適切な提案タイミング: ...
- 想定される反論: ...

## フェーズ別台本

### フェーズ1: ニーズの言語化
**セリフ例:**
> ...

**ポイント:** ...

（以下フェーズ2〜6を続ける）

## 反論処理集
| 反論 | 返し |
|-----|------|
| ... | ... |
```

---

## 実務ルール

- 候補者プロファイルは文字起こしから読み取れる情報だけで構成する（推測を混ぜない）
- 台本は「面接担当者が読んでそのまま話せる」レベルの具体的なセリフにする
- 候補者が示した興味・反応を必ず台本のフックに組み込む
- 価格提示は必ず価値提案の後に行う
- 反論処理は最低5パターン用意する

---

## Loom MCP 設定（文字起こし取得に必要）

### 設定ファイルの場所

Loom MCPサーバーの認証情報（cookie）は以下のファイルで管理されている：

```
~/.claude.json
└── projects["/Users/deguchishouma/team-info"]
    └── mcpServers
        └── loom
            └── env.LOOM_COOKIE  ← ここのcookieが期限切れになる
```

### cookieの更新手順

1. ブラウザで [loom.com](https://www.loom.com) にログイン
2. 開発者ツール（F12）→「Application」→「Cookies」→ `loom.com`
3. `connect.sid` の値をコピー
4. 以下のPythonコマンドで更新：

```bash
python3 -c "
import json, pathlib
NEW_COOKIE = 'ここに新しいcookieの値を貼り付け'
p = pathlib.Path('/Users/deguchishouma/.claude.json')
d = json.loads(p.read_text())
d['projects']['/Users/deguchishouma/team-info']['mcpServers']['loom']['env']['LOOM_COOKIE'] = NEW_COOKIE
p.write_text(json.dumps(d, ensure_ascii=False, separators=(',', ':')))
print('Cookie updated')
"
```

5. Claude Codeを再起動してMCPサーバーを再接続

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
