// @vitest-environment jsdom
import { describe, expect, it } from 'vitest';
import React from 'react';
import { render, screen } from "@testing-library/react";
import DocsList from "@/components/basket/DocsList";

describe("DocsList", () => {
  it("renders titles", () => {
    render(
      <DocsList
        items={[{ id: "1", title: "Doc1", updated_at: "2025-01-01", preview: "..." }]}
      />
    );
    expect(screen.getByText("Doc1")).toBeTruthy();
  });

  it("handles empty state", () => {
    render(<DocsList items={[]} />);
    expect(screen.getByText(/No documents/)).toBeTruthy();
  });
});
