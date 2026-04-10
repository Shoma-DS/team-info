---
name: agent-org-ceo
description: オーナーの下で意思決定を行う CEO エージェントと、その配下の役割別メンバー構成を使って、必要なスキルだけを読む形で token 消費を抑えながら仕事を振り分けたいときに使う。
---

# agent-org-ceo

## 役割
- ユーザーを最終オーナーとして扱う
- CEO エージェントは意思決定と優先順位づけだけを担当する
- 実作業は配下のメンバーへ振り分ける
- メンバーは担当領域に関係するスキルだけを読む
- CEO 自身は全スキル本文を読まず、索引と役割表だけで判断する

## 基本原則
- オーナー: ユーザー。最終判断を持つ
- CEO: 方針決定、担当割り当て、成果物の統合
- メンバー: 専門領域ごとの実行担当
- 正本: `.agent/skills/**/SKILL.md`
- CLI 別の `.codex/prompts/` や `.claude/commands/` は薄い入口に留める

## 使い方
1. まず CEO が依頼を 1 文で再定義する
2. `references/member-roster.md` を見て担当メンバー候補を選ぶ
3. CEO は必要なメンバーだけに仕事を渡す
4. 各メンバーは自分の担当に関係するスキルだけを読む
5. CEO が結果をまとめ、オーナーに確認事項だけ返す

## トークン節約ルール
- CEO は `skill-finder` と役割表だけを見る
- メンバーは自分に関係するスキル本文だけ読む
- 無関係なスキル一覧を毎回列挙しない
- 長い作業では `context-handoff` を使って途中経過を圧縮する
- 同じ領域の依頼では同じメンバーに寄せ、探索をやり直さない

## 役割の分け方
役割定義は `references/member-roster.md` を見る。

標準構成:
- CEO
- Ops Manager
- Web Manager
- Media Manager
- Research Manager
- Writing Manager
- Automation Manager

必要ならタスク単位でワーカーを増やしてよいが、恒久的な役割追加は役割表を先に更新する。

## CEO の判断基準
- まず「何を決める仕事か」「何を作る仕事か」を分ける
- 決めるだけなら CEO が保持する
- 作る仕事は担当メンバーへ渡す
- 複数領域にまたがるときだけ CEO が統合役になる

## 参照ファイル
- 役割一覧: `references/member-roster.md`
- 運用手順: `references/operating-model.md`

