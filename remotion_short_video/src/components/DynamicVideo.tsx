import React, { useMemo, useEffect, useState } from 'react';
import { OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { SubtitlesHighlight } from './SubtitlesHighlight';
import { getCurrentSubtitle, SubtitleEntry } from '../utils/srtParser';
import { VideoConfig } from '../config/video-config';
import { loadSubtitles, calculateDurationFromSubtitles } from '../utils/dynamicLoader';

interface DynamicVideoProps {
  config: VideoConfig;
}

export const DynamicVideo: React.FC<DynamicVideoProps> = ({ config }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const [subtitles, setSubtitles] = useState<SubtitleEntry[]>([]);
  const [loading, setLoading] = useState(true);
  
  const currentTime = frame / fps;

  // Load subtitles dynamically
  useEffect(() => {
    const loadSubs = async () => {
      setLoading(true);
      try {
        const loadedSubtitles = await loadSubtitles(config.subtitlesFile);
        setSubtitles(loadedSubtitles);
      } catch (error) {
        console.error('Failed to load subtitles:', error);
        setSubtitles([]);
      } finally {
        setLoading(false);
      }
    };

    loadSubs();
  }, [config.subtitlesFile]);

  const currentSubtitle = getCurrentSubtitle(subtitles, currentTime);

  // Render different layouts based on configuration
  const renderVideoLayout = () => {
    const { layout, layoutSpecific } = config;

    switch (layout) {
      case 'center':
        return (
          <OffthreadVideo 
            src={staticFile(config.videoFile)} 
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              objectPosition: 'center'
            }}
          />
        );

      case 'bottom':
        const bottomConfig = layoutSpecific?.bottom;
        return (
          <>
            <OffthreadVideo 
              src={staticFile(config.videoFile)} 
              style={{
                width: '100%',
                height: bottomConfig?.videoHeight || '50%',
                position: 'absolute',
                bottom: 0,
                objectFit: 'cover',
                objectPosition: 'center'
              }}
            />
          </>
        );

      case 'circle':
        const circleConfig = layoutSpecific?.circle;
        return (
          <div style={{
            position: 'absolute',
            top: `${circleConfig?.position.top || 40}px`,
            left: `${circleConfig?.position.left || 40}px`,
            width: `${circleConfig?.size || 350}px`,
            height: `${circleConfig?.size || 350}px`,
            borderRadius: '50%',
            overflow: 'hidden',
            border: `${circleConfig?.borderWidth || 4}px solid ${circleConfig?.borderColor || '#ffffff'}`,
            zIndex: 10
          }}>
            <OffthreadVideo 
              src={staticFile(config.videoFile)} 
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                objectPosition: 'center'
              }}
            />
          </div>
        );

      default:
        return null;
    }
  };

  // Get container styles based on layout
  const getContainerStyles = (): React.CSSProperties => {
    const { layout, layoutSpecific } = config;
    
    const baseStyles: React.CSSProperties = {
      width: '100%',
      height: '100%',
      position: 'relative'
    };

    if (layout === 'bottom' || layout === 'circle') {
      return {
        ...baseStyles,
        backgroundColor: layoutSpecific?.bottom?.backgroundColor || '#000000'
      };
    }

    return baseStyles;
  };

  // Get subtitle positioning for bottom layout
  const getSubtitleContainer = () => {
    const { layout, layoutSpecific, subtitlesConfig } = config;

    if (layout === 'bottom') {
      const bottomConfig = layoutSpecific?.bottom;
      return (
        <div style={{
          position: 'absolute',
          top: bottomConfig?.subtitlesTop || '60%',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '100%',
          zIndex: 10
        }}>
          <SubtitlesHighlight
            text={currentSubtitle || ''}
            position={subtitlesConfig.position}
            fontSize={subtitlesConfig.fontSize}
            fontFamily={subtitlesConfig.fontFamily}
            color={subtitlesConfig.color}
            strokeWidth={subtitlesConfig.strokeWidth}
            strokeColor={subtitlesConfig.strokeColor}
          />
        </div>
      );
    }

    // Default subtitle positioning for center and circle layouts
    return (
      <SubtitlesHighlight
        text={currentSubtitle || ''}
        position={subtitlesConfig.position}
        fontSize={subtitlesConfig.fontSize}
        fontFamily={subtitlesConfig.fontFamily}
        color={subtitlesConfig.color}
        strokeWidth={subtitlesConfig.strokeWidth}
        strokeColor={subtitlesConfig.strokeColor}
      />
    );
  };

  if (loading) {
    return (
      <div style={{ 
        width: '100%', 
        height: '100%', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        backgroundColor: '#000000',
        color: 'white',
        fontSize: '24px'
      }}>
        Loading subtitles...
      </div>
    );
  }

  return (
    <div style={getContainerStyles()}>
      {renderVideoLayout()}
      {currentSubtitle && getSubtitleContainer()}
    </div>
  );
};