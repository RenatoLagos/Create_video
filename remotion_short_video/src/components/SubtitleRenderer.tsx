import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { SubtitleChunk } from '../utils/chunk-srt';

interface SubtitleConfig {
  id: string;
  name: string;
  description: string;
  typography: {
    fontFamily: string;
    fontWeight: number;
    fontSize: number;
    letterSpacing: string;
    lineHeight: number;
  };
  colors: {
    primary: string;
    activeWord: string;
    unspokenWord: string;
    stroke: string;
  };
  stroke: {
    width: number;
    enabled: boolean;
  };
  wordBackground: {
    enabled: boolean;
    color: string;
    opacity: number;
    borderRadius: number;
    padding: {
      horizontal: number;
      vertical: number;
    };
  };
  spacing: {
    lineSpacing: number;
    wordSpacing: string;
  };
  animations: {
    style: 'slide-fade' | 'fade-only' | 'scale-fade' | 'none';
    duration: number;
    easing: string;
    slideDistance: number;
    fadeInDelay: number;
    fadeOutDelay: number;
    scaleEffect: {
      enabled: boolean;
      scale: number;
      duration: number;
    };
  };
  positioning: {
    position: 'top' | 'center' | 'bottom';
    verticalAlign: 'top' | 'center' | 'bottom';
    horizontalAlign: 'left' | 'center' | 'right';
    maxWidth: string;
    margin: {
      top: string;
      bottom: string;
      left: string;
      right: string;
    };
  };
}

interface SubtitleRendererProps {
  chunks: SubtitleChunk[];
  config: SubtitleConfig;
  fps: number;
}

