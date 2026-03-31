import {
	AbsoluteFill,
	Audio,
	Img,
	interpolate,
	Loop,
	Sequence,
	staticFile,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import {useMemo} from 'react';

type SlideLayout =
	| 'hook'
	| 'section'
	| 'evidence'
	| 'emphasis'
	| 'story'
	| 'closing'
	| 'profile';

type SlideEntry = {
	index: number;
	text: string;
	image: string | null;
	label?: string;
	layout?: SlideLayout;
	headline?: string | null;
	body?: string | null;
	highlight?: string | null;
	searchQuery?: string;
};

type CanvasSlideshowProps = {
	audioSrc: string;
	bgmSrc?: string;
	bgmVolume?: number;
	slides: SlideEntry[];
};

type TimedSlideEntry = {
	entry: SlideEntry;
	from: number;
	durationInFrames: number;
	slideIndex: number;
};

type SlideDisplay = {
	label: string;
	layout: SlideLayout;
	headline: string;
	body: string | null;
	highlight: string | null;
	accent: string;
};

const baseTextStyle: React.CSSProperties = {
	fontFamily: '"Noto Sans JP", "Hiragino Kaku Gothic ProN", sans-serif',
	color: '#f5f5f0',
	lineHeight: 1.8,
	letterSpacing: '0.05em',
	margin: 0,
};

const FALLBACK_GRADIENTS = [
	'linear-gradient(135deg, #0d1b2a 0%, #1b2a4a 100%)',
	'linear-gradient(135deg, #1a0a2e 0%, #2d1b4e 100%)',
	'linear-gradient(135deg, #0a1a0d 0%, #1a3020 100%)',
	'linear-gradient(135deg, #2a0d0d 0%, #4a1a1a 100%)',
	'linear-gradient(135deg, #0d2a2a 0%, #1a4040 100%)',
];

const ACCENT_BY_LAYOUT: Record<SlideLayout, string> = {
	hook: '#f4d35e',
	section: '#8ecae6',
	evidence: '#ffb703',
	emphasis: '#90be6d',
	story: '#f5f5f0',
	closing: '#d4a373',
	profile: '#e5989b',
};

const LABEL_BY_LAYOUT: Record<SlideLayout, string> = {
	hook: '導入',
	section: '切り替え',
	evidence: '具体例',
	emphasis: '要点',
	story: '解説',
	closing: '締め',
	profile: '人物',
};

const isCenteredLayout = (layout: SlideLayout): boolean => {
	return layout === 'hook' || layout === 'section' || layout === 'closing';
};

const truncateCopy = (text: string, limit: number): string => {
	const compact = text.replace(/\s+/gu, ' ').trim();
	if (compact.length <= limit) {
		return compact;
	}

	return `${compact
		.slice(0, Math.max(limit - 1, 0))
		.replace(/[ 、,，。.!！?？]+$/u, '')}…`;
};

const splitSentences = (text: string): string[] => {
	return text
		.replace(/\s+/gu, ' ')
		.trim()
		.split(/(?<=[。！？!?])\s*/u)
		.filter(Boolean);
};

const detectLayout = (text: string, slideIndex: number): SlideLayout => {
	if (slideIndex === 0) {
		return 'hook';
	}

	if (/^(最後に|まとめると|まとめ|結論)/u.test(text.trim())) {
		return 'closing';
	}

	if (text.trim().length <= 28) {
		return 'emphasis';
	}

	if (/^(ここからは|まず|次に|最後に)/u.test(text.trim())) {
		return 'section';
	}

	if (/(私|僕|自分|プロフィール|経歴|実績|発信|運営)/u.test(text)) {
		return 'profile';
	}

	if (/\d/u.test(text) || /(例えば|たとえば|具体|実際|データ|調査|事例|結果|%)/u.test(text)) {
		return 'evidence';
	}

	return 'story';
};

const pickHighlight = (text: string): string | null => {
	const quoted = text.match(/[「『](.{4,24}?)[」』]/u);
	if (quoted?.[1]) {
		return truncateCopy(quoted[1], 18);
	}

	const numbered = text.match(/(\d+つ|\d+選)/u);
	if (numbered?.[1]) {
		return numbered[1];
	}

	for (const keyword of ['結論', '要点', 'ポイント', 'コツ', '理由', '方法', '比較', '事例']) {
		if (text.includes(keyword)) {
			return keyword;
		}
	}

	return null;
};

const deriveDisplayCopy = (
	text: string,
	slideIndex: number
): Omit<SlideDisplay, 'accent' | 'label' | 'layout'> & {layout: SlideLayout} => {
	const sentences = splitSentences(text);
	const lead = sentences[0] ?? text.trim();
	const remainder = sentences.slice(1).join('');
	const layout = detectLayout(text, slideIndex);

	if (layout === 'hook') {
		return {
			layout,
			headline: truncateCopy(lead, 34),
			body: remainder ? truncateCopy(sentences.slice(1, 3).join(''), 88) : null,
			highlight: pickHighlight(text),
		};
	}

	if (layout === 'emphasis') {
		return {
			layout,
			headline: truncateCopy(text, 34),
			body: null,
			highlight: pickHighlight(text),
		};
	}

	return {
		layout,
		headline: truncateCopy(lead, 34),
		body: remainder ? truncateCopy(remainder, 88) : null,
		highlight: pickHighlight(text),
	};
};

const resolveSlideDisplay = (entry: SlideEntry, slideIndex: number): SlideDisplay => {
	const derived = deriveDisplayCopy(entry.text, slideIndex);
	const layout = entry.layout ?? derived.layout;

	return {
		layout,
		label: entry.label?.trim() || LABEL_BY_LAYOUT[layout],
		headline: entry.headline?.trim() || derived.headline,
		body: entry.body?.trim() || derived.body,
		highlight: entry.highlight?.trim() || derived.highlight,
		accent: ACCENT_BY_LAYOUT[layout],
	};
};

const getHeadlineSize = (display: SlideDisplay): number => {
	if (display.layout === 'hook') {
		return display.headline.length > 24 ? 64 : 76;
	}

	if (display.layout === 'section') {
		return display.headline.length > 24 ? 58 : 66;
	}

	if (display.layout === 'emphasis') {
		return display.headline.length > 22 ? 54 : 62;
	}

	if (display.layout === 'closing') {
		return display.headline.length > 24 ? 56 : 64;
	}

	return display.headline.length > 30 ? 44 : 52;
};

const estimateSlideWeight = (entry: SlideEntry, slideIndex: number): number => {
	const display = resolveSlideDisplay(entry, slideIndex);
	const textLength = `${display.headline}${display.body ?? ''}`.replace(/\s+/gu, '').length;
	const base = Math.max(textLength, 18);

	switch (display.layout) {
		case 'hook':
			return base * 1.15;
		case 'section':
			return Math.max(base * 0.9, 20);
		case 'emphasis':
			return Math.max(base * 0.85, 16);
		case 'evidence':
			return base * 1.05;
		case 'closing':
			return Math.max(base * 0.95, 18);
		default:
			return base;
	}
};

const buildSlideDurations = (
	slides: SlideEntry[],
	totalDurationInFrames: number
): number[] => {
	if (slides.length === 0) {
		return [];
	}

	const weights = slides.map((entry, slideIndex) =>
		estimateSlideWeight(entry, slideIndex)
	);
	const totalWeight = weights.reduce((sum, weight) => sum + weight, 0);
	const rawDurations = weights.map((weight) => (weight / totalWeight) * totalDurationInFrames);
	const durations = rawDurations.map((duration) => Math.floor(duration));
	let remainder = totalDurationInFrames - durations.reduce((sum, duration) => sum + duration, 0);

	const rankedByFraction = rawDurations
		.map((duration, index) => ({
			index,
			fraction: duration - Math.floor(duration),
		}))
		.sort((a, b) => b.fraction - a.fraction);

	let cursor = 0;
	while (remainder > 0 && rankedByFraction.length > 0) {
		const target = rankedByFraction[cursor % rankedByFraction.length];
		durations[target.index] += 1;
		remainder -= 1;
		cursor += 1;
	}

	return durations;
};

const Slide: React.FC<{
	entry: SlideEntry;
	durationInFrames: number;
	slideIndex: number;
	totalSlides: number;
	frame: number;
}> = ({entry, durationInFrames, slideIndex, totalSlides, frame}) => {
	const {fps} = useVideoConfig();
	const fadeFrames = Math.min(Math.floor(0.6 * fps), Math.floor(durationInFrames / 4));
	const display = resolveSlideDisplay(entry, slideIndex);
	const progressRatio = totalSlides <= 1 ? 1 : (slideIndex + 1) / totalSlides;

	const opacity = interpolate(
		frame,
		[0, fadeFrames, durationInFrames - fadeFrames, durationInFrames],
		[0, 1, 1, 0],
		{extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
	);
	const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.05], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	const panX = Math.sin((frame / fps) * 0.05) * 0.8;
	const panY = Math.cos((frame / fps) * 0.04) * 0.6;
	const fallbackBg = FALLBACK_GRADIENTS[slideIndex % FALLBACK_GRADIENTS.length];

	return (
		<AbsoluteFill style={{opacity}}>
			{entry.image ? (
				<Img
					src={staticFile(entry.image)}
					style={{
						width: '100%',
						height: '100%',
						objectFit: 'cover',
						filter: 'brightness(0.55) saturate(0.85)',
						transform: `scale(${scale}) translate(${panX}%, ${panY}%)`,
					}}
				/>
			) : (
				<AbsoluteFill style={{background: fallbackBg}} />
			)}
				<AbsoluteFill
					style={{
						background:
							'linear-gradient(to top, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0.15) 55%, rgba(0,0,0,0.05) 100%)',
					}}
				/>
				<AbsoluteFill
					style={{
						paddingTop: 42,
						paddingLeft: 54,
						paddingRight: 54,
						paddingBottom: 42,
					}}
				>
					<div
						style={{
							height: 6,
							borderRadius: 999,
							background: 'rgba(255,255,255,0.14)',
							overflow: 'hidden',
						}}
					>
						<div
							style={{
								width: `${Math.max(progressRatio * 100, 6)}%`,
								height: '100%',
								background: display.accent,
								boxShadow: `0 0 24px ${display.accent}`,
							}}
						/>
					</div>
					<div
						style={{
							display: 'flex',
							justifyContent: 'flex-end',
							alignItems: 'center',
							marginTop: 20,
						}}
					>
						<span
							style={{
								...baseTextStyle,
								fontSize: 18,
								letterSpacing: '0.14em',
								color: 'rgba(245,245,240,0.68)',
							}}
						>
							{slideIndex + 1} / {totalSlides}
						</span>
					</div>
				</AbsoluteFill>
				<AbsoluteFill
					style={{
						justifyContent:
						isCenteredLayout(display.layout)
							? 'center'
							: 'flex-end',
					alignItems:
						display.layout === 'hook' ? 'center' : 'flex-start',
					paddingTop: 120,
					paddingBottom: 92,
					paddingLeft: 110,
					paddingRight: 110,
				}}
			>
				<div
					style={{
						width: '100%',
							maxWidth:
								isCenteredLayout(display.layout)
									? 1160
									: 980,
						background:
							display.layout === 'hook'
								? 'linear-gradient(180deg, rgba(6,10,18,0.28) 0%, rgba(6,10,18,0.58) 100%)'
								: 'linear-gradient(180deg, rgba(5,10,18,0.18) 0%, rgba(5,10,18,0.58) 100%)',
						border: '1px solid rgba(255,255,255,0.14)',
						borderRadius: 24,
						padding:
							display.layout === 'hook'
								? '46px 54px'
								: display.layout === 'section'
									? '40px 48px'
									: '30px 34px',
						backdropFilter: 'blur(10px)',
						boxShadow: '0 22px 80px rgba(0,0,0,0.28)',
					}}
				>
					{display.highlight ? (
						<span
							style={{
								...baseTextStyle,
								display: 'inline-flex',
								alignItems: 'center',
								justifyContent: 'center',
								marginBottom: 18,
								padding: '8px 16px',
								borderRadius: 999,
								background: 'rgba(255,255,255,0.08)',
								border: `1px solid ${display.accent}`,
								color: display.accent,
								fontSize: 18,
								fontWeight: 700,
								letterSpacing: '0.12em',
							}}
						>
							{display.highlight}
						</span>
					) : null}
					<div
						style={{
							display: 'flex',
							alignItems: 'center',
							gap: 14,
							marginBottom: display.body ? 22 : 16,
							justifyContent:
								display.layout === 'hook' ? 'center' : 'flex-start',
						}}
					>
						<div
							style={{
								width: 54,
								height: 2,
								background: display.accent,
								boxShadow: `0 0 24px ${display.accent}`,
							}}
						/>
						<span
							style={{
								...baseTextStyle,
								color: display.accent,
								fontSize: 16,
								fontWeight: 700,
								letterSpacing: '0.24em',
								textTransform: 'uppercase',
							}}
						>
							{display.label}
						</span>
					</div>
					<h1
						style={{
								...baseTextStyle,
								textAlign: isCenteredLayout(display.layout) ? 'center' : 'left',
								fontSize: getHeadlineSize(display),
								lineHeight: 1.25,
								fontWeight: 700,
								maxWidth: isCenteredLayout(display.layout) ? 980 : 840,
								marginBottom: display.body ? 18 : 0,
							}}
					>
						{display.headline}
					</h1>
					{display.body ? (
						<p
							style={{
								...baseTextStyle,
								textAlign: isCenteredLayout(display.layout) ? 'center' : 'left',
								fontSize: display.layout === 'hook' ? 28 : 30,
								color: 'rgba(245,245,240,0.88)',
								maxWidth: isCenteredLayout(display.layout) ? 900 : 780,
							}}
						>
							{display.body}
						</p>
					) : null}
				</div>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

const buildSlideTimeline = (
	slides: SlideEntry[],
	totalDurationInFrames: number
): TimedSlideEntry[] => {
	if (slides.length === 0) {
		return [];
	}

	const slideDurations = buildSlideDurations(slides, totalDurationInFrames);
	let offset = 0;

	return slides.map((entry, i) => {
		const durationInFrames = slideDurations[i] ?? 1;
		const from = offset;
		offset += durationInFrames;

		return {
			entry,
			from,
			durationInFrames,
			slideIndex: i,
		};
	});
};

const SlidesTrack: React.FC<{
	slides: SlideEntry[];
	totalDurationInFrames: number;
}> = ({slides, totalDurationInFrames}) => {
	const frame = useCurrentFrame();
	const timeline = useMemo(
		() => buildSlideTimeline(slides, totalDurationInFrames),
		[slides, totalDurationInFrames]
	);

	if (timeline.length === 0) {
		return <AbsoluteFill style={{backgroundColor: '#0a0a0a'}} />;
	}

	const activeSlide =
		timeline.find(
			(item) => frame >= item.from && frame < item.from + item.durationInFrames
		) ?? timeline[timeline.length - 1];

	return (
			<Slide
				entry={activeSlide.entry}
				durationInFrames={activeSlide.durationInFrames}
				slideIndex={activeSlide.slideIndex}
				totalSlides={timeline.length}
				frame={frame - activeSlide.from}
			/>
		);
};

const BgmLoop: React.FC<{src: string; volume: number}> = ({src, volume}) => {
	const {durationInFrames, fps} = useVideoConfig();
	const bgmFrames = Math.floor(180 * fps);
	const loopCount = Math.ceil(durationInFrames / bgmFrames) + 1;
	const fadeFrames = Math.floor(2.5 * fps);
	return (
		<Loop durationInFrames={bgmFrames} times={loopCount}>
			<Audio
				src={staticFile(src)}
				volume={(f) => {
					if (f < fadeFrames) return (f / fadeFrames) * volume;
					if (f > bgmFrames - fadeFrames)
						return ((bgmFrames - f) / fadeFrames) * volume;
					return volume;
				}}
			/>
		</Loop>
	);
};

export const CanvaSlideshow: React.FC<CanvasSlideshowProps> = ({
	audioSrc,
	bgmSrc,
	bgmVolume = 0.15,
	slides,
}) => {
	const {durationInFrames} = useVideoConfig();
	return (
		<AbsoluteFill style={{backgroundColor: '#0a0a0a'}}>
			<Audio src={staticFile(audioSrc)} />
			{bgmSrc && <BgmLoop src={bgmSrc} volume={bgmVolume} />}
			<Sequence name="画像スライド" durationInFrames={durationInFrames}>
				<SlidesTrack
					slides={slides}
					totalDurationInFrames={durationInFrames}
				/>
			</Sequence>
		</AbsoluteFill>
	);
};
