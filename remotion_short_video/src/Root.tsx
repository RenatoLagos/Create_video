import "./index.css";
import { Composition } from "remotion";
import { z } from "zod";
import { DynamicVideoWrapper } from "./components/DynamicVideoWrapper";
import { SequencedVideoWrapper } from "./components/SequencedVideoWrapper";
import { KaraokeVideoWrapper } from "./components/KaraokeVideo";
import { getAllVideoConfigs } from "./utils/configLoader";
import { getAllSequencedVideoConfigs } from "./utils/sequencedConfigLoader";
import { getAvailableTemplates } from "./utils/templateConfigLoader";

// Zod schemas for props validation
const DynamicVideoConfigSchema = z.object({
  config: z.object({
    id: z.string(),
    title: z.string(),
    videoFile: z.string(),
    subtitlesFile: z.string(),
    layout: z.enum(['center', 'bottom', 'circle']),
    fps: z.number(),
    width: z.number(),
    height: z.number()
  })
});

const SequencedVideoConfigSchema = z.object({
  config: z.object({
    id: z.string(),
    title: z.string(),
    videoFile: z.string(),
    subtitlesFile: z.string(),
    segmentedPromptsFile: z.string(),
    fps: z.number(),
    width: z.number(),
    height: z.number(),
    debugMode: z.boolean().optional()
  })
});

const KaraokeVideoConfigSchema = z.object({
  config: z.object({
    videoFile: z.string(),
    subtitlesFile: z.string(),
    templateStyle: z.string().optional(),
    debugMode: z.boolean().optional()
  })
});

export const RemotionRoot: React.FC = () => {
  const videoConfigs = getAllVideoConfigs();
  const sequencedVideoConfigs = getAllSequencedVideoConfigs();
  const availableTemplates = getAvailableTemplates();

  // Configuraciones de ejemplo para karaoke
  const karaokeConfigs = [
    {
      id: 'karaoke-example',
      videoFile: 'video.mp4',
      subtitlesFile: 'video/03_VideoProcessing/03_subtitles/clean_subtitles.srt',
      templateStyle: 'karaoke',
      debugMode: true
    },
    {
      id: 'lower-thirds-example',
      videoFile: 'video.mp4',
      subtitlesFile: 'video/03_VideoProcessing/03_subtitles/clean_subtitles.srt',
      templateStyle: 'lower-thirds',
      debugMode: true
    }
  ];

  return (
    <>
      {/* Composiciones dinámicas existentes */}
      {videoConfigs.map((config) => (
        <Composition
          key={config.id}
          id={config.id}
          component={DynamicVideoWrapper as React.ComponentType<unknown>}
          durationInFrames={config.durationInFrames || 690}
          fps={config.fps}
          width={config.width}
          height={config.height}
          defaultProps={{
            config
          }}
          schema={DynamicVideoConfigSchema}
        />
      ))}

      {/* Composiciones secuenciadas existentes */}
      {sequencedVideoConfigs.map((config) => (
        <Composition
          key={config.id}
          id={config.id}
          component={SequencedVideoWrapper as React.ComponentType<unknown>}
          durationInFrames={config.durationInFrames || 1200}
          fps={config.fps}
          width={config.width}
          height={config.height}
          defaultProps={{
            config
          }}
          schema={SequencedVideoConfigSchema}
        />
      ))}

      {/* Nuevas composiciones de karaoke */}
      {karaokeConfigs.map((config) => (
        <Composition
          key={config.id}
          id={config.id}
          component={KaraokeVideoWrapper as React.ComponentType<unknown>}
          durationInFrames={1800} // 60 segundos a 30fps
          fps={30}
          width={1920}
          height={1920}
          defaultProps={{
            config
          }}
          schema={KaraokeVideoConfigSchema}
        />
      ))}

      {/* Composición genérica que usa variable de entorno MOGRT_STYLE */}
      <Composition
        id="karaoke-env-style"
        component={KaraokeVideoWrapper as React.ComponentType<unknown>}
        durationInFrames={1800}
        fps={30}
        width={1920}
        height={1920}
        defaultProps={{
          config: {
            videoFile: 'video.mp4',
            subtitlesFile: 'video/03_VideoProcessing/03_subtitles/clean_subtitles.srt',
            debugMode: true
          }
        }}
        schema={KaraokeVideoConfigSchema}
      />
    </>
  );
};
