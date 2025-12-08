import { NextResponse } from "next/server";
import { getGovernanceStatus } from "@/lib/governance/featureFlags";

export async function GET() {
  try {
    const status = getGovernanceStatus();
    
    return NextResponse.json({
      ...status,
      timestamp: new Date().toISOString(),
      canon_version: "v2.0"
    });
    
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to get governance status" }, 
      { status: 500 }
    );
  }
}