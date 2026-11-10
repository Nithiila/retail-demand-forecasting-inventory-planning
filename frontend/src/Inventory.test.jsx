import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Inventory from "./Inventory.jsx";
import { api } from "./api.js";

vi.mock("./api.js", () => ({ api: { inventory: vi.fn(), risks: vi.fn(), recommendations: vi.fn() } }));

beforeEach(() => { vi.clearAllMocks(); api.inventory.mockResolvedValue({ items: [{ product_id: "P1", store_id: "S1", stock_quantity: 4, safety_stock: 8, reorder_point: 20, recommended_order_quantity: 16 }] }); api.risks.mockResolvedValue({ items: [{ product_id: "P1", store_id: "S1", risk_level: "critical", recommendation: "Place replenishment order now" }] }); api.recommendations.mockResolvedValue({ items: [{ product_id: "P1", store_id: "S1", recommended_order_quantity: 16 }] }); });

describe("Inventory", () => {
  it("renders stock metrics, risk indicators, and recommendations", async () => { render(<Inventory />); expect(screen.getByRole("status")).toBeInTheDocument(); expect(await screen.findByText("critical")).toBeInTheDocument(); expect(screen.getByText("Place replenishment order now")).toBeInTheDocument(); expect(screen.getByText("16 units")).toBeInTheDocument(); });
  it("shows errors and empty states", async () => { api.inventory.mockRejectedValueOnce(new Error("API offline")); render(<Inventory />); expect(await screen.findByRole("alert")).toHaveTextContent("API offline"); });
  it("shows an empty inventory state", async () => { api.inventory.mockResolvedValueOnce({ items: [] }); api.risks.mockResolvedValueOnce({ items: [] }); api.recommendations.mockResolvedValueOnce({ items: [] }); render(<Inventory />); expect(await screen.findByText("No inventory records are available.")).toBeInTheDocument(); });
});
