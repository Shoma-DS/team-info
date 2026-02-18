import {
	AbsoluteFill,
	Audio,
	Easing,
	Img,
	Sequence,
	continueRender,
	delayRender,
	interpolate,
	spring,
	staticFile,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import { useMemo, useState, useEffect, type CSSProperties } from 'react';
import { getAudioData, visualizeAudioWaveform } from '@remotion/media-utils';

// ── Fonts ────────────────────────────────────────────────────

const yosugaraFontFace = new FontFace(
	'Yosugara',
	`url(${staticFile('assets/fonts/yosugaraver1_2.ttf')})`,
);
yosugaraFontFace.load().then((f) => document.fonts.add(f)).catch(() => { });
const yosugaraFamily = '"Yosugara", cursive';

// ── Song metadata (manually set per cover) ──────────────────
const SONG_TITLE = 'Tomorrow never knows';
const SONG_ARTIST = 'Mr.Children';

// ── Typography ──────────────────────────────────────────────

const lyricsFont: CSSProperties = {
	fontFamily: yosugaraFamily,
	letterSpacing: '0.04em',
	textAlign: 'center',
};

// ── Lyric Animation Data Types ──────────────────────────────

type WordTimestamp = {
	word: string;
	start: number; // seconds relative to line start
	end: number;
};

type LyricAnimationEntry = {
	time: number;
	duration: number;
	text: string;
	label: string;
	emotion: string;
	words?: WordTimestamp[]; // word-level timestamps for karaoke mode
	animation: {
		in: string;
		out: string;
		props: {
			inDurationFrames: number;
			outDurationFrames: number;
		};
	};
};

const HIRAGANA_FALLBACK_MAP: Record<string, string> = {
	// Phrase-level fallbacks
	'面影': 'おもかげ',
	'無邪気': 'むじゃき',
	'孤独': 'こどく',
	'駆け抜ける': 'かけぬける',
	'駆け抜けるけれど': 'かけぬけるけれど',
	'眺めていた': 'ながめていた',
	'すれ違う': 'すれちがう',
	'伸ばそう': 'のばそう',
	'遥かなる': 'はるかなる',
	'避けて': 'さけて',
	'遅れても': 'おくれても',
	'哀しさも': 'かなしさも',
	'僕はゆくのさ': 'ぼくはゆくのさ',
	'僕らは': 'ぼくらは',
	'闇の': 'やみの',
	'為に': 'ために',
	// Character-level fallbacks
	'僕': 'ぼく',
	'闇': 'やみ',
	'伸': 'のば',
	'哀': 'かな',
	'孤': 'こ',
	'影': 'かげ',
	'抜': 'ぬ',
	'為': 'ため',
	'眺': 'なが',
	'遅': 'おく',
	'違': 'ちが',
	'遥': 'はる',
	'避': 'さ',
	'邪': 'じゃ',
};

const isKanji = (char: string): boolean => /[\p{Script=Han}]/u.test(char);
const hasYosugaraGlyph = (char: string, supportedCodepoints: Set<number> | null): boolean => {
	if (!isKanji(char)) return true;
	if (!supportedCodepoints) return true;
	return supportedCodepoints.has(char.codePointAt(0) ?? -1);
};

const needsHiraganaFallback = (
	text: string,
	supportedCodepoints: Set<number> | null
): boolean => {
	for (const ch of [...text]) {
		if (isKanji(ch) && !hasYosugaraGlyph(ch, supportedCodepoints)) return true;
	}
	return false;
};

const toHiraganaFallback = (
	text: string,
	supportedCodepoints: Set<number> | null
): string => {
	if (!supportedCodepoints) return text;
	let out = text;
	const missing = new Set(
		[...text].filter((ch) => isKanji(ch) && !hasYosugaraGlyph(ch, supportedCodepoints))
	);
	if (missing.size === 0) return text;

	const keys = Object.keys(HIRAGANA_FALLBACK_MAP)
		.sort((a, b) => b.length - a.length)
		.filter((key) => [...key].some((ch) => missing.has(ch)));
	for (const key of keys) {
		out = out.split(key).join(HIRAGANA_FALLBACK_MAP[key]);
	}
	return out;
};

const semanticSplitChars = new Set([
	' ',
	'　',
	'、',
	'。',
	'・',
	',',
	'，',
	'!',
	'！',
	'?',
	'？',
	'…',
	'―',
	'-',
	'〜',
]);

const particleChars = new Set(['は', 'が', 'を', 'に', 'へ', 'と', 'で', 'も', 'の', 'や', 'か']);

const visibleLength = (value: string): number => value.replace(/[\s\u3000]+/g, '').length;

const splitLyricIntoLines = (text: string): string[] => {
	const source = text.trim();
	if (visibleLength(source) <= 18) {
		return [source];
	}

	const chars = [...source];
	if (chars.length < 8) {
		return [source];
	}

	const min = 3;
	const max = chars.length - 3;
	const center = chars.length / 2;
	let bestIndex = -1;
	let bestScore = Number.POSITIVE_INFINITY;

	for (let i = min; i <= max; i++) {
		const prev = chars[i - 1];
		const next = chars[i];
		let score = Math.abs(i - center) * 2;

		if (prev === ' ' || prev === '　') score -= 7;
		if (semanticSplitChars.has(prev)) score -= 4;
		if (particleChars.has(prev)) score -= 2;
		if (particleChars.has(next)) score += 1.5;

		if (score < bestScore) {
			bestScore = score;
			bestIndex = i;
		}
	}

	if (bestIndex <= 0) {
		return [source];
	}

	const line1 = chars.slice(0, bestIndex).join('').trimEnd();
	const line2 = chars.slice(bestIndex).join('').trimStart();
	if (!line1 || !line2) {
		return [source];
	}
	return [line1, line2];
};

const splitWordsIntoLines = (words: WordTimestamp[], lines: string[]): WordTimestamp[][] => {
	if (lines.length < 2 || words.length < 2) {
		return [words];
	}

	const target = visibleLength(lines[0]);
	let cumulative = 0;
	let bestBoundary = -1;
	let bestScore = Number.POSITIVE_INFINITY;

	for (let i = 1; i < words.length; i++) {
		cumulative += visibleLength(words[i - 1].word);
		let score = Math.abs(cumulative - target) * 2;
		const prev = words[i - 1].word;
		if (prev.endsWith(' ') || prev.endsWith('　')) score -= 3;
		if (prev.endsWith(',') || prev.endsWith('、') || prev.endsWith('・')) score -= 2;

		if (score < bestScore) {
			bestScore = score;
			bestBoundary = i;
		}
	}

	if (bestBoundary <= 0 || bestBoundary >= words.length) {
		return [words];
	}

	return [words.slice(0, bestBoundary), words.slice(bestBoundary)];
};

const KARAOKE_PROGRESS_SPEED = 1.1;

// ── Lyric Line Component ────────────────────────────────────

const LyricLine: React.FC<{
	text: string;
	animationIn: string;
	animationOut: string;
	inDuration: number;
	outDuration: number;
	label: string;
	words?: WordTimestamp[];
	lineFrame?: number;
	lineDurationInFrames?: number;
	supportedCodepoints?: Set<number> | null;
}> = ({
	text,
	animationIn,
	animationOut,
	inDuration,
	outDuration,
	label,
	words,
	lineFrame,
	lineDurationInFrames,
	supportedCodepoints = null,
}) => {
	const currentFrame = useCurrentFrame();
	const { fps, durationInFrames: compDurationInFrames } = useVideoConfig();
	const frame = lineFrame ?? currentFrame;
	const durationInFrames = lineDurationInFrames ?? compDurationInFrames;
	const useHiraganaFallback = useMemo(
		() => needsHiraganaFallback(text, supportedCodepoints),
		[text, supportedCodepoints]
	);
	const displayText = useMemo(
		() => (useHiraganaFallback ? toHiraganaFallback(text, supportedCodepoints) : text),
		[text, useHiraganaFallback, supportedCodepoints]
	);
	const displayWords = useMemo(() => {
		if (!words || words.length === 0) return [];
		if (!useHiraganaFallback) return words;
		return words.map((w) => ({
			...w,
			word: toHiraganaFallback(w.word, supportedCodepoints),
		}));
	}, [words, useHiraganaFallback, supportedCodepoints]);
	const lines = useMemo(() => splitLyricIntoLines(displayText), [displayText]);
	const karaokeWordLines = useMemo(() => {
		if (displayWords.length === 0) return [];
		return splitWordsIntoLines(displayWords, lines);
	}, [displayWords, lines]);
	const charsByLine = useMemo(() => {
		let charIndex = 0;
		return lines.map((line) =>
			[...line].map((char) => ({ char, index: charIndex++ }))
		);
	}, [lines]);

	const outStart = durationInFrames - outDuration;

	// ── In animation progress ──
	const inProgress = interpolate(frame, [0, inDuration], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
		easing: Easing.out(Easing.cubic),
	});

	// ── Out animation progress ──
	const outProgress = outDuration > 0
		? interpolate(frame, [outStart, durationInFrames], [0, 1], {
			extrapolateLeft: 'clamp',
			extrapolateRight: 'clamp',
			easing: Easing.in(Easing.cubic),
		})
			: 0;

	// ── Cross dissolve (always applied to text appearance) ──
	const crossDissolveIn = interpolate(frame, [0, Math.max(1, inDuration)], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
		easing: Easing.out(Easing.cubic),
	});
	const crossDissolveOut = outDuration > 0
		? interpolate(frame, [Math.max(0, durationInFrames - outDuration), durationInFrames], [1, 0], {
			extrapolateLeft: 'clamp',
			extrapolateRight: 'clamp',
			easing: Easing.in(Easing.cubic),
		})
		: 1;
	const crossDissolveOpacity = crossDissolveIn * crossDissolveOut;

	// ── Compute In styles ──
	const computeInStyle = (): CSSProperties => {
		switch (animationIn) {
			case 'SlideInLeft':
				return { transform: `translateX(${(1 - inProgress) * -100}%)` };
			case 'SlideInRight':
				return { transform: `translateX(${(1 - inProgress) * 100}%)` };
			case 'SlideInTop':
				return { transform: `translateY(${(1 - inProgress) * -80}px)` };
			case 'SlideInBottom':
				return { transform: `translateY(${(1 - inProgress) * 80}px)` };
			case 'FadeInSlow':
				return {
					opacity: interpolate(frame, [0, Math.max(inDuration, 20)], [0, 1], {
						extrapolateLeft: 'clamp',
						extrapolateRight: 'clamp',
					}),
				};
			case 'FadeInFast':
				return {
					opacity: interpolate(frame, [0, Math.min(inDuration, 8)], [0, 1], {
						extrapolateLeft: 'clamp',
						extrapolateRight: 'clamp',
					}),
				};
			case 'StaggeredFadeIn':
				// Handled per-character below
				return {};
			case 'PopIn': {
				const s = spring({ fps, frame, config: { damping: 8, mass: 0.6, stiffness: 180 } });
				return { transform: `scale(${s})` };
			}
			case 'Typewriter':
				// Handled per-character below
				return {};
			case 'ScaleUp':
				return { transform: `scale(${0.5 + inProgress * 0.5})` };
			case 'BlurIn':
				return {
					filter: `blur(${(1 - inProgress) * 10}px)`,
					opacity: inProgress,
				};
			case 'ZoomIn':
				return { transform: `scale(${inProgress})` };
			default:
				return { opacity: inProgress };
		}
	};

	// ── Compute Out styles ──
	const computeOutStyle = (): CSSProperties => {
		if (outDuration <= 0) return {}; // CutOut: handled by Sequence duration

		switch (animationOut) {
			case 'BlurOut':
				return {
					filter: `blur(${outProgress * 10}px)`,
					opacity: 1 - outProgress,
				};
			case 'FadeOut':
				return { opacity: 1 - outProgress };
			case 'CutOut':
				return {};
			case 'ScaleDown':
				return { transform: `scale(${1 - outProgress})` };
			case 'ZoomOut':
				return { transform: `scale(${1 - outProgress * 0.5})` };
			default:
				return { opacity: 1 - outProgress };
		}
	};

	// ── Text color: always white ──
	const textColor = '#ffffff';

	// ── Glow: always present, stronger on chorus ──
	const getGlow = (): string => {
		if (label === 'Chorus' || label === 'サビ') {
			return '0 0 14px rgba(255,255,255,0.55), 0 0 28px rgba(186,227,255,0.48), 0 0 56px rgba(160,209,255,0.28)';
		}
		return '0 0 10px rgba(255,255,255,0.46), 0 0 22px rgba(184,222,255,0.3), 0 0 44px rgba(145,198,255,0.2)';
	};

	// ── Font size based on section ──
	const getFontSize = (): number => {
		const isChorus = label === 'Chorus' || label === 'サビ';
		const base = 82;
		const chorusBoost = isChorus ? 6 : 0;
		const longPenalty = visibleLength(text) > 28 ? 6 : 0;
		return Math.max(58, base + chorusBoost - longPenalty);
	};

	// ── Karaoke highlight color ──
	const karaokeHighlight = '#66ccff';

	// ── Karaoke mode: word-level highlighting ──
	if (animationIn === 'Karaoke' && words && words.length > 0) {
		// frame is relative to this Sequence (starts at 0)
		const currentTime = frame / fps;
		const karaokeTime = currentTime * KARAOKE_PROGRESS_SPEED;

		return (
			<AbsoluteFill
				style={{
					justifyContent: 'center',
					alignItems: 'center',
					opacity: crossDissolveOpacity,
					...computeOutStyle(),
				}}
			>
					<div
						style={{
							...lyricsFont,
							fontSize: getFontSize(),
							fontWeight: 600,
							textShadow: getGlow(),
							display: 'flex',
							flexDirection: 'column',
							alignItems: 'center',
							gap: 8,
							lineHeight: 1.22,
						}}
					>
						{karaokeWordLines.map((wordLine, lineIndex) => (
							<div
								key={lineIndex}
								style={{ display: 'flex', justifyContent: 'center', flexWrap: 'nowrap' }}
							>
								{wordLine.map((w, i) => {
									// Progress within this word: 0 = not started, 1 = fully sung
									// Guard against invalid/zero-length ranges from alignment data.
									const wordProgress =
										w.end <= w.start
											? (karaokeTime >= w.start ? 1 : 0)
											: interpolate(karaokeTime, [w.start, w.end], [0, 1], {
												extrapolateLeft: 'clamp',
												extrapolateRight: 'clamp',
											});

									return (
										<span
											key={`${lineIndex}-${i}`}
											style={{
												position: 'relative',
												display: 'inline-block',
												color: 'rgba(255,255,255,0.35)',
												whiteSpace: 'pre',
											}}
										>
											{/* Highlighted overlay using clip mask */}
											<span
												style={{
													position: 'absolute',
													left: 0,
													top: 0,
													color: karaokeHighlight,
													clipPath: `inset(0 ${(1 - wordProgress) * 100}% 0 0)`,
													textShadow: `0 0 16px ${karaokeHighlight}`,
												}}
											>
												{w.word}
											</span>
											{w.word}
										</span>
									);
								})}
							</div>
						))}
					</div>
				</AbsoluteFill>
			);
		}

	// ── Staggered / Typewriter rendering ──
	if (animationIn === 'StaggeredFadeIn' || animationIn === 'Typewriter') {
		const charDelay = animationIn === 'Typewriter' ? 2 : 3;

		return (
			<AbsoluteFill
				style={{
					justifyContent: 'center',
					alignItems: 'center',
					opacity: crossDissolveOpacity,
					...computeOutStyle(),
				}}
			>
				<div
						style={{
							...lyricsFont,
							fontSize: getFontSize(),
							fontWeight: 600,
							color: textColor,
							textShadow: getGlow(),
							display: 'flex',
							flexDirection: 'column',
							alignItems: 'center',
							gap: 8,
							lineHeight: 1.22,
						}}
					>
						{charsByLine.map((lineChars, lineIndex) => (
							<div key={lineIndex}>
								{lineChars.map(({ char, index }) => {
									const charProgress = interpolate(
										frame,
										[index * charDelay, index * charDelay + charDelay],
										[0, 1],
										{ extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
									);
									return (
										<span
											key={`${lineIndex}-${index}`}
											style={{
												opacity: charProgress,
												transform: animationIn === 'StaggeredFadeIn'
													? `translateY(${(1 - charProgress) * 12}px)`
													: undefined,
											}}
										>
											{char}
										</span>
									);
								})}
							</div>
						))}
					</div>
				</AbsoluteFill>
			);
	}

	// ── Standard rendering ──
	const inStyle = computeInStyle();
	const outStyle = computeOutStyle();

	// Merge transform strings if both in and out have transforms
	const mergedTransform = [inStyle.transform, outStyle.transform]
		.filter(Boolean)
		.join(' ');

	const mergedStyle: CSSProperties = {
		...inStyle,
		...outStyle,
		...(mergedTransform ? { transform: mergedTransform } : {}),
		// opacity: multiply both if both defined
		opacity: ((typeof inStyle.opacity === 'number' ? inStyle.opacity : 1) *
			(typeof outStyle.opacity === 'number' ? outStyle.opacity : 1)) *
			crossDissolveOpacity,
	};

	// Merge filter strings
	if (inStyle.filter && outStyle.filter) {
		mergedStyle.filter = `${inStyle.filter} ${outStyle.filter}`;
	}

	return (
		<AbsoluteFill
			style={{
				justifyContent: 'center',
				alignItems: 'center',
			}}
		>
				<div
					style={{
						...lyricsFont,
						fontSize: getFontSize(),
						fontWeight: 600,
						color: textColor,
						textShadow: getGlow(),
						display: 'flex',
						flexDirection: 'column',
						alignItems: 'center',
						gap: 8,
						lineHeight: 1.22,
						...mergedStyle,
					}}
				>
						{lines.map((line, i) => (
							<div key={i}>{line}</div>
						))}
					</div>
			</AbsoluteFill>
		);
};

