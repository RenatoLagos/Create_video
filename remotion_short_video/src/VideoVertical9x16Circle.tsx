import React, { useMemo } from 'react';
import { OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { SubtitlesHighlight } from './components/SubtitlesHighlight';
import { parseSRT, getCurrentSubtitle } from './utils/srtParser';
import { CURRENT_FONT } from './config/fonts';

export const VideoVertical9x16Circle: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  const currentTime = frame / fps;

  // Subtitles will be passed as props from the sequenced video system
  const subtitles = useMemo(() => {
    return []; // Empty - will be handled by parent component
  }, []);

  const currentSubtitle = getCurrentSubtitle(subtitles, currentTime);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', backgroundColor: '#000000' }}>
      {/* Video en círculo - superior izquierda */}
      <div style={{
        position: 'absolute',
        top: '40px',
        left: '40px',
        width: '350px',
        height: '350px',
        borderRadius: '50%',
        overflow: 'hidden',
        border: '4px solid #ffffff',
        zIndex: 10
      }}>
        <OffthreadVideo 
          src={staticFile("video.mp4")} 
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center'
          }}
        />
      </div>
      
      {/* Subtítulos en el medio */}
      {currentSubtitle && (
        <SubtitlesHighlight
          text={currentSubtitle}
          position="center"
          fontFamily={CURRENT_FONT}
        />
      )}
    </div>
  );
}; 