/**
 * Script de ejemplo para demostrar el uso del sistema modular de subtítulos karaoke
 * 
 * Este archivo muestra diferentes formas de usar el sistema y puede ejecutarse
 * para probar las funcionalidades básicas.
 */

// Ejemplos de comandos para renderizar videos con diferentes estilos

const examples = {
  // Ejemplo 1: Usar variable de entorno para seleccionar estilo
  environmentStyle: {
    description: "Usar variable de entorno MOGRT_STYLE",
    commands: {
      windows: [
        "set MOGRT_STYLE=karaoke",
        "npx remotion render src/index.ts karaoke-env-style out/karaoke-env.mp4"
      ],
      linux: [
        "MOGRT_STYLE=lower-thirds npx remotion render src/index.ts karaoke-env-style out/lower-thirds-env.mp4"
      ]
    }
  },

  // Ejemplo 2: Usar composiciones predefinidas
  predefinedCompositions: {
    description: "Usar composiciones con estilos predefinidos",
    commands: {
      all: [
        "npx remotion render src/index.ts karaoke-example out/karaoke.mp4",
        "npx remotion render src/index.ts lower-thirds-example out/lower-thirds.mp4"
      ]
    }
  },

  // Ejemplo 3: Listar todas las composiciones disponibles
  listCompositions: {
    description: "Ver todas las composiciones disponibles",
    commands: {
      all: [
        "npx remotion compositions src/index.ts"
      ]
    }
  },

  // Ejemplo 4: Renderizar con diferentes configuraciones
  customConfigurations: {
    description: "Ejemplos con configuraciones personalizadas",
    commands: {
      all: [
        "# Renderizar con debug activado",
        "npx remotion render src/index.ts karaoke-example out/debug-karaoke.mp4 --props='{\"config\":{\"debugMode\":true}}'",
        "",
        "# Renderizar con archivo de subtítulos personalizado",
        "npx remotion render src/index.ts karaoke-example out/custom-srt.mp4 --props='{\"config\":{\"subtitlesFile\":\"mi-archivo.srt\"}}'"
      ]
    }
  }
};

// Configuraciones de plantilla disponibles
const availableTemplates = {
  karaoke: {
    description: "Estilo karaoke clásico con slide & fade",
    features: [
      "Animaciones slide-fade",
      "Chunks cortos (7 caracteres máx)",
      "Colores vibrantes",
      "Fuente Poppins bold"
    ],
    bestFor: "Videos musicales, contenido dinámico"
  },
  
  "lower-thirds": {
    description: "Estilo de tercio inferior profesional",
    features: [
      "Animaciones fade-only",
      "Chunks largos (12 caracteres máx)",
      "Fondo sólido",
      "Fuente Figtree"
    ],
    bestFor: "Documentales, entrevistas, contenido educativo"
  },
  
  elegant: {
    description: "Estilo elegante con animaciones suaves",
    features: [
      "Animaciones scale-fade",
      "Chunks medianos (9 caracteres máx)",
      "Tipografía refinada",
      "Fuente Nunito"
    ],
    bestFor: "Presentaciones corporativas, contenido premium"
  }
};

// Función para mostrar ejemplos de uso
function showUsageExamples() {
  console.log('🎬 Sistema Modular de Subtítulos Karaoke - Ejemplos de Uso');
  console.log('=' .repeat(70));
  
  Object.entries(examples).forEach(([key, example]) => {
    console.log(`\n📋 ${example.description}`);
    console.log('-' .repeat(50));
    
    Object.entries(example.commands).forEach(([platform, commands]) => {
      if (platform !== 'all') {
        console.log(`\n${platform.toUpperCase()}:`);
      }
      
      commands.forEach(command => {
        if (command.startsWith('#')) {
          console.log(`\n${command}`);
        } else if (command === '') {
          console.log('');
        } else {
          console.log(`  ${command}`);
        }
      });
    });
  });
}

// Función para mostrar información de plantillas
function showTemplateInfo() {
  console.log('\n\n🎨 Plantillas Disponibles');
  console.log('=' .repeat(70));
  
  Object.entries(availableTemplates).forEach(([name, info]) => {
    console.log(`\n📄 ${name.toUpperCase()}`);
    console.log(`   ${info.description}`);
    console.log(`   💡 Mejor para: ${info.bestFor}`);
    console.log('   ✨ Características:');
    info.features.forEach(feature => {
      console.log(`      • ${feature}`);
    });
  });
}

// Función para mostrar estructura de archivos
function showFileStructure() {
  console.log('\n\n📁 Estructura de Archivos del Sistema');
  console.log('=' .repeat(70));
  
  const structure = `
src/
├── configs/                    # 🎛️  Configuraciones de plantillas
│   ├── karaoke.json           #     Estilo karaoke clásico
│   ├── lower-thirds.json      #     Estilo tercio inferior
│   └── elegant.json           #     Estilo elegante
├── components/
│   ├── KaraokeVideo.tsx       # 🎬 Componente principal
│   └── SubtitleRenderer.tsx   # 🎨 Renderizador de subtítulos
├── utils/
│   ├── chunk-srt.ts           # ✂️  Procesamiento de SRT
│   └── templateConfigLoader.ts # 📥 Carga de configuraciones
└── test/
    └── karaokeSystemTest.ts   # 🧪 Pruebas del sistema
`;
  
  console.log(structure);
}

// Función para mostrar comandos de desarrollo
function showDevelopmentCommands() {
  console.log('\n\n🛠️  Comandos de Desarrollo');
  console.log('=' .repeat(70));
  
  const devCommands = [
    {
      command: 'npm run dev',
      description: 'Iniciar servidor de desarrollo'
    },
    {
      command: 'npx remotion preview src/index.ts',
      description: 'Abrir preview interactivo'
    },
    {
      command: 'npx remotion compositions src/index.ts',
      description: 'Listar todas las composiciones'
    },
    {
      command: 'npx remotion render src/index.ts [composition] out/video.mp4',
      description: 'Renderizar composición específica'
    },
    {
      command: 'npx remotion render src/index.ts [composition] out/video.mp4 --props="{...}"',
      description: 'Renderizar con props personalizadas'
    }
  ];
  
  devCommands.forEach(({ command, description }) => {
    console.log(`\n📝 ${command}`);
    console.log(`   ${description}`);
  });
}

// Función principal
function main() {
  showUsageExamples();
  showTemplateInfo();
  showFileStructure();
  showDevelopmentCommands();
  
  console.log('\n\n🚀 ¡Listo para usar el sistema de subtítulos karaoke!');
  console.log('📖 Consulta KARAOKE_SYSTEM.md para documentación completa');
  console.log('=' .repeat(70));
}

// Ejecutar si se llama directamente
if (require.main === module) {
  main();
}

// Exportar para uso en otros archivos
module.exports = {
  examples,
  availableTemplates,
  showUsageExamples,
  showTemplateInfo,
  showFileStructure,
  showDevelopmentCommands
};