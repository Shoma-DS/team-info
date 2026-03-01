import { Composition } from "remotion";
import { SleepTravelLong } from "./SleepTravelLong";
import { AcoRielCover } from "./AcoRielCover";
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
        id="AcoRielCover"
        component={AcoRielCover}
        durationInFrames={7524}
        fps={30}
        width={1920}
        height={1080}
      />

      <Composition
        id="AcoRielLyricCover"
        component={AcoRielLyricCover}
        durationInFrames={7524}
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
        id="AcoRiel-SAY-YES-Lyric"
        component={AcoRielLyricCover}
        durationInFrames={8966}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          songFolder: 'songs/SAY_YES',
          songTitle: 'SAY YES',
          songArtist: 'CHAGE and ASKA',
          audioAssetPath: 'assets/channels/acoriel/songs/SAY_YES.mp3',
        }}
      />
      <Composition
        id="AcoRiel-SAY-YES-MultiBG"
        component={AcoRielLyricCoverMultiBG}
        durationInFrames={8966}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          songFolder: 'songs/SAY_YES',
          songTitle: 'SAY YES',
          songArtist: 'CHAGE and ASKA',
          audioAssetPath: 'assets/channels/acoriel/songs/SAY_YES.mp3',
          backgroundVideos: ['bg_video_1.mp4', 'bg_video_2.mp4', 'bg_video_3.mp4'],
          bgSegmentSeconds: 10,
          bgCrossfadeSeconds: 2,
        }}
      />
    </>
  );
};
