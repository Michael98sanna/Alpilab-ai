/**
 * Lab programs catalog for UI V0.7+.
 * toolId is the only executable identifier (never display name → shell).
 */

export type ProgramStatus =
  | "operational"
  | "configured"
  | "unavailable"
  | "future";

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
    icon: "🟢",
    description: "Programma gestionale / laboratorio",
    status: "operational",
    toolId: "windows.alpilab_check.open",
    voiceHint: "Apri Alpilab Check",
    actionLabel: "Apri",
  },
  {
    id: "thermal_camera",
    name: "Termocamera",
    icon: "🟢",
    description: "Software diagnostico termocamera",
    status: "operational",
    toolId: "windows.thermal_camera.open",
    voiceHint: "Apri il programma della termocamera",
    actionLabel: "Apri",
  },
  {
    id: "microscope",
    name: "Microscopio",
    icon: "🟢",
    description: "Software microscopio",
    status: "operational",
    toolId: "windows.microscope.open",
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
    icon: "🟢",
    description: "Software Borneo Schematics",
    status: "operational",
    toolId: "windows.borneo.open",
    voiceHint: "Apri Borneo",
    actionLabel: "Apri",
  },
];

export function statusLabel(status: ProgramStatus): string {
  switch (status) {
    case "operational":
      return "OPERATIVO";
    case "configured":
      return "NON ANCORA CONFIGURATO";
    case "unavailable":
      return "NON DISPONIBILE";
    case "future":
      return "INTEGRAZIONE FUTURA";
  }
}

export function canExecuteProgram(program: LabProgram): boolean {
  return (
    program.status === "operational" &&
    program.toolId !== null
  );
}

export type OpenableToolId =
  | "windows.3utools.open"
  | "windows.alpilab_check.open"
  | "windows.thermal_camera.open"
  | "windows.microscope.open"
  | "windows.borneo.open";

export function isOpenableToolId(toolId: string | null): toolId is OpenableToolId {
  return (
    toolId === "windows.3utools.open" ||
    toolId === "windows.alpilab_check.open" ||
    toolId === "windows.thermal_camera.open" ||
    toolId === "windows.microscope.open" ||
    toolId === "windows.borneo.open"
  );
}
