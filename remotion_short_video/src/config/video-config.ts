import { FontFamily } from './fonts';

export interface VideoConfig {
  id: string;
  title: string;
  videoFile: string;
  audioFile?: string;
  subtitlesFile: string;
  durationInFrames?: number; // Optional - will be calculated if not provided
  fps: number;
  width: number;
  height: number;
  layout: 'center' | 'bottom' | 'circle';
  subtitlesConfig: {
    position: 'top' | 'center' | 'bottom';
    fontSize: number;
    fontFamily: FontFamily;
    color: string;
    strokeWidth: number;
    strokeColor: string;
  };
  layoutSpecific?: {
    // For circle layout
    circle?: {
      size: number;
      position: { top: number; left: number };
      borderWidth: number;
      borderColor: string;
    };
    // For bottom layout
    bottom?: {
      videoHeight: string; // percentage
      subtitlesTop: string; // percentage
      backgroundColor: string;
    };
  };
}

export interface VideoCollection {
  defaultConfig: Partial<VideoConfig>;
  videos: VideoConfig[];
}

// Default configuration that can be extended
export const DEFAULT_VIDEO_CONFIG: Partial<VideoConfig> = {
  fps: 30,
  width: 1080,
  height: 1920,
  subtitlesConfig: {
    position: 'center',
    fontSize: 64,
    fontFamily: 'Poppins',
    color: 'white',
    strokeWidth: 22,
    strokeColor: 'black',
  },
  layoutSpecific: {
    circle: {
      size: 350,
      position: { top: 40, left: 40 },
      borderWidth: 4,
      borderColor: '#ffffff',
    },
    bottom: {
      videoHeight: '50%',
      subtitlesTop: '60%',
      backgroundColor: '#000000',
    },
  },
};

// Load and merge video configuration
export function loadVideoConfig(config: Partial<VideoConfig>): VideoConfig {
  return {
    ...DEFAULT_VIDEO_CONFIG,
    ...config,
    subtitlesConfig: {
      ...DEFAULT_VIDEO_CONFIG.subtitlesConfig!,
      ...config.subtitlesConfig,
    },
    layoutSpecific: {
      circle: {
        ...DEFAULT_VIDEO_CONFIG.layoutSpecific!.circle!,
        ...config.layoutSpecific?.circle,
      },
      bottom: {
        ...DEFAULT_VIDEO_CONFIG.layoutSpecific!.bottom!,
        ...config.layoutSpecific?.bottom,
      },
    },
  } as VideoConfig;
}