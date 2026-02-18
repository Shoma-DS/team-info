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
import { useMemo, useState, useEffect, type CSSProperties } from 'react';
import { getAudioData, visualizeAudioWaveform } from '@remotion/media-utils';
import { loadFont as loadHachiMaruPop } from '@remotion/google-fonts/HachiMaruPop';

const { fontFamily: hachiMaruPopFamily } = loadHachiMaruPop();
const yosugaraFontFace = new FontFace(
	'Yosugara',
	`url(${staticFile('assets/fonts/yosugaraver1_2.ttf')})`,
);
yosugaraFontFace.load().then((f) => document.fonts.add(f)).catch(() => { });
const yosugaraFamily = '"Yosugara", cursive';
const playwriteFamily = '"Playwrite NZ", "Playwrite NZ Basic", cursive';

if (typeof document !== 'undefined' && !document.getElementById('playwrite-nz-font-link')) {
	const link = document.createElement('link');
	link.id = 'playwrite-nz-font-link';
	link.rel = 'stylesheet';
	link.href =
		'https://fonts.googleapis.com/css2?family=Playwrite+NZ:wght@100..400&display=swap';
	document.head.appendChild(link);
}

type ScriptType = 'kanji' | 'hiragana' | 'latin';

const classifyChar = (char: string, prevType: ScriptType | null): ScriptType => {
	if (/[\p{Script=Hiragana}]/u.test(char)) return 'hiragana';
	if (/[A-Za-z0-9]/.test(char)) return 'latin';
	if (/[\p{Script=Han}]/u.test(char)) return 'kanji';
	if (/[\p{Script=Katakana}]/u.test(char)) return 'hiragana';
	return prevType ?? 'kanji';
};

const fontByScript = (type: ScriptType): string => {
	if (type === 'hiragana') return yosugaraFamily;
	if (type === 'latin') return playwriteFamily;
	return hachiMaruPopFamily;
};

const ScriptStyledText: React.FC<{ text: string }> = ({ text }) => {
	const chars = [...text];
	const segments: Array<{ type: ScriptType; text: string }> = [];
	let prevType: ScriptType | null = null;
	for (const ch of chars) {
		const type = classifyChar(ch, prevType);
		const last = segments[segments.length - 1];
		if (last && last.type === type) {
			last.text += ch;
		} else {
			segments.push({ type, text: ch });
		}
		prevType = type;
	}
	return (
		<>
			{segments.map((seg, i) => (
				<span key={`${seg.type}-${i}`} style={{ fontFamily: fontByScript(seg.type), whiteSpace: 'pre' }}>
					{seg.text}
				</span>
			))}
		</>
	);
};

// ── Song metadata (manually set per cover) ──────────────────
const SONG_TITLE = 'LOVE PHANTOM';
const SONG_ARTIST = "B'z";

// ── Typography ──────────────────────────────────────────────

const lyricsFont: CSSProperties = {
	fontFamily: hachiMaruPopFamily,
	letterSpacing: '0.04em',
	textAlign: 'center',
};

// ── Music Particles ─────────────────────────────────────────

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

				// Re-spawn with new random properties each cycle.
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

// Angel feathers – multiple small feathers falling continuously
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
						// drop-shadow follows the PNG alpha (text contour), not the image rectangle
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

	// Wider smoothing window for gentler motion
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
	const rx = barWidth / 2; // pill shape

	return (
		<svg
			width={width}
			height={1080}
			style={{ position: 'absolute', left: 0, top: 0, pointerEvents: 'none' }}
		>
			<defs>
				<linearGradient id="bar-grad-up" x1="0" y1="1" x2="0" y2="0">
					<stop offset="0%" stopColor="rgba(255,255,255,0.08)" />
					<stop offset="40%" stopColor="rgba(240,240,255,0.5)" />
					<stop offset="100%" stopColor="rgba(255,255,255,0.75)" />
				</linearGradient>
				<linearGradient id="bar-grad-down" x1="0" y1="0" x2="0" y2="1">
					<stop offset="0%" stopColor="rgba(255,255,255,0.06)" />
					<stop offset="100%" stopColor="rgba(240,240,255,0.02)" />
				</linearGradient>
				<filter id="spec-glow-soft">
					<feGaussianBlur in="SourceGraphic" stdDeviation="3.5" />
				</filter>
			</defs>

			{/* Soft glow layer */}
			<g filter="url(#spec-glow-soft)">
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

			{/* Main bars (upward) */}
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
						fill="url(#bar-grad-up)"
						opacity={0.45 + v * 0.5}
					/>
				);
			})}

			{/* Mirror bars (downward, subtle reflection) */}
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
						fill="url(#bar-grad-down)"
						opacity={0.2 + v * 0.15}
					/>
				);
			})}
		</svg>
	);
};

