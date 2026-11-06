import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App.jsx";

describe("dashboard", () => {
  it("renders the command center and navigation", () => {
    render(<App />);
    expect(screen.getByText("Retail demand command center")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Forecasts" })).toBeInTheDocument();
    expect(screen.getByText("At-risk SKUs")).toBeInTheDocument();
  });
});
