import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { ImageScene } from "../components/ImageScene";
import {
  VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
  useViralAdultAffiliateFont,
} from "../fonts";

const TITLE = "会社に見切りをつける直前の人の特徴9選_20260412";
const TOTAL_FRAMES = 11594;
const FPS = 30;
const FADE_FRAMES = 18;

const SCENES = [
  {
    key: "hook",
    from: 0,
    to: 1080,
    src: staticFile(`viral/${TITLE}/materials/00_hook.jpg`),
    motionType: "zoom_in" as const,
    motionProfile: "gentle" as const,
    motionIntensity: 0.2,
    label: "もう頑張れない",
    subLabel: "会社に見切りをつける直前の人の特徴9選",
  },
  {
    key: "section1",
    from: 1080,
    to: 4320,
    src: staticFile(`viral/${TITLE}/materials/01_main_1.jpg`),
    motionType: "pan_right" as const,
    motionProfile: "gentle" as const,
    motionIntensity: 0.18,
    label: "SECTION 1",
    subLabel: "気力・集中・反応",
  },
  {
    key: "section2",
    from: 4320,
    to: 7560,
    src: staticFile(`viral/${TITLE}/materials/02_main_2.jpg`),
    motionType: "pan_left" as const,
    motionProfile: "gentle" as const,
    motionIntensity: 0.18,
    label: "SECTION 2",
    subLabel: "人間関係・評価・将来像",
  },
  {
    key: "section3",
    from: 7560,
    to: 10440,
    src: staticFile(`viral/${TITLE}/materials/03_main_3.jpg`),
    motionType: "zoom_out" as const,
    motionProfile: "gentle" as const,
    motionIntensity: 0.16,
    label: "SECTION 3",
    subLabel: "生活・感覚・決断の手前",
  },
  {
    key: "cta",
    from: 10440,
    to: TOTAL_FRAMES,
    src: staticFile(`viral/${TITLE}/materials/99_cta.jpg`),
    motionType: "static" as const,
    motionProfile: "still" as const,
    motionIntensity: 0,
    label: "SAVE",
    subLabel: "あとで見返してください",
  },
];

const CIRCLE_NUMS = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨"];

const POINT_CARD_DATA = [
  {
    circle: CIRCLE_NUMS[0],
    title: "頑張る前に、もう疲れている",
    detail: "気力が戻る前に次の仕事が来て\nずっと空回りしている状態です",
    img: staticFile(`viral/${TITLE}/materials/01_main_1.jpg`),
    from: 1200, to: 1980,
  },
  {
    circle: CIRCLE_NUMS[1],
    title: "仕事の話を聞くだけで、気分が沈む",
    detail: "話を聞いた瞬間に気持ちが落ちるのは\n心が拒否反応を起こしているサインです",
    img: staticFile(`viral/${TITLE}/materials/01_main_1.jpg`),
    from: 2040, to: 2820,
  },
  {
    circle: CIRCLE_NUMS[2],
    title: "ミスやトラブルに反応しなくなった",
    detail: "感情が動かなくなるのは\n心が自分を守るために麻痺しているからです",
    img: staticFile(`viral/${TITLE}/materials/01_main_1.jpg`),
    from: 2880, to: 3600,
  },
  {
    circle: CIRCLE_NUMS[3],
    title: "職場の人に、何も期待しなくなった",
    detail: "期待がなくなると関わりも薄れていきます\n職場への帰属意識が消えているサインです",
    img: staticFile(`viral/${TITLE}/materials/02_main_2.jpg`),
    from: 4440, to: 5280,
  },
  {
    circle: CIRCLE_NUMS[4],
    title: "評価されなくても、悔しくなくなった",
    detail: "悔しいと思えなくなったのは\n成長への意欲が完全に途切れているからです",
    img: staticFile(`viral/${TITLE}/materials/02_main_2.jpg`),
    from: 5340, to: 6120,
  },
  {
    circle: CIRCLE_NUMS[5],
    title: "今の会社にいる数年後が想像できない",
    detail: "未来が見えない職場に居続けると\n無意識に別の道を探し始めています",
    img: staticFile(`viral/${TITLE}/materials/02_main_2.jpg`),
    from: 6180, to: 6960,
  },
  {
    circle: CIRCLE_NUMS[6],
    title: "休みの日にまで、回復しかしていない",
    detail: "2日休んでも疲れが取れないなら\n体と心はとっくに限界を超えています",
    img: staticFile(`viral/${TITLE}/materials/03_main_3.jpg`),
    from: 7680, to: 8520,
  },
  {
    circle: CIRCLE_NUMS[7],
    title: "転職した人の話を、前より真剣に聞いてしまう",
    detail: "他人事だった転職の話がリアルに聞こえたら\n気持ちがそちらへ向いているサインです",
    img: staticFile(`viral/${TITLE}/materials/03_main_3.jpg`),
    from: 8580, to: 9360,
  },
  {
    circle: CIRCLE_NUMS[8],
    title: "辞めたいより、ここではないと感じる",
    detail: "「辞めたい」は感情ですが\n「ここではない」は確信に近い感覚です",
    img: staticFile(`viral/${TITLE}/materials/03_main_3.jpg`),
    from: 9420, to: 10200,
  },
];

