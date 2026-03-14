import {
  fontFamily as adultAffiliateGoogleFontFamily,
  getInfo as getAdultAffiliateFontInfo,
} from "@remotion/google-fonts/MochiyPopOne";
import { useEffect } from "react";

export const VIRAL_ADULT_AFFILIATE_FONT_FAMILY = [
  `"${adultAffiliateGoogleFontFamily}"`,
  '"Hiragino Maru Gothic ProN"',
  '"Hiragino Sans"',
  '"Yu Gothic"',
  '"Meiryo"',
  "sans-serif",
].join(", ");

const loadFontStylesheet = (href: string): void => {
  if (typeof document === "undefined") {
    return;
  }

  const existing = document.head.querySelector<HTMLLinkElement>(
    `link[data-remotion-font-href="${href}"]`,
  );
  if (existing) {
    return;
  }

  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = href;
  link.setAttribute("data-remotion-font-href", href);
  document.head.appendChild(link);
};

const useFontStylesheet = (href: string): void => {
  useEffect(() => {
    loadFontStylesheet(href);
  }, [href]);
};

export const useViralAdultAffiliateFont = (): void => {
  useFontStylesheet(getAdultAffiliateFontInfo().url);
};