// ── Music Particles (from AcoRielCover) ─────────────────────

type LightParticle = {
	lifeFrames: number;
	spawnOffset: number;
	driftAmp: number;
	driftFreq: number;
	phase: number;
};

const seedRand = (seed: number): (() => number) => {
	let s = seed >>> 0;
	return () => {
		s += 0x6d2b79f5;
		let t = Math.imul(s ^ (s >>> 15), 1 | s);
		t ^= t + Math.imul(t ^ (t >>> 7), 61 | t);
		return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
	};
};

const hash01 = (n: number): number => {
	const x = Math.sin(n * 12.9898) * 43758.5453123;
	return x - Math.floor(x);
};

const MusicParticles: React.FC = () => {
	const frame = useCurrentFrame();

	const particles = useMemo(() => {
		const rnd = seedRand(20260213);
		return new Array(56).fill(null).map((): LightParticle => ({
			lifeFrames: Math.floor(420 + rnd() * 440),
			spawnOffset: Math.floor(rnd() * 6000),
			driftAmp: 0.018 + rnd() * 0.05,
			driftFreq: 0.0025 + rnd() * 0.0055,
			phase: rnd() * Math.PI * 2,
		}));
	}, []);

	return (
		<AbsoluteFill style={{ pointerEvents: 'none' }}>
			{particles.map((p, i) => {
				const elapsed = frame + p.spawnOffset;
				const cycle = Math.floor(elapsed / p.lifeFrames);
				const local = elapsed % p.lifeFrames;
				const t = local / p.lifeFrames;

				const spawnX = 0.08 + hash01(cycle * 67.3 + i * 19.1) * 0.84;
				const size = 8 + hash01(cycle * 79.7 + i * 23.9) * 50;
				const yPct = 1.12 - t * 1.28;

				const swayMain =
					Math.sin(frame * p.driftFreq + p.phase) * p.driftAmp;
				const swaySub =
					Math.sin(frame * (p.driftFreq * 0.52) + p.phase * 1.6) *
					(p.driftAmp * 0.5);
				const xPct = spawnX + swayMain + swaySub;

				const fadeEdge =
					yPct < 0.1
						? yPct / 0.1
						: yPct > 0.9
							? (1 - yPct) / 0.1
							: 1;
				const flicker =
					0.74 +
					Math.sin(frame * (0.013 + (i % 7) * 0.002) + i * 2.8) * 0.28 +
					Math.sin(frame * (0.03 + (i % 5) * 0.002) + i * 1.7) * 0.16;

				const lifeFadeIn = interpolate(t, [0, 0.14], [0, 1], {
					extrapolateLeft: 'clamp',
					extrapolateRight: 'clamp',
				});
				const lifeFadeOut = interpolate(t, [0.68, 1], [1, 0], {
					extrapolateLeft: 'clamp',
					extrapolateRight: 'clamp',
				});
				const isOutside = xPct < -0.08 || xPct > 1.08 || yPct < -0.14 || yPct > 1.12;
				const opacity = isOutside
					? 0
					: Math.max(0, 0.42 * fadeEdge * flicker * lifeFadeIn * lifeFadeOut);

				const whiteTone = 242 + (i % 3) * 5;
				const color = `rgba(${whiteTone},${whiteTone},${whiteTone},${opacity})`;
				const glow = `0 0 ${size * 1.7}px rgba(255,255,255,0.26), 0 0 ${size * 4.9}px rgba(255,255,255,0.18)`;
				const blurPx = interpolate(size, [8, 58], [2.5, 6.4], {
					extrapolateLeft: 'clamp',
					extrapolateRight: 'clamp',
				});

				return (
					<div
						key={`p-${i}`}
						style={{
							position: 'absolute',
							left: `${xPct * 100}%`,
							top: `${yPct * 100}%`,
							width: size,
							height: size,
							borderRadius: '50%',
							background: color,
							boxShadow: glow,
							filter: `blur(${blurPx}px)`,
							transform: 'translate(-50%, -50%)',
						}}
					/>
				);
			})}
		</AbsoluteFill>
	);
};