export const SubtitleRenderer: React.FC<SubtitleRendererProps> = ({
  chunks,
  config,
  fps
}) => {
  const frame = useCurrentFrame();
  
  // Encontrar el fragmento activo
  const activeChunk = chunks.find(
    chunk => frame >= chunk.startFrame && frame <= chunk.endFrame
  );
  
  if (!activeChunk) {
    return null;
  }
  
  // Calcular progreso de la animación
  const animationDurationFrames = Math.round(config.animations.duration * fps);
  
  // Animaciones de entrada y salida
  const fadeInProgress = interpolate(
    frame,
    [activeChunk.startFrame, activeChunk.startFrame + animationDurationFrames],
    [0, 1],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: getEasing(config.animations.easing)
    }
  );
  
  const fadeOutProgress = interpolate(
    frame,
    [activeChunk.endFrame - animationDurationFrames, activeChunk.endFrame],
    [1, 0],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: getEasing(config.animations.easing)
    }
  );
  
  const opacity = Math.min(fadeInProgress, fadeOutProgress);
  
  // Calcular transformaciones según el estilo de animación
  const getAnimationTransform = (): React.CSSProperties => {
    const { style, slideDistance, scaleEffect } = config.animations;
    let transform = '';
    
    switch (style) {
      case 'slide-fade':
        const slideY = interpolate(
          fadeInProgress,
          [0, 1],
          [slideDistance, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );
        transform += `translateY(${slideY}px) `;
        break;
        
      case 'scale-fade':
        if (scaleEffect.enabled) {
          const scale = interpolate(
            fadeInProgress,
            [0, 1],
            [scaleEffect.scale, 1],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          );
          transform += `scale(${scale}) `;
        }
        break;
        
      case 'fade-only':
      case 'none':
      default:
        // Solo fade, sin transformaciones adicionales
        break;
    }
    
    return { transform: transform.trim() || 'none' };
  };
  
  // Estilos de posicionamiento
  const getPositionStyles = (): React.CSSProperties => {
    const { position, horizontalAlign, margin } = config.positioning;
    
    let positionStyles: React.CSSProperties = {
      position: 'absolute',
      maxWidth: config.positioning.maxWidth,
    };
    
    // Posicionamiento horizontal
    switch (horizontalAlign) {
      case 'left':
        positionStyles.left = margin.left;
        break;
      case 'right':
        positionStyles.right = margin.right;
        break;
      case 'center':
      default:
        positionStyles.left = '50%';
        positionStyles.transform = 'translateX(-50%)';
        break;
    }
    
    // Posicionamiento vertical
    switch (position) {
      case 'top':
        positionStyles.top = margin.top;
        break;
      case 'bottom':
        positionStyles.bottom = margin.bottom;
        break;
      case 'center':
      default:
        positionStyles.top = '50%';
        positionStyles.transform = positionStyles.transform 
          ? `${positionStyles.transform} translateY(-50%)`
          : 'translateY(-50%)';
        break;
    }
    
    return positionStyles;
  };
  
  // Estilos de tipografía
  const getTypographyStyles = (): React.CSSProperties => {
    const { typography, colors, stroke, wordBackground, spacing } = config;
    
    let styles: React.CSSProperties = {
      fontFamily: getFontFamily(typography.fontFamily),
      fontWeight: typography.fontWeight,
      fontSize: `${typography.fontSize}px`,
      letterSpacing: typography.letterSpacing,
      lineHeight: typography.lineHeight,
      color: colors.primary,
      margin: 0,
      padding: 0,
      textAlign: 'center',
      wordSpacing: spacing.wordSpacing,
    };
    
    // Aplicar stroke si está habilitado
    if (stroke.enabled) {
      styles.WebkitTextStroke = `${stroke.width}px ${colors.stroke}`;
      styles.paintOrder = 'stroke fill';
    }
    
    // Aplicar fondo de palabra si está habilitado
    if (wordBackground.enabled) {
      styles.backgroundColor = wordBackground.color;
      styles.borderRadius = `${wordBackground.borderRadius}px`;
      styles.padding = `${wordBackground.padding.vertical}px ${wordBackground.padding.horizontal}px`;
    }
    
    return styles;
  };
  
  const positionStyles = getPositionStyles();
  const animationTransform = getAnimationTransform();
  const typographyStyles = getTypographyStyles();
  
  // Combinar transformaciones
  const finalTransform = [
    positionStyles.transform || '',
    animationTransform.transform || ''
  ].filter(Boolean).join(' ');
  
  return (
    <div
      style={{
        ...positionStyles,
        transform: finalTransform || 'none',
        opacity,
        zIndex: 10,
        textRendering: 'optimizeLegibility',
        WebkitFontSmoothing: 'antialiased',
        MozOsxFontSmoothing: 'grayscale',
      }}
    >
      <p style={typographyStyles}>
        {activeChunk.text}
      </p>
      
      {/* Debug info (opcional) */}
      {process.env.NODE_ENV === 'development' && (
        <div style={{
          position: 'absolute',
          top: '-30px',
          left: '0',
          fontSize: '12px',
          color: 'yellow',
          backgroundColor: 'rgba(0,0,0,0.7)',
          padding: '2px 6px',
          borderRadius: '3px'
        }}>
          Chunk {activeChunk.chunkIndex + 1}/{activeChunk.totalChunks} | Frame: {frame}
        </div>
      )}
    </div>
  );
};

// Utilidades auxiliares
function getFontFamily(fontName: string): string {
  const fontMap: Record<string, string> = {
    'Figtree': "'Figtree', 'Montserrat', system-ui, -apple-system, sans-serif",
    'Poppins': "'Poppins', 'Montserrat', system-ui, -apple-system, sans-serif",
    'Nunito': "'Nunito', 'Montserrat', system-ui, -apple-system, sans-serif"
  };
  
  return fontMap[fontName] || fontMap['Poppins'];
}

function getEasing(easingName: string): (input: number) => number {
  const easingMap: Record<string, (input: number) => number> = {
    'ease-in': Easing.in(Easing.ease),
    'ease-out': Easing.out(Easing.ease),
    'ease-in-out': Easing.inOut(Easing.ease),
    'linear': Easing.linear,
  };
  
  return easingMap[easingName] || Easing.out(Easing.ease);
}