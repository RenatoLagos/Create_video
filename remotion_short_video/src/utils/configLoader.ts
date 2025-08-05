import { VideoConfig, VideoCollection, loadVideoConfig } from '../config/video-config';
import videosData from '../config/videos.json';
import { configSwitcher } from './configSwitcher';

/**
 * Load video configuration from JSON
 */
export function loadVideoCollection(): VideoCollection {
  return videosData as VideoCollection;
}

/**
 * Get a specific video configuration by ID
 */
export function getVideoConfig(videoId: string): VideoConfig | null {
  const collection = loadVideoCollection();
  const videoData = collection.videos.find(video => video.id === videoId);
  
  if (!videoData) {
    console.error(`Video configuration not found for ID: ${videoId}`);
    return null;
  }

  // Merge with default configuration
  const mergedConfig = {
    ...collection.defaultConfig,
    ...videoData,
    subtitlesConfig: {
      ...collection.defaultConfig.subtitlesConfig,
      ...videoData.subtitlesConfig,
    },
  };

  return loadVideoConfig(mergedConfig);
}

/**
 * Get all available video configurations (main + examples)
 */
export function getAllVideoConfigs(): VideoConfig[] {
  // Use the configSwitcher to get all configurations including examples
  return configSwitcher.getAllConfigs();
}

/**
 * Validate video configuration
 */
export function validateVideoConfig(config: VideoConfig): boolean {
  const required = ['id', 'title', 'videoFile', 'subtitlesFile', 'layout'];
  return required.every(field => config[field as keyof VideoConfig] !== undefined);
}