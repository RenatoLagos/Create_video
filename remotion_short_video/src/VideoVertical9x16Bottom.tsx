import React, { useMemo } from 'react';
import { OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { SubtitlesHighlight } from './components/SubtitlesHighlight';
import { parseSRT, getCurrentSubtitle } from './utils/srtParser';
import { CURRENT_FONT } from './config/fonts';

export const VideoVertical9x16Bottom: React.FC = () => {
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
      {/* Video en la mitad inferior */}
      <OffthreadVideo 
        src={staticFile("video.mp4")} 
        style={{
          width: '100%',
          height: '50%',
          position: 'absolute',
          bottom: 0,
          objectFit: 'cover',
          objectPosition: 'center'
        }}
      />
      
      {/* Subtítulos ligeramente abajo del centro */}
      {currentSubtitle && (
        <div style={{
          position: 'absolute',
          top: '60%',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '100%',
          zIndex: 10
        }}>
          <SubtitlesHighlight
            text={currentSubtitle}
            position="center"
            fontSize={64}
            fontFamily={CURRENT_FONT}
          />
        </div>
      )}
    </div>
  );
}; 