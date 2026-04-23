import { loadFont } from "@remotion/google-fonts/NotoSansJP";

// フォントのロードを実行
const { fontFamily } = loadFont();

export const VIRAL_ADULT_AFFILIATE_FONT_FAMILY = [
  `"${fontFamily}"`,
  '"Hiragino Maru Gothic ProN"',
  '"Hiragino Sans"',
  '"Yu Gothic"',
  '"Meiryo"',
  "sans-serif",
].join(", ");

/** 後方互換のため残す。 */
export const useViralAdultAffiliateFont = (): void => {
  // すでにモジュールロード時に読み込まれているため何もしない
};
