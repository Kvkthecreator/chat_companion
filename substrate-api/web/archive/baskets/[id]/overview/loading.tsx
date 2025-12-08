import SpinnerClient from "../_components/SpinnerClient";

const useSpinner = process.env.NEXT_PUBLIC_NAV_SPINNER === "1";

export default function Loading() {
  if (process.env.NEXT_PUBLIC_NAV_PERF_PHASE1 !== "1") return null;
  return (
    <div className="p-6">
      {/* lightweight skeletons for instant paint */}
      <div className="mb-4 h-6 w-40 rounded bg-muted/60" />
      <div className="mb-6 h-4 w-72 rounded bg-muted/50" />
      <div className="relative h-48 w-full rounded bg-muted/40">
        {useSpinner ? <SpinnerClient size="md" /> : null}
      </div>
    </div>
  );
}
