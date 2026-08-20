/**
 * System clipboard helpers. Never log clipboard contents.
 */

export async function writeClipboardText(text: string): Promise<boolean> {
  if (!text) return false;
  try {
    if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    /* fall through */
  }
  return fallbackCopy(text);
}

export async function readClipboardText(): Promise<string | null> {
  try {
    if (typeof navigator !== "undefined" && navigator.clipboard?.readText) {
      return await navigator.clipboard.readText();
    }
  } catch {
    return null;
  }
  return null;
}

function fallbackCopy(text: string): boolean {
  if (typeof document === "undefined") return false;
  const el = document.createElement("textarea");
  el.value = text;
  el.setAttribute("readonly", "");
  el.style.position = "fixed";
  el.style.left = "-9999px";
  document.body.appendChild(el);
  el.select();
  let ok = false;
  try {
    ok = document.execCommand("copy");
  } catch {
    ok = false;
  }
  document.body.removeChild(el);
  return ok;
}

export function getDomSelectionText(): string {
  if (typeof window === "undefined") return "";
  return window.getSelection()?.toString() ?? "";
}

export function selectElementText(el: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(el);
  const sel = window.getSelection();
  if (!sel) return;
  sel.removeAllRanges();
  sel.addRange(range);
}
