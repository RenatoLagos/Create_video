import { SubtitleEntry } from './srtParser';

export interface ChunkConfig {
  maxChars: number;
  minDuration: number;
  fps: number;
  gapFrames: number;
  wordBreakPriority: string[];
}

export interface SubtitleChunk {
  startFrame: number;
  endFrame: number;
  text: string;
  originalSubtitle: SubtitleEntry;
  chunkIndex: number;
  totalChunks: number;
}

/**
 * Procesa subtítulos SRT y los divide en fragmentos según la configuración
 */
export function chunkSRT(
  subtitles: SubtitleEntry[],
  config: ChunkConfig
): SubtitleChunk[] {
  const chunks: SubtitleChunk[] = [];
  
  console.log('🔄 Iniciando chunking de SRT con configuración:', config);
  
  subtitles.forEach((subtitle) => {
    const subtitleChunks = chunkSingleSubtitle(subtitle, config);
    chunks.push(...subtitleChunks);
  });
  
  console.log(`✅ Chunking completado: ${chunks.length} fragmentos generados`);
  return chunks;
}

/**
 * Divide un subtítulo individual en fragmentos
 */
function chunkSingleSubtitle(
  subtitle: SubtitleEntry,
  config: ChunkConfig
): SubtitleChunk[] {
  const { maxChars, minDuration, fps, gapFrames } = config;
  const text = subtitle.text.trim();
  
  // Si el texto es corto, devolver como un solo fragmento
  if (text.length <= maxChars) {
    return [{
      startFrame: Math.round(subtitle.startTime * fps),
      endFrame: Math.round(subtitle.endTime * fps),
      text,
      originalSubtitle: subtitle,
      chunkIndex: 0,
      totalChunks: 1
    }];
  }
  
  // Dividir el texto en fragmentos
  const textChunks = splitTextIntoChunks(text, maxChars, config.wordBreakPriority);
  const totalDuration = subtitle.endTime - subtitle.startTime;
  const minFrameDuration = Math.round(minDuration * fps);
  
  // Calcular duración por fragmento
  const baseDurationPerChunk = totalDuration / textChunks.length;
  const frameDurationPerChunk = Math.max(
    Math.round(baseDurationPerChunk * fps),
    minFrameDuration
  );
  
  const chunks: SubtitleChunk[] = [];
  let currentStartFrame = Math.round(subtitle.startTime * fps);
  
  textChunks.forEach((chunkText, index) => {
    const startFrame = currentStartFrame;
    const endFrame = startFrame + frameDurationPerChunk;
    
    chunks.push({
      startFrame,
      endFrame,
      text: chunkText.trim(),
      originalSubtitle: subtitle,
      chunkIndex: index,
      totalChunks: textChunks.length
    });
    
    // Añadir gap entre fragmentos
    currentStartFrame = endFrame + gapFrames;
  });
  
  // Ajustar el último fragmento para que termine con el subtítulo original
  if (chunks.length > 0) {
    const lastChunk = chunks[chunks.length - 1];
    lastChunk.endFrame = Math.round(subtitle.endTime * fps);
  }
  
  return chunks;
}

/**
 * Divide texto en fragmentos respetando las prioridades de ruptura
 */
function splitTextIntoChunks(
  text: string,
  maxChars: number,
  breakPriority: string[]
): string[] {
  const chunks: string[] = [];
  let remainingText = text;
  
  while (remainingText.length > 0) {
    if (remainingText.length <= maxChars) {
      chunks.push(remainingText);
      break;
    }
    
    // Buscar el mejor punto de ruptura
    let bestBreakPoint = -1;
    let bestPriority = -1;
    
    for (let i = 0; i < Math.min(maxChars, remainingText.length); i++) {
      const char = remainingText[i];
      const priority = breakPriority.indexOf(char);
      
      if (priority !== -1 && priority > bestPriority) {
        bestBreakPoint = i;
        bestPriority = priority;
      }
    }
    
    // Si no se encuentra un buen punto de ruptura, cortar en maxChars
    if (bestBreakPoint === -1) {
      bestBreakPoint = maxChars - 1;
    }
    
    // Extraer el fragmento
    const chunk = remainingText.substring(0, bestBreakPoint + 1);
    chunks.push(chunk);
    remainingText = remainingText.substring(bestBreakPoint + 1);
  }
  
  return chunks.filter(chunk => chunk.trim().length > 0);
}

/**
 * Obtiene el fragmento activo en un frame específico
 */
export function getActiveChunk(
  chunks: SubtitleChunk[],
  currentFrame: number
): SubtitleChunk | null {
  return chunks.find(
    chunk => currentFrame >= chunk.startFrame && currentFrame <= chunk.endFrame
  ) || null;
}

/**
 * Obtiene todos los fragmentos activos en un tiempo específico (en segundos)
 */
export function getActiveChunkByTime(
  chunks: SubtitleChunk[],
  currentTime: number,
  fps: number
): SubtitleChunk | null {
  const currentFrame = Math.round(currentTime * fps);
  return getActiveChunk(chunks, currentFrame);
}