/** 参考動画スタイル: 白背景 + 赤太字テロップ + いらすとやキャラ */
const WhiteCardHook: React.FC = () => {
  const frame = useCurrentFrame();
  const HOOK_END = 420;
  if (frame >= HOOK_END) return null;

  const fadeIn = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = interpolate(frame, [HOOK_END - 15, HOOK_END], [1, 0], {
    extrapolateLeft: "clamp",
  });
  const opacity = Math.min(fadeIn, fadeOut);

  const bounce = spring({ fps: FPS, frame, config: { damping: 12, stiffness: 180 } });
  const scale = interpolate(bounce, [0, 1], [0.82, 1]);

  const lines = ["会社に見切りをつける", "直前の人の特徴9選"];

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#ffffff",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-start",
        paddingTop: 56,
        pointerEvents: "none",
        opacity,
      }}
    >
      {/* テキスト部分 */}
      <div
        style={{
          transform: `scale(${scale})`,
          textAlign: "center",
        }}
      >
        {lines.map((line, i) => (
          <div
            key={i}
            style={{
              fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
              fontSize: 102,
              fontWeight: 900,
              color: "#e8150c",
              lineHeight: 1.25,
              letterSpacing: "0.02em",
            }}
          >
            {line}
          </div>
        ))}
      </div>
      {/* いらすとや キャラクター */}
      <img
        src={staticFile(`viral/${TITLE}/materials/hook_illust.png`)}
        style={{
          marginTop: 28,
          height: 320,
          objectFit: "contain",
        }}
      />
    </AbsoluteFill>
  );
};

const SceneImage: React.FC<{ scene: (typeof SCENES)[number] }> = ({ scene }) => {
  return (
    <ImageScene
      src={scene.src}
      motionType={scene.motionType}
      motionProfile={scene.motionProfile}
      motionIntensity={scene.motionIntensity}
      originX={0.52}
      originY={0.48}
    />
  );
};

