import React from 'react';
import { DynamicVideo } from './DynamicVideo';
import { VideoConfig } from '../config/video-config';

/**
 * Wrapper component to handle dynamic video configurations
 * This component receives the configuration as props from Remotion
 */
interface DynamicVideoWrapperProps {
  config: VideoConfig;
}

export const DynamicVideoWrapper: React.FC<DynamicVideoWrapperProps> = ({ config }) => {
  return <DynamicVideo config={config} />;
};