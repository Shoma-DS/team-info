
export const VIRAL_ADULT_AFFILIATE_FONT_FAMILY = [
  '"Hiragino Maru Gothic ProN"',
  '"Hiragino Sans"',
  '"Yu Gothic"',
  '"Meiryo"',
  "sans-serif",
].join(", ");

// 後方互換のため残す。現在はローカルの日本語フォントへ寄せているため、
// モジュールロード時の外部フォント取得は行わない。
export const useViralAdultAffiliateFont = (): void => {};
