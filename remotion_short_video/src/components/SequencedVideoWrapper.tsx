import React from 'react';
import { SequencedVideo } from './SequencedVideo';
import { SequencedVideoConfig } from '../utils/sequencedConfigLoader';

/**
 * Wrapper component for SequencedVideo to handle props from Remotion
 */
interface SequencedVideoWrapperProps {
  config: SequencedVideoConfig;
}

export const SequencedVideoWrapper: React.FC<SequencedVideoWrapperProps> = ({ config }) => {
  return (
    <SequencedVideo
      videoFile={config.videoFile}
      subtitlesFile={config.subtitlesFile}
      segmentedPromptsFile={config.segmentedPromptsFile}
      debugMode={config.debugMode}
    />
  );
};