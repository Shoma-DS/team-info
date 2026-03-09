import {
	AbsoluteFill,
	Audio,
	Img,
	interpolate,
	Sequence,
	staticFile,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import {useMemo} from 'react';

// ===== 型定義 =====
type SlideEntry = {
	index: number;
	text: string;
	image: string; // Remotion/my-video/public/ からの相対パス
};

type CanvasSlideshowProps = {
	audioSrc: string;         // 音声ファイルパス (staticFile 用)
	manifestSrc: string;      // manifest.json パス (staticFile 用)
	slides: SlideEntry[];     // manifest.json の内容を直接渡す
};

// ===== テキストスタイル =====
const baseTextStyle: React.CSSProperties = {
	fontFamily: '"Noto Sans JP", "Hiragino Kaku Gothic ProN", sans-serif',
	color: '#f5f5f0',
	textAlign: 'center',
	lineHeight: 1.7,
	letterSpacing: '0.04em',
};

// ===== スライド1枚コンポーネント =====
const Slide: React.FC<{
	entry: SlideEntry;
	durationInFrames: number;
}> = ({entry, durationInFrames}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const fadeFrames = Math.floor(0.5 * fps); // 0.5秒フェード

	const opacity = interpolate(
		frame,
		[0, fadeFrames, durationInFrames - fadeFrames, durationInFrames],
		[0, 1, 1, 0],
		{extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
	);

	// ズームイン効果
	const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.04], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	return (
		<AbsoluteFill style={{opacity}}>
			{/* スライド画像 */}
			<Img
				src={staticFile(entry.image)}
				style={{
					width: '100%',
					height: '100%',
					objectFit: 'cover',
					transform: `scale(${scale})`,
				}}
			/>
			{/* テキストオーバーレイ */}
			<AbsoluteFill
				style={{
					background:
						'linear-gradient(to top, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.1) 60%, rgba(0,0,0,0) 100%)',
					justifyContent: 'flex-end',
					alignItems: 'center',
					paddingBottom: 80,
					paddingLeft: 120,
					paddingRight: 120,
				}}
			>
				<p
					style={{
						...baseTextStyle,
						fontSize: 44,
						maxWidth: 1600,
						background: 'rgba(0,0,0,0.3)',
						borderRadius: 12,
						padding: '16px 32px',
						backdropFilter: 'blur(2px)',
					}}
				>
					{entry.text}
				</p>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

// ===== メインコンポーネント =====
export const CanvaSlideshow: React.FC<CanvasSlideshowProps> = ({
	audioSrc,
	slides,
}) => {
	const {durationInFrames} = useVideoConfig();

	// 各スライドの表示フレーム数を均等分割
	const slideDuration = useMemo(
		() => Math.floor(durationInFrames / Math.max(slides.length, 1)),
		[durationInFrames, slides.length]
	);

	return (
		<AbsoluteFill style={{backgroundColor: '#0d0d0d'}}>
			{/* 音声 */}
			<Audio src={staticFile(audioSrc)} />

			{/* スライド */}
			{slides.map((entry, i) => {
				const from = i * slideDuration;
				// 最後のスライドは残り全フレームを使う
				const dur =
					i === slides.length - 1
						? durationInFrames - from
						: slideDuration;
				return (
					<Sequence key={entry.index} from={from} durationInFrames={dur}>
						<Slide entry={entry} durationInFrames={dur} />
					</Sequence>
				);
			})}
		</AbsoluteFill>
	);
};
