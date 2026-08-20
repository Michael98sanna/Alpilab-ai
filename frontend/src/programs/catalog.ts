/**
 * Lab programs catalog for UI V0.7.
 * toolId is the only executable identifier (never display name → shell).
 */

export type ProgramStatus = "operational" | "configured" | "future";

export type ProgramId =
  | "3utools"
  | "alpilab_check"
  | "thermal_camera"
  | "microscope"
  | "zxw"
  | "borneo";

export interface LabProgram {
  id: ProgramId;
  name: string;
  icon: string;
  description: string;
  status: ProgramStatus;
  /** Executable ToolRegistry id when operational and openable. */
  toolId: string | null;
  /** NL phrase for voice-ready / chat parity (same identifiers later). */
  voiceHint: string;
  actionLabel: string;
}

export const LAB_PROGRAMS: LabProgram[] = [
  {
    id: "3utools",
    name: "3uTools",
    icon: "🟢",
    description: "Utility Windows per dispositivi Apple",
    status: "operational",
    toolId: "windows.3utools.open",
    voiceHint: "Apri 3uTools",
    actionLabel: "Apri",
  },
  {
    id: "alpilab_check",
    name: "Alpilab Check",
    icon: "🟡",
    description: "Software Alpilab Check (listino via bridge in chat; apertura app non configurata)",
    status: "configured",
    toolId: null,
    voiceHint: "Apri Alpilab Check",
    actionLabel: "Apri",
  },
  {
    id: "thermal_camera",
    name: "Termocamera",
    icon: "🟡",
    description: "Software diagnostico termocamera",
    status: "configured",
    toolId: null,
    voiceHint: "Apri il programma della termocamera",
    actionLabel: "Apri",
  },
  {
    id: "microscope",
    name: "Microscopio",
    icon: "🟡",
    description: "Software microscopio",
    status: "configured",
    toolId: null,
    voiceHint: "Apri il microscopio",
    actionLabel: "Apri",
  },
  {
    id: "zxw",
    name: "ZXW",
    icon: "⚪",
    description: "Schematics / documentazione tecnica",
    status: "future",
    toolId: null,
    voiceHint: "Apri ZXW",
    actionLabel: "Integrazione futura",
  },
  {
    id: "borneo",
    name: "Borneo",
    icon: "⚪",
    description: "Software Borneo",
    status: "future",
    toolId: null,
    voiceHint: "Apri Borneo",
    actionLabel: "Integrazione futura",
  },
];

export function statusLabel(status: ProgramStatus): string {
  switch (status) {
    case "operational":
      return "OPERATIVO";
    case "configured":
      return "NON ANCORA CONFIGURATO";
    case "future":
      return "INTEGRAZIONE FUTURA";
  }
}

export function canExecuteProgram(program: LabProgram): boolean {
  return program.status === "operational" && program.toolId !== null;
}
