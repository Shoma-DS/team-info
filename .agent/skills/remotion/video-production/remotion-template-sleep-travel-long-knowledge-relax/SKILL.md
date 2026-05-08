---
name: remotion-template-sleep-travel-long-knowledge-relax
description: sleep_travelチャンネルのlong_knowledge_relaxテンプレート専用編集スキル。長尺睡眠導入の構成に沿ってRemotionを編集する。
---

# sleep_travel long_knowledge_relax 専用スキル

## このスキルの役割
- `sleep_travel` チャンネルの長尺睡眠導入動画を、低刺激・音声主役・ゆるやかな知識提供の方向へ編集する。
- 40-120分の長尺でも破綻しないよう、素材選定、タイムライン設計、字幕、BGMループ、レンダリング案内まで一貫して管理する。
- 視聴者が眠りに入りやすいことを最優先し、目を引く演出よりも「違和感の少なさ」「急に起こさないこと」「耳疲れしないこと」を優先する。

## 絶対パスルール（必須）
- ユーザーにコマンドを渡すときは、固定の `/Users/...` ではなく `TEAM_INFO_ROOT` から絶対パスを組み立てる。
- 例外なく、レンダリング・lint・rclone の案内は `"$TEAM_INFO_ROOT/..."` 形式にする。

## 入力前提
- チャンネル: `sleep_travel`
- テンプレート: `long_knowledge_relax`
- 親スキル `remotion-video-production` で選択済みであること。

## 最初に読むもの（必須）
- `Remotion/my-video/public/assets/channels/sleep_travel/channel_info.md`
- `Remotion/my-video/public/assets/channels/sleep_travel/templates/long_knowledge_relax.md`
- 既存実装を更新する場合は、対象コンポーネントと `Remotion/my-video/src/Root.tsx`

## 参照ファイル
- `Remotion/my-video/public/assets/channels/sleep_travel/channel_info.md`
- `Remotion/my-video/public/assets/channels/sleep_travel/templates/long_knowledge_relax.md`
- `Remotion/my-video/src/`

## 素材参照先
- 台本: `Remotion/scripts/voice_scripts/`
- AI生成音声: `outputs/sleep_travel/audio/`
- 手動録音ナレーション: `outputs/sleep_travel/recorded_narration/`
- Remotion用の最終ナレーション配置先: `Remotion/my-video/public/assets/channels/sleep_travel/audio.mp3`
- 背景画像: `Remotion/my-video/public/assets/channels/sleep_travel/backgrounds/`
- BGM: `Remotion/my-video/public/assets/channels/sleep_travel/bgm/`
- エフェクトテンプレート: `Remotion/my-video/public/assets/channels/sleep_travel/effects/templates/`

## 睡眠導入品質ルール（必須）
- 画面変化は遅く、予測可能にする。急なカット、強いズーム、短周期の点滅、派手なパーティクルは禁止。
- 背景は暗めで低コントラストに寄せる。ただし字幕が読めないほど暗くしない。
- 章切り替えはフェード、ゆるいパン/ズーム、短い無音寄りの余白でつなぎ、視聴者を覚醒させる演出を入れない。
- 音声ナレーションを主役にし、BGMは常に控えめにする。BGMや効果音が言葉の輪郭を邪魔する場合は音量を下げる。
- 効果音を追加する場合は、眠りを妨げない環境音・柔らかい音に限定する。通知音、金属音、強い低音、急な立ち上がり音は禁止。
- 字幕は読ませるためではなく、聞き逃し補助として置く。長文・頻繁な切り替え・画面中央の大きな主張を避ける。
- CTAは冒頭1回、終盤1回まで。短く柔らかく、睡眠導入の流れを切らない文にする。

## 長尺構成ルール
- 基本構成は、オープニング 60-120秒、本編 3-4章、エンディング 30-60秒。
- 各章は 10-15分目安だが、音声尺を優先して自然に配分する。
- 章タイトルは短く、落ち着いた表示にする。過度な強調、派手な装飾、強い色差は使わない。
- エンディングは余韻を残してフェードアウトし、急に終了しない。

