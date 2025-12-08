import { runOnce } from "@/api/pipelines/p3_signals/consumer";

async function loop() {
  const intervalMs = parseInt(process.env.P3_INTERVAL_MS || "15000", 10); // 15s default
  // eslint-disable-next-line no-constant-condition
  while (true) {
    try {
      const r = await runOnce();
      if (process.stdout) console.log(`[p3] ${new Date().toISOString()} processed=${r.processed} advanced=${r.advanced}`);
    } catch (e) {
      console.error("[p3] error in loop", e);
    }
    await new Promise(res => setTimeout(res, intervalMs));
  }
}

loop();