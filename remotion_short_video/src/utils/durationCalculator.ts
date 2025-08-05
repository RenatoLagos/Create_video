import { staticFile } from 'remotion';
import { parseSRT } from './srtParser';
import { VideoConfig } from '../config/video-config';

/**
 * Calculate video duration based on subtitle timing
 */
export async function calculateVideoDuration(subtitlesFile: string, fps: number): Promise<number> {
  try {
    // In a real application, you would fetch the SRT file
    // For now, we'll use a synchronous approach with fetch
    const response = await fetch(staticFile(subtitlesFile));
    const srtContent = await response.text();
    const subtitles = parseSRT(srtContent);
    
    if (subtitles.length === 0) {
      console.warn('No subtitles found, using default duration');
      return 690; // Default 23 seconds at 30fps
    }

    // Get the end time of the last subtitle and add a buffer
    const lastSubtitle = subtitles[subtitles.length - 1];
    const durationInSeconds = lastSubtitle.endTime + 2; // Add 2 second buffer
    return Math.ceil(durationInSeconds * fps);
  } catch (error) {
    console.error('Error calculating duration:', error);
    return Math.ceil(23 * fps); // Fallback to 23 seconds
  }
}

/**
 * Update video config with calculated duration
 */
export async function updateConfigWithDuration(config: VideoConfig): Promise<VideoConfig> {
  if (config.durationInFrames) {
    // Duration already set, return as is
    return config;
  }

  const calculatedDuration = await calculateVideoDuration(config.subtitlesFile, config.fps);
  return {
    ...config,
    durationInFrames: calculatedDuration
  };
}

/**
 * Batch update multiple configs with calculated durations
 */
export async function updateAllConfigsWithDuration(configs: VideoConfig[]): Promise<VideoConfig[]> {
  const updatedConfigs = await Promise.all(
    configs.map(config => updateConfigWithDuration(config))
  );
  return updatedConfigs;
}