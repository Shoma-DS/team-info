/**
 * TenshokuShort20260416.tsx — 【そりゃ辞めるわ】優秀な人が黙って去る会社の特徴3選
 * 生成日: 2026-04-16 | 尺: 79.8秒
 */
import React from "react";
import { staticFile } from "remotion";
import { SUBTITLE_TIMELINE } from "./generated/TenshokuShort20260416Subtitles";
import { ViralTemplate } from "./components/ViralTemplate";
import { useViralAdultAffiliateFont } from "./fonts";

export const TenshokuShort20260416: React.FC = () => {
  useViralAdultAffiliateFont();
  const totalFrames = 2394;

  return (
    <ViralTemplate
      totalFrames={totalFrames}
      audioSrc={staticFile("audio/転職ショート_20260416/narration.wav")}
      subtitles={SUBTITLE_TIMELINE}
      hook={{
        text: "優秀な人が黙って去る会社\nの特徴3選",
        imageSrc: staticFile("viral/転職ショート_20260416/hook.png"),
        durationFrames: 240,
        callouts: [
          {
            fromFrame: 118,
            text: "一つでも当てはまったら\n今の会社は危険かも",
            imageSrc: staticFile("viral/転職ショート_20260416/hook_illust.png"),
          },
        ],
      }}
      sections={[
        {
          title: "① 現場の意見が完全スルーされる",
          imageSrc: staticFile("viral/転職ショート_20260416/s1.png"),
          photoSrc: staticFile("viral/転職ショート_20260416/p1.png"),
          visuals: [
            { fromFrame: 0, kind: "illustration", src: staticFile("viral/転職ショート_20260416/s1.png") },
            { fromFrame: 77, kind: "photo", src: staticFile("viral/転職ショート_20260416/p1.png") },
            { fromFrame: 238, kind: "illustration", src: staticFile("viral/転職ショート_20260416/illust_mushi_business.png") },
            { fromFrame: 387, kind: "illustration", src: staticFile("viral/転職ショート_20260416/illust_kazetooshi_bad.png") },
            { fromFrame: 506, kind: "illustration", src: staticFile("viral/転職ショート_20260416/illust_jinzai_hikinuki.png") },
          ],
          fromFrame: 240,
          durationFrames: 905 - 240,
          switchFrame: 90,
        },
        {
          title: "② 頑張った分だけ損をする評価",
          imageSrc: staticFile("viral/転職ショート_20260416/s2.png"),
          photoSrc: staticFile("viral/転職ショート_20260416/p2.png"),
          visuals: [
            { fromFrame: 0, kind: "illustration", src: staticFile("viral/転職ショート_20260416/s2.png") },
            { fromFrame: 72, kind: "photo", src: staticFile("viral/転職ショート_20260416/p2.png") },
            { fromFrame: 173, kind: "illustration", src: staticFile("viral/転職ショート_20260416/s2.png") },
            { fromFrame: 319, kind: "illustration", src: staticFile("viral/転職ショート_20260416/illust_kazetooshi_bad.png") },
            { fromFrame: 460, kind: "illustration", src: staticFile("viral/転職ショート_20260416/illust_jinzai_hikinuki.png") },
          ],
          fromFrame: 905,
          durationFrames: 1510 - 905,
          switchFrame: 60,
        },
        {
          title: "③ 尊敬できる上司が一人もいない",
          imageSrc: staticFile("viral/転職ショート_20260416/s3.png"),
          photoSrc: staticFile("viral/転職ショート_20260416/p3.png"),
          visuals: [
            { fromFrame: 0, kind: "illustration", src: staticFile("viral/転職ショート_20260416/s3.png") },
            { fromFrame: 77, kind: "photo", src: staticFile("viral/転職ショート_20260416/p3.png") },
            { fromFrame: 213, kind: "illustration", src: staticFile("viral/転職ショート_20260416/illust_joushi_buka_men.jpg") },
            { fromFrame: 335, kind: "illustration", src: staticFile("viral/転職ショート_20260416/s3.png") },
            { fromFrame: 466, kind: "illustration", src: staticFile("viral/転職ショート_20260416/illust_jinzai_hikinuki.png") },
          ],
          fromFrame: 1510,
          durationFrames: 2110 - 1510,
          switchFrame: 60,
        },
      ]}
      cta={{
        fromFrame: 2110,
        durationFrames: 2394 - 2110,
        switchFrame: 138,
        imageSrc1: staticFile("viral/転職ショート_20260416/cta.png"),
        imageSrc2: staticFile("viral/転職ショート_20260416/cta_alt.png"),
      }}
      sfx={[
        { fromFrame: 0, src: staticFile("audio/転職ショート_20260416/sfx/logo-animation2.mp3"), volume: 0.12 },
        { fromFrame: 118, src: staticFile("audio/転職ショート_20260416/sfx/cute-motion1.mp3"), volume: 0.08 },
        { fromFrame: 240, src: staticFile("audio/転職ショート_20260416/sfx/papa1.mp3"), volume: 0.06 },
        { fromFrame: 905, src: staticFile("audio/転職ショート_20260416/sfx/nyu3.mp3"), volume: 0.06 },
        { fromFrame: 1510, src: staticFile("audio/転職ショート_20260416/sfx/papa1.mp3"), volume: 0.06 },
        { fromFrame: 2110, src: staticFile("audio/転職ショート_20260416/sfx/cute-motion1.mp3"), volume: 0.06 },
      ]}
      isHorizontal={false}
    />
  );
};