// ── Angel Feathers (from AcoRielCover) ──────────────────────

type FeatherSprite = {
	x: number;
	startOffset: number;
	fallDuration: number;
	scale: number;
	baseAngle: number;
	tiltRange: number;
	flipX: number;
	baseOpacity: number;
	swayAmp: number;
	swayFreq: number;
	spinFreq: number;
	phase: number;
};

const AngelFeathers: React.FC = () => {
	const frame = useCurrentFrame();
	const featherImage = staticFile('assets/angel_feather_sheet.png');

	const feathers = useMemo(() => {
		const rnd = seedRand(20260214);
		return new Array(26).fill(null).map((): FeatherSprite => ({
			x: 0.06 + rnd() * 0.88,
			startOffset: rnd(),
			fallDuration: 280 + rnd() * 320,
			scale: 0.12 + rnd() * 2.2,
			baseAngle: -35 + rnd() * 70,
			tiltRange: 8 + rnd() * 14,
			flipX: rnd() > 0.5 ? 1 : -1,
			baseOpacity: 0.25 + rnd() * 0.55,
			swayAmp: 0.01 + rnd() * 0.035,
			swayFreq: 0.006 + rnd() * 0.01,
			spinFreq: 0.008 + rnd() * 0.018,
			phase: rnd() * Math.PI * 2,
		}));
	}, []);

	return (
		<AbsoluteFill style={{ pointerEvents: 'none' }}>
			{feathers.map((f, i) => {
				const loop = ((frame + f.startOffset * f.fallDuration) % f.fallDuration) / f.fallDuration;
				const gravityY = Math.pow(loop, 1.55);
				const sway =
					Math.sin(frame * f.swayFreq + f.phase) * f.swayAmp +
					Math.sin(frame * f.swayFreq * 0.48 + f.phase * 1.4) * (f.swayAmp * 0.6);
				const xPct = f.x + sway;
				const yPct = -0.12 + gravityY * 1.28;

				const edgeFade =
					loop < 0.12 ? loop / 0.12 : loop > 0.92 ? (1 - loop) / 0.08 : 1;
				const scale = f.scale;
				const blurPx = interpolate(scale, [0.12, 2.3], [0.1, 6.2], {
					extrapolateLeft: 'clamp',
					extrapolateRight: 'clamp',
				});
				const opacity = Math.max(0.06, f.baseOpacity * edgeFade);
				const rotate =
					f.baseAngle + Math.sin(frame * f.spinFreq + f.phase) * f.tiltRange;
				const featherWidth = 54 * scale;
				const featherHeight = 54 * scale;

				return (
					<div
						key={`feather-${i}`}
						style={{
							position: 'absolute',
							left: `${xPct * 100}%`,
							top: `${yPct * 100}%`,
							width: featherWidth,
							height: featherHeight,
							transform: `translate(-50%, -50%) scaleX(${f.flipX}) rotate(${rotate}deg)`,
							opacity,
							mixBlendMode: 'normal',
							pointerEvents: 'none',
						}}
					>
						<Img
							src={featherImage}
							style={{
								width: '100%',
								height: '100%',
								objectFit: 'contain',
								filter: `blur(${blurPx}px)`,
							}}
						/>
					</div>
				);
			})}
		</AbsoluteFill>
	);
};

