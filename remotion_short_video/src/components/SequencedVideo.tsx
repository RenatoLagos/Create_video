import React, { useMemo, useEffect, useState } from 'react';
import { OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
// No longer importing the old components - implementing layouts inline
import { SubtitlesHighlight } from './SubtitlesHighlight';
import { parseSRT, getCurrentSubtitle, SubtitleEntry } from '../utils/srtParser';
import { 
  loadSegmentedPrompts, 
  getActiveSegment, 
  TimelineSegment, 
  LayoutType,
  logTimeline 
} from '../utils/segmentedPromptsParser';
import { CURRENT_FONT } from '../config/fonts';

interface SequencedVideoProps {
  videoFile: string;
  subtitlesFile: string;
  segmentedPromptsFile: string;
  debugMode?: boolean;
}

export const SequencedVideo: React.FC<SequencedVideoProps> = ({
  videoFile,
  subtitlesFile,
  segmentedPromptsFile,
  debugMode = false
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  const [timeline, setTimeline] = useState<TimelineSegment[]>([]);
  const [subtitles, setSubtitles] = useState<SubtitleEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load timeline and subtitles
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Load timeline from segmented prompts
        const timelineData = await loadSegmentedPrompts(staticFile(segmentedPromptsFile));
        setTimeline(timelineData);
        
        if (debugMode) {
          logTimeline(timelineData);
        }

        // Load subtitles
        const subtitlesResponse = await fetch(staticFile(subtitlesFile));
        const srtContent = await subtitlesResponse.text();
        const subtitlesData = parseSRT(srtContent);
        setSubtitles(subtitlesData);

        console.log(`✅ Loaded ${timelineData.length} timeline segments and ${subtitlesData.length} subtitle entries`);
        
      } catch (err) {
        console.error('Failed to load data:', err);
        setError(`Failed to load data: ${err}`);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [segmentedPromptsFile, subtitlesFile, debugMode]);

  // Get current active segment and layout
  const activeSegment = getActiveSegment(timeline, currentTime);
  const currentLayout: LayoutType = activeSegment?.layout || 'center';
  
  // Get current subtitle
  const currentSubtitle = getCurrentSubtitle(subtitles, currentTime);

  // Debug info
  const debugInfo = useMemo(() => {
    if (!debugMode) return null;
    
    return {
      currentTime: currentTime.toFixed(2),
      currentLayout,
      activeSegment: activeSegment ? {
        phraseNumber: activeSegment.phraseNumber,
        editingSuggestion: activeSegment.editingSuggestion,
        startTime: activeSegment.startTime,
        endTime: activeSegment.endTime
      } : null,
      currentSubtitle: currentSubtitle || 'No subtitle'
    };
  }, [currentTime, currentLayout, activeSegment, currentSubtitle, debugMode]);

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
        fontSize: '24px',
        flexDirection: 'column',
        gap: '20px'
      }}>
        <div>Loading sequenced video...</div>
        <div style={{ fontSize: '16px', opacity: 0.7 }}>
          Timeline: {segmentedPromptsFile}<br/>
          Subtitles: {subtitlesFile}<br/>
          Video: {videoFile}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#cc0000',
        color: 'white',
        fontSize: '20px',
        textAlign: 'center',
        padding: '40px'
      }}>
        <div>
          <div style={{ fontSize: '32px', marginBottom: '20px' }}>❌ Error</div>
          <div>{error}</div>
        </div>
      </div>
    );
  }

  // Render layout-specific video positioning and styling
  const renderVideoWithLayout = () => {
    const baseVideoProps = {
      src: staticFile(videoFile),
      style: {
        objectFit: 'cover' as const,
        objectPosition: 'center' as const
      }
    };

    switch (currentLayout) {
      case 'center':
        // Full video - like VideoVertical9x16Center
        return (
          <OffthreadVideo 
            {...baseVideoProps}
            style={{
              ...baseVideoProps.style,
              width: '100%',
              height: '100%'
            }}
          />
        );

      case 'bottom':
        // Video in bottom half - like VideoVertical9x16Bottom
        return (
          <div style={{ width: '100%', height: '100%', backgroundColor: '#000000' }}>
            <OffthreadVideo 
              {...baseVideoProps}
              style={{
                ...baseVideoProps.style,
                width: '100%',
                height: '50%',
                position: 'absolute',
                bottom: 0
              }}
            />
          </div>
        );

      case 'circle':
        // Circular video - like VideoVertical9x16Circle
        return (
          <div style={{ width: '100%', height: '100%', backgroundColor: '#000000' }}>
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
                {...baseVideoProps}
                style={{
                  ...baseVideoProps.style,
                  width: '100%',
                  height: '100%'
                }}
              />
            </div>
          </div>
        );

      default:
        return (
          <OffthreadVideo 
            {...baseVideoProps}
            style={{
              ...baseVideoProps.style,
              width: '100%',
              height: '100%'
            }}
          />
        );
    }
  };

  // Get subtitle positioning based on layout
  const getSubtitlePosition = () => {
    switch (currentLayout) {
      case 'center':
        return 'center';
      case 'bottom':
        return 'center'; // Positioned above video in bottom half
      case 'circle':
        return 'center';
      default:
        return 'bottom';
    }
  };

  // Get subtitle container style for bottom layout
  const getSubtitleContainerStyle = () => {
    if (currentLayout === 'bottom') {
      return {
        position: 'absolute' as const,
        top: '60%',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '100%',
        zIndex: 10
      };
    }
    return {};
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      {/* Main video with layout-specific positioning */}
      {renderVideoWithLayout()}
      
      {/* Subtitles with layout-appropriate positioning */}
      {currentSubtitle && (
        <div style={getSubtitleContainerStyle()}>
          <SubtitlesHighlight
            text={currentSubtitle}
            position={getSubtitlePosition() as 'top' | 'center' | 'bottom'}
            fontSize={64}
            fontFamily={CURRENT_FONT}
          />
        </div>
      )}
      
      {/* Debug overlay */}
      {debugMode && debugInfo && (
        <div style={{
          position: 'absolute',
          top: '10px',
          left: '10px',
          backgroundColor: 'rgba(0,0,0,0.8)',
          color: 'white',
          padding: '10px',
          fontSize: '12px',
          fontFamily: 'monospace',
          zIndex: 100,
          borderRadius: '5px'
        }}>
          <div>⏱️ Time: {debugInfo.currentTime}s</div>
          <div>🎬 Layout: {currentLayout.toUpperCase()}</div>
          <div>📝 Suggestion: {activeSegment?.editingSuggestion || 'None'}</div>
          <div>📖 Phrase: #{activeSegment?.phraseNumber || 'N/A'}</div>
          <div>💬 Subtitle: {debugInfo.currentSubtitle}</div>
        </div>
      )}
    </div>
  );
};