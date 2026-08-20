import { describe, it, expect } from "vitest";
import {
  LAB_PROGRAMS,
  canExecuteProgram,
  statusLabel,
} from "../programs/catalog";

describe("programs catalog V0.7", () => {
  it("includes required programs with correct statuses", () => {
    const byId = Object.fromEntries(LAB_PROGRAMS.map((p) => [p.id, p]));
    expect(byId["3utools"].status).toBe("operational");
    expect(byId["3utools"].toolId).toBe("windows.3utools.open");
    expect(byId.alpilab_check.status).toBe("operational");
    expect(byId.alpilab_check.toolId).toBeNull();
    expect(byId.thermal_camera.status).toBe("configured");
    expect(byId.microscope.status).toBe("configured");
    expect(byId.zxw.status).toBe("future");
    expect(byId.borneo.status).toBe("future");
  });

  it("only 3utools is executable from UI", () => {
    const executable = LAB_PROGRAMS.filter(canExecuteProgram);
    expect(executable.map((p) => p.id)).toEqual(["3utools"]);
  });

  it("status labels are user-facing", () => {
    expect(statusLabel("operational")).toBe("OPERATIVO");
    expect(statusLabel("configured")).toBe("NON ANCORA CONFIGURATO");
    expect(statusLabel("future")).toBe("INTEGRAZIONE FUTURA");
  });
});
