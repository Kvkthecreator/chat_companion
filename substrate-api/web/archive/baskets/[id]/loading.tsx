// Server Component (catch-all loader under /baskets/[id])
import SpinnerClient from "./_components/SpinnerClient";

const useSpinner = process.env.NEXT_PUBLIC_NAV_SPINNER === "1";

export default function Loading() {
  return (
    <div className="p-6">
      {/* minimal skeleton for instant paint */}
      <div className="mb-3 h-5 w-36 rounded bg-muted/60" />
      <div className="relative h-32 w-full rounded bg-muted/40">
        {useSpinner ? <SpinnerClient size="sm" /> : null}
      </div>
    </div>
  );
}