// ── Linear Spectrum (Bottom Bar) ────────────────────────────

const useSongAudioData = (src: string) => {
	const [audioData, setAudioData] = useState<Awaited<
		ReturnType<typeof getAudioData>
	> | null>(null);

	useEffect(() => {
		const handle = delayRender(
			`Waiting for song audio data src="${src}"`,
			{ timeoutInMilliseconds: 180000 }
		);

		getAudioData(src, { sampleRate: 6000 })
			.then((data) => setAudioData(data))
			.catch((err) => {
				console.error('Failed to load audio data:', err);
				setAudioData(null);
			})
			.finally(() => continueRender(handle));
	}, [src]);

	return audioData;
};

const ChannelBrandBadge: React.FC = () => {
	const icon = staticFile('assets/channel-icon.png');
	const wordmark = staticFile('assets/channel-wordmark.png');

	return (
		<AbsoluteFill style={{ pointerEvents: 'none' }}>
			<div
				style={{
					position: 'absolute',
					top: 14,
					left: 12,
					width: 1280,
					height: 280,
				}}
			>
				<Img
					src={icon}
					style={{
						position: 'absolute',
						left: 0,
						top: 0,
						width: 160,
						height: 160,
						objectFit: 'cover',
						borderRadius: 9999,
						filter:
							'drop-shadow(0 0 14px rgba(255,255,255,0.3)) drop-shadow(0 0 30px rgba(209,192,235,0.24))',
					}}
				/>
				<Img
					src={wordmark}
					style={{
						position: 'absolute',
						left: -240,
						top: -220,
						width: 1300,
						height: 620,
						objectFit: 'contain',
						filter:
							'drop-shadow(0 0 24px rgba(255,255,255,0.5)) drop-shadow(0 0 54px rgba(214,197,241,0.36)) drop-shadow(0 0 92px rgba(255,255,255,0.22))',
					}}
				/>
			</div>
		</AbsoluteFill>
	);
};

