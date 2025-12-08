import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";

// Simple activity tracking - in production this would use WebSocket connections, 
// session data, or more sophisticated user activity detection
const userActivityMap = new Map<string, number>();
const ACTIVITY_THRESHOLD = 5 * 60 * 1000; // 5 minutes

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ basketId: string }> }
) {
  try {
    const { basketId } = await params;
    const supabase = createRouteHandlerClient({ cookies });
    
    // Get authenticated user
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({ hasActivity: false });
    }

    // Check recent activity for this user/basket combination
    const activityKey = `${user.id}:${basketId}`;
    const lastActivity = userActivityMap.get(activityKey) || 0;
    const now = Date.now();
    
    const hasRecentActivity = (now - lastActivity) < ACTIVITY_THRESHOLD;

    return NextResponse.json({ 
      hasActivity: hasRecentActivity,
      lastActivity: lastActivity > 0 ? new Date(lastActivity).toISOString() : null,
      timeSinceActivity: lastActivity > 0 ? now - lastActivity : null
    });

  } catch (error) {
    console.error("Activity check error:", error);
    return NextResponse.json({ hasActivity: false });
  }
}

// Update activity timestamp
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ basketId: string }> }
) {
  try {
    const { basketId } = await params;
    const supabase = createRouteHandlerClient({ cookies });
    
    // Get authenticated user
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Update activity timestamp
    const activityKey = `${user.id}:${basketId}`;
    userActivityMap.set(activityKey, Date.now());

    return NextResponse.json({ success: true });

  } catch (error) {
    console.error("Activity update error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

// Cleanup old activity data periodically
setInterval(() => {
  const now = Date.now();
  const cleanupThreshold = 24 * 60 * 60 * 1000; // 24 hours
  
  for (const [key, timestamp] of userActivityMap.entries()) {
    if (now - timestamp > cleanupThreshold) {
      userActivityMap.delete(key);
    }
  }
}, 60 * 60 * 1000); // Cleanup every hour