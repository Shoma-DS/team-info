# Draft Save Log

## Article

- Title: `AIに仕事を任せるために、僕がやっていること`
- Markdown: `article.md`
- Plain text: `article_plain.txt`
- Header: `assets/header/ai-agent-work-delegation-header-v2.png`
- Inline image manifest: `x-draft-assets.md`

## Completed After Review

- Replaced the old non-5:2 header with a new `2500x1000` 5:2 header.
- Added `header_prompt.md`.
- Retrieved and saved the Loom video details/transcript.
- Added `sources.md`.
- Updated the article header image reference.
- Regenerated `article_plain.txt` from `article.md`.
- Synced the completed article package to the personal output copy.

## Not Yet Completed

- Previous article public URL is still missing.

## X Draft Save Scope Used

The Vivaldi / Kimi WebBridge draft save used this scope:

- Send title: `AIに仕事を任せるために、僕がやっていること`
- Send body: `article_x_paste_with_placeholders.txt`
- Upload header: `assets/header/ai-agent-work-delegation-header-v2.jpg`
- Insert all non-header images at the Markdown image positions in `article.md`
- Stop at draft save only
- Do not click `Post`, `Publish`, `投稿する`, or `公開`

## Current Status

X Articles draft is saved in Vivaldi. Replace the previous article URL placeholder before publishing if the public URL is available.

## 2026-05-25 Attempt

- Kimi WebBridge health: OK (`running: true`, `extension_connected: true`)
- Opened: `https://x.com/compose/articles`
- Result: redirected to X login screen (`https://x.com/i/jf/onboarding/web?redirect_after_login=%2Fcompose%2Farticles&mode=login`)
- Action needed: user must log in to X in the opened browser tab. The agent does not handle passwords or login credentials.

## 2026-05-25 Vivaldi Draft Save

- Browser: Vivaldi via Kimi WebBridge session `x-article-draft`
- Draft URL: `https://x.com/compose/articles/edit/2058900550494683136`
- Title saved: `AIに仕事を任せるために、僕がやっていること`
- Header saved: `assets/header/ai-agent-work-delegation-header-v2.jpg`
- Body source for X paste: `article_x_paste_with_placeholders.txt`
- Inline body images inserted: 15
- Preview check: OK
  - Intro, X, ジモティー, LP, 法人研修, まとめ, and final previous-article lead all visible
  - Preview image count: 16 including the header
  - `Provide a caption` / `Edit media` UI text was not present in preview content
- Publish status: not published. `Publish` / `Post` was not clicked.
- Remaining item: previous article URL placeholder remains as `※前回記事の公開URLを入れる場所です。`

## 2026-05-25 Code Block / Line Break Fix

- Regenerated `article_plain.txt` so file trees keep Markdown code fences and backtick tree markers.
- Regenerated `article_x_paste_with_placeholders.txt` from `article.md` with:
  - ` ```text ` / ` ``` ` fences around file structures, flow diagrams, and copy-paste prompts
  - preserved ASCII tree line breaks
  - heading blocks kept as X headings
  - body image placeholders kept in the same order
- Updated the Vivaldi X draft.
- Preview check: OK
  - ` ```text` fence is visible before `Desktop/`
  - tree line `` `-- AI法人研修/ `` is visible
  - Intro, X, ジモティー, LP, 法人研修, まとめ, and final previous-article lead are visible
  - Preview image count: 16 including the header
- Note: X Articles accepted internal `code-block` temporarily, but preview/save converted it back to normal text. The saved draft therefore uses visible Markdown code fences so readers still see the file structures as code blocks.
