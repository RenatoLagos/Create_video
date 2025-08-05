import { chunkSrtForKaraoke, calculateTotalDuration, getCurrentChunk, getChunkProgress } from '../utils/karaokeChunker';
import fs from 'fs';
import path from 'path';

/**
 * Función de prueba para validar el chunker de karaoke
 */
export function testKaraokeChunker() {
  console.log('🧪 Iniciando pruebas del Karaoke Chunker...\n');

  try {
    // Leer el archivo SRT de prueba
    const srtPath = path.join(process.cwd(), 'public/video/03_VideoProcessing/03_subtitles/clean_subtitles.srt');
    const srtContent = fs.readFileSync(srtPath, 'utf-8');

    console.log('📄 Archivo SRT cargado correctamente\n');

    // Probar con diferentes configuraciones
    const testConfigs = [
      { name: 'Configuración por defecto', options: {} },
      { name: 'Chunks cortos (5 chars)', options: { maxChars: 5 } },
      { name: 'Chunks largos (10 chars)', options: { maxChars: 10 } },
      { name: 'Duración mínima larga (2s)', options: { minDuration: 2.0 } },
      { name: 'Con gaps entre chunks', options: { gapFrames: 5 } }
    ];

    for (const config of testConfigs) {
      console.log(`\n🔍 Probando: ${config.name}`);
      console.log('─'.repeat(50));

      const chunks = chunkSrtForKaraoke(srtContent, config.options);
      const totalDuration = calculateTotalDuration(chunks);

      console.log(`📊 Resultados:`);
      console.log(`   • Total de chunks: ${chunks.length}`);
      console.log(`   • Duración total: ${totalDuration} frames (${(totalDuration / 30).toFixed(2)}s)`);
      
      // Mostrar algunos chunks de ejemplo
      console.log(`   • Primeros 3 chunks:`);
      chunks.slice(0, 3).forEach((chunk, index) => {
        console.log(`     ${index + 1}. "${chunk.text}" (${chunk.start}-${chunk.end})`);
      });

      // Probar funciones utilitarias
      if (chunks.length > 0) {
        const testFrame = chunks[0].start + 10;
        const currentChunk = getCurrentChunk(chunks, testFrame);
        const progress = currentChunk ? getChunkProgress(currentChunk, testFrame) : 0;
        
        console.log(`   • Prueba frame ${testFrame}:`);
        console.log(`     - Chunk activo: "${currentChunk?.text || 'ninguno'}"`);
        console.log(`     - Progreso: ${(progress * 100).toFixed(1)}%`);
      }
    }

    console.log('\n✅ Todas las pruebas completadas exitosamente!');
    return true;

  } catch (error) {
    console.error('❌ Error en las pruebas:', error);
    return false;
  }
}

// Ejecutar pruebas si el archivo se ejecuta directamente
if (require.main === module) {
  testKaraokeChunker();
}