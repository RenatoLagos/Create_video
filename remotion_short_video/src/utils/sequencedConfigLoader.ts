/**
 * Configuration loader for sequenced videos
 * Loads configuration for videos that use timeline-based layout switching
 */

export interface SequencedVideoConfig {
  id: string;
  title: string;
  videoFile: string;
  subtitlesFile: string;
  segmentedPromptsFile: string;
  fps: number;
  width: number;
  height: number;
  debugMode?: boolean;
  durationInFrames?: number; // Will be calculated if not provided
}

export interface SequencedVideoCollection {
  defaultConfig: Partial<SequencedVideoConfig>;
  videos: SequencedVideoConfig[];
}

import sequencedVideosData from '../config/sequenced-videos.json';

/**
 * Load sequenced video configuration from JSON
 */
export function loadSequencedVideoCollection(): SequencedVideoCollection {
  return sequencedVideosData as SequencedVideoCollection;
}

/**
 * Get a specific sequenced video configuration by ID
 */
export function getSequencedVideoConfig(videoId: string): SequencedVideoConfig | null {
  const collection = loadSequencedVideoCollection();
  const videoData = collection.videos.find(video => video.id === videoId);
  
  if (!videoData) {
    console.error(`Sequenced video configuration not found for ID: ${videoId}`);
    return null;
  }

  // Merge with default configuration
  const mergedConfig = {
    ...collection.defaultConfig,
    ...videoData,
  };

  return mergedConfig as SequencedVideoConfig;
}

/**
 * Get all available sequenced video configurations
 */
export function getAllSequencedVideoConfigs(): SequencedVideoConfig[] {
  const collection = loadSequencedVideoCollection();
  return collection.videos.map(videoData => {
    const mergedConfig = {
      ...collection.defaultConfig,
      ...videoData,
    };
    return mergedConfig as SequencedVideoConfig;
  });
}

/**
 * Calculate duration from segmented prompts file
 */
export async function calculateSequencedVideoDuration(segmentedPromptsFile: string, fps: number): Promise<number> {
  try {
    const response = await fetch(segmentedPromptsFile);
    const data = await response.json();
    
    // Find the latest end time from all phrases
    const phrases = data.analysis?.phrases_with_video_prompts || [];
    let maxEndTime = 0;
    
    phrases.forEach((phrase: any) => {
      if (phrase.segmentation?.segments) {
        phrase.segmentation.segments.forEach((segment: any) => {
          if (segment.timing?.end_time > maxEndTime) {
            maxEndTime = segment.timing.end_time;
          }
        });
      } else if (phrase.timing?.end_time > maxEndTime) {
        maxEndTime = phrase.timing.end_time;
      }
    });
    
    // Add 2 second buffer
    const durationInSeconds = maxEndTime + 2;
    return Math.ceil(durationInSeconds * fps);
  } catch (error) {
    console.error('Error calculating sequenced video duration:', error);
    return Math.ceil(40 * fps); // Fallback to 40 seconds
  }
}

/**
 * Update sequenced video config with calculated duration
 */
export async function updateSequencedConfigWithDuration(config: SequencedVideoConfig): Promise<SequencedVideoConfig> {
  if (config.durationInFrames) {
    // Duration already set, return as is
    return config;
  }

  const calculatedDuration = await calculateSequencedVideoDuration(config.segmentedPromptsFile, config.fps);
  return {
    ...config,
    durationInFrames: calculatedDuration
  };
}