// ── Intro Overlay ───────────────────────────────────────────

// ── Handwriting Reveal ───────────────────────────────────────
// Reveals text left-to-right with a soft leading-edge glow,
// simulating a pen writing across the screen.

// Text reveal with left-to-right mask + optional feather pen
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

			{/* Pen-tip glow */}
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

			{/* Feather pen */}
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

// ── Line schedule for sequential handwriting ────────────────
// Each line: { startFrame, writeFrames, yOffset (px from center) }
// Total must fit within 5 sec (150 frames @30fps).
// Line 1: Acoustic Cover       – fast
// Line 2: Song title            – slower
// Line 3: Original by …        – fast
// Line 4: Covered by + wordmark – fast
const LINE_SCHEDULE = [
	{ start: 0, write: 18 },   // Line 1 (0–18)
	{ start: 20, write: 55 },  // Line 2 (20–75) ← ゆっくり
	{ start: 77, write: 18 },  // Line 3 (77–95)
	{ start: 97, write: 18 },  // Line 4 (97–115)
] as const;

const IntroOverlay: React.FC<{
	title: string;
	artist: string;
	durationFrames: number;
}> = ({ title, artist, durationFrames }) => {
	const frame = useCurrentFrame();
	const wordmark = staticFile('assets/channel-wordmark.png');
	const featherPen = staticFile('assets/feather_pen.png');

	// Overall fade in / fade out
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

	// Determine which line is currently being written (for pen display)
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
				{/* Line 1: Acoustic Cover */}
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

				{/* Line 2: Song title */}
				<TextReveal
					startFrame={LINE_SCHEDULE[1].start}
					writeFrames={LINE_SCHEDULE[1].write}
					{...penProps(1)}
				>
					<span
						style={{
							fontFamily: yosugaraFamily,
							fontSize: 125,
							fontWeight: 400,
							color: '#e8dcc0',
							textShadow:
								'0 0 30px rgba(212,196,144,0.35), 0 2px 40px rgba(212,196,144,0.15)',
							lineHeight: 1.45,
							paddingBottom: 10,
							letterSpacing: '0.04em',
							whiteSpace: 'nowrap',
						}}
					>
						<ScriptStyledText text={title} />
					</span>
				</TextReveal>

				{/* Line 3: Original by */}
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
						<ScriptStyledText text={`Original by ${artist}`} />
					</span>
				</TextReveal>

				{/* Divider – appears with line 4 */}
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

				{/* Line 4: Covered by + wordmark */}
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
					<ScriptStyledText text="チャンネル登録よろしくお願いします" />
				</span>
			</div>
		</AbsoluteFill>
	);
};

// ── Main Composition ────────────────────────────────────────

export const AcoRielCover: React.FC = () => {
	const frame = useCurrentFrame();
	const { durationInFrames, fps } = useVideoConfig();

	// Intro/Outro timing
	const introFrames = Math.floor(7 * fps); // 7 seconds
	const outroFrames = Math.floor(8 * fps); // 8 seconds
	const outroStart = durationInFrames - outroFrames;

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

			{/* Pencil writing sound – fades out when text finishes writing (~115f) */}
			<Sequence durationInFrames={introFrames}>
				<Audio
					src={staticFile('assets/write_with_pencil.mp3')}
					volume={(f) => {
						// Fade out around frame 100-120 (when last line finishes)
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
			<Sequence from={introFrames}>
				<Audio src={staticFile('assets/audio.wav')} />
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

			{/* Outro */}
			<Sequence from={outroStart} durationInFrames={outroFrames}>
				<OutroOverlay durationFrames={outroFrames} />
			</Sequence>
		</AbsoluteFill>
	);
};