const LinearSpectrum: React.FC = () => {
	const frame = useCurrentFrame();
	const { fps, width } = useVideoConfig();
	const barCount = 48;
	const audioData = useSongAudioData(staticFile('assets/audio.wav'));

	if (!audioData) return null;

	const waveform = visualizeAudioWaveform({
		audioData,
		frame,
		fps,
		numberOfSamples: barCount,
		windowInSeconds: 0.3,
		normalize: true,
	});

	const smoothed = waveform.map((_, i) => {
		let sum = 0;
		let count = 0;
		for (let j = -2; j <= 2; j++) {
			const idx = i + j;
			if (idx >= 0 && idx < waveform.length) {
				const w = j === 0 ? 2 : 1;
				sum += Math.max(0, waveform[idx]) * w;
				count += w;
			}
		}
		return Math.pow(count > 0 ? sum / count : 0, 0.7);
	});

	const spectrumWidth = Math.min(1100, width * 0.58);
	const gap = 3;
	const barWidth = (spectrumWidth - gap * (barCount - 1)) / barCount;
	const maxHeight = 80;
	const startX = (width - spectrumWidth) / 2;
	const centerY = 1020;
	const rx = barWidth / 2;

	return (
		<svg
			width={width}
			height={1080}
			style={{ position: 'absolute', left: 0, top: 0, pointerEvents: 'none' }}
		>
			<defs>
				<linearGradient id="bar-grad-up-lc" x1="0" y1="1" x2="0" y2="0">
					<stop offset="0%" stopColor="rgba(255,255,255,0.08)" />
					<stop offset="40%" stopColor="rgba(240,240,255,0.5)" />
					<stop offset="100%" stopColor="rgba(255,255,255,0.75)" />
				</linearGradient>
				<linearGradient id="bar-grad-down-lc" x1="0" y1="0" x2="0" y2="1">
					<stop offset="0%" stopColor="rgba(255,255,255,0.06)" />
					<stop offset="100%" stopColor="rgba(240,240,255,0.02)" />
				</linearGradient>
				<filter id="spec-glow-soft-lc">
					<feGaussianBlur in="SourceGraphic" stdDeviation="3.5" />
				</filter>
			</defs>

			<g filter="url(#spec-glow-soft-lc)">
				{smoothed.map((v, i) => {
					const h = 3 + v * maxHeight;
					const x = startX + i * (barWidth + gap);
					return (
						<rect
							key={`g-${i}`}
							x={x}
							y={centerY - h}
							width={barWidth}
							height={h}
							rx={rx}
							fill="rgba(220,225,255,0.25)"
						/>
					);
				})}
			</g>

			{smoothed.map((v, i) => {
				const h = 3 + v * maxHeight;
				const x = startX + i * (barWidth + gap);
				return (
					<rect
						key={`b-${i}`}
						x={x}
						y={centerY - h}
						width={barWidth}
						height={h}
						rx={rx}
						fill="url(#bar-grad-up-lc)"
						opacity={0.45 + v * 0.5}
					/>
				);
			})}

			{smoothed.map((v, i) => {
				const h = (3 + v * maxHeight) * 0.35;
				const x = startX + i * (barWidth + gap);
				return (
					<rect
						key={`m-${i}`}
						x={x}
						y={centerY + 2}
						width={barWidth}
						height={h}
						rx={rx}
						fill="url(#bar-grad-down-lc)"
						opacity={0.2 + v * 0.15}
					/>
				);
			})}
		</svg>
	);
};

// ── Intro Overlay ───────────────────────────────────────────

