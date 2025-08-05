import fs from 'fs';
import path from 'path';
import { ChunkingOptions } from './karaokeChunker';

export interface KaraokeVideoConfig {
  id: string;
  title: string;
  videoFile: string;
  subtitlesFile: string;
  karaokeOptions: ChunkingOptions;
  style: string; // Para futuros estilos: 'slide-fade', 'neon-glow', 'typewriter', etc.
  fps: number;
  width: number;
  height: number;
  durationInFrames?: number;
}

/**
 * Carga todas las configuraciones de video karaoke disponibles
 */
export function getAllKaraokeVideoConfigs(): KaraokeVideoConfig[] {
  try {
    const configPath = path.join(process.cwd(), 'src/config/karaoke-config.json');
    
    if (!fs.existsSync(configPath)) {
      console.warn('⚠️ Archivo karaoke-config.json no encontrado, creando configuración por defecto');
      return getDefaultKaraokeConfigs();
    }

    const configData = fs.readFileSync(configPath, 'utf-8');
    const configs = JSON.parse(configData) as KaraokeVideoConfig[];

    console.log(`📋 Cargadas ${configs.length} configuraciones de karaoke`);
    
    // Validar configuraciones
    const validConfigs = configs.filter(config => {
      if (!config.id || !config.title || !config.subtitlesFile) {
        console.warn(`⚠️ Configuración inválida saltada: ${config.id || 'sin ID'}`);
        return false;
      }
      return true;
    });

    return validConfigs;
  } catch (error) {
    console.error('❌ Error cargando configuraciones de karaoke:', error);
    return getDefaultKaraokeConfigs();
  }
}

/**
 * Obtiene una configuración específica por ID
 */
export function getKaraokeVideoConfig(id: string): KaraokeVideoConfig | null {
  const configs = getAllKaraokeVideoConfigs();
  return configs.find(config => config.id === id) || null;
}

/**
 * Configuraciones por defecto en caso de error
 */
function getDefaultKaraokeConfigs(): KaraokeVideoConfig[] {
  return [
    {
      id: 'karaoke-default',
      title: 'Default Karaoke Video',
      videoFile: 'video.mp4',
      subtitlesFile: 'video/03_VideoProcessing/03_subtitles/clean_subtitles.srt',
      karaokeOptions: {
        maxChars: 7,
        minDuration: 1.2,
        fps: 30,
        gapFrames: 0
      },
      style: 'slide-fade',
      fps: 30,
      width: 1920,
      height: 1920,
      durationInFrames: 1800
    }
  ];
}

/**
 * Valida si existe el archivo SRT especificado en la configuración
 */
export function validateKaraokeConfig(config: KaraokeVideoConfig): boolean {
  const srtPath = path.join(process.cwd(), 'public', config.subtitlesFile);
  
  if (!fs.existsSync(srtPath)) {
    console.error(`❌ Archivo SRT no encontrado: ${srtPath}`);
    return false;
  }

  console.log(`✅ Configuración karaoke válida: ${config.id}`);
  return true;
}

/**
 * Obtiene la ruta completa del archivo SRT
 */
export function getKaraokeSrtPath(config: KaraokeVideoConfig): string {
  return path.join(process.cwd(), 'public', config.subtitlesFile);
}

/**
 * Obtiene la ruta completa del archivo de video
 */
export function getKaraokeVideoPath(config: KaraokeVideoConfig): string {
  return path.join(process.cwd(), 'public', config.videoFile);
}