import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import LandingPage from "./LandingPage";

describe("LandingPage", () => {
  it("explains the evidence-first workflow and links to paper upload", () => {
    render(<MemoryRouter><LandingPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: /your next research insight/i })).toBeInTheDocument();
    expect(screen.getByText(/trace the evidence/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /add your first paper/i })).toHaveAttribute("href", "/library");
    expect(screen.getByText(/source pages preserved/i)).toBeInTheDocument();
  });
});