const TextReveal: React.FC<{
	children: React.ReactNode;
	startFrame: number;
	writeFrames: number;
	style?: CSSProperties;
	showPen?: boolean;
	penSrc?: string;
	penWidth?: number;
	penYOffset?: number;
}> = ({ children, startFrame, writeFrames, style, showPen, penSrc, penWidth, penYOffset }) => {
	const frame = useCurrentFrame();
	const elapsed = frame - startFrame;

	const progress = interpolate(elapsed, [0, writeFrames], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
		easing: Easing.out(Easing.cubic),
	});

	const penX = progress * 100;
	const penVisible = showPen && penSrc && progress > 0 && progress < 0.985;
	const penFloatY = Math.sin(frame * 0.2) * 2.2;
	const penTilt = Math.sin(frame * 0.16) * 7;
	const edgeStart = Math.max(0, penX - 8);

	return (
		<div
			style={{
				position: 'relative',
				display: 'inline-block',
				overflow: 'visible',
				...style,
			}}
		>
			<div
				style={{
					maskImage: `linear-gradient(to right, black ${edgeStart}%, black ${penX}%, transparent ${penX + 0.5}%)`,
					WebkitMaskImage: `linear-gradient(to right, black ${edgeStart}%, black ${penX}%, transparent ${penX + 0.5}%)`,
				}}
			>
				{children}
			</div>

			{penVisible && (
				<div
					style={{
						position: 'absolute',
						left: `${penX}%`,
						top: '50%',
						width: 6,
						height: 6,
						borderRadius: '50%',
						background: 'rgba(255,255,255,0.7)',
						boxShadow:
							'0 0 12px 4px rgba(255,255,255,0.4), 0 0 30px 8px rgba(212,196,144,0.25)',
						transform: 'translate(-50%, -50%)',
						pointerEvents: 'none',
					}}
				/>
			)}

			{penVisible && (
				<Img
					src={penSrc!}
					style={{
						position: 'absolute',
						left: `${penX}%`,
						top: '50%',
						width: penWidth ?? 130,
						height: 'auto',
						objectFit: 'contain',
						transform: `translate(-22%, calc(-88% + ${penFloatY}px)) rotate(${penTilt}deg)`,
						filter:
							'drop-shadow(0 0 10px rgba(255,255,255,0.45)) drop-shadow(0 0 20px rgba(212,196,144,0.28))',
						pointerEvents: 'none',
						opacity: 0.92,
						marginTop: penYOffset ?? -30,
					}}
				/>
			)}
		</div>
	);
};

const StrokeOrderTitle: React.FC<{
	text: string;
	startFrame: number;
	writeFrames: number;
}> = ({ text, startFrame, writeFrames }) => {
	const frame = useCurrentFrame();
	const elapsed = frame - startFrame;
	const chars = [...text];
	const count = Math.max(1, chars.length);

	return (
		<div
			style={{
				position: 'relative',
				display: 'inline-flex',
				alignItems: 'center',
				letterSpacing: '0.04em',
				whiteSpace: 'nowrap',
			}}
		>
			{chars.map((char, i) => {
				const charStart = (i / count) * writeFrames * 0.9;
				const charEnd = charStart + Math.max(5, writeFrames / count * 1.4);
				const charProgress = interpolate(elapsed, [charStart, charEnd], [0, 1], {
					extrapolateLeft: 'clamp',
					extrapolateRight: 'clamp',
					easing: Easing.out(Easing.cubic),
				});
				const fillOpacity = interpolate(charProgress, [0.35, 1], [0, 1], {
					extrapolateLeft: 'clamp',
					extrapolateRight: 'clamp',
				});

				return (
					<span
						key={`${char}-${i}`}
						style={{
							position: 'relative',
							display: 'inline-block',
							color: 'rgba(232,220,192,0.12)',
						}}
					>
						<span
							style={{
								position: 'absolute',
								left: 0,
								top: 0,
								color: 'transparent',
								WebkitTextStroke: '1.8px rgba(255,236,191,0.92)',
								clipPath: `inset(0 ${(1 - charProgress) * 100}% 0 0)`,
								filter:
									'drop-shadow(0 0 10px rgba(255,228,171,0.58)) drop-shadow(0 0 22px rgba(255,220,145,0.38))',
								whiteSpace: 'pre',
							}}
						>
							{char}
						</span>
						<span
							style={{
								position: 'absolute',
								left: 0,
								top: 0,
								color: '#e8dcc0',
								opacity: fillOpacity,
								textShadow:
									'0 0 24px rgba(212,196,144,0.38), 0 0 54px rgba(212,196,144,0.22)',
								whiteSpace: 'pre',
							}}
						>
							{char}
						</span>
						<span style={{ opacity: 0 }}>{char}</span>
					</span>
				);
			})}
		</div>
	);
};

const LINE_SCHEDULE = [
	{ start: 0, write: 18 },
	{ start: 20, write: 55 },
	{ start: 77, write: 18 },
	{ start: 97, write: 18 },
] as const;

