import React from 'react';
import { AbsoluteFill, useVideoConfig, useCurrentFrame, spring, interpolate } from 'remotion';
import { VIRAL_ADULT_AFFILIATE_FONT_FAMILY } from '../fonts';

interface SectionLayoutProps {
  title:
 string;
  imageSrc:
 string;
}

export const SectionLayout: React.FC<SectionLayoutProps> = ({
  title,
  imageSrc
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // アニメーション: ポップアップ効果
  const imageScale = spring({
    fps,
    frame: Math.max(0, frame - 5), // ちょっと遅らせて表示
    config: { damping: 14, stiffness: 200 }
  });

  const textOpacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: 'clamp' });
  const textY = interpolate(frame, [0, 15], [30, 0], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ backgroundColor: '#FAFAFA', alignItems: 'center' }}>
      {/* セクションタイトル (上部) */}
      <div
        style={{
          position: 'absolute',
          top: '12%',
          width: '90%',
          textAlign: 'center',
          opacity: textOpacity,
          transform: `translateY(${textY}px)`,
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: 76,
            fontWeight: 900,
            fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
            color: '#2C3E50',
            lineHeight: 1.3,
            letterSpacing: '0.04em',
            // 軽く白フチ＆ドロップシャドウで読みやすく
            WebkitTextStroke: '6px #FFFFFF',
            textShadow: '0 8px 15px rgba(0,0,0,0.15)',
          }}
        >
          <span style={{ 
            position: 'absolute', top: 0, left: 0, width: '100%', 
            color: '#2C3E50', WebkitTextStroke: '0px' 
          }}>
            {title}
          </span>
          {title}
        </h2>
      </div>

      {/* いらすとや画像 (中央) */}
      <div
        style={{
          position: 'absolute',
          top: '32%',
          height: '42%',
          width: '90%',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          transform: `scale(${imageScale})`
        }}
      >
        <img
          src={imageSrc}
          style={{ 
            maxHeight: '100%', 
            maxWidth: '100%', 
            objectFit: 'contain',
            filter: 'drop-shadow(0 15px 25px rgba(0,0,0,0.1))'
          }}
        />
      </div>

      {/* 下部は SubtitleTrack のために空けておく (yPercent: 78 程度を想定) */}
    </AbsoluteFill>
  );
};
