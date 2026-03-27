import { Composition, Folder } from "remotion";
import { AcoRielLyricCover, AcoRielLyricCoverMultiBG } from "./AcoRielLyricCover";
import { CanvaSlideshow } from "./CanvaSlideshow";
import { SleepTravelLong } from "./SleepTravelLong";
import chiseigakuSlides from "../public/assets/slide_images/地政学/manifest.json";
import { ViralVideo as ViralVideoGachi } from "./viral/アダルトアフィリ/ガチで脱いだ女性芸能人3選_20260313";
import { ViralVideoJimusho } from "./viral/アダルトアフィリ/事務所に売られた芸能人3選_20260316";
import {
  EditableViralVideo,
  viralStudioEditorSchema,
} from "./viral/editor/EditableViralVideo";
import { ViralClipEditor } from "./viral/editor/ViralClipEditor";
import { viralEditorPresets } from "./viral/editor/presets";
import { withErrorBoundary } from "./ErrorBoundary";

const SleepTravelLongSafe = withErrorBoundary(SleepTravelLong, "SleepTravelLong");
const CanvaSlideshowSafe = withErrorBoundary(CanvaSlideshow, "CanvaSlideshow");
const AcoRielLyricCoverMultiBGSafe = withErrorBoundary(AcoRielLyricCoverMultiBG, "AcoRielLyricCoverMultiBG");
const AcoRielLyricCoverSafe = withErrorBoundary(AcoRielLyricCover, "AcoRielLyricCover");
const ViralVideoGachiSafe = withErrorBoundary(ViralVideoGachi, "ガチで脱いだ女性芸能人3選");
const ViralVideoJimushoSafe = withErrorBoundary(ViralVideoJimusho, "事務所に売られた芸能人3選");
const EditableViralVideoSafe = withErrorBoundary(EditableViralVideo, "EditableViralVideo");
const ViralClipEditorSafe = withErrorBoundary(ViralClipEditor, "ViralClipEditor");

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Folder name="SleepTravel">
        <Composition
          id="SleepTravelLong"
          component={SleepTravelLongSafe}
          durationInFrames={144216}
          fps={30}
          width={1920}
          height={1080}
        />
      </Folder>

      <Folder name="Slideshow">
        <Composition
          id="SleepTravel-地政学-Slideshow"
          component={CanvaSlideshowSafe}
          durationInFrames={144210}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            audioSrc: "assets/slide_images/地政学/audio.mp3",
            slides: chiseigakuSlides,
          }}
        />
      </Folder>

      <Folder name="AcoRiel">
        <Composition
          id="AcoRiel-Joifuru-MultiBG"
          component={AcoRielLyricCoverMultiBGSafe}
          durationInFrames={5438}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            songFolder: "songs/Joifuru",
            songTitle: "じょいふる",
            songArtist: "いきものがかり",
            prerenderedBgVideo: "bg_prerendered_seed457882377.mp4",
          }}
        />
        <Composition
          id="AcoRiel-TomorrowNeverKnows-Lyric"
          component={AcoRielLyricCoverSafe}
          durationInFrames={8100}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            songFolder: "songs/Tomorrow_never_knows",
            songTitle: "Tomorrow never knows",
            songArtist: "Mr.Children",
            audioAssetPath: "assets/channels/acoriel/songs/Tomorrow_never_knows.mp3",
          }}
        />
      </Folder>

      <Folder name="Viral">
        <Folder name="アダルトアフィリ">
          <Composition
            id="ガチで脱いだ女性芸能人3選-20260313"
            component={ViralVideoGachiSafe}
            durationInFrames={1887}
            fps={30}
            width={1080}
            height={1920}
          />
          <Composition
            id="事務所に売られた芸能人3選-20260316"
            component={ViralVideoJimushoSafe}
            durationInFrames={1550}
            fps={30}
            width={1080}
            height={1920}
          />
        </Folder>

        <Folder name="Studio-Editor">
          {viralEditorPresets.map((preset) => {
            return (
              <Composition
                key={preset.id}
                id={`${preset.id}-GUI`}
                component={EditableViralVideoSafe}
                schema={viralStudioEditorSchema}
                durationInFrames={preset.durationInFrames}
                fps={preset.fps}
                width={preset.width}
                height={preset.height}
                defaultProps={preset.props}
              />
            );
          })}
        </Folder>

        <Folder name="Clip-Editor">
          <Composition
            id="Viral-Clip-Editor"
            component={ViralClipEditorSafe}
            durationInFrames={1}
            fps={30}
            width={1920}
            height={1080}
            defaultProps={{
              initialPresetId: viralEditorPresets[0].id,
            }}
          />
        </Folder>
      </Folder>
    </>
  );
};
