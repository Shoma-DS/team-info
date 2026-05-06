/**
 * TenshokuShort20260506.tsx — 【見逃すと危険】転職を考えた方がいいサイン3選
 * VOICEVOX生成前の新規ショート構成を、既存の転職ショート素材で組む。
 */
import React from "react";
import { staticFile } from "remotion";
import { SUBTITLE_TIMELINE } from "./generated/TenshokuShort20260506Subtitles";
import { ViralTemplate } from "./components/ViralTemplate";
import { useViralAdultAffiliateFont } from "./fonts";

const asset = (name: string) => staticFile(`viral/転職ショート_20260416/${name}`);
const sfx = (name: string) => staticFile(`audio/転職ショート_20260416/sfx/${name}`);

export const TenshokuShort20260506: React.FC = () => {
  useViralAdultAffiliateFont();
  const totalFrames = 2642;

  return (
    <ViralTemplate
      totalFrames={totalFrames}
      audioSrc={staticFile("audio/転職ショート_20260506/narration.wav")}
      subtitles={SUBTITLE_TIMELINE}
      hook={{
        text: "転職を考えた方がいい\nサイン3選",
        imageSrc: asset("hook.png"),
        durationFrames: 240,
        callouts: [
          {
            fromFrame: 116,
            text: "一つでも当てはまるなら\n今の環境は要注意",
            imageSrc: asset("hook_illust.png"),
          },
        ],
      }}
      sections={[
        {
          title: "① 朝、会社に行く前から疲れている",
          imageSrc: asset("s1.png"),
          photoSrc: asset("p1.png"),
          visuals: [
            { fromFrame: 0, kind: "illustration", src: asset("s1.png") },
            { fromFrame: 80, kind: "photo", src: asset("p1.png") },
            { fromFrame: 225, kind: "illustration", src: asset("illust_mushi_business.png") },
            { fromFrame: 430, kind: "illustration", src: asset("illust_kazetooshi_bad.png") },
            { fromFrame: 575, kind: "illustration", src: asset("illust_jinzai_hikinuki.png") },
          ],
          fromFrame: 240,
          durationFrames: 670,
          switchFrame: 80,
        },
        {
          title: "② 相談しても何も変わらない",
          imageSrc: asset("s2.png"),
          photoSrc: asset("p2.png"),
          visuals: [
            { fromFrame: 0, kind: "illustration", src: asset("s2.png") },
            { fromFrame: 72, kind: "photo", src: asset("p2.png") },
            { fromFrame: 210, kind: "illustration", src: asset("illust_mushi_business.png") },
            { fromFrame: 350, kind: "illustration", src: asset("illust_kazetooshi_bad.png") },
            { fromFrame: 555, kind: "illustration", src: asset("illust_jinzai_hikinuki.png") },
          ],
          fromFrame: 910,
          durationFrames: 680,
          switchFrame: 72,
        },
        {
          title: "③ ここにいても成長できない",
          imageSrc: asset("s3.png"),
          photoSrc: asset("p3.png"),
          visuals: [
            { fromFrame: 0, kind: "illustration", src: asset("s3.png") },
            { fromFrame: 72, kind: "photo", src: asset("p3.png") },
            { fromFrame: 210, kind: "illustration", src: asset("illust_joushi_buka_men.jpg") },
            { fromFrame: 360, kind: "illustration", src: asset("s3.png") },
            { fromFrame: 535, kind: "illustration", src: asset("illust_jinzai_hikinuki.png") },
          ],
          fromFrame: 1590,
          durationFrames: 570,
          switchFrame: 72,
        },
      ]}
      cta={{
        fromFrame: 2160,
        durationFrames: totalFrames - 2160,
        switchFrame: 130,
        imageSrc1: asset("cta.png"),
        imageSrc2: asset("cta_alt.png"),
      }}
      sfx={[
        { fromFrame: 0, src: sfx("logo-animation2.mp3"), volume: 0.12 },
        { fromFrame: 116, src: sfx("cute-motion1.mp3"), volume: 0.08 },
        { fromFrame: 240, src: sfx("papa1.mp3"), volume: 0.06 },
        { fromFrame: 910, src: sfx("nyu3.mp3"), volume: 0.06 },
        { fromFrame: 1590, src: sfx("papa1.mp3"), volume: 0.06 },
        { fromFrame: 2160, src: sfx("cute-motion1.mp3"), volume: 0.06 },
      ]}
      isHorizontal={false}
    />
  );
};
