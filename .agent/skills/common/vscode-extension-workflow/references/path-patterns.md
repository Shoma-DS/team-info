# VS Code 系拡張の配置先パターン

## まず見る場所

### VS Code
```bash
find "$HOME/.vscode/extensions" -maxdepth 1 -type d
```

### Cursor
```bash
find "$HOME/.cursor/extensions" -maxdepth 1 -type d
```

### antigravity
```bash
find "$HOME/.antigravity/extensions" -maxdepth 1 -type d
```

### VSCodium
```bash
find "$HOME/.vscode-oss/extensions" -maxdepth 1 -type d
```

## 拡張のフォルダ名
- 基本形:
  - `publisher.name-version`
- 変形:
  - `publisher.name-version-universal`
  - `publisher.name-version-platform`

## 対象拡張の絞り方
`package.json` から `publisher` `name` `version` を読み、次のように探す。

```bash
find "$HOME/.antigravity/extensions" -maxdepth 1 -type d | rg "/<publisher>\\.<name>-<version>(-.*)?$"
```

同じ考え方で `~/.cursor/extensions` や `~/.vscode/extensions` も探す。

## ソース repo の探し方

### workspace 直下を先に探す
```bash
find "[workspace root]" -maxdepth 4 -name package.json
```

### ホーム配下の候補を探す
```bash
find "$HOME" -maxdepth 4 -name package.json 2>/dev/null
```

### 拡張らしい repo か確認する
- `package.json` に次があるかを見る
  - `publisher`
  - `engines.vscode`
  - `contributes.commands` または `contributes.customEditors`

## 既存拡張を更新する最短手順
1. ソース repo でビルド
2. 使っているエディタの既存拡張フォルダを特定
3. `dist/` と `package.json` をそのフォルダへ反映
4. エディタで `Developer: Reload Window`

## symlink で置く最短手順
```bash
ln -sfn "[source repo absolute path]" "$HOME/.cursor/extensions/<publisher>.<name>-<version>"
```

`Cursor` の部分は、使うエディタに合わせて読み替える。

## 迷いやすい点
- `antigravity` では `-universal` 付きの既存フォルダが本体になっていることがある
- CLI で入れた拡張と、フォルダへ直接置いた拡張が混ざることがある
- workspace フォルダと実際のソース repo は別のことがある
- `.code-workspace` が外部フォルダを向いていることがある

