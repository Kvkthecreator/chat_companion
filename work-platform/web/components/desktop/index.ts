/**
 * Desktop UI Components
 *
 * Chat-as-wallpaper with true floating windows (draggable, resizable).
 *
 * Part of Desktop UI Architecture v2.0 (Workspace Mode)
 * See: /docs/implementation/DESKTOP_UI_IMPLEMENTATION_PLAN.md
 */

// Core components
export { DesktopProvider, useDesktop, useDesktopSafe, useBasketId } from './DesktopProvider';
export type { WindowId, WindowState, WindowHighlight, DockItemState, DesktopState } from './DesktopProvider';
export { Desktop } from './Desktop';
export { Dock } from './Dock';
export { DockItem } from './DockItem';
export { FloatingWindow } from './FloatingWindow';
// Legacy modal-style window (kept for reference)
export { Window } from './Window';
export { WindowBackdrop } from './WindowBackdrop';

// Window content components
export { ContextWindowContent } from './windows/ContextWindowContent';
export { WorkWindowContent } from './windows/WorkWindowContent';
export { OutputsWindowContent } from './windows/OutputsWindowContent';
export { RecipesWindowContent } from './windows/RecipesWindowContent';
export { ScheduleWindowContent } from './windows/ScheduleWindowContent';
