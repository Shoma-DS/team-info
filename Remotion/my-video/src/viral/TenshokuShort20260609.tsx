/**
 * Job-change vertical short generated from the script narration.
 * It combines the Aoyama Ryusei narration, subtitle timeline, downloaded illustration assets,
 * and reused short-video SFX through the shared ViralTemplate.
 */
import React from "react";
import { staticFile } from "remotion";
import { SUBTITLE_TIMELINE } from "./generated/TenshokuShort20260609Subtitles";
import { ViralTemplate } from "./components/ViralTemplate";
import { useViralAdultAffiliateFont } from "./fonts";

const imageAsset = (name: string) => staticFile(`viral/job_change_20260609/irasutoya/${name}`);
const sfx = (name: string) => staticFile(`audio/転職ショート_20260416/sfx/${name}`);

export const TenshokuShort20260609: React.FC = () => {
  useViralAdultAffiliateFont();
  const totalFrames = 1410;

  return (
    <ViralTemplate
      totalFrames={totalFrames}
      audioSrc={staticFile("audio/job_change_20260609/narration.wav")}
      subtitles={SUBTITLE_TIMELINE}
      hook={{
        text: "転職面接で\n通る人がやること3選",
        imageSrc: imageAsset("00_hook_interview.png"),
        durationFrames: 318,
        callouts: [
          {
            fromFrame: 132,
            text: "準備の差が\nそのまま伝わる",
            imageSrc: imageAsset("01_interview_job_hunting.png"),
          },
        ],
      }}
      sections={[
        {
          title: "① 会社の課題を読む",
          imageSrc: imageAsset("02_s1_kj.png"),
          photoSrc: imageAsset("03_s1_monitor.png"),
          visuals: [
            { fromFrame: 0, kind: "illustration", src: imageAsset("02_s1_kj.png") },
            { fromFrame: 150, kind: "photo", src: imageAsset("03_s1_monitor.png") },
            { fromFrame: 270, kind: "illustration", src: imageAsset("00_hook_interview.png") },
          ],
          fromFrame: 318,
          durationFrames: 336,
          switchFrame: 84,
        },
        {
          title: "② 答えを一文で決める",
          imageSrc: imageAsset("04_s2_presentation.png"),
          photoSrc: imageAsset("05_s2_worried_worker.png"),
          visuals: [
            { fromFrame: 0, kind: "illustration", src: imageAsset("04_s2_presentation.png") },
            { fromFrame: 180, kind: "photo", src: imageAsset("05_s2_worried_worker.png") },
          ],
          fromFrame: 654,
          durationFrames: 396,
          switchFrame: 84,
        },
        {
          title: "③ 逆質問を用意する",
          imageSrc: imageAsset("06_s3_smiling_workers.png"),
          photoSrc: imageAsset("07_s3_talk_workers.png"),
          visuals: [
            { fromFrame: 0, kind: "illustration", src: imageAsset("06_s3_smiling_workers.png") },
            { fromFrame: 168, kind: "photo", src: imageAsset("07_s3_talk_workers.png") },
          ],
          fromFrame: 1050,
          durationFrames: 264,
          switchFrame: 84,
        },
      ]}
      cta={{
        fromFrame: 1314,
        durationFrames: totalFrames - 1314,
        switchFrame: 36,
        imageSrc1: imageAsset("99_cta_motivated_workers.png"),
        imageSrc2: imageAsset("01_interview_job_hunting.png"),
      }}
      sfx={[
        { fromFrame: 0, src: sfx("logo-animation2.mp3"), volume: 0.1 },
        { fromFrame: 132, src: sfx("cute-motion1.mp3"), volume: 0.06 },
        { fromFrame: 318, src: sfx("papa1.mp3"), volume: 0.05 },
        { fromFrame: 654, src: sfx("nyu3.mp3"), volume: 0.05 },
        { fromFrame: 1050, src: sfx("papa1.mp3"), volume: 0.05 },
        { fromFrame: 1314, src: sfx("cute-motion1.mp3"), volume: 0.05 },
      ]}
      isHorizontal={false}
    />
  );
};