## 素材選択ルール（必須）
- 素材選択時は、対象フォルダを走査して「実在する候補ファイル」を番号付きで提示する。
- 「音声素材 / 台本 / 背景画像 / BGM / エフェクト設定」の5項目を、必ず1つずつ順番に確定する。
- まとめて推測して選ばない。ユーザーが明示した素材がある場合も、実在確認してから確定する。
- 拡張子フィルタ:
- 音声素材: `.mp3` `.wav` `.m4a`
- 台本: `.md` `.txt`
- 背景画像: `.png` `.jpg` `.jpeg`
- BGM: `.mp3`
- 候補0件の項目があれば、先に不足を報告して補充を依頼する。
- 候補提示時は、可能ならファイル名に加えて相対パス、用途メモ、尺やサイズなど確認できた情報を添える。
- カスタムエフェクトを新規作成した場合は、都度「日本語名」を付けてテンプレートとして保存する。
- エフェクトテンプレート保存先: `Remotion/my-video/public/assets/channels/sleep_travel/effects/templates/`
- 保存時は、次回再利用できるよう目的・適用シーン・主要パラメータを残す。

## ナレーション音声の運用ルール（必須）
- 睡眠導入の長尺では、ユーザーが録音したナレーションを優先する。
- VOICEVOXなどのAI生成音声は、ユーザーが明示した場合、または手動録音が未提供の場合の代替として扱う。
- 手動録音ファイルの投入先は `outputs/sleep_travel/recorded_narration/` とする。
- Remotionで実際に読む最終音声は `Remotion/my-video/public/assets/channels/sleep_travel/audio.mp3` に統一する。
- 録音ファイルを選択したら、レンダリング前に必要に応じて `.mp3` へ変換し、上記の最終配置先へ置く。
- 元の録音ファイルは削除しない。`recorded_narration/` を原本保管場所として残す。
- 既存の `audio.mp3` を上書きする場合は、ユーザーに「選択した録音ナレーションをRemotion用の audio.mp3 として配置します」と明示してから行う。
- 音声ファイルが複数パートに分かれている場合は、勝手に連結しない。連結順、無音間隔、完成版ファイル名をユーザーに確認する。

## 手動録音ナレーションの準備手順
1. ユーザーに録音済みファイルを `outputs/sleep_travel/recorded_narration/` へ入れてもらう。
2. 候補を走査し、`.mp3` `.wav` `.m4a` の実在ファイルを番号付きで提示する。
3. 選択された録音ファイルについて、可能なら尺、形式、ファイルサイズを確認する。
4. 台本ファイルと録音内容が一致しているか確認する。一致しない可能性がある場合は、字幕ズレのリスクとして報告する。
5. `.wav` や `.m4a` の場合は、レンダリング互換性を優先して `.mp3` に変換する。変換後の配置先は `Remotion/my-video/public/assets/channels/sleep_travel/audio.mp3`。
6. `.mp3` の場合も、Remotion用の最終ナレーションとして `Remotion/my-video/public/assets/channels/sleep_travel/audio.mp3` にコピーして使う。
7. 音量が小さい、ノイズが多い、冒頭や末尾に不要な無音がある場合は、編集前にユーザーへ確認する。勝手に強いノイズ処理や大幅なカットをしない。

## 録音ナレーション配置コマンド例
- `.mp3` をそのまま配置する場合:
  ```bash
  cp "$TEAM_INFO_ROOT/outputs/sleep_travel/recorded_narration/[録音ファイル名].mp3" "$TEAM_INFO_ROOT/Remotion/my-video/public/assets/channels/sleep_travel/audio.mp3"
  ```
- `.wav` または `.m4a` を `.mp3` に変換して配置する場合:
  ```bash
  ffmpeg -y -i "$TEAM_INFO_ROOT/outputs/sleep_travel/recorded_narration/[録音ファイル名].wav" -codec:a libmp3lame -b:a 192k "$TEAM_INFO_ROOT/Remotion/my-video/public/assets/channels/sleep_travel/audio.mp3"
  ```