const BackgroundTrack: React.FC = () => {
  const frame = useCurrentFrame();
  const currentIndex = SCENES.findIndex((scene) => frame >= scene.from && frame < scene.to);
  const safeIndex = currentIndex >= 0 ? currentIndex : SCENES.length - 1;
  const current = SCENES[safeIndex];
  const previous = safeIndex > 0 ? SCENES[safeIndex - 1] : null;
  const relativeFrame = frame - current.from;
  const fading = previous !== null && relativeFrame < FADE_FRAMES;
  const opacity = fading ? relativeFrame / FADE_FRAMES : 1;

  return (
    <AbsoluteFill>
      {fading && previous ? (
        <AbsoluteFill style={{ opacity: 1 - opacity }}>
          <SceneImage scene={previous} />
        </AbsoluteFill>
      ) : null}
      <AbsoluteFill style={{ opacity }}>
        <SceneImage scene={current} />
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(8,14,24,0.12) 0%, rgba(8,14,24,0.34) 58%, rgba(8,14,24,0.68) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

/** セクション中（フック後〜CTA前）は白背景で画面を覆う */
const SectionWhiteBg: React.FC = () => {
  const frame = useCurrentFrame();
  if (frame < 1080 || frame >= 10440) return null;
  return <AbsoluteFill style={{ backgroundColor: "#ffffff" }} />;
};

/** 各ポイントを「番号+タイトル / 画像 / 詳細テロップ」のカード形式で表示 */
const PointCardScene: React.FC = () => {
  const frame = useCurrentFrame();
  const card = POINT_CARD_DATA.find((c) => frame >= c.from && frame < c.to);
  if (!card) return null;

  const localFrame = frame - card.from;
  const duration = card.to - card.from;
  const opacity = interpolate(
    localFrame,
    [0, 8, duration - 12, duration],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const detailLines = card.detail.split("\n");

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#ffffff",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        paddingTop: 50,
        pointerEvents: "none",
        opacity,
      }}
    >
      {/* 番号 + タイトル */}
      <div
        style={{
          fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
          fontSize: 58,
          fontWeight: 900,
          color: "#1a1a1a",
          textAlign: "center",
          lineHeight: 1.3,
          maxWidth: 1100,
          paddingLeft: 24,
          paddingRight: 24,
        }}
      >
        {card.circle}{card.title}
      </div>
      {/* 画像: objectFit contain で引き伸ばさず表示 */}
      <img
        src={card.img}
        style={{
          marginTop: 28,
          width: 620,
          height: 310,
          objectFit: "contain",
          borderRadius: 14,
          background: "#f5f5f5",
        }}
      />
      {/* 詳細テロップ */}
      <div style={{ marginTop: 28, textAlign: "center" }}>
        {detailLines.map((line, i) => (
          <div
            key={i}
            style={{
              fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
              fontSize: 36,
              fontWeight: 600,
              color: "#333333",
              lineHeight: 1.65,
            }}
          >
            {line}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};


const ClosingCard: React.FC = () => {
  const frame = useCurrentFrame();
  const ctaScene = SCENES[SCENES.length - 1];
  if (frame < ctaScene.from) {
    return null;
  }

  const localFrame = frame - ctaScene.from;
  const opacity = interpolate(localFrame, [0, 18], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          opacity,
        }}
      >
        <div
          style={{
            width: 760,
            padding: "34px 42px",
            borderRadius: 36,
            background: "rgba(255,255,255,0.14)",
            border: "1px solid rgba(255,255,255,0.22)",
            textAlign: "center",
            boxShadow: "0 30px 60px rgba(0,0,0,0.18)",
          }}
        >
          <div
            style={{
              color: "#ffffff",
              fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
              fontSize: 48,
              fontWeight: 900,
              lineHeight: 1.2,
            }}
          >
            当てはまるものがあったら
          </div>
          <div
            style={{
              color: "#fff0b5",
              fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
              fontSize: 54,
              fontWeight: 900,
              lineHeight: 1.2,
              marginTop: 12,
            }}
          >
            保存して見返してください
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const JobChangeViralHorizontal20260412: React.FC = () => {
  useViralAdultAffiliateFont();

  return (
    <AbsoluteFill style={{ backgroundColor: "#0b1220" }}>
      {/* フック・CTA 用背景画像（セクション中は SectionWhiteBg で上書き） */}
      <Sequence durationInFrames={TOTAL_FRAMES}>
        <BackgroundTrack />
      </Sequence>
      {/* セクション中は白背景 */}
      <Sequence durationInFrames={TOTAL_FRAMES}>
        <SectionWhiteBg />
      </Sequence>
      {/* フックテロップ */}
      <Sequence durationInFrames={420}>
        <WhiteCardHook />
      </Sequence>
      {/* 各ポイントカード */}
      <Sequence durationInFrames={TOTAL_FRAMES}>
        <PointCardScene />
      </Sequence>
      {/* CTA */}
      <Sequence durationInFrames={TOTAL_FRAMES}>
        <ClosingCard />
      </Sequence>
      <Sequence durationInFrames={TOTAL_FRAMES}>
        <Audio src={staticFile(`viral/${TITLE}/audio/narration.mp3`)} volume={1} />
      </Sequence>
    </AbsoluteFill>
  );
};
