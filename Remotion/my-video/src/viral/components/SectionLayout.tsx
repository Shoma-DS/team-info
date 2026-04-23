import React from 'react';
import { AbsoluteFill, useVideoConfig, useCurrentFrame, spring, interpolate } from 'remotion';
import { VIRAL_ADULT_AFFILIATE_FONT_FAMILY } from '../fonts';

interface SectionLayoutProps {
  title: string;
  imageSrc: string;
  photoSrc?: string;
  switchFrame?: number;
}

export const SectionLayout: React.FC<SectionLayoutProps> = ({
  title,
  imageSrc,
  photoSrc,
  switchFrame = 60
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // アニメーション: イラストのポップアップ効果
  const imageScale = spring({
    fps,
    frame: Math.max(0, frame - 5),
    config: { damping: 14, stiffness: 200 }
  });

  const textOpacity = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: 'clamp' });

  // 切り替え演出の定義
  const showPhoto = photoSrc && frame >= switchFrame;
  const transitionFrames = 10;
  
  // イラストの不透明度（写真が出る時に消える）
  const imageOpacity = interpolate(
    frame,
    [switchFrame, switchFrame + transitionFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // 写真の不透明度
  const photoOpacity = interpolate(
    frame,
    [switchFrame, switchFrame + transitionFrames],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <AbsoluteFill style={{ backgroundColor: '#FFFFFF', alignItems: 'center' }}>
      {/* セクションタイトル (上部) */}
      <div
        style={{
          position: 'absolute',
          top: '4%',
          width: '90%',
          textAlign: 'center',
          opacity: textOpacity,
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: 100,
            fontWeight: 900,
            fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
            color: '#000000',
            lineHeight: 1.2,
            letterSpacing: '0.01em',
          }}
        >
          {title}
        </h2>
      </div>

      {/* コンテンツエリア (中央) - イラストを文字に被らない最大サイズで表示 */}
      <AbsoluteFill style={{ top: '25%', height: '40%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        {/* イラスト */}
        <div
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            opacity: imageOpacity,
            // 文字に被らないギリギリの大きさに調整
            transform: `scale(${imageScale * 1.35})`,
            visibility: frame >= switchFrame + transitionFrames ? 'hidden' : 'visible'
          }}
        >
          <img
            src={imageSrc}
            style={{ 
              maxHeight: '100%', 
              maxWidth: '100%', 
              objectFit: 'contain',
            }}
          />
        </div>

        {/* 写真 (存在する場合のみ) */}
        {photoSrc && (
          <div
            style={{
              position: 'absolute',
              width: '100%',
              height: '100%',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              opacity: photoOpacity,
              visibility: frame < switchFrame ? 'hidden' : 'visible'
            }}
          >
            <img
              src={photoSrc}
              style={{ 
                width: '42%',
                height: 'auto',
                aspectRatio: '16/9',
                objectFit: 'cover',
                borderRadius: '8px',
                border: '3px solid #FFFFFF',
                boxShadow: '0 8px 25px rgba(0,0,0,0.1)'
              }}
            />
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
