import React from "react";
import { staticFile } from "remotion";
import { ViralTemplate } from "../components/ViralTemplate";
import { useViralAdultAffiliateFont } from "../fonts";
import { SUBTITLE_TIMELINE } from "../generated/TenshokuShort20260412Subtitles";

const TITLE = "会社に見切りをつける直前の人の特徴9選_20260412";
const TOTAL_FRAMES = 10735;

const CIRCLE_NUMS = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨"];


export const JobChangeViralHorizontal20260412: React.FC = () => {
  useViralAdultAffiliateFont();

  return (
    <ViralTemplate
      totalFrames={TOTAL_FRAMES}
      audioSrc={staticFile(`viral/${TITLE}/audio/narration_fast.wav`)}
      subtitles={SUBTITLE_TIMELINE}
      hook={{
        text: "会社に見切りをつける\n直前の人の特徴9選",
        imageSrc: staticFile(`viral/${TITLE}/materials/hook_illust.png`),
        durationFrames: 200, // ffmpegで抽出した正確なタイミング
      }}
      sections={[
        { title: `${CIRCLE_NUMS[0]} 頑張る前に、もう疲れている`, imageSrc: staticFile(`viral/${TITLE}/materials/01_main_1_new.png`), photoSrc: staticFile(`viral/${TITLE}/materials/01_main_1_photo.png`), fromFrame: 200, durationFrames: 1419 - 200, switchFrame: 600 },
        { title: `${CIRCLE_NUMS[1]} 仕事の話を聞くだけで、気分が沈む`, imageSrc: staticFile(`viral/${TITLE}/materials/02_main_2_new.png`), photoSrc: staticFile(`viral/${TITLE}/materials/02_main_2_photo.png`), fromFrame: 1419, durationFrames: 2439 - 1419, switchFrame: 500 },
        { title: `${CIRCLE_NUMS[2]} ミスやトラブルに反応しなくなった`, imageSrc: staticFile(`viral/${TITLE}/materials/03_main_3_new.png`), photoSrc: staticFile(`viral/${TITLE}/materials/03_main_3_photo.png`), fromFrame: 2439, durationFrames: 3521 - 2439, switchFrame: 540 },
        { title: `${CIRCLE_NUMS[3]} 職場の人に、何も期待しなくなった`, imageSrc: staticFile(`viral/${TITLE}/materials/04_main_4_new.png`), photoSrc: staticFile(`viral/${TITLE}/materials/04_main_4_photo.png`), fromFrame: 3521, durationFrames: 4549 - 3521, switchFrame: 510 },
        { title: `${CIRCLE_NUMS[4]} 評価されなくても、悔しくなくなった`, imageSrc: staticFile(`viral/${TITLE}/materials/05_main_5_new.png`), photoSrc: staticFile(`viral/${TITLE}/materials/05_main_5_photo.png`), fromFrame: 4549, durationFrames: 5771 - 4549, switchFrame: 610 },
        { title: `${CIRCLE_NUMS[5]} 今の会社にいる数年後が想像できない`, imageSrc: staticFile(`viral/${TITLE}/materials/06_main_6_new.png`), photoSrc: staticFile(`viral/${TITLE}/materials/06_main_6_photo.png`), fromFrame: 5771, durationFrames: 6804 - 5771, switchFrame: 510 },
        { title: `${CIRCLE_NUMS[6]} 休みの日にまで、回復しかしていない`, imageSrc: staticFile(`viral/${TITLE}/materials/01_main_1_new.png`), photoSrc: staticFile(`viral/${TITLE}/materials/07_main_7_photo.png`), fromFrame: 6804, durationFrames: 7846 - 6804, switchFrame: 520 },
        { title: `${CIRCLE_NUMS[7]} 転職した人の話を、前より真剣に聞いてしまう`, imageSrc: staticFile(`viral/${TITLE}/materials/02_main_2_new.png`), photoSrc: staticFile(`viral/${TITLE}/materials/08_main_8_photo.png`), fromFrame: 7846, durationFrames: 8816 - 7846, switchFrame: 480 },
        { title: `${CIRCLE_NUMS[8]} 辞めたいより、ここではないと感じる`, imageSrc: staticFile(`viral/${TITLE}/materials/03_main_3_new.png`), photoSrc: staticFile(`viral/${TITLE}/materials/09_main_9_photo.png`), fromFrame: 8816, durationFrames: 9814 - 8816, switchFrame: 500 },
      ]}
      cta={{
        fromFrame: 9814,
        durationFrames: TOTAL_FRAMES - 9814,
        switchFrame: 99999, // 画像の切り替えはなし（1枚のみ）
        imageSrc1: staticFile(`viral/${TITLE}/materials/99_cta.jpg`),
        imageSrc2: staticFile(`viral/${TITLE}/materials/99_cta.jpg`), // 同じ画像でフォールバック
      }}
      isHorizontal={true}
    />
  );
};