const IntroOverlay: React.FC<{
	title: string;
	artist: string;
	durationFrames: number;
}> = ({ title, artist, durationFrames }) => {
	const frame = useCurrentFrame();
	const wordmark = staticFile('assets/channel-wordmark.png');
	const featherPen = staticFile('assets/feather_pen.png');

	const fadeIn = interpolate(frame, [0, 15], [0, 1], {
		extrapolateRight: 'clamp',
		easing: Easing.out(Easing.cubic),
	});
	const fadeOut = interpolate(
		frame,
		[durationFrames - 25, durationFrames],
		[1, 0],
		{ extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
	);
	const opacity = Math.min(fadeIn, fadeOut);

	const activeLineIdx = useMemo(() => {
		for (let i = 0; i < LINE_SCHEDULE.length; i++) {
			const l = LINE_SCHEDULE[i];
			const elapsed = frame - l.start;
			if (elapsed >= 0 && elapsed < l.write) return i;
		}
		return -1;
	}, [frame]);

	const penProps = (lineIdx: number) => ({
		showPen: activeLineIdx === lineIdx,
		penSrc: featherPen,
		penWidth: lineIdx === 1 ? 145 : 120,
		penYOffset: lineIdx === 1 ? -34 : -26,
	});

	return (
		<AbsoluteFill
			style={{
				justifyContent: 'center',
				alignItems: 'center',
				opacity,
				backgroundColor: 'rgba(5,5,10,0.6)',
			}}
		>
			<div
				style={{
					...lyricsFont,
					display: 'flex',
					flexDirection: 'column',
					alignItems: 'center',
					gap: 20,
				}}
			>
				<TextReveal
					startFrame={LINE_SCHEDULE[0].start}
					writeFrames={LINE_SCHEDULE[0].write}
					{...penProps(0)}
				>
					<span
						style={{
							fontFamily: yosugaraFamily,
							fontSize: 48,
							fontWeight: 400,
							color: 'rgba(192,200,216,0.6)',
							letterSpacing: '0.06em',
							whiteSpace: 'nowrap',
						}}
					>
						Acoustic Cover
					</span>
				</TextReveal>

					<TextReveal
						startFrame={LINE_SCHEDULE[1].start}
						writeFrames={LINE_SCHEDULE[1].write}
						{...penProps(1)}
					>
						<div
							style={{
								fontFamily: yosugaraFamily,
								fontSize: 125,
								fontWeight: 400,
								lineHeight: 1.45,
								paddingBottom: 10,
							}}
						>
							<StrokeOrderTitle
								text={title}
								startFrame={LINE_SCHEDULE[1].start}
								writeFrames={LINE_SCHEDULE[1].write}
							/>
						</div>
					</TextReveal>

				<TextReveal
					startFrame={LINE_SCHEDULE[2].start}
					writeFrames={LINE_SCHEDULE[2].write}
					{...penProps(2)}
				>
					<span
						style={{
							fontFamily: yosugaraFamily,
							fontSize: 32,
							fontWeight: 400,
							color: 'rgba(255,255,255,0.5)',
							whiteSpace: 'nowrap',
						}}
					>
						Original by {artist}
					</span>
				</TextReveal>

				<div
					style={{
						width: 80,
						height: 1,
						background:
							'linear-gradient(90deg, transparent, rgba(192,200,216,0.4), transparent)',
						opacity: interpolate(
							frame - LINE_SCHEDULE[3].start,
							[0, 5],
							[0, 1],
							{ extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
						),
					}}
				/>

				<TextReveal
					startFrame={LINE_SCHEDULE[3].start}
					writeFrames={LINE_SCHEDULE[3].write}
					{...penProps(3)}
				>
					<div
						style={{
							display: 'flex',
							alignItems: 'center',
							gap: 12,
							whiteSpace: 'nowrap',
							paddingTop: 110,
							paddingBottom: 110,
							marginTop: -110,
							marginBottom: -110,
						}}
					>
						<span
							style={{
								fontFamily: yosugaraFamily,
								fontSize: 26,
								fontWeight: 400,
								color: 'rgba(184,160,212,0.7)',
								letterSpacing: '0.15em',
							}}
						>
							Covered by
						</span>
						<Img
							src={wordmark}
							style={{
								height: 300,
								objectFit: 'contain',
								marginTop: -110,
								marginBottom: -110,
								marginLeft: -60,
								marginRight: -20,
								filter:
									'drop-shadow(0 0 12px rgba(255,255,255,0.4)) drop-shadow(0 0 28px rgba(214,197,241,0.3))',
							}}
						/>
					</div>
				</TextReveal>
			</div>
		</AbsoluteFill>
	);
};

// ── Outro Overlay ───────────────────────────────────────────

const OutroOverlay: React.FC<{ durationFrames: number }> = ({
	durationFrames,
}) => {
	const frame = useCurrentFrame();
	const channelIcon = staticFile('assets/channel-icon.png');
	const channelWordmark = staticFile('assets/channel-wordmark.png');

	const fadeIn = interpolate(frame, [0, 30], [0, 1], {
		extrapolateRight: 'clamp',
		easing: Easing.out(Easing.cubic),
	});
	const fadeOut = interpolate(
		frame,
		[durationFrames - 45, durationFrames],
		[1, 0],
		{ extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
	);
	const opacity = Math.min(fadeIn, fadeOut);

	return (
		<AbsoluteFill
			style={{
				justifyContent: 'center',
				alignItems: 'center',
				opacity,
				backgroundColor: 'rgba(5,5,10,0.7)',
			}}
		>
			<div
				style={{
					...lyricsFont,
					display: 'flex',
					flexDirection: 'column',
					alignItems: 'center',
					gap: 18,
				}}
			>
				<Img
					src={channelIcon}
					style={{
						width: 420,
						height: 420,
						objectFit: 'cover',
						borderRadius: 9999,
						filter:
							'drop-shadow(0 0 24px rgba(255,255,255,0.36)) drop-shadow(0 0 48px rgba(207,188,236,0.28))',
					}}
				/>
				<Img
					src={channelWordmark}
					style={{
						width: 940,
						height: 980,
						objectFit: 'contain',
						marginTop: -360,
						filter:
							'drop-shadow(0 0 24px rgba(255,255,255,0.5)) drop-shadow(0 0 54px rgba(214,197,241,0.36)) drop-shadow(0 0 92px rgba(255,255,255,0.22))',
					}}
				/>
				<span
					style={{
						fontSize: 16,
						fontWeight: 400,
						color: 'rgba(255,255,255,0.4)',
						letterSpacing: '0.3em',
						marginTop: -360,
					}}
				>
					ACOUSTIC COVER BAND
				</span>
				<div
					style={{
						width: 40,
						height: 1,
						background:
							'linear-gradient(90deg, transparent, rgba(192,200,216,0.3), transparent)',
						marginTop: -20,
					}}
				/>
				<span
					style={{
						fontFamily: yosugaraFamily,
						fontSize: 30,
						fontWeight: 600,
						color: 'rgba(255,255,255,0.86)',
						marginTop: 8,
						textShadow: '0 0 14px rgba(255,255,255,0.34)',
					}}
				>
					チャンネル登録よろしくお願いします
				</span>
			</div>
		</AbsoluteFill>
	);
};

// ── Lyric Animation Layer ───────────────────────────────────

const LyricAnimationLayer: React.FC<{
	data: LyricAnimationEntry[];
	songStartFrame: number;
	songEndFrame?: number;
	supportedCodepoints?: Set<number> | null;
}> = ({ data, songStartFrame, songEndFrame, supportedCodepoints = null }) => {
	const frame = useCurrentFrame();
	const { fps } = useVideoConfig();
	const maxSongFrames = Math.max(1, (songEndFrame ?? Infinity) - songStartFrame);
	const maxSongSeconds = maxSongFrames / fps;
	const effectiveData = useMemo(() => {
		if (data.length === 0) return [];
		if (!Number.isFinite(maxSongSeconds)) return data;
		const copied = data.map((entry) => ({ ...entry }));
		const last = copied[copied.length - 1];
		const maxDuration = Math.max(0, maxSongSeconds - last.time);
		if (maxDuration > last.duration) {
			last.duration = maxDuration;
		}
		return copied;
	}, [data, maxSongSeconds]);

	const songDurationFrames = useMemo(() => {
		if (effectiveData.length === 0) return 1;
		return Math.max(
			1,
			...effectiveData.map((entry) => Math.round((entry.time + entry.duration) * fps)),
			Math.round(maxSongFrames),
		);
	}, [effectiveData, fps, maxSongFrames]);

	const songFrame = frame - songStartFrame;
	if (songFrame < 0 || songFrame >= maxSongFrames) {
		return <AbsoluteFill style={{ pointerEvents: 'none' }} />;
	}

	const songTime = songFrame / fps;
	let activeEntry: LyricAnimationEntry | null = null;
	for (let i = effectiveData.length - 1; i >= 0; i--) {
		const entry = effectiveData[i];
		if (songTime >= entry.time && songTime < entry.time + entry.duration) {
			activeEntry = entry;
			break;
		}
	}

	return (
		<AbsoluteFill style={{ pointerEvents: 'none' }}>
			<Sequence from={songStartFrame} durationInFrames={songDurationFrames}>
				{activeEntry ? (
					<LyricLine
						text={activeEntry.text}
						animationIn={activeEntry.animation.in}
						animationOut={activeEntry.animation.out}
						inDuration={activeEntry.animation.props.inDurationFrames}
						outDuration={activeEntry.animation.props.outDurationFrames}
						label={activeEntry.label}
						words={activeEntry.words}
						lineFrame={songFrame - Math.round(activeEntry.time * fps)}
						lineDurationInFrames={Math.max(
							1,
							Math.round(activeEntry.duration * fps)
						)}
						supportedCodepoints={supportedCodepoints}
					/>
				) : null}
			</Sequence>
		</AbsoluteFill>
	);
};

// ── Main Composition ────────────────────────────────────────

export const AcoRielLyricCover: React.FC = () => {
	const frame = useCurrentFrame();
	const { durationInFrames, fps } = useVideoConfig();

	// Intro/Outro timing
	const introFrames = Math.floor(7 * fps);
	const tailSilenceFrames = Math.round(2 * fps);
	const outroLeadFrames = Math.round(0.3 * fps);
	const audioFadeOutFrames = Math.max(1, Math.round(0.5 * fps));
	const audioEndFrame = Math.max(introFrames + 1, durationInFrames - tailSilenceFrames);
	const outroStart = Math.max(introFrames, audioEndFrame - outroLeadFrames);
	const outroFrames = Math.max(1, durationInFrames - outroStart);

	// Load lyric animation data
	const [lyricData, setLyricData] = useState<LyricAnimationEntry[]>([]);
	const [supportedCodepoints, setSupportedCodepoints] = useState<Set<number> | null>(null);

	useEffect(() => {
		fetch(staticFile('assets/lyric_animation_data.json'))
			.then((res) => res.json())
			.then((data) => setLyricData(data))
			.catch((err) => console.error('Failed to load lyric data:', err));
	}, []);

	useEffect(() => {
		fetch(staticFile('assets/fonts/yosugaraver1_2.codepoints.json'))
			.then((res) => res.json())
			.then((data: { codepoints?: number[] }) => {
				const points = Array.isArray(data?.codepoints) ? data.codepoints : [];
				setSupportedCodepoints(new Set(points));
			})
			.catch((err) => {
				console.warn('Failed to load Yosugara codepoints:', err);
				setSupportedCodepoints(null);
			});
	}, []);

	// Background pan/zoom
	const panX = Math.sin((frame / fps) * 0.025) * 1.2;
	const panY = Math.cos((frame / fps) * 0.018) * 0.8;
	const zoom = 1.05 + Math.sin((frame / fps) * 0.012) * 0.02;

	return (
		<AbsoluteFill style={{ backgroundColor: '#0a0a12' }}>
			{/* Background image */}
			<Img
				src={staticFile('assets/background.png')}
				style={{
					width: '100%',
					height: '100%',
					objectFit: 'cover',
					filter: 'brightness(0.35) saturate(0.65)',
					transform: `scale(${zoom}) translate(${panX}%, ${panY}%)`,
				}}
			/>

			{/* Gradient overlay */}
			<AbsoluteFill
				style={{
					background:
						'radial-gradient(ellipse at 50% 40%, rgba(30,25,50,0.3), rgba(5,5,10,0.75))',
				}}
			/>

			{/* Vignette */}
			<AbsoluteFill
				style={{
					background:
						'radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.5) 100%)',
				}}
			/>

			{frame < outroStart && <ChannelBrandBadge />}

			{/* Music particles */}
			<MusicParticles />

			{/* Pencil writing sound */}
			<Sequence durationInFrames={introFrames}>
				<Audio
					src={staticFile('assets/write_with_pencil.mp3')}
					volume={(f) => {
						const writeEnd = 120;
						const fadeStart = writeEnd - 20;
						if (f >= fadeStart) {
							return interpolate(f, [fadeStart, writeEnd], [0.7, 0], {
								extrapolateLeft: 'clamp',
								extrapolateRight: 'clamp',
							});
						}
						if (f >= writeEnd) return 0;
						return 0.7;
					}}
				/>
			</Sequence>

				{/* Song audio – starts after intro */}
				<Sequence
					from={introFrames}
					durationInFrames={Math.max(1, audioEndFrame - introFrames)}
				>
					<Audio
						src={staticFile('assets/audio.wav')}
						volume={(f) => {
							const audioDurationFrames = Math.max(1, audioEndFrame - introFrames);
							const fadeStart = Math.max(0, audioDurationFrames - audioFadeOutFrames);
							if (f < fadeStart) return 1;
							return interpolate(f, [fadeStart, audioDurationFrames], [1, 0], {
								extrapolateLeft: 'clamp',
								extrapolateRight: 'clamp',
							});
						}}
					/>
				</Sequence>

			{/* Spectrum */}
			<LinearSpectrum />

			{/* Intro */}
			<Sequence durationInFrames={introFrames}>
				<IntroOverlay
					title={SONG_TITLE}
					artist={SONG_ARTIST}
					durationFrames={introFrames}
				/>
			</Sequence>

			{/* Angel feathers – after intro */}
			<Sequence from={introFrames}>
				<AngelFeathers />
			</Sequence>

			{/* ★ Lyric Animation Layer ★ */}
				{lyricData.length > 0 && (
					<LyricAnimationLayer
						data={lyricData}
						songStartFrame={introFrames}
						songEndFrame={outroStart}
						supportedCodepoints={supportedCodepoints}
					/>
				)}

			{/* Outro */}
			<Sequence from={outroStart} durationInFrames={outroFrames}>
				<OutroOverlay durationFrames={outroFrames} />
			</Sequence>
		</AbsoluteFill>
	);
};
