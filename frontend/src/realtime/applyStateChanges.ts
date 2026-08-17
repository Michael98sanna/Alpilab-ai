import type { DiagnosticTest, RepairState } from "../types";
import { mapDiagnosticStatus } from "./types";

type Changes = Record<string, unknown>;

function mapDiagnosticTest(raw: Record<string, unknown>): DiagnosticTest {
  return {
    id: String(raw.id),
    name: String(raw.name),
    value: raw.value ? String(raw.value) : undefined,
    status: mapDiagnosticStatus(String(raw.status)),
  };
}

export function applySessionChanges(state: RepairState, changes: Changes): RepairState {
  let next = state;

  if (changes.repair_context && typeof changes.repair_context === "object") {
    const ctx = changes.repair_context as Record<string, unknown>;
    next = {
      ...next,
      session: {
        ...next.session,
        ...(ctx.label !== undefined ? { label: String(ctx.label) } : {}),
        ...(ctx.device !== undefined
          ? { device: ctx.device ? String(ctx.device) : null }
          : {}),
        ...(ctx.issue !== undefined
          ? { issue: ctx.issue ? String(ctx.issue) : null }
          : {}),
        ...(ctx.status !== undefined
          ? { status: ctx.status === "paused" ? "paused" : "active" }
          : {}),
        ...(ctx.diagnosis_label !== undefined
          ? { diagnosisLabel: String(ctx.diagnosis_label) }
          : {}),
      },
    };
  }

  if (changes.diagnostic_test && typeof changes.diagnostic_test === "object") {
    const test = mapDiagnosticTest(changes.diagnostic_test as Record<string, unknown>);
    next = {
      ...next,
      tests: next.tests.map((t) => (t.id === test.id ? { ...t, ...test } : t)),
      savingTestId: null,
      stateError: null,
    };
  }

  if (Array.isArray(changes.diagnostics)) {
    next = {
      ...next,
      tests: changes.diagnostics.map((t) =>
        mapDiagnosticTest(t as Record<string, unknown>),
      ),
      savingTestId: null,
      stateError: null,
    };
  }

  if (typeof changes.assistant_status === "string") {
    next = {
      ...next,
      coreState: changes.assistant_status as RepairState["coreState"],
    };
  }

  return next;
}
