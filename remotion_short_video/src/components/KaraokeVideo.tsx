import React, { useState, useEffect } from 'react';
import { OffthreadVideo, staticFile, useVideoConfig } from 'remotion';
import { SubtitleRenderer } from './SubtitleRenderer';
import { chunkSRT, SubtitleChunk } from '../utils/chunk-srt';
import { parseSRT, SubtitleEntry } from '../utils/srtParser';
import { loadTemplateConfig, getTemplateConfigFromEnv, TemplateConfig } from '../utils/templateConfigLoader';

interface KaraokeVideoProps {
  videoFile: string;
  subtitlesFile: string;
  templateStyle?: string; // Opcional, si no se proporciona usa MOGRT_STYLE env var
  debugMode?: boolean;
}

export const KaraokeVideo: React.FC<KaraokeVideoProps> = ({
  videoFile,
  subtitlesFile,
  templateStyle,
  debugMode = false
}) => {
  const { fps } = useVideoConfig();
  const [subtitles, setSubtitles] = useState<SubtitleEntry[]>([]);
  const [chunks, setChunks] = useState<SubtitleChunk[]>([]);
  const [templateConfig, setTemplateConfig] = useState<TemplateConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [subtitlesFile, templateStyle]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('🚀 Iniciando carga de datos para KaraokeVideo');
      
      // 1. Cargar configuración de plantilla
      let config: TemplateConfig;
      if (templateStyle) {
        config = await loadTemplateConfig(templateStyle);
      } else {
        config = await getTemplateConfigFromEnv();
      }
      setTemplateConfig(config);
      
      // 2. Cargar y parsear subtítulos
      console.log('📄 Cargando subtítulos desde:', subtitlesFile);
      const response = await fetch(staticFile(subtitlesFile));
      if (!response.ok) {
        throw new Error(`Error al cargar subtítulos: ${response.status}`);
      }
      
      const srtContent = await response.text();
      const parsedSubtitles = parseSRT(srtContent);
      setSubtitles(parsedSubtitles);
      
      // 3. Generar chunks usando la configuración
      console.log('✂️ Generando chunks con configuración:', config.name);
      const generatedChunks = chunkSRT(parsedSubtitles, config.chunking);
      setChunks(generatedChunks);
      
      console.log('✅ Datos cargados exitosamente');
      console.log(`📊 Estadísticas:`);
      console.log(`   - Subtítulos originales: ${parsedSubtitles.length}`);
      console.log(`   - Chunks generados: ${generatedChunks.length}`);
      console.log(`   - Plantilla: ${config.name}`);
      
    } catch (err) {
      console.error('❌ Error al cargar datos:', err);
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  // Mostrar estado de carga
  if (loading) {
    return (
      <div style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#000000',
        color: 'white',
        fontSize: '24px'
      }}>
        <div>🔄 Cargando configuración karaoke...</div>
        {debugMode && (
          <div style={{ fontSize: '14px', marginTop: '10px', opacity: 0.7 }}>
            Plantilla: {templateStyle || 'desde variable de entorno'}
          </div>
        )}
      </div>
    );
  }

  // Mostrar error
  if (error || !templateConfig) {
    return (
      <div style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#000000',
        color: '#ff4444',
        fontSize: '20px',
        padding: '20px',
        textAlign: 'center'
      }}>
        <div>❌ Error al cargar configuración</div>
        <div style={{ fontSize: '14px', marginTop: '10px', opacity: 0.8 }}>
          {error || 'Configuración de plantilla no disponible'}
        </div>
        {debugMode && (
          <div style={{ fontSize: '12px', marginTop: '20px', opacity: 0.6 }}>
            Archivo de subtítulos: {subtitlesFile}<br/>
            Plantilla solicitada: {templateStyle || 'variable de entorno'}
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      {/* Video principal */}
      <OffthreadVideo
        src={staticFile(videoFile)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover'
        }}
      />
      
      {/* Subtítulos karaoke */}
      <SubtitleRenderer
        chunks={chunks}
        config={templateConfig}
        fps={fps}
      />
      
      {/* Panel de debug (opcional) */}
      {debugMode && (
        <div style={{
          position: 'absolute',
          top: '10px',
          left: '10px',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          color: 'white',
          padding: '10px',
          borderRadius: '5px',
          fontSize: '12px',
          fontFamily: 'monospace',
          maxWidth: '300px',
          zIndex: 20
        }}>
          <div><strong>🎬 Debug Info</strong></div>
          <div>Plantilla: {templateConfig.name}</div>
          <div>Estilo: {templateConfig.animations.style}</div>
          <div>Subtítulos: {subtitles.length}</div>
          <div>Chunks: {chunks.length}</div>
          <div>Max chars: {templateConfig.chunking.maxChars}</div>
          <div>Min duration: {templateConfig.chunking.minDuration}s</div>
          <div>FPS: {fps}</div>
        </div>
      )}
      
      {/* Indicador de plantilla (esquina superior derecha) */}
      {debugMode && (
        <div style={{
          position: 'absolute',
          top: '10px',
          right: '10px',
          backgroundColor: templateConfig.colors.primary,
          color: templateConfig.colors.stroke,
          padding: '5px 10px',
          borderRadius: '15px',
          fontSize: '12px',
          fontWeight: 'bold',
          zIndex: 20
        }}>
          {templateConfig.id.toUpperCase()}
        </div>
      )}
    </div>
  );
};

// Componente wrapper para usar con Remotion
interface KaraokeVideoWrapperProps {
  config: {
    videoFile: string;
    subtitlesFile: string;
    templateStyle?: string;
    debugMode?: boolean;
  };
}

export const KaraokeVideoWrapper: React.FC<KaraokeVideoWrapperProps> = ({ config }) => {
  return (
    <KaraokeVideo
      videoFile={config.videoFile}
      subtitlesFile={config.subtitlesFile}
      templateStyle={config.templateStyle}
      debugMode={config.debugMode}
    />
  );
};