import { VideoConfig, VideoCollection } from '../config/video-config';
import videosData from '../config/videos.json';
import examplesData from '../config/video-examples.json';

/**
 * Utility to easily switch between different video configurations
 */
export class VideoConfigSwitcher {
  private mainConfigs: VideoCollection;
  private exampleConfigs: VideoCollection;

  constructor() {
    this.mainConfigs = videosData as VideoCollection;
    this.exampleConfigs = examplesData as VideoCollection;
  }

  /**
   * Get configuration from main videos.json
   */
  getMainConfig(videoId: string): VideoConfig | null {
    const video = this.mainConfigs.videos.find(v => v.id === videoId);
    if (!video) return null;

    return this.mergeWithDefaults(video, this.mainConfigs.defaultConfig);
  }

  /**
   * Get configuration from examples
   */
  getExampleConfig(videoId: string): VideoConfig | null {
    const video = this.exampleConfigs.examples?.find(v => v.id === videoId);
    if (!video) return null;

    return this.mergeWithDefaults(video, this.exampleConfigs.defaultConfig);
  }

  /**
   * Get all available configurations (main + examples)
   */
  getAllConfigs(): VideoConfig[] {
    const mainConfigs = this.mainConfigs.videos.map(video => 
      this.mergeWithDefaults(video, this.mainConfigs.defaultConfig)
    );

    const exampleConfigs = (this.exampleConfigs.examples || []).map(video => 
      this.mergeWithDefaults(video, this.exampleConfigs.defaultConfig)
    );

    return [...mainConfigs, ...exampleConfigs];
  }

  /**
   * Get configurations by layout type
   */
  getConfigsByLayout(layout: 'center' | 'bottom' | 'circle'): VideoConfig[] {
    return this.getAllConfigs().filter(config => config.layout === layout);
  }

  /**
   * Get configurations by font family
   */
  getConfigsByFont(fontFamily: string): VideoConfig[] {
    return this.getAllConfigs().filter(
      config => config.subtitlesConfig.fontFamily === fontFamily
    );
  }

  /**
   * Create a custom configuration by modifying an existing one
   */
  createCustomConfig(baseConfigId: string, overrides: Partial<VideoConfig>): VideoConfig | null {
    const baseConfig = this.getMainConfig(baseConfigId) || this.getExampleConfig(baseConfigId);
    if (!baseConfig) return null;

    return {
      ...baseConfig,
      ...overrides,
      subtitlesConfig: {
        ...baseConfig.subtitlesConfig,
        ...overrides.subtitlesConfig,
      },
      layoutSpecific: {
        circle: {
          ...baseConfig.layoutSpecific?.circle,
          ...overrides.layoutSpecific?.circle,
        },
        bottom: {
          ...baseConfig.layoutSpecific?.bottom,
          ...overrides.layoutSpecific?.bottom,
        },
      },
    };
  }

  private mergeWithDefaults(video: any, defaults: any): VideoConfig {
    return {
      ...defaults,
      ...video,
      subtitlesConfig: {
        ...defaults.subtitlesConfig,
        ...video.subtitlesConfig,
      },
      layoutSpecific: {
        circle: {
          ...defaults.layoutSpecific?.circle,
          ...video.layoutSpecific?.circle,
        },
        bottom: {
          ...defaults.layoutSpecific?.bottom,
          ...video.layoutSpecific?.bottom,
        },
      },
    } as VideoConfig;
  }
}

// Export singleton instance
export const configSwitcher = new VideoConfigSwitcher();