import { loadDefaultJapaneseParser } from "budoux";

const WHITESPACE_RE = /[\s\u3000]+/gu;
const DISPLAY_PUNCTUATION_RE = /[、。,.!?！？…：:；;・]/gu;
const BOUNDARY_CLASS = "[\\s\\u3000、。,.!?！？…：:；;「」『』（）()［］\\[\\]【】<>〈〉《》・/\\\\〜～—-]";
const FILLER_WORDS = [
  "えー",
  "ええと",
  "えっと",
  "えーと",
  "えーっと",
  "あの",
  "あのー",
  "まあ",
  "その",
  "そのー",
  "うーん",
];

const escapeRegExp = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const FILLER_RE = new RegExp(
  `(^|${BOUNDARY_CLASS})(?:${FILLER_WORDS.map(escapeRegExp).join("|")})(?=$|${BOUNDARY_CLASS})`,
  "gu",
);

const budouxParser = loadDefaultJapaneseParser();

const TOKEN_RE = new RegExp(
  "[\\s\\u3000]+|[A-Za-z0-9]+|[０-９]+|[一-龠々〆〤ぁ-んァ-ヶー]+|[、。,.!?！？…：:；;「」『』（）()\\[\\]【】<>〈〉《》・]|.",
  "gu",
);

type SegmentLike = { segment: string };
type SegmenterLike = {
  segment: (input: string) => Iterable<SegmentLike>;
};

export type NormalizeTextOptions = {
  stripFillers?: boolean;
  stripPunctuation?: boolean;
  collapseWhitespace?: boolean;
};

export type WrapTextOptions = NormalizeTextOptions & {
  maxCharsPerLine: number;
  preserveExistingLineBreaks?: boolean;
};

const stripFillersFromLine = (value: string) => {
  return value.replace(FILLER_RE, (_match, prefix: string) => prefix ?? "");
};

const normalizeLine = (value: string, options: NormalizeTextOptions = {}) => {
  const { stripFillers = false, stripPunctuation = false, collapseWhitespace = true } = options;
  let next = value.replace(/\r/g, "");

  if (stripFillers) {
    next = stripFillersFromLine(next);
  }

  if (stripPunctuation) {
    next = next.replace(DISPLAY_PUNCTUATION_RE, "");
  }

  if (collapseWhitespace) {
    next = next.replace(WHITESPACE_RE, " ");
  }

  return next.trim();
};

const splitToSegments = (text: string): string[] => {
  try {
    const parsed = budouxParser
      .parse(text)
      .map((segment) => segment.trim())
      .filter((segment) => segment.length > 0);

    if (parsed.length > 0) {
      return parsed;
    }
  } catch {
    // BudouX が想定外の入力で失敗した場合だけ、従来の分割へ落とす。
  }

  const segmenter = (Intl as unknown as { Segmenter?: new (
    locale: string | string[],
    options: { granularity: "word" },
  ) => SegmenterLike }).Segmenter;

  if (typeof segmenter === "function") {
    const instance = new segmenter("ja", { granularity: "word" });
    return Array.from(instance.segment(text), (part) => part.segment).filter((segment) => segment.length > 0);
  }

  return text.match(TOKEN_RE) ?? [];
};

const visibleLength = (value: string) => {
  return value.replace(WHITESPACE_RE, "").replace(DISPLAY_PUNCTUATION_RE, "").length;
};

const isWeakBoundaryToken = (token: string) => {
  return [
    "は",
    "が",
    "を",
    "に",
    "へ",
    "と",
    "で",
    "も",
    "の",
    "や",
    "か",
    "ね",
    "よ",
    "ぞ",
    "さ",
    "な",
    "だ",
    "です",
    "ます",
    "でした",
    "たい",
    "て",
    "でし",
    "から",
    "まで",
    "より",
    "だけ",
    "ほど",
    "くらい",
    "けど",
    "けれど",
    "ので",
    "のに",
    "しかし",
    "でも",
  ].includes(token);
};

const cleanDisplayLine = (value: string, options: NormalizeTextOptions = {}) => {
  return normalizeLine(value, options);
};

