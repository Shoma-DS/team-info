import { Composition, Folder } from "remotion";
import { SleepTravelLong } from "./SleepTravelLong";
import { AcoRielLyricCover } from "./AcoRielLyricCover";
import { CanvaSlideshow } from "./CanvaSlideshow";
import chiseigakuSlides from "../public/assets/slide_images/地政学/manifest.json";
import { ViralVideo } from "./viral/ViralVideo_芸能人エンタメ_20260310";

// Each <Composition> is an entry in the sidebar!

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Folder name="SleepTravel">
        <Composition
          id="SleepTravelLong"
          component={SleepTravelLong}
          durationInFrames={144216}
          fps={30}
          width={1920}
          height={1080}
        />
      </Folder>

      <Folder name="Slideshow">
        <Composition
          id="SleepTravel-地政学-Slideshow"
          component={CanvaSlideshow}
          durationInFrames={144210}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            audioSrc: 'assets/slide_images/地政学/audio.mp3',
            slides: chiseigakuSlides,
          }}
        />
      </Folder>

      <Folder name="AcoRiel">
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
      </Folder>

      <Folder name="Viral">
        <Composition
          id="Viral-shorts-20260310"
          component={ViralVideo}
          durationInFrames={1620}
          fps={30}
          width={1080}
          height={1920}
        />
      </Folder>

    </>
  );
};
