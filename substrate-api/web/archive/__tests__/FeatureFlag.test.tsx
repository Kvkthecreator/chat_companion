import { useFeatureFlag } from "@/lib/hooks/useFeatureFlag";

test("env flag reads true", () => {
  process.env.NEXT_PUBLIC_SHOWCONTEXTPANEL = "true";
  expect(useFeatureFlag("showContextPanel")).toBe(true);
});

