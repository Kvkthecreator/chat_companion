'use client';

/**
 * Desktop
 *
 * Main container for the Desktop UI system.
 * Chat as wallpaper with true floating windows (draggable, resizable).
 *
 * Structure:
 * - Top Dock (always visible)
 * - Chat content (wallpaper, always full-width)
 * - Window container (relative positioning for floating windows)
 * - Floating windows (draggable, resizable, no backdrop)
 *
 * Part of Desktop UI Architecture v2.0 (Workspace Mode)
 * See: /docs/implementation/DESKTOP_UI_IMPLEMENTATION_PLAN.md
 */

import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { Dock } from './Dock';
import { FloatingWindow } from './FloatingWindow';
import { ContextWindowContent } from './windows/ContextWindowContent';
import { WorkWindowContent } from './windows/WorkWindowContent';
import { OutputsWindowContent } from './windows/OutputsWindowContent';
import { RecipesWindowContent } from './windows/RecipesWindowContent';
import { ScheduleWindowContent } from './windows/ScheduleWindowContent';
import {
  FileText,
  Zap,
  Lightbulb,
  Target,
  Calendar,
} from 'lucide-react';

interface DesktopProps {
  children: ReactNode; // Chat interface
  className?: string;
}

export function Desktop({ children, className }: DesktopProps) {
  return (
    <div className={cn('flex h-full flex-col', className)}>
      {/* Top Dock */}
      <Dock />

      {/* Main workspace area */}
      <div className={cn(
        'relative flex-1 overflow-hidden',
        // Mobile: leave room for bottom dock
        'max-md:pb-14'
      )}>
        {/* Chat Wallpaper (always full-width, behind windows) */}
        <div className="h-full overflow-hidden">
          {children}
        </div>

        {/* Floating Windows (true floating, draggable, resizable) */}
        <FloatingWindow
          windowId="context"
          title="Context"
          icon={<FileText className="h-4 w-4" />}
          defaultWidth={420}
          defaultHeight={500}
        >
          <ContextWindowContent />
        </FloatingWindow>

        <FloatingWindow
          windowId="work"
          title="Work"
          icon={<Zap className="h-4 w-4" />}
          defaultWidth={480}
          defaultHeight={400}
        >
          <WorkWindowContent />
        </FloatingWindow>

        <FloatingWindow
          windowId="outputs"
          title="Outputs"
          icon={<Lightbulb className="h-4 w-4" />}
          defaultWidth={520}
          defaultHeight={450}
        >
          <OutputsWindowContent />
        </FloatingWindow>

        <FloatingWindow
          windowId="recipes"
          title="Recipes"
          icon={<Target className="h-4 w-4" />}
          defaultWidth={400}
          defaultHeight={350}
        >
          <RecipesWindowContent />
        </FloatingWindow>

        <FloatingWindow
          windowId="schedule"
          title="Schedule"
          icon={<Calendar className="h-4 w-4" />}
          defaultWidth={400}
          defaultHeight={350}
        >
          <ScheduleWindowContent />
        </FloatingWindow>
      </div>
    </div>
  );
}

export default Desktop;
