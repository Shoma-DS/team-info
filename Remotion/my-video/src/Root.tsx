import { Composition, Folder } from "remotion";
import { AcoRielLyricCover, AcoRielLyricCoverMultiBG } from "./AcoRielLyricCover";
import { CanvaSlideshow, type SlideEntry } from "./CanvaSlideshow";
import { SleepTravelLong } from "./SleepTravelLong";
// import chiseigakuSlides from "../public/assets/slide_images/地政学/manifest.json";
const chiseigakuSlides: SlideEntry[] = [];
import { ViralVideo as ViralVideoGachi } from "./viral/アダルトアフィリ/ガチで脱いだ女性芸能人3選_20260313";
import { ViralVideoJimusho } from "./viral/アダルトアフィリ/事務所に売られた芸能人3選_20260316";
import { JobChangeViralHorizontal20260412 } from "./viral/転職横動画/会社に見切りをつける直前の人の特徴9選_20260412";
import {
  EditableViralVideo,
  type ViralStudioEditorProps,
  viralStudioEditorSchema,
} from "./viral/editor/EditableViralVideo";
import { ViralClipEditor } from "./viral/editor/ViralClipEditor";
import { viralEditorPresets } from "./viral/editor/presets";
import { TenshokuShort20260416 } from "./viral/TenshokuShort20260416";
import { withErrorBoundary } from "./ErrorBoundary";

const SleepTravelLongSafe = withErrorBoundary(SleepTravelLong, "SleepTravelLong");
const CanvaSlideshowSafe = withErrorBoundary(CanvaSlideshow, "CanvaSlideshow");
const AcoRielLyricCoverMultiBGSafe = withErrorBoundary(AcoRielLyricCoverMultiBG, "AcoRielLyricCoverMultiBG");
const AcoRielLyricCoverSafe = withErrorBoundary(AcoRielLyricCover, "AcoRielLyricCover");
const ViralVideoGachiSafe = withErrorBoundary(ViralVideoGachi, "ガチで脱いだ女性芸能人3選");
const ViralVideoJimushoSafe = withErrorBoundary(ViralVideoJimusho, "事務所に売られた芸能人3選");
const JobChangeViralHorizontal20260412Safe = withErrorBoundary(
  JobChangeViralHorizontal20260412,
  "会社に見切りをつける直前の人の特徴9選_20260412",
);
const EditableViralVideoSafe = withErrorBoundary(EditableViralVideo, "EditableViralVideo");
const ViralClipEditorSafe = withErrorBoundary(ViralClipEditor, "ViralClipEditor");
const TenshokuShort20260416Safe = withErrorBoundary(TenshokuShort20260416, "転職ショート_20260416");

const getEditableViralDuration = (props: ViralStudioEditorProps): number => {
  return Math.max(
    props.hookDurationFrames,
    ...props.scenes.map((scene) => scene.to),
    ...props.subtitles.map((subtitle) => subtitle.to),
  );
};

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
        <Composition
          id="AcoRiel-Love-so-sweet-MultiBG"
          component={AcoRielLyricCoverMultiBGSafe}
          durationInFrames={8141}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            songFolder: "songs/Love_so_sweet",
            songTitle: "Love so sweet",
            songArtist: "嵐",
            prerenderedBgVideo: "bg_prerendered_seed1334449256.mp4",
          }}
        />
      </Folder>

      <Folder name="Viral">
        <Folder name="転職">
          <Composition
            id="優秀な人が黙って去る会社の特徴3選-20260416"
            component={TenshokuShort20260416Safe}
            durationInFrames={2394}

            fps={30}
            width={1920}
            height={1080}
          />
        </Folder>
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

        <Folder name="転職横動画">
          <Composition
            id="会社に見切りをつける直前の人の特徴9選-20260412"
            component={JobChangeViralHorizontal20260412Safe}
            durationInFrames={11594}
            fps={30}
            width={1280}
            height={720}
          />
        </Folder>

        <Folder name="Studio-Editor">
          <Composition
            id="Viral-Studio-Template"
            component={EditableViralVideoSafe}
            schema={viralStudioEditorSchema}
            durationInFrames={viralEditorPresets[0].durationInFrames}
            fps={30}
            width={1080}
            height={1920}
            defaultProps={viralEditorPresets[0].props}
            calculateMetadata={({ props }) => ({
              durationInFrames: getEditableViralDuration(props),
            })}
          />
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
