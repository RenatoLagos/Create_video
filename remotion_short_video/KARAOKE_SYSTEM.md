# Sistema Modular de Subtítulos Karaoke para Remotion

Este sistema permite reproducir en Remotion el mismo estilo de subtítulos karaoke que obtienes con SubMachine en Premiere, pero con una implementación modular y configurable que soporta diferentes plantillas (.mogrt) con distintos estilos y animaciones.

## 🏗️ Arquitectura del Sistema

### 1. Configuraciones de Plantillas (`src/configs/`)

Cada archivo JSON en esta carpeta define una plantilla completa:

- **`karaoke.json`** - Estilo karaoke clásico con slide & fade
- **`lower-thirds.json`** - Estilo de tercio inferior con fondo sólido
- **`elegant.json`** - Estilo elegante con animaciones suaves

#### Estructura de Configuración

```json
{
  "id": "nombre-plantilla",
  "name": "Nombre Descriptivo",
  "description": "Descripción del estilo",
  "typography": {
    "fontFamily": "Poppins",
    "fontWeight": 900,
    "fontSize": 64,
    "letterSpacing": "1px",
    "lineHeight": 1.2
  },
  "colors": {
    "primary": "#ffffff",
    "activeWord": "#ffff00",
    "unspokenWord": "#888888",
    "stroke": "#000000"
  },
  "animations": {
    "style": "slide-fade", // slide-fade | fade-only | scale-fade | none
    "duration": 0.3,
    "easing": "ease-out"
  },
  "chunking": {
    "maxChars": 7,
    "minDuration": 1.2,
    "fps": 30,
    "gapFrames": 0
  }
}
```

### 2. Utilidad de Procesamiento SRT (`src/utils/chunk-srt.ts`)

Procesa archivos .srt y los divide en fragmentos según la configuración:

```typescript
import { chunkSRT, getActiveChunkByTime } from '../utils/chunk-srt';

// Generar chunks desde subtítulos
const chunks = chunkSRT(subtitles, config.chunking);

// Obtener chunk activo en tiempo específico
const activeChunk = getActiveChunkByTime(chunks, currentTime, fps);
```

### 3. Componente de Renderizado (`src/components/SubtitleRenderer.tsx`)

Componente genérico que aplica estilos y animaciones:

```typescript
<SubtitleRenderer
  chunks={chunks}
  config={templateConfig}
  fps={fps}
/>
```

### 4. Componente Principal (`src/components/KaraokeVideo.tsx`)

Integra todo el sistema:

```typescript
<KaraokeVideo
  videoFile="video.mp4"
  subtitlesFile="subtitles.srt"
  templateStyle="karaoke" // opcional
  debugMode={true}
/>
```

## 🚀 Uso del Sistema

### Método 1: Variable de Entorno

Configura la variable `MOGRT_STYLE` para seleccionar la plantilla:

```bash
# Windows
set MOGRT_STYLE=karaoke
npx remotion render src/index.ts karaoke-env-style out/video.mp4

# Linux/Mac
MOGRT_STYLE=lower-thirds npx remotion render src/index.ts karaoke-env-style out/video.mp4
```

### Método 2: Configuración Directa

Usa composiciones específicas ya configuradas:

```bash
# Renderizar con estilo karaoke
npx remotion render src/index.ts karaoke-example out/karaoke.mp4

# Renderizar con estilo lower-thirds
npx remotion render src/index.ts lower-thirds-example out/lower-thirds.mp4
```

### Método 3: Configuración Programática

Crea nuevas composiciones en `Root.tsx`:

```typescript
const customKaraokeConfig = {
  id: 'mi-video-karaoke',
  videoFile: 'mi-video.mp4',
  subtitlesFile: 'mis-subtitulos.srt',
  templateStyle: 'elegant',
  debugMode: false
};
```

## 🎨 Creación de Nuevas Plantillas

### Paso 1: Crear Archivo de Configuración

Crea un nuevo archivo JSON en `src/configs/`:

```json
{
  "id": "mi-estilo",
  "name": "Mi Estilo Personalizado",
  "description": "Descripción de mi estilo",
  // ... resto de configuración
}
```

### Paso 2: Registrar Plantilla

Añade el nombre a la lista en `templateConfigLoader.ts`:

