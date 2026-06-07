/**
 * New job-change vertical short built from the existing ViralTemplate.
 * It uses generated 20260602 visuals and a VOICEVOX narration paced to 61 seconds.
 */
import React from "react";
import { staticFile } from "remotion";
import { SUBTITLE_TIMELINE } from "./generated/TenshokuShort20260602Subtitles";
import { ViralTemplate } from "./components/ViralTemplate";
import { useViralAdultAffiliateFont } from "./fonts";

const generatedAsset = (name: string) => staticFile(`viral/job_change_20260602/${name}`);
const sfx = (name: string) => staticFile(`audio/転職ショート_20260416/sfx/${name}`);

export const TenshokuShort20260602: React.FC = () => {
  useViralAdultAffiliateFont();
  const totalFrames = 1843;

  return (
    <ViralTemplate
      totalFrames={totalFrames}
      audioSrc={staticFile("audio/job_change_20260602/narration.mp3")}
      subtitles={SUBTITLE_TIMELINE}
      hook={{
        text: "転職で後悔しない人が\n先にやること3選",
        imageSrc: generatedAsset("hook_prepare.png"),
        durationFrames: 143,
        callouts: [
          {
            fromFrame: 69,
            text: "辞める前にこれだけは\n必ず確認して",
            imageSrc: generatedAsset("hook_prepare.png"),
          },
        ],
      }}
      sections={[
        {
          title: "① 辞めたい理由を書き出す",
          imageSrc: generatedAsset("s1_reason.png"),
          photoSrc: generatedAsset("s1_reason.png"),
          visuals: [
            { fromFrame: 0, kind: "photo", src: generatedAsset("s1_reason.png") },
            { fromFrame: 310, kind: "photo", src: generatedAsset("hook_prepare.png") },
            { fromFrame: 489, kind: "photo", src: generatedAsset("s1_reason.png") },
          ],
          fromFrame: 143,
          durationFrames: 523,
          switchFrame: 47,
        },
        {
          title: "② 実績を数字で言えるようにする",
          imageSrc: generatedAsset("s2_achievement.png"),
          photoSrc: generatedAsset("s2_achievement.png"),
          visuals: [
            { fromFrame: 0, kind: "photo", src: generatedAsset("s2_achievement.png") },
            { fromFrame: 257, kind: "photo", src: generatedAsset("s2_achievement.png") },
            { fromFrame: 453, kind: "photo", src: generatedAsset("s2_achievement.png") },
          ],
          fromFrame: 666,
          durationFrames: 471,
          switchFrame: 47,
        },
        {
          title: "③ 譲れない条件を三つ決める",
          imageSrc: generatedAsset("s3_conditions.png"),
          photoSrc: generatedAsset("s3_conditions.png"),
          visuals: [
            { fromFrame: 0, kind: "photo", src: generatedAsset("s3_conditions.png") },
            { fromFrame: 298, kind: "photo", src: generatedAsset("s3_conditions.png") },
            { fromFrame: 390, kind: "photo", src: generatedAsset("s3_conditions.png") },
          ],
          fromFrame: 1137,
          durationFrames: 426,
          switchFrame: 47,
        },
      ]}
      cta={{
        fromFrame: 1563,
        durationFrames: totalFrames - 1563,
        switchFrame: 84,
        imageSrc1: generatedAsset("cta_write_one.png"),
        imageSrc2: generatedAsset("cta_write_one.png"),
      }}
      sfx={[
        { fromFrame: 0, src: sfx("logo-animation2.mp3"), volume: 0.12 },
        { fromFrame: 69, src: sfx("cute-motion1.mp3"), volume: 0.08 },
        { fromFrame: 143, src: sfx("papa1.mp3"), volume: 0.06 },
        { fromFrame: 666, src: sfx("nyu3.mp3"), volume: 0.06 },
        { fromFrame: 1137, src: sfx("papa1.mp3"), volume: 0.06 },
        { fromFrame: 1563, src: sfx("cute-motion1.mp3"), volume: 0.06 },
      ]}
      isHorizontal={false}
    />
  );
};
