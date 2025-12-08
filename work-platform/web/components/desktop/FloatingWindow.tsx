'use client';

/**
 * FloatingWindow
 *
 * True floating window component with drag and resize capabilities.
 * No backdrop - windows float freely over the chat wallpaper.
 * Uses react-rnd for drag/resize functionality.
 *
 * Part of Desktop UI Architecture v2.0 (Workspace Mode)
 * See: /docs/implementation/DESKTOP_UI_IMPLEMENTATION_PLAN.md
 */

import { useEffect, useCallback, useState, useRef, type ReactNode } from 'react';
import { Rnd } from 'react-rnd';
import { X, Minus, Maximize2, Minimize2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { useDesktop, type WindowId } from './DesktopProvider';

// Default window sizes and positions
const DEFAULT_WIDTH = 480;
const DEFAULT_HEIGHT = 400;
const MIN_WIDTH = 320;
const MIN_HEIGHT = 200;

// Stagger offset for cascading new windows
const STAGGER_OFFSET = 30;

// Default positions by window type (staggered from top-right)
const DEFAULT_POSITIONS: Record<WindowId, { x: number; y: number }> = {
  context: { x: -1, y: 60 },   // -1 means calculate from right edge
  work: { x: -1, y: 90 },
  outputs: { x: -1, y: 120 },
  recipes: { x: -1, y: 150 },
  schedule: { x: -1, y: 180 },
};

interface FloatingWindowProps {
  windowId: WindowId;
  title: string;
  icon: ReactNode;
  children: ReactNode;
  className?: string;
  defaultWidth?: number;
  defaultHeight?: number;
}

export function FloatingWindow({
  windowId,
  title,
  icon,
  children,
  className,
  defaultWidth = DEFAULT_WIDTH,
  defaultHeight = DEFAULT_HEIGHT,
}: FloatingWindowProps) {
  const { closeWindow, isWindowOpen, activeWindow, openWindow } = useDesktop();
  const isOpen = isWindowOpen(windowId);
  const isActive = activeWindow === windowId;
  const containerRef = useRef<HTMLDivElement>(null);

  // Track window position and size
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [size, setSize] = useState({ width: defaultWidth, height: defaultHeight });
  const [isMaximized, setIsMaximized] = useState(false);
  const [preMaximizeState, setPreMaximizeState] = useState<{
    position: { x: number; y: number };
    size: { width: number; height: number };
  } | null>(null);
  const [hasInitialized, setHasInitialized] = useState(false);

  // Calculate initial position based on container size
  useEffect(() => {
    if (isOpen && !hasInitialized && containerRef.current) {
      const container = containerRef.current.parentElement;
      if (container) {
        const containerRect = container.getBoundingClientRect();
        const defaultPos = DEFAULT_POSITIONS[windowId];

        let x = defaultPos.x;
        let y = defaultPos.y;

        // If x is -1, calculate from right edge with padding
        if (x === -1) {
          x = containerRect.width - defaultWidth - 20;
        }

        // Ensure window stays within bounds
        x = Math.max(0, Math.min(x, containerRect.width - defaultWidth));
        y = Math.max(0, Math.min(y, containerRect.height - defaultHeight));

        setPosition({ x, y });
        setHasInitialized(true);
      }
    }
  }, [isOpen, hasInitialized, windowId, defaultWidth, defaultHeight]);

  // Reset initialization when window closes
  useEffect(() => {
    if (!isOpen) {
      setHasInitialized(false);
      setIsMaximized(false);
      setPreMaximizeState(null);
    }
  }, [isOpen]);

  // Handle escape key to close active window
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && isActive) {
        closeWindow(windowId);
      }
    },
    [isOpen, isActive, closeWindow, windowId]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Bring window to front when clicked
  const handleWindowClick = useCallback(() => {
    if (!isActive) {
      openWindow(windowId);
    }
  }, [isActive, openWindow, windowId]);

  // Toggle maximize
  const handleMaximize = useCallback(() => {
    if (isMaximized) {
      // Restore previous state
      if (preMaximizeState) {
        setPosition(preMaximizeState.position);
        setSize(preMaximizeState.size);
      }
      setIsMaximized(false);
    } else {
      // Save current state and maximize
      setPreMaximizeState({ position, size });
      setPosition({ x: 0, y: 0 });
      const container = containerRef.current?.parentElement;
      if (container) {
        const rect = container.getBoundingClientRect();
        setSize({ width: rect.width, height: rect.height });
      }
      setIsMaximized(true);
    }
  }, [isMaximized, position, size, preMaximizeState]);

  // Don't render if not open
  if (!isOpen) {
    return null;
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        'pointer-events-none absolute inset-0 z-40',
        isActive && 'z-50',
        className
      )}
    >
      <Rnd
        size={{ width: size.width, height: size.height }}
        position={{ x: position.x, y: position.y }}
        onDragStop={(e, d) => {
          setPosition({ x: d.x, y: d.y });
        }}
        onResizeStop={(e, direction, ref, delta, position) => {
          setSize({
            width: parseInt(ref.style.width, 10),
            height: parseInt(ref.style.height, 10),
          });
          setPosition(position);
        }}
        minWidth={MIN_WIDTH}
        minHeight={MIN_HEIGHT}
        bounds="parent"
        dragHandleClassName="window-drag-handle"
        enableResizing={!isMaximized}
        disableDragging={isMaximized}
        onMouseDown={handleWindowClick}
        className="pointer-events-auto"
      >
        <div
          className={cn(
            'flex h-full flex-col rounded-lg border bg-card shadow-2xl',
            isActive
              ? 'border-primary/50 ring-1 ring-primary/20'
              : 'border-border',
            // Animation on open
            'animate-in fade-in zoom-in-95 duration-200'
          )}
          role="dialog"
          aria-modal="false"
          aria-labelledby={`window-title-${windowId}`}
        >
          {/* Window Header (Drag Handle) */}
          <div
            className={cn(
              'window-drag-handle flex cursor-move items-center justify-between rounded-t-lg border-b px-3 py-2',
              isActive ? 'bg-muted/50 border-border' : 'bg-muted/30 border-border/50'
            )}
          >
            <div className="flex items-center gap-2">
              <span className={cn('text-muted-foreground', isActive && 'text-primary')}>
                {icon}
              </span>
              <h2
                id={`window-title-${windowId}`}
                className={cn(
                  'text-sm font-semibold select-none',
                  isActive ? 'text-foreground' : 'text-muted-foreground'
                )}
              >
                {title}
              </h2>
            </div>
            <div className="flex items-center gap-0.5">
              {/* Minimize */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => closeWindow(windowId)}
                className="h-6 w-6 p-0 hover:bg-muted"
                aria-label="Minimize window"
              >
                <Minus className="h-3.5 w-3.5" />
              </Button>
              {/* Maximize */}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleMaximize}
                className="h-6 w-6 p-0 hover:bg-muted"
                aria-label={isMaximized ? 'Restore window' : 'Maximize window'}
              >
                {isMaximized ? (
                  <Minimize2 className="h-3.5 w-3.5" />
                ) : (
                  <Maximize2 className="h-3.5 w-3.5" />
                )}
              </Button>
              {/* Close */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => closeWindow(windowId)}
                className="h-6 w-6 p-0 hover:bg-destructive/10 hover:text-destructive"
                aria-label="Close window"
              >
                <X className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>

          {/* Window Content */}
          <div className="flex-1 overflow-y-auto rounded-b-lg bg-card">
            {children}
          </div>

          {/* Resize indicator (bottom-right corner) */}
          {!isMaximized && (
            <div className="absolute bottom-0 right-0 h-4 w-4 cursor-se-resize opacity-0 hover:opacity-100">
              <svg
                className="h-4 w-4 text-muted-foreground/50"
                viewBox="0 0 16 16"
                fill="currentColor"
              >
                <path d="M14 14H12V12H14V14ZM14 10H12V8H14V10ZM10 14H8V12H10V14Z" />
              </svg>
            </div>
          )}
        </div>
      </Rnd>
    </div>
  );
}

export default FloatingWindow;
