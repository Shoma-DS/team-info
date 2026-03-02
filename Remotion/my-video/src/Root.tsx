import { Composition } from "remotion";
import { SleepTravelLong } from "./SleepTravelLong";
import { AcoRielLyricCover, AcoRielLyricCoverMultiBG } from "./AcoRielLyricCover";

// Each <Composition> is an entry in the sidebar!

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="SleepTravelLong"
        component={SleepTravelLong}
        durationInFrames={144216}
        fps={30}
        width={1920}
        height={1080}
      />

      <Composition
        id="AcoRiel-TomorrowNeverKnows-Lyric"
        component={AcoRielLyricCover}
        durationInFrames={8100}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          songFolder: 'songs/Tomorrow_never_knows',
          songTitle: 'Tomorrow never knows',
          songArtist: 'Mr.Children',
          audioAssetPath: 'assets/channels/acoriel/songs/Tomorrow_never_knows.mp3',
        }}
      />

      <Composition
        id="AcoRiel-Seishun-Amigo-MultiBG"
        component={AcoRielLyricCoverMultiBG}
        durationInFrames={9630}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          songFolder: 'songs/青春アミーゴ',
          songTitle: '青春アミーゴ',
          songArtist: '修二と彰',
          // 事前合成済み背景動画を使用（prerender_bg_video.py で生成）
          prerenderedBgVideo: 'bg_prerendered.mp4',
        }}
      />
    </>
  );
};
