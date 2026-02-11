import {
	AbsoluteFill,
	Audio,
	Easing,
	Img,
	Sequence,
	continueRender,
	delayRender,
	interpolate,
	staticFile,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import {useMemo, useState, useEffect, type CSSProperties} from 'react';
import {getAudioData, useAudioData, visualizeAudioWaveform} from '@remotion/media-utils';

type SubtitleSegment = {
	start: number;
	end: number;
	text: string;
};

const baseTextStyles: CSSProperties = {
	color: 'rgba(245,245,245,0.96)',
	textShadow:
		'0 0 10px rgba(255,255,255,0.42), 0 0 26px rgba(255,220,170,0.36), 0 2px 10px rgba(0,0,0,0.72)',
	fontSize: 44,
	lineHeight: 1.5,
	fontFamily:
		'"Hiragino Mincho ProN","Yu Mincho","Noto Serif JP","Times New Roman",serif',
	letterSpacing: '0.03em',
};

const getSubtitleSentences = (rawText: string): string[] => {
	const stripped = rawText
		.replace(/^#{1,6}\s.*$/gm, '')
		.replace(/^\s*[-*]\s+/gm, '')
		.replace(/\r/g, '')
		.trim();
	if (!stripped) {
		return [];
	}

	return stripped
		.split(/(?<=[。！？\n])/u)
		.map((s) => s.replace(/\n+/g, ' ').trim())
		.filter((s) => s.length > 0);
};

const buildSubtitleSegments = (
	rawText: string,
	durationInFrames: number
): SubtitleSegment[] => {
	const sentences = getSubtitleSentences(rawText);
	if (sentences.length === 0) {
		return [];
	}

	const totalChars = sentences.reduce((sum, s) => sum + s.length, 0);
	let cursor = 0;
	const segments: SubtitleSegment[] = [];

	for (const sentence of sentences) {
		const ratio = sentence.length / Math.max(totalChars, 1);
		const chunk = Math.max(20, Math.floor(durationInFrames * ratio));
		const start = cursor;
		const end = Math.min(durationInFrames, start + chunk);
		segments.push({start, end, text: sentence});
		cursor = end;
	}

	if (segments.length > 0) {
		segments[segments.length - 1] = {
			...segments[segments.length - 1],
			end: durationInFrames,
		};
	}

	return segments;
};

type Sparkle = {
	x: number;
	y: number;
	size: number;
	delay: number;
	cycle: number;
};

const useLightweightAudioData = (src: string) => {
	const [audioData, setAudioData] = useState<Awaited<ReturnType<typeof getAudioData>> | null>(null);

	useEffect(() => {
		const handle = delayRender(`Waiting for audio metadata with src="${src}" to be loaded`, {
			timeoutInMilliseconds: 180000,
		});

		getAudioData(src, {sampleRate: 6000})
			.then((data) => {
				setAudioData(data);
			})
			.catch((err) => {
				console.error('Failed to load audio data for spectrum:', err);
				setAudioData(null);
			})
			.finally(() => {
				continueRender(handle);
			});
	}, [src]);

	return audioData;
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

const Sparkles: React.FC = () => {
	const frame = useCurrentFrame();
	const sparkles = useMemo(() => {
		const rnd = seedRand(20260212);
		return new Array(36).fill(null).map((): Sparkle => {
			return {
				x: 0.12 + rnd() * 0.76,
				y: 0.18 + rnd() * 0.66,
				size: 2 + rnd() * 4.5,
				delay: Math.floor(rnd() * 240),
				cycle: 130 + Math.floor(rnd() * 180),
			};
		});
	}, []);

	return (
		<AbsoluteFill>
			{sparkles.map((s, i) => {
				const local = (frame + s.delay) % s.cycle;
				const fadeIn = 18;
				const fadeOutStart = s.cycle - 30;
				let opacity = 0;
				if (local < fadeIn) {
					opacity = local / fadeIn;
				} else if (local > fadeOutStart) {
					opacity = 1 - (local - fadeOutStart) / (s.cycle - fadeOutStart);
				} else {
					opacity = 1;
				}
				const shimmer = 0.75 + Math.sin((frame + i * 13) / 22) * 0.25;
				const finalOpacity = opacity * shimmer * 0.35;

				return (
					<div
						key={i}
						style={{
							position: 'absolute',
							left: `${s.x * 100}%`,
							top: `${s.y * 100}%`,
							width: s.size,
							height: s.size,
							borderRadius: '50%',
							background: 'rgba(255,235,200,0.9)',
							boxShadow: '0 0 10px rgba(255,200,120,0.5)',
							opacity: finalOpacity,
							transform: `translate(-50%, -50%) scale(${0.7 + shimmer * 0.45})`,
						}}
					/>
				);
			})}
		</AbsoluteFill>
	);
};

const Spectrum: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps, width, height} = useVideoConfig();
	const dotCount = 72;
	const spectrumSamples = 120;
	const dotDirections = useMemo(() => {
		return new Array(dotCount).fill(null).map((_, i) => {
			const a = (i / dotCount) * Math.PI * 2;
			return {cos: Math.cos(a), sin: Math.sin(a)};
		});
	}, [dotCount]);
	const barDirections = useMemo(() => {
		return new Array(spectrumSamples).fill(null).map((_, i) => {
			const a = (i / spectrumSamples) * Math.PI * 2;
			return {cos: Math.cos(a), sin: Math.sin(a)};
		});
	}, [spectrumSamples]);
	const audioData = useLightweightAudioData(staticFile('assets/audio.mp3'));
	if (!audioData) {
		return null;
	}

	const points = visualizeAudioWaveform({
		audioData,
		frame,
		fps,
		numberOfSamples: spectrumSamples,
		windowInSeconds: 0.48,
		normalize: true,
	});

	const smoothed = points.map((_, i) => {
		let sum = 0;
		let count = 0;
		for (let j = -2; j <= 2; j++) {
			const idx = i + j;
			if (idx >= 0 && idx < points.length) {
				sum += Math.max(0, points[idx]);
				count++;
			}
		}
		const avg = count > 0 ? sum / count : 0;
		return Math.pow(avg, 0.7);
	});

	const level = smoothed.reduce((acc, v) => acc + v, 0) / Math.max(smoothed.length, 1);
	const cx = width / 2;
	const cy = height / 2;
	const radius = Math.min(width, height) * 0.24;
	const spinDeg = frame * 0.092;

	return (
		<svg
			width={width}
			height={height}
			style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none'}}
		>
			<defs>
				<filter id="spectrum-glow" x="-40%" y="-40%" width="180%" height="180%">
					<feGaussianBlur in="SourceGraphic" stdDeviation="5.2" result="blur-strong" />
					<feGaussianBlur in="SourceGraphic" stdDeviation="2.4" result="blur-soft" />
					<feMerge>
						<feMergeNode in="blur-strong" />
						<feMergeNode in="blur-soft" />
						<feMergeNode in="SourceGraphic" />
					</feMerge>
				</filter>
			</defs>

			<circle
				cx={cx}
				cy={cy}
				r={radius}
				fill="none"
				stroke="rgba(255,255,255,0.2)"
				strokeWidth={2}
			/>

			<g filter="url(#spectrum-glow)" transform={`rotate(${spinDeg} ${cx} ${cy})`}>
				{dotDirections.map((dir, i) => {
					const x = cx + dir.cos * radius;
					const y = cy + dir.sin * radius;
					const dotR = 2.7 + level * 0.9;
					return (
						<circle
							key={`dot-${i}`}
							cx={x}
							cy={y}
							r={dotR}
							fill="rgba(255,255,255,0.92)"
						/>
					);
				})}

				{smoothed.map((v, i) => {
					const dir = barDirections[i];
					const outer = radius + 8;
					const length = 16 + v * 78;
					const inner = outer - length;
					const x1 = cx + dir.cos * inner;
					const y1 = cy + dir.sin * inner;
					const x2 = cx + dir.cos * outer;
					const y2 = cy + dir.sin * outer;
					const sw = 6.6 + v * 5.8;

					return (
						<line
							key={`bar-${i}`}
							x1={x1}
							y1={y1}
							x2={x2}
							y2={y2}
							stroke="rgba(255,255,255,0.88)"
							strokeWidth={sw}
							strokeLinecap="round"
							opacity={0.5 + v * 0.42}
						/>
					);
				})}
			</g>
		</svg>
	);
};

export const SleepTravelLong: React.FC = () => {
	const frame = useCurrentFrame();
	const {durationInFrames, fps} = useVideoConfig();
	const bgmData = useAudioData(staticFile('assets/bgm.mp3'));
	const [script, setScript] = useState('');

	useEffect(() => {
		fetch(staticFile('assets/script.md'))
			.then((res) => res.text())
			.then((txt) => setScript(txt))
			.catch(() => {
				setScript('');
			});
	}, []);

	const subtitles = useMemo(
		() => buildSubtitleSegments(script, durationInFrames),
		[script, durationInFrames]
	);

	const currentSubtitle = subtitles.find(
		(s) => frame >= s.start && frame < s.end
	);
	const subtitleOpacity = (() => {
		if (!currentSubtitle) {
			return 0;
		}
		const fade = Math.min(18, Math.floor((currentSubtitle.end - currentSubtitle.start) / 3));
		const local = frame - currentSubtitle.start;
		const remain = currentSubtitle.end - frame;
		if (local < fade) {
			return local / Math.max(fade, 1);
		}
		if (remain < fade) {
			return remain / Math.max(fade, 1);
		}
		return 1;
	})();

	const bgmSegmentFrames = Math.max(
		Math.floor((bgmData?.durationInSeconds ?? 90) * fps),
		Math.floor(20 * fps)
	);
	const fadeFrames = Math.floor(2.5 * fps);
	const stepFrames = Math.max(1, bgmSegmentFrames - fadeFrames);
	const loopCount = Math.ceil(durationInFrames / stepFrames) + 1;

	const panX = Math.sin((frame / fps) * 0.03) * 1.5;
	const panY = Math.cos((frame / fps) * 0.02) * 1.2;
	const zoom = 1.03 + Math.sin((frame / fps) * 0.015) * 0.015;

	return (
		<AbsoluteFill style={{backgroundColor: '#080808'}}>
			<Img
				src={staticFile('assets/background.png')}
				style={{
					width: '100%',
					height: '100%',
					objectFit: 'cover',
					filter: 'brightness(0.58) saturate(0.9)',
					transform: `scale(${zoom}) translate(${panX}%, ${panY}%)`,
				}}
			/>
			<AbsoluteFill
				style={{
					background:
						'radial-gradient(circle at 50% 78%, rgba(255,140,40,0.08), rgba(0,0,0,0.58))',
				}}
			/>
			<Sparkles />

			<Audio src={staticFile('assets/audio.mp3')} />
			{new Array(loopCount).fill(null).map((_, i) => {
				const from = i * stepFrames;
				return (
					<Sequence key={i} from={from} durationInFrames={bgmSegmentFrames}>
						<Audio
							src={staticFile('assets/bgm.mp3')}
							volume={(f) => {
								if (f < fadeFrames) {
									return (f / fadeFrames) * 0.11;
								}
								if (f > bgmSegmentFrames - fadeFrames) {
									return (
										((bgmSegmentFrames - f) / fadeFrames) *
										0.11
									);
								}
								return 0.11;
							}}
						/>
					</Sequence>
				);
			})}

			<Spectrum />

			<AbsoluteFill
				style={{
					justifyContent: 'flex-end',
					alignItems: 'center',
					paddingBottom: 130,
					pointerEvents: 'none',
				}}
			>
				<div
					style={{
						...baseTextStyles,
						maxWidth: 1540,
						textAlign: 'center',
						padding: '18px 28px',
						borderRadius: 16,
						background: 'rgba(0,0,0,0.26)',
						backdropFilter: 'blur(2px)',
						filter: 'drop-shadow(0 0 10px rgba(255,245,220,0.45))',
						opacity: subtitleOpacity,
						transform: `translateY(${interpolate(
							subtitleOpacity,
							[0, 1],
							[12, 0],
							{
								extrapolateLeft: 'clamp',
								extrapolateRight: 'clamp',
								easing: Easing.out(Easing.cubic),
							}
						)}px)`,
					}}
				>
					{currentSubtitle?.text ?? ''}
				</div>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
