import "./index.css";
import { Composition } from "remotion";
import { z } from "zod";
import { DynamicVideoWrapper } from "./components/DynamicVideoWrapper";
import { SequencedVideoWrapper } from "./components/SequencedVideoWrapper";
import { getAllVideoConfigs } from "./utils/configLoader";
import { getAllSequencedVideoConfigs } from "./utils/sequencedConfigLoader";

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

export const RemotionRoot: React.FC = () => {
  const videoConfigs = getAllVideoConfigs();
  const sequencedVideoConfigs = getAllSequencedVideoConfigs();

  return (
    <>
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
    </>
  );
};