const wrapParagraph = (paragraph: string, options: WrapTextOptions): string[] => {
  const normalizedParagraph = normalizeLine(paragraph, {
    stripFillers: options.stripFillers,
    collapseWhitespace: true,
    stripPunctuation: false,
  });

  if (!normalizedParagraph) {
    return [];
  }

  const tokens = splitToSegments(normalizedParagraph).filter((token) => token.trim().length > 0);
  if (tokens.length === 0) {
    return [];
  }

  const targetChars = Math.max(1, options.maxCharsPerLine);
  const softLimit = Math.max(targetChars + 6, Math.ceil(targetChars * 1.5));
  const dp = new Array<number>(tokens.length + 1).fill(Number.POSITIVE_INFINITY);
  const nextBreak = new Array<number>(tokens.length + 1).fill(tokens.length);
  dp[tokens.length] = 0;

  for (let i = tokens.length - 1; i >= 0; i -= 1) {
    let width = 0;

    for (let j = i; j < tokens.length; j += 1) {
      width += visibleLength(tokens[j]);

      if (width === 0) {
        continue;
      }

      if (width > softLimit && j > i) {
        break;
      }

      const isLastLine = j === tokens.length - 1;
      const diff = targetChars - width;
      let penalty = diff * diff;

      if (width > targetChars) {
        penalty += (width - targetChars) * (width - targetChars) * 2;
      }

      if (!isLastLine && width < Math.max(4, Math.round(targetChars * 0.5))) {
        penalty += 24;
      }

      if (!isLastLine && isWeakBoundaryToken(tokens[j])) {
        penalty += 12;
      }

      if (j + 1 < tokens.length && isWeakBoundaryToken(tokens[j + 1])) {
        penalty += 8;
      }

      if (dp[j + 1] + penalty < dp[i]) {
        dp[i] = dp[j + 1] + penalty;
        nextBreak[i] = j + 1;
      }
    }
  }

  const lines: string[] = [];
  let index = 0;

  while (index < tokens.length) {
    const breakIndex = Math.max(index + 1, nextBreak[index]);
    const rawLine = tokens.slice(index, breakIndex).join("");
    const line = cleanDisplayLine(rawLine, {
      stripFillers: options.stripFillers,
      stripPunctuation: options.stripPunctuation,
    });

    if (line) {
      lines.push(line);
    }

    index = breakIndex;
  }

  return lines;
};

export const normalizeDisplayText = (text: string, options: NormalizeTextOptions = {}) => {
  const lines = text.replace(/\r/g, "").split(/\n+/);
  const normalizedLines = lines
    .map((line) => normalizeLine(line, options))
    .filter((line) => line.length > 0);

  return normalizedLines.join("\n");
};

export const flattenDisplayText = (text: string, options: NormalizeTextOptions = {}) => {
  return normalizeDisplayText(text, options).replace(/\n+/g, " ").replace(WHITESPACE_RE, " ").trim();
};

export const splitJapaneseSentences = (text: string) => {
  const flattened = flattenDisplayText(text, {
    stripFillers: true,
    stripPunctuation: false,
  });

  if (!flattened) {
    return [];
  }

  return flattened
    .split(/(?<=[。！？!?])\s*/u)
    .map((sentence) => sentence.trim())
    .filter((sentence) => sentence.length > 0);
};

export const splitDisplayLines = (text: string, options: WrapTextOptions) => {
  const source = options.preserveExistingLineBreaks === false
    ? [normalizeLine(text, { stripFillers: options.stripFillers, collapseWhitespace: true })]
    : normalizeDisplayText(text, {
        stripFillers: options.stripFillers,
        stripPunctuation: false,
      })
        .split(/\n+/)
        .filter((line) => line.length > 0);

  return source.flatMap((paragraph) => wrapParagraph(paragraph, options));
};

export const formatWrappedText = (text: string, options: WrapTextOptions) => {
  return splitDisplayLines(text, options).join("\n");
};

export const getVisibleTextLength = (text: string) => {
  return text.replace(WHITESPACE_RE, "").replace(DISPLAY_PUNCTUATION_RE, "").length;
};
