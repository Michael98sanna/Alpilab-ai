import type { CoreState } from "../types";

export type CoreStatusVariant = "idle" | "active" | "warning" | "error";

export interface CoreStatusConfig {
  /** Visible label in the status bar */
  label: string;
  /** Screen reader label */
  ariaLabel: string;
  variant: CoreStatusVariant;
}

/** Single source of truth: status → label → animation variant */
export const CORE_STATUS_CONFIG: Record<CoreState, CoreStatusConfig> = {
  IDLE: {
    label: "ALPILAB AI",
    ariaLabel: "Alpilab pronto",
    variant: "idle",
  },
  LISTENING: {
    label: "STO ASCOLTANDO...",
    ariaLabel: "Alpilab sta ascoltando",
    variant: "active",
  },
  THINKING: {
    label: "STO PENSANDO...",
    ariaLabel: "Alpilab sta elaborando",
    variant: "active",
  },
  SPEAKING: {
    label: "STO PARLANDO...",
    ariaLabel: "Alpilab sta parlando",
    variant: "active",
  },
  WORKING: {
    label: "STO LAVORANDO...",
    ariaLabel: "Alpilab sta eseguendo un'azione",
    variant: "active",
  },
  WARNING: {
    label: "ATTENZIONE",
    ariaLabel: "Alpilab — attenzione richiesta",
    variant: "warning",
  },
  ERROR: {
    label: "SI È VERIFICATO UN ERRORE",
    ariaLabel: "Alpilab — errore",
    variant: "error",
  },
};

export function getCoreStatusConfig(state: CoreState): CoreStatusConfig {
  return CORE_STATUS_CONFIG[state];
}
