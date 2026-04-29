import React from "react";
import { staticFile } from "remotion";
import { ViralTemplate } from "../components/ViralTemplate";
import { useViralAdultAffiliateFont } from "../fonts";
import { SUBTITLE_TIMELINE } from "../generated/TenshokuShort20260412Subtitles";

const TITLE = "会社に見切りをつける直前の人の特徴9選_20260412";
const TOTAL_FRAMES = 11594;

const CIRCLE_NUMS = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨"];


export const JobChangeViralHorizontal20260412: React.FC = () => {
  useViralAdultAffiliateFont();

  return (
    <ViralTemplate
      totalFrames={TOTAL_FRAMES}
      audioSrc={staticFile(`viral/${TITLE}/audio/narration.mp3`)}
      subtitles={SUBTITLE_TIMELINE}
      hook={{
        text: "会社に見切りをつける\n直前の人の特徴9選",
        imageSrc: staticFile(`viral/${TITLE}/materials/hook_illust.png`),
        durationFrames: 216, // ffmpegで抽出した正確なタイミング
      }}
      sections={[
        { title: `${CIRCLE_NUMS[0]} 頑張る前に、もう疲れている`, photoSrc: staticFile(`viral/${TITLE}/materials/01_main_1.jpg`), fromFrame: 216, durationFrames: 1532 - 216, switchFrame: 30 },
        { title: `${CIRCLE_NUMS[1]} 仕事の話を聞くだけで、気分が沈む`, photoSrc: staticFile(`viral/${TITLE}/materials/01_main_1.jpg`), fromFrame: 1532, durationFrames: 2634 - 1532, switchFrame: 30 },
        { title: `${CIRCLE_NUMS[2]} ミスやトラブルに反応しなくなった`, photoSrc: staticFile(`viral/${TITLE}/materials/01_main_1.jpg`), fromFrame: 2634, durationFrames: 3803 - 2634, switchFrame: 30 },
        { title: `${CIRCLE_NUMS[3]} 職場の人に、何も期待しなくなった`, photoSrc: staticFile(`viral/${TITLE}/materials/02_main_2.jpg`), fromFrame: 3803, durationFrames: 4913 - 3803, switchFrame: 30 },
        { title: `${CIRCLE_NUMS[4]} 評価されなくても、悔しくなくなった`, photoSrc: staticFile(`viral/${TITLE}/materials/02_main_2.jpg`), fromFrame: 4913, durationFrames: 6233 - 4913, switchFrame: 30 },
        { title: `${CIRCLE_NUMS[5]} 今の会社にいる数年後が想像できない`, photoSrc: staticFile(`viral/${TITLE}/materials/02_main_2.jpg`), fromFrame: 6233, durationFrames: 7348 - 6233, switchFrame: 30 },
        { title: `${CIRCLE_NUMS[6]} 休みの日にまで、回復しかしていない`, photoSrc: staticFile(`viral/${TITLE}/materials/03_main_3.jpg`), fromFrame: 7348, durationFrames: 8474 - 7348, switchFrame: 30 },
        { title: `${CIRCLE_NUMS[7]} 転職した人の話を、前より真剣に聞いてしまう`, photoSrc: staticFile(`viral/${TITLE}/materials/03_main_3.jpg`), fromFrame: 8474, durationFrames: 9521 - 8474, switchFrame: 30 },
        { title: `${CIRCLE_NUMS[8]} 辞めたいより、ここではないと感じる`, photoSrc: staticFile(`viral/${TITLE}/materials/03_main_3.jpg`), fromFrame: 9521, durationFrames: 10599 - 9521, switchFrame: 30 },
      ]}
      cta={{
        fromFrame: 10599,
        durationFrames: TOTAL_FRAMES - 10599,
        switchFrame: 99999, // 画像の切り替えはなし（1枚のみ）
        imageSrc1: staticFile(`viral/${TITLE}/materials/99_cta.jpg`),
        imageSrc2: staticFile(`viral/${TITLE}/materials/99_cta.jpg`), // 同じ画像でフォールバック
      }}
      isHorizontal={true}
    />
  );
};
