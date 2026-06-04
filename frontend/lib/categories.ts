// Per-category accent colours + icons used across cards, the category grid and
// detail pages. Keyed by category name; falls back to a neutral accent.

export interface CategoryStyle {
  /** Accent colour (hex) for borders, dots and chips. */
  accent: string;
  /** Translucent background tint for chips. */
  tint: string;
  icon: string;
}

const STYLES: Record<string, CategoryStyle> = {
  Music: { accent: "#f472b6", tint: "rgba(244,114,182,0.14)", icon: "🎵" },
  Tech: { accent: "#60a5fa", tint: "rgba(96,165,250,0.14)", icon: "💻" },
  Art: { accent: "#fbbf24", tint: "rgba(251,191,36,0.14)", icon: "🎨" },
  Theatre: { accent: "#a78bfa", tint: "rgba(167,139,250,0.14)", icon: "🎭" },
  Sports: { accent: "#34d399", tint: "rgba(52,211,153,0.14)", icon: "🏟️" },
  "Food & Drink": { accent: "#fb923c", tint: "rgba(251,146,60,0.14)", icon: "🍷" },
  Film: { accent: "#f87171", tint: "rgba(248,113,113,0.14)", icon: "🎬" },
  Community: { accent: "#2dd4bf", tint: "rgba(45,212,191,0.14)", icon: "🌍" },
};

const FALLBACK: CategoryStyle = {
  accent: "#7c6cff",
  tint: "rgba(124,108,255,0.14)",
  icon: "📌",
};

export function categoryStyle(name: string | null | undefined): CategoryStyle {
  if (!name) return FALLBACK;
  return STYLES[name] ?? FALLBACK;
}
