import { staticFile } from 'remotion';

export interface TemplateConfig {
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
  chunking: {
    maxChars: number;
    minDuration: number;
    fps: number;
    gapFrames: number;
    wordBreakPriority: string[];
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

/**
 * Carga una configuración de plantilla desde un archivo JSON
 */
export async function loadTemplateConfig(templateName: string): Promise<TemplateConfig> {
  try {
    console.log(`🔄 Cargando configuración de plantilla: ${templateName}`);
    
    const configPath = `configs/${templateName}.json`;
    const response = await fetch(staticFile(configPath));
    
    if (!response.ok) {
      throw new Error(`Error al cargar configuración: ${response.status} ${response.statusText}`);
    }
    
    const config: TemplateConfig = await response.json();
    
    // Validar configuración
    validateTemplateConfig(config);
    
    console.log(`✅ Configuración cargada exitosamente:`, config.name);
    return config;
    
  } catch (error) {
    console.error(`❌ Error al cargar configuración de plantilla '${templateName}':`, error);
    
    // Devolver configuración por defecto en caso de error
    return getDefaultTemplateConfig();
  }
}

/**
 * Obtiene la configuración de plantilla basada en variable de entorno
 */
export async function getTemplateConfigFromEnv(): Promise<TemplateConfig> {
  // Obtener el estilo desde variable de entorno o usar 'karaoke' por defecto
  const templateStyle = process.env.MOGRT_STYLE || 'karaoke';
  
  console.log(`🎯 Usando estilo de plantilla: ${templateStyle}`);
  
  return await loadTemplateConfig(templateStyle);
}

/**
 * Lista todas las configuraciones de plantilla disponibles
 */
export function getAvailableTemplates(): string[] {
  // En un entorno real, esto podría leer dinámicamente el directorio
  // Por ahora, devolvemos una lista estática
  return ['karaoke', 'lower-thirds'];
}

/**
 * Valida que una configuración de plantilla tenga todos los campos requeridos
 */
function validateTemplateConfig(config: any): void {
  const requiredFields = [
    'id', 'name', 'description', 'typography', 'colors', 'stroke',
    'wordBackground', 'spacing', 'animations', 'chunking', 'positioning'
  ];
  
  for (const field of requiredFields) {
    if (!config[field]) {
      throw new Error(`Campo requerido faltante en configuración: ${field}`);
    }
  }
  
  // Validaciones específicas
  if (!config.typography.fontFamily || !config.typography.fontSize) {
    throw new Error('Configuración de tipografía incompleta');
  }
  
  if (!config.chunking.maxChars || !config.chunking.minDuration) {
    throw new Error('Configuración de chunking incompleta');
  }
}

/**
 * Configuración por defecto en caso de error
 */
function getDefaultTemplateConfig(): TemplateConfig {
  return {
    id: 'default',
    name: 'Default Style',
    description: 'Configuración por defecto de emergencia',
    typography: {
      fontFamily: 'Poppins',
      fontWeight: 900,
      fontSize: 64,
      letterSpacing: '1px',
      lineHeight: 1.2
    },
    colors: {
      primary: '#ffffff',
      activeWord: '#ffff00',
      unspokenWord: '#888888',
      stroke: '#000000'
    },
    stroke: {
      width: 22,
      enabled: true
    },
    wordBackground: {
      enabled: false,
      color: 'rgba(0, 0, 0, 0.7)',
      opacity: 0.8,
      borderRadius: 8,
      padding: {
        horizontal: 12,
        vertical: 6
      }
    },
    spacing: {
      lineSpacing: 1.4,
      wordSpacing: '0.2em'
    },
    animations: {
      style: 'fade-only',
      duration: 0.3,
      easing: 'ease-out',
      slideDistance: 0,
      fadeInDelay: 0.1,
      fadeOutDelay: 0.1,
      scaleEffect: {
        enabled: false,
        scale: 1.0,
        duration: 0
      }
    },
    chunking: {
      maxChars: 7,
      minDuration: 1.2,
      fps: 30,
      gapFrames: 0,
      wordBreakPriority: [' ', ',', '.', ';', ':', '!', '?']
    },
    positioning: {
      position: 'center',
      verticalAlign: 'center',
      horizontalAlign: 'center',
      maxWidth: '90%',
      margin: {
        top: '5%',
        bottom: '5%',
        left: '5%',
        right: '5%'
      }
    }
  };
}

/**
 * Combina configuración base con overrides específicos
 */
export function mergeTemplateConfig(
  baseConfig: TemplateConfig,
  overrides: Partial<TemplateConfig>
): TemplateConfig {
  return {
    ...baseConfig,
    ...overrides,
    typography: {
      ...baseConfig.typography,
      ...overrides.typography
    },
    colors: {
      ...baseConfig.colors,
      ...overrides.colors
    },
    animations: {
      ...baseConfig.animations,
      ...overrides.animations
    },
    chunking: {
      ...baseConfig.chunking,
      ...overrides.chunking
    },
    positioning: {
      ...baseConfig.positioning,
      ...overrides.positioning
    }
  };
}