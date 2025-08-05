import { staticFile } from 'remotion';
import { parseSRT, SubtitleEntry } from './srtParser';

/**
 * Dynamically load SRT file content
 */
export async function loadSubtitlesFromFile(subtitlesFile: string): Promise<SubtitleEntry[]> {
  try {
    const response = await fetch(staticFile(subtitlesFile));
    const srtContent = await response.text();
    return parseSRT(srtContent);
  } catch (error) {
    console.error('Error loading subtitles:', error);
    return [];
  }
}

/**
 * Load subtitles synchronously for use in Remotion components
 * This returns a promise that should be resolved in useMemo
 */
export function loadSubtitles(subtitlesFile: string): Promise<SubtitleEntry[]> {
  return loadSubtitlesFromFile(subtitlesFile);
}

/**
 * Calculate video duration in frames based on the longest subtitle or video metadata
 */
export function calculateDurationFromSubtitles(subtitles: SubtitleEntry[], fps: number): number {
  if (subtitles.length === 0) return 690; // fallback to default

  const lastSubtitle = subtitles[subtitles.length - 1];
  const durationInSeconds = lastSubtitle.endTime + 1; // Add 1 second buffer
  return Math.ceil(durationInSeconds * fps);
}

/**
 * Utility to get video metadata (duration) - for future implementation
 * This would require additional setup for video metadata extraction
 */
export function getVideoDuration(videoFile: string): Promise<number> {
  return new Promise((resolve) => {
    // For now, return a default duration
    // In a full implementation, this would analyze video metadata
    resolve(23); // 23 seconds default
  });
}