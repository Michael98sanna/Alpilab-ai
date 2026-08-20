/**
 * Custom app context menus only on desktop/fine-pointer UIs.
 * Android / tablet keep native long-press selection menus.
 */
export function shouldUseAppContextMenu(): boolean {
  if (typeof window === "undefined" || typeof navigator === "undefined") {
    return false;
  }
  const ua = navigator.userAgent.toLowerCase();
  if (/android|iphone|ipad|ipod|mobile/.test(ua)) {
    return false;
  }
  try {
    if (window.matchMedia("(pointer: coarse)").matches) {
      return false;
    }
  } catch {
    /* ignore */
  }
  return true;
}