- 変換前に尺を確認する場合:
  ```bash
  ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$TEAM_INFO_ROOT/outputs/sleep_travel/recorded_narration/[録音ファイル名].wav"
  ```
- 既存の `audio.mp3` を上書きするコマンドは、ユーザーが録音素材を選択した後にだけ実行する。

## 録音品質の推奨
- 形式は `.wav`、48kHz、24bit または 16bit を推奨する。難しければ `.mp3` でもよい。
- 1本の完成ナレーションとして書き出す。章ごとの分割しかない場合は、連結方針を確認してから扱う。
- 冒頭に0.5-1.0秒、末尾に1.0-3.0秒程度の自然な余白を残す。
- ノイズ、リップノイズ、衣擦れ、机の振動、息が強く当たる音が目立つ場合は、動画化前に録り直しや軽い整音を検討する。
- 音量は大きすぎず、BGMを重ねても言葉が聞き取れる程度にそろえる。

## 素材選定の判断基準
- 音声素材: 手動録音ナレーションを優先する。ノイズが少なく、音量差が小さく、長尺で聞き疲れしにくいものを選ぶ。
- 台本: 音声化済みテキストと一致しているものを選ぶ。差分がある場合は、字幕ズレのリスクとして報告する。
- 背景画像: 1920x1080以上、暗め、低刺激、細部がうるさくないものを優先する。
- BGM: ループしても継ぎ目が目立ちにくく、ナレーション帯域を邪魔しないものを優先する。
- エフェクト: 低刺激（軽いズーム、微弱なパン、長めのフェード）を基本にする。

## Remotion実装ルール（必須）
- 背景画像差し替え、補助画像、効果音、字幕など、同じ種類で区間が重ならない素材は、種類ごとに `<Sequence>` を1本へ統合する。
- 同種素材を `map(...<Sequence>...)` で量産せず、タイムライン配列から現在フレームに対応する素材を選んで描画・再生する。
- BGM だけは例外として `<Loop>` 1つで管理してよいが、`<Sequence>` を分割して疑似ループを組まない。
- クロスフェードなど同種素材の重なりが本当に必要な場面を除き、同種レイヤーを複数本に分けない。
- 生成・更新する **すべての `<Sequence>` に `name` を付ける。** 例: `背景画像`, `補助画像`, `字幕`, `BGM`, `音声 ナレーション`。
- 字幕の折り返しは `Remotion/my-video/src/textLayout.ts` の BudouX ベース共通ヘルパーに寄せる。SleepTravelLong 側で独自の改行ロジックを増やさない。

## 実装品質ルール
- 動画尺は音声素材を基準に決める。固定尺に音声を無理に合わせない。
- BGMは `<Loop durationInFrames={bgmSegmentFrames} times={loopCount}>` を1つ使い、`loopCount = Math.ceil(durationInFrames / bgmSegmentFrames) + 1` で動画末尾まで確実に届かせる。
- `<Loop>` の `times` は必ず指定する。省略すると音声がレンダリングされない場合がある。
- BGMの先頭と末尾には必要に応じてフェードを入れ、ループ境界の違和感を抑える。
- 字幕タイミングは音声進行に追従させる。完全な文字起こしタイムコードがない場合は、台本の文量比で暫定配分し、ズレの可能性を報告する。
- オーディオスペクトラムは白線1系統のシンプル表示にし、画面下部で控えめに動かす。
- 既存の共通ヘルパーがある場合は優先して使う。長尺専用コンポーネント内に重複ロジックを増やさない。

## 編集フロー
1. テンプレート定義を読み、シーン構成と実装仕様を確認する。
2. チャンネル情報を読み、禁止事項・トーン・CTA方針を確認する。
3. 素材を必ず1つずつ確認して確定する。
- 音声素材（手動録音 `outputs/sleep_travel/recorded_narration/` を優先。必要時のみAI生成音声 `outputs/sleep_travel/audio/`）
- 台本
- 背景画像
- BGM
- エフェクト設定
4. 確定した音声素材を、必要に応じて `Remotion/my-video/public/assets/channels/sleep_travel/audio.mp3` へコピーまたは変換する。
5. 音声尺と台本文量から、動画尺、章配分、字幕配分の方針を決める。
6. エフェクト設定が既存テンプレートにない場合は、適切な日本語名で新規テンプレートを保存する。
7. `Remotion/my-video/src/` に長尺向けコンポーネントを実装または更新する。
8. 次を必須で満たす。
- 背景画像をベース表示
- 音声主役、BGMは控えめ音量
- BGMをシームレスループ（`<Loop durationInFrames={bgmSegmentFrames} times={loopCount}>` を1つ使う）
  - `loopCount = Math.ceil(durationInFrames / bgmSegmentFrames) + 1` で必ず動画の最後までカバー
  - **`times` を省略すると音声がレンダリングされない**（Remotion 仕様）ので必ず指定する
- BGMループは必ず `<Sequence>` を複数生成するパターンではなく `<Loop>` 1つに統一する
- 背景画像や字幕など非重複な同種レイヤーは `<Sequence>` 1本で管理する
- 各 `<Sequence>` には役割が一目で分かる `name` を付ける
- 字幕を音声進行に合わせる
- 字幕の自然な改行は BudouX ベースの共通ヘルパーで整形する
- 字幕をフェードイン/フェードアウト
- 白線のシンプルなオーディオスペクトラム表示
9. 必要なら `Remotion/my-video/src/Root.tsx` にCompositionを追加する。
10. `npm --prefix "$TEAM_INFO_ROOT/Remotion/my-video" run lint` を実行する。
11. レンダリングは勝手に実行しない。必要な場合はユーザー承認を取るか、コピペ可能な `cd "$TEAM_INFO_ROOT/Remotion/my-video" && npx remotion render ... --output="$TEAM_INFO_ROOT/outputs/sleep_travel/renders/..."` コマンドを提示する。
- レンダリング前の確認文言は必ず `出力しますか？書き出しますか？` を使う。
- 過去ターンで承認があっても、レンダリング直前に毎回確認する。
- レンダリング出力先は必ず `outputs/sleep_travel/renders/` を使う。
- レンダリング完了後に Step 12 のコマンドも提示する。
12. レンダリング完了後、以下のコマンドで Google Drive にコピーする（コマンドをユーザーに提示するだけ・自分では実行しない）：
   ```bash
   rclone copy "$TEAM_INFO_ROOT/outputs/sleep_travel/renders/[ファイル名].mp4" "gdrive:1QKaUP9fvA46mINkpSR1b2wqrIBE6By0t/outputs/寝ながらトラベル/" --progress
   ```
   - rclone が未設定の場合は `.agent/skills/common/git-workflow/gdrive-copy/SKILL.md` の初回セットアップ手順を案内する。
13. 実施内容、編集ファイル、使用した録音ナレーション、lint結果、未レンダリングの場合はレンダリング未実行であることを報告する。

## 完了前チェックリスト
- [ ] `channel_info.md` と `long_knowledge_relax.md` を読んだ
- [ ] 手動録音ナレーション候補を `outputs/sleep_travel/recorded_narration/` から確認した
- [ ] 音声素材 / 台本 / 背景画像 / BGM / エフェクト設定を実在ファイルから確定した
- [ ] 確定した音声を `Remotion/my-video/public/assets/channels/sleep_travel/audio.mp3` に配置した
- [ ] 音声尺を基準に動画尺を決めた
- [ ] 背景は低刺激で、急なカットや強い点滅がない
- [ ] BGMは `<Loop>` 1つで最後まで届く
- [ ] BGMの `times` を明示した
- [ ] 非重複の同種レイヤーを `<Sequence>` 1本に統合した
- [ ] すべての `<Sequence>` に `name` を付けた
- [ ] 字幕改行は `textLayout.ts` の BudouX ベース共通ヘルパーを使った
- [ ] 字幕はフェードし、音声進行に追従している
- [ ] 白線オーディオスペクトラムが控えめに表示される
- [ ] CTAが過剰でない
- [ ] lintを実行し、結果を報告した
- [ ] レンダリングを勝手に実行していない
