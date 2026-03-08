import type { CSSProperties } from 'react';
import { Img, staticFile } from 'remotion';

type AcoRielWordmarkProps = {
	tone?: 'neutral' | 'light';
	style?: CSSProperties;
	detailFilter?: string;
	detailOpacity?: number;
};

export const AcoRielWordmark: React.FC<AcoRielWordmarkProps> = ({
	tone = 'neutral',
	style,
	detailFilter,
	detailOpacity = 1,
}) => {
	const detailSource = staticFile('assets/channels/acoriel/common/channel-wordmark.png');

	const detailLayerStyle: CSSProperties =
		tone === 'light'
			? {
				filter: detailFilter ?? 'invert(1) brightness(1.06)',
				opacity: detailOpacity,
			}
			: {
				filter: detailFilter ?? 'brightness(1.14) contrast(1.1)',
				opacity: detailOpacity,
			};

	const wrapperStyle: CSSProperties = {
		display: 'inline-block',
		lineHeight: 0,
		pointerEvents: 'none',
		...style,
	};

	const ghostStyle: CSSProperties = {
		display: 'block',
		width: style?.width ?? 'auto',
		height: style?.height ?? 'auto',
		objectFit: 'contain',
		opacity: 0,
		pointerEvents: 'none',
	};

	const overlayStyle: CSSProperties = {
		position: 'absolute',
		inset: 0,
		width: '100%',
		height: '100%',
		objectFit: 'contain',
		pointerEvents: 'none',
	};

	const markerStyle: CSSProperties =
		tone === 'light'
			? {
				position: 'absolute',
				left: '8%',
				right: '28%',
				top: '35%',
				height: '25%',
				background: 'rgba(7,9,12,0.74)',
				borderRadius: '4px 6px 4px 5px / 4px 3px 5px 3px',
				transform: 'rotate(-0.7deg) skewX(-3deg)',
				filter: 'blur(0.9px)',
				pointerEvents: 'none',
			}
			: {
				position: 'absolute',
				left: '8%',
				right: '28%',
				top: '35%',
				height: '25%',
				background: 'rgba(8,10,14,0.56)',
				borderRadius: '4px 6px 4px 5px / 4px 3px 5px 3px',
				transform: 'rotate(-0.7deg) skewX(-3deg)',
				filter: 'blur(0.75px)',
				pointerEvents: 'none',
			};

	return (
		<span
			style={{
				position: style?.position === 'absolute' ? 'absolute' : 'relative',
				...wrapperStyle,
			}}
		>
			<Img src={detailSource} style={ghostStyle} />
			<span style={markerStyle} />
			<Img
				src={detailSource}
				style={{
					...overlayStyle,
					...detailLayerStyle,
				}}
			/>
		</span>
	);
};
