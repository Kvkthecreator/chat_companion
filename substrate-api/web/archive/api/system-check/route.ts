import { NextRequest, NextResponse } from "next/server";
import { apiUrl } from "@/lib/env";

const CHECK_PATHS = [
  "/api/baskets/demo-basket-id/commits",
  "/api/baskets/demo-basket-id/change-queue?status=pending",
  "/api/agent-run",
];

export async function GET(request: NextRequest) {
  const checks: { path: string; status: number | null; validJson: boolean }[] = [];

  for (const path of CHECK_PATHS) {
    const url = apiUrl(path);

    try {
      const res = await fetch(url, { cache: "no-store" });
      let validJson = false;
      const ct = res.headers.get("content-type") || "";
      if (ct.includes("application/json")) {
        try {
          await res.clone().json();
          validJson = true;
        } catch {
          validJson = false;
        }
      }
      checks.push({ path, status: res.status, validJson });
    } catch {
      checks.push({ path, status: null, validJson: false });
    }
  }

  return NextResponse.json({ checks });
}
