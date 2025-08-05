// Configuración de fuentes para subtítulos
export type FontFamily = 'Figtree' | 'Poppins' | 'Nunito';

export interface FontConfig {
  name: FontFamily;
  displayName: string;
  description: string;
  bestFor: string;
}

export const AVAILABLE_FONTS: FontConfig[] = [
  {
    name: 'Figtree',
    displayName: 'Figtree',
    description: 'Geométrica y moderna, similar a Aventra',
    bestFor: 'UI y diseño moderno'
  },
  {
    name: 'Poppins', 
    displayName: 'Poppins',
    description: 'Redondeada y muy legible',
    bestFor: 'Contenido amigable y accesible'
  },
  {
    name: 'Nunito',
    displayName: 'Nunito',
    description: 'Suave y elegante',
    bestFor: 'Texto largo y subtítulos'
  }
];

// Fuente por defecto
export const DEFAULT_FONT: FontFamily = 'Figtree';

// Para cambiar la fuente globalmente, modifica esta constante
export const CURRENT_FONT: FontFamily = 'Poppins'; // Cambia aquí: 'Figtree' | 'Poppins' | 'Nunito' 