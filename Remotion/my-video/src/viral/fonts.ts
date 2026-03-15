import {
  fontFamily as adultAffiliateGoogleFontFamily,
  loadFont,
} from "@remotion/google-fonts/MochiyPopOne";

// モジュールロード時に呼ぶことで delayRender が内部で発行され、
// remotion still / render ともにフォント読み込みを待ってからレンダリングする
loadFont();

export const VIRAL_ADULT_AFFILIATE_FONT_FAMILY = [
  `"${adultAffiliateGoogleFontFamily}"`,
  '"Hiragino Maru Gothic ProN"',
  '"Hiragino Sans"',
  '"Yu Gothic"',
  '"Meiryo"',
  "sans-serif",
].join(", ");

/** @deprecated フォントはモジュールロード時に自動で読み込まれるため不要。後方互換のため残す */
export const useViralAdultAffiliateFont = (): void => {};
