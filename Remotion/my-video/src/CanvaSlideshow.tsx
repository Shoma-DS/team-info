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

type SlideEntry = {
	index: number;
	text: string;
	image: string | null;
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

const baseTextStyle: React.CSSProperties = {
	fontFamily: '"Noto Sans JP", "Hiragino Kaku Gothic ProN", sans-serif',
	color: '#f5f5f0',
	textAlign: 'center',
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

const Slide: React.FC<{
	entry: SlideEntry;
	durationInFrames: number;
	slideIndex: number;
	frame: number;
}> = ({entry, durationInFrames, slideIndex, frame}) => {
	const {fps} = useVideoConfig();
	const fadeFrames = Math.min(Math.floor(0.6 * fps), Math.floor(durationInFrames / 4));

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
					justifyContent: 'flex-end',
					alignItems: 'center',
					paddingBottom: 100,
					paddingLeft: 140,
					paddingRight: 140,
				}}
			>
				<p
					style={{
						...baseTextStyle,
						fontSize: entry.text.length > 60 ? 40 : 48,
						maxWidth: 1560,
						background: 'rgba(0,0,0,0.28)',
						borderRadius: 14,
						padding: '20px 36px',
						backdropFilter: 'blur(3px)',
						boxShadow: '0 0 40px rgba(255,245,220,0.12)',
					}}
				>
					{entry.text}
				</p>
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

	const slideDuration = Math.floor(totalDurationInFrames / slides.length);

	return slides.map((entry, i) => {
		const from = i * slideDuration;
		const durationInFrames =
			i === slides.length - 1 ? totalDurationInFrames - from : slideDuration;

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
			<Sequence durationInFrames={durationInFrames}>
				<SlidesTrack
					slides={slides}
					totalDurationInFrames={durationInFrames}
				/>
			</Sequence>
		</AbsoluteFill>
	);
};
