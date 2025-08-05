import { parseSRT } from './srtParser';

export interface KaraokeChunk {
  start: number; // Frame de inicio
  end: number;   // Frame de fin
  text: string;  // Texto del chunk
  originalSubtitleId: number; // ID del subtítulo original
  chunkIndex: number; // Índice del chunk dentro del subtítulo
}

export interface ChunkingOptions {
  maxChars?: number;    // Máximo de caracteres por chunk (default: 7)
  minDuration?: number; // Duración mínima en segundos (default: 1.2)
  fps?: number;         // Frames por segundo (default: 30)
  gapFrames?: number;   // Frames de separación entre chunks (default: 0)
}

/**
 * Convierte un archivo SRT en chunks para animación karaoke
 * Divide cada línea de subtítulo en fragmentos de máximo X caracteres
 * con una duración mínima especificada
 */
export function chunkSrtForKaraoke(
  srtContent: string,
  options: ChunkingOptions = {}
): KaraokeChunk[] {
  const {
    maxChars = 7,
    minDuration = 1.2,
    fps = 30,
    gapFrames = 0
  } = options;

  // Parsear el SRT usando nuestro parser existente
  const items = parseSRT(srtContent);
  const chunks: KaraokeChunk[] = [];

  console.log(`🎤 Karaoke Chunker iniciando con ${items.length} subtítulos`);
  console.log(`📏 Configuración: maxChars=${maxChars}, minDuration=${minDuration}s, fps=${fps}`);

  for (let itemIndex = 0; itemIndex < items.length; itemIndex++) {
    const item = items[itemIndex];
    
    if (!item.startTime || !item.endTime || !item.text) {
      console.warn(`⚠️ Subtítulo ${itemIndex + 1} incompleto, saltando...`);
      continue;
    }

    // Limpiar el texto y dividir en palabras
    const cleanText = item.text.replace(/\n/g, ' ').trim();
    const words = cleanText.split(/\s+/).filter((word: string) => word.length > 0);
    
    if (words.length === 0) {
      console.warn(`⚠️ Subtítulo ${itemIndex + 1} sin palabras válidas, saltando...`);
      continue;
    }

    console.log(`📝 Procesando subtítulo ${itemIndex + 1}: "${cleanText}" (${words.length} palabras)`);

    // Calcular duración total disponible (startTime y endTime ya están en segundos)
    const totalDurationSeconds = item.endTime - item.startTime;

    // Agrupar palabras en chunks
    const wordChunks: string[][] = [];
    let currentChunk: string[] = [];

    for (let i = 0; i < words.length; i++) {
      const word = words[i];
      const testChunk = [...currentChunk, word];
      const testText = testChunk.join(' ');

      // Si agregar esta palabra excede el límite de caracteres
      if (currentChunk.length > 0 && testText.length > maxChars) {
        // Guardar el chunk actual y empezar uno nuevo
        wordChunks.push([...currentChunk]);
        currentChunk = [word];
      } else {
        // Agregar la palabra al chunk actual
        currentChunk.push(word);
      }

      // Si es la última palabra, guardar el chunk
      if (i === words.length - 1 && currentChunk.length > 0) {
        wordChunks.push([...currentChunk]);
      }
    }

    console.log(`🔄 Dividido en ${wordChunks.length} chunks:`, wordChunks.map(chunk => `"${chunk.join(' ')}"`));

    // Convertir chunks de palabras a chunks con timing
    for (let chunkIndex = 0; chunkIndex < wordChunks.length; chunkIndex++) {
      const wordChunk = wordChunks[chunkIndex];
      const chunkText = wordChunk.join(' ');

      // Calcular duración por chunk
      let chunkDuration = totalDurationSeconds / wordChunks.length;
      chunkDuration = Math.max(chunkDuration, minDuration);

      // Calcular timing (startTime y endTime ya están en segundos)
      const startTimeSeconds = item.startTime + (chunkIndex * (totalDurationSeconds / wordChunks.length));
      const endTimeSeconds = startTimeSeconds + chunkDuration;

      // Convertir a frames
      const startFrame = Math.round(startTimeSeconds * fps);
      const endFrame = Math.round(endTimeSeconds * fps);

      // Aplicar gap si es necesario
      const finalStartFrame = startFrame + (chunkIndex * gapFrames);
      const finalEndFrame = endFrame + (chunkIndex * gapFrames);

      const chunk: KaraokeChunk = {
        start: finalStartFrame,
        end: finalEndFrame,
        text: chunkText,
        originalSubtitleId: itemIndex + 1,
        chunkIndex: chunkIndex
      };

      chunks.push(chunk);

      console.log(`✅ Chunk ${chunkIndex + 1}/${wordChunks.length}: "${chunkText}" (frames ${finalStartFrame}-${finalEndFrame})`);
    }
  }

  console.log(`🎯 Chunking completado: ${chunks.length} chunks generados`);
  return chunks;
}

/**
 * Calcula la duración total en frames necesaria para todos los chunks
 */
export function calculateTotalDuration(chunks: KaraokeChunk[]): number {
  if (chunks.length === 0) return 0;
  
  const maxEndFrame = Math.max(...chunks.map(chunk => chunk.end));
  return maxEndFrame + 30; // Agregar 30 frames de buffer al final
}

/**
 * Obtiene todos los chunks activos en un frame específico
 */
export function getActiveChunks(chunks: KaraokeChunk[], frame: number): KaraokeChunk[] {
  return chunks.filter(chunk => frame >= chunk.start && frame <= chunk.end);
}

/**
 * Obtiene el chunk que debería estar activo en un frame específico
 * (solo devuelve el primer chunk activo si hay múltiples)
 */
export function getCurrentChunk(chunks: KaraokeChunk[], frame: number): KaraokeChunk | null {
  const activeChunks = getActiveChunks(chunks, frame);
  return activeChunks.length > 0 ? activeChunks[0] : null;
}

/**
 * Calcula el progreso de animación para un chunk en un frame específico
 * Retorna un valor entre 0 y 1
 */
export function getChunkProgress(chunk: KaraokeChunk, frame: number): number {
  if (frame < chunk.start) return 0;
  if (frame > chunk.end) return 1;
  
  const totalFrames = chunk.end - chunk.start;
  const currentFrames = frame - chunk.start;
  
  return Math.min(Math.max(currentFrames / totalFrames, 0), 1);
}