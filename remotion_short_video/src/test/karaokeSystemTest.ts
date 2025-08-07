/**
 * Pruebas para el sistema modular de subtítulos karaoke
 * 
 * Este archivo contiene pruebas unitarias y de integración para validar
 * que el sistema de karaoke funciona correctamente con diferentes configuraciones.
 */

import { chunkSRT, getActiveChunk, SubtitleChunk } from '../utils/chunk-srt';
import { parseSRT, SubtitleEntry } from '../utils/srtParser';
import { loadTemplateConfig, getAvailableTemplates } from '../utils/templateConfigLoader';

// Datos de prueba
const mockSRTContent = `1
00:00:01,000 --> 00:00:03,000
Hola mundo, esto es una prueba

2
00:00:04,000 --> 00:00:07,000
De nuestro sistema de subtítulos karaoke

3
00:00:08,000 --> 00:00:10,000
Con diferentes configuraciones`;

const mockSubtitles: SubtitleEntry[] = [
  {
    id: 1,
    startTime: 1.0,
    endTime: 3.0,
    text: "Hola mundo, esto es una prueba"
  },
  {
    id: 2,
    startTime: 4.0,
    endTime: 7.0,
    text: "De nuestro sistema de subtítulos karaoke"
  },
  {
    id: 3,
    startTime: 8.0,
    endTime: 10.0,
    text: "Con diferentes configuraciones"
  }
];

/**
 * Prueba la funcionalidad de chunking con diferentes configuraciones
 */
export function testChunking() {
  console.log('🧪 Iniciando pruebas de chunking...');
  
  // Configuración de prueba para chunks cortos
  const shortChunkConfig = {
    maxChars: 5,
    minDuration: 1.0,
    fps: 30,
    gapFrames: 2,
    wordBreakPriority: [' ', ',', '.', ';', ':', '!', '?']
  };
  
  // Configuración de prueba para chunks largos
  const longChunkConfig = {
    maxChars: 15,
    minDuration: 2.0,
    fps: 30,
    gapFrames: 0,
    wordBreakPriority: [' ', ',', '.', ';', ':', '!', '?']
  };
  
  console.log('📊 Probando configuración de chunks cortos:');
  const shortChunks = chunkSRT(mockSubtitles, shortChunkConfig);
  console.log(`   - Subtítulos originales: ${mockSubtitles.length}`);
  console.log(`   - Chunks generados: ${shortChunks.length}`);
  
  console.log('📊 Probando configuración de chunks largos:');
  const longChunks = chunkSRT(mockSubtitles, longChunkConfig);
  console.log(`   - Subtítulos originales: ${mockSubtitles.length}`);
  console.log(`   - Chunks generados: ${longChunks.length}`);
  
  // Validar que los chunks tienen la estructura correcta
  shortChunks.forEach((chunk, index) => {
    if (!chunk.text || chunk.startFrame < 0 || chunk.endFrame <= chunk.startFrame) {
      console.error(`❌ Error en chunk ${index}:`, chunk);
    }
  });
  
  console.log('✅ Pruebas de chunking completadas');
  return { shortChunks, longChunks };
}

/**
 * Prueba la funcionalidad de obtener chunks activos
 */
export function testActiveChunkRetrieval() {
  console.log('🧪 Iniciando pruebas de recuperación de chunks activos...');
  
  const config = {
    maxChars: 8,
    minDuration: 1.5,
    fps: 30,
    gapFrames: 1,
    wordBreakPriority: [' ', ',', '.', ';', ':', '!', '?']
  };
  
  const chunks = chunkSRT(mockSubtitles, config);
  
  // Probar diferentes momentos
  const testTimes = [0.5, 1.5, 2.5, 4.5, 6.0, 8.5, 11.0];
  
  testTimes.forEach(time => {
    const frame = Math.round(time * config.fps);
    const activeChunk = getActiveChunk(chunks, frame);
    
    console.log(`⏰ Tiempo ${time}s (frame ${frame}):`);
    if (activeChunk) {
      console.log(`   - Chunk activo: "${activeChunk.text}"`);
      console.log(`   - Frames: ${activeChunk.startFrame} - ${activeChunk.endFrame}`);
    } else {
      console.log(`   - Sin chunk activo`);
    }
  });
  
  console.log('✅ Pruebas de recuperación de chunks completadas');
  return chunks;
}

/**
 * Prueba la carga de configuraciones de plantillas
 */
export async function testTemplateLoading() {
  console.log('🧪 Iniciando pruebas de carga de plantillas...');
  
  const availableTemplates = getAvailableTemplates();
  console.log(`📋 Plantillas disponibles: ${availableTemplates.join(', ')}`);
  
  // Probar carga de cada plantilla
  for (const templateName of availableTemplates) {
    try {
      console.log(`🔄 Cargando plantilla: ${templateName}`);
      const config = await loadTemplateConfig(templateName);
      
      console.log(`   ✅ ${config.name} cargada exitosamente`);
      console.log(`   - Estilo de animación: ${config.animations.style}`);
      console.log(`   - Max chars: ${config.chunking.maxChars}`);
      console.log(`   - Fuente: ${config.typography.fontFamily}`);
      
    } catch (error) {
      console.error(`   ❌ Error cargando ${templateName}:`, error);
    }
  }
  
  // Probar carga de plantilla inexistente
  try {
    console.log('🔄 Probando plantilla inexistente...');
    await loadTemplateConfig('plantilla-inexistente');
    console.log('   ✅ Configuración por defecto cargada correctamente');
  } catch (error) {
    console.error('   ❌ Error inesperado:', error);
  }
  
  console.log('✅ Pruebas de carga de plantillas completadas');
}

/**
 * Prueba la funcionalidad de parsing de SRT
 */
export function testSRTParsing() {
  console.log('🧪 Iniciando pruebas de parsing SRT...');
  
  const parsedSubtitles = parseSRT(mockSRTContent);
  
  console.log(`📄 Contenido SRT parseado:`);
  console.log(`   - Subtítulos encontrados: ${parsedSubtitles.length}`);
  
  parsedSubtitles.forEach((subtitle, index) => {
    console.log(`   ${index + 1}. "${subtitle.text}" (${subtitle.startTime}s - ${subtitle.endTime}s)`);
  });
  
  // Validar estructura
  const isValid = parsedSubtitles.every(sub => 
    sub.id > 0 && 
    sub.startTime >= 0 && 
    sub.endTime > sub.startTime && 
    sub.text.length > 0
  );
  
  if (isValid) {
    console.log('✅ Parsing SRT exitoso');
  } else {
    console.error('❌ Error en parsing SRT');
  }
  
  return parsedSubtitles;
}

/**
 * Ejecuta todas las pruebas del sistema
 */
export async function runAllTests() {
  console.log('🚀 Iniciando suite completa de pruebas del sistema karaoke...');
  console.log('=' .repeat(60));
  
  try {
    // Prueba 1: Parsing SRT
    testSRTParsing();
    console.log('');
    
    // Prueba 2: Chunking
    testChunking();
    console.log('');
    
    // Prueba 3: Recuperación de chunks activos
    testActiveChunkRetrieval();
    console.log('');
    
    // Prueba 4: Carga de plantillas
    await testTemplateLoading();
    console.log('');
    
    console.log('🎉 Todas las pruebas completadas exitosamente');
    
  } catch (error) {
    console.error('💥 Error durante las pruebas:', error);
  }
  
  console.log('=' .repeat(60));
}

/**
 * Genera estadísticas de rendimiento para diferentes configuraciones
 */
export function generatePerformanceStats() {
  console.log('📊 Generando estadísticas de rendimiento...');
  
  const configs = [
    { name: 'Chunks Cortos', maxChars: 5, minDuration: 1.0 },
    { name: 'Chunks Medianos', maxChars: 8, minDuration: 1.5 },
    { name: 'Chunks Largos', maxChars: 12, minDuration: 2.0 }
  ];
  
  configs.forEach(({ name, maxChars, minDuration }) => {
    const config = {
      maxChars,
      minDuration,
      fps: 30,
      gapFrames: 1,
      wordBreakPriority: [' ', ',', '.', ';', ':', '!', '?']
    };
    
    const startTime = performance.now();
    const chunks = chunkSRT(mockSubtitles, config);
    const endTime = performance.now();
    
    const avgChunkLength = chunks.reduce((sum, chunk) => sum + chunk.text.length, 0) / chunks.length;
    const totalDuration = chunks.reduce((sum, chunk) => sum + (chunk.endFrame - chunk.startFrame), 0) / config.fps;
    
    console.log(`📈 ${name}:`);
    console.log(`   - Tiempo de procesamiento: ${(endTime - startTime).toFixed(2)}ms`);
    console.log(`   - Chunks generados: ${chunks.length}`);
    console.log(`   - Longitud promedio: ${avgChunkLength.toFixed(1)} caracteres`);
    console.log(`   - Duración total: ${totalDuration.toFixed(1)}s`);
    console.log('');
  });
}

// Exportar función principal para uso en desarrollo
if (typeof window !== 'undefined') {
  (window as any).testKaraokeSystem = runAllTests;
  (window as any).karaokePerformanceStats = generatePerformanceStats;
}