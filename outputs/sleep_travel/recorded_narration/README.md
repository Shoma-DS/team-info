# recorded_narration

睡眠導入動画で使う手動録音ナレーションの置き場です。

## 入れるファイル
- 推奨: `.wav` または `.mp3`
- 可能: `.m4a`
- 1動画につき、完成版の通しナレーションを1ファイル置く

## 命名例
- `2026-05-08_地政学_世界を動かす地理の読み方_recorded.wav`
- `2026-05-08_地政学_世界を動かす地理の読み方_recorded.mp3`

## 運用
- このフォルダは録音素材の保管場所です。
- Remotionで使う最終音声は、スキル手順に従って `Remotion/my-video/public/assets/channels/sleep_travel/audio.mp3` に配置します。

## 配置コマンド例
`.mp3` をそのまま使う場合:

```bash
cp "$TEAM_INFO_ROOT/outputs/sleep_travel/recorded_narration/[録音ファイル名].mp3" "$TEAM_INFO_ROOT/Remotion/my-video/public/assets/channels/sleep_travel/audio.mp3"
```

`.wav` や `.m4a` を `.mp3` に変換して使う場合:

```bash
ffmpeg -y -i "$TEAM_INFO_ROOT/outputs/sleep_travel/recorded_narration/[録音ファイル名].wav" -codec:a libmp3lame -b:a 192k "$TEAM_INFO_ROOT/Remotion/my-video/public/assets/channels/sleep_travel/audio.mp3"
```