```typescript
export function getAvailableTemplates(): string[] {
  return ['karaoke', 'lower-thirds', 'elegant', 'mi-estilo'];
}
```

### Paso 3: Probar la Plantilla

```bash
MOGRT_STYLE=mi-estilo npx remotion render src/index.ts karaoke-env-style out/test.mp4
```

## 🔧 Parámetros de Configuración

### Tipografía
- `fontFamily`: Familia de fuente (Poppins, Figtree, Nunito)
- `fontWeight`: Peso de la fuente (100-900)
- `fontSize`: Tamaño en píxeles
- `letterSpacing`: Espaciado entre caracteres
- `lineHeight`: Altura de línea

### Colores
- `primary`: Color principal del texto
- `activeWord`: Color de la palabra activa (karaoke)
- `unspokenWord`: Color de palabras no habladas
- `stroke`: Color del contorno

### Animaciones
- `style`: Tipo de animación
  - `slide-fade`: Deslizamiento con fade
  - `fade-only`: Solo fade in/out
  - `scale-fade`: Escala con fade
  - `none`: Sin animaciones
- `duration`: Duración de la animación (segundos)
- `easing`: Tipo de easing

### Chunking (División de Texto)
- `maxChars`: Máximo caracteres por fragmento
- `minDuration`: Duración mínima por fragmento (segundos)
- `fps`: Frames por segundo
- `gapFrames`: Frames de separación entre fragmentos
- `wordBreakPriority`: Prioridad de caracteres para división

### Posicionamiento
- `position`: Posición vertical (top, center, bottom)
- `verticalAlign`: Alineación vertical
- `horizontalAlign`: Alineación horizontal
- `maxWidth`: Ancho máximo del contenedor
- `margin`: Márgenes del contenedor

## 🐛 Modo Debug

Activa el modo debug para ver información útil:

```typescript
<KaraokeVideo
  // ... otras props
  debugMode={true}
/>
```

Muestra:
- Información de la plantilla activa
- Estadísticas de chunks
- Configuración de chunking
- Indicador visual de plantilla

## 📁 Estructura de Archivos

```
src/
├── configs/                    # Configuraciones de plantillas
│   ├── karaoke.json           # Estilo karaoke clásico
│   ├── lower-thirds.json      # Estilo tercio inferior
│   └── elegant.json           # Estilo elegante
├── components/
│   ├── KaraokeVideo.tsx       # Componente principal
│   └── SubtitleRenderer.tsx   # Renderizador de subtítulos
└── utils/
    ├── chunk-srt.ts           # Procesamiento de SRT
    └── templateConfigLoader.ts # Carga de configuraciones
```

## 🎯 Casos de Uso

### Producción de Videos Educativos
```bash
MOGRT_STYLE=lower-thirds npx remotion render src/index.ts karaoke-env-style out/leccion.mp4
```

### Contenido de Redes Sociales
```bash
MOGRT_STYLE=karaoke npx remotion render src/index.ts karaoke-env-style out/social.mp4
```

### Presentaciones Corporativas
```bash
MOGRT_STYLE=elegant npx remotion render src/index.ts karaoke-env-style out/corporativo.mp4
```

## 🔄 Migración desde SubMachine

1. **Exporta tus subtítulos** desde Premiere como .srt
2. **Analiza los parámetros** de tu .mogrt en SubMachine
3. **Crea una configuración JSON** que replique esos parámetros
4. **Ajusta los valores** de chunking para obtener el timing deseado
5. **Renderiza y compara** con el resultado original

## 🚨 Solución de Problemas

### Error: "Configuración no encontrada"
- Verifica que el archivo JSON existe en `src/configs/`
- Comprueba que el nombre de la plantilla es correcto
- Revisa la sintaxis JSON

### Subtítulos no aparecen
- Verifica la ruta del archivo .srt
- Comprueba que el archivo .srt tiene el formato correcto
- Revisa la duración de la composición

### Animaciones no funcionan
- Verifica los parámetros de animación en la configuración
- Comprueba que la duración de la animación es apropiada
- Revisa los valores de easing

Este sistema te permite tener la flexibilidad de SubMachine directamente en Remotion, con la ventaja adicional de poder versionar y compartir configuraciones fácilmente.