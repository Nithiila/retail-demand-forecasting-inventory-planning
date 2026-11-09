import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Forecast from "./Forecast.jsx";
import { api } from "./api.js";

vi.mock("./api.js", () => ({ api: { forecasts: vi.fn(), demandHistory: vi.fn(), products: vi.fn(), stores: vi.fn() } }));

beforeEach(() => { vi.clearAllMocks(); api.forecasts.mockResolvedValue({ items: [{ product_id: "P1", store_id: "S1", target_week: "2024-02-01", predicted_demand: 20, model_name: "moving_average" }] }); api.demandHistory.mockResolvedValue({ items: [{ product_id: "P1", store_id: "S1", week_start: "2024-01-25", actual_demand: 15 }] }); api.products.mockResolvedValue({ items: [{ product_id: "P1", product_name: "Product One" }] }); api.stores.mockResolvedValue({ items: [{ store_id: "S1", store_name: "Store One" }] }); });

describe("Forecast", () => {
  it("renders historical and predicted demand with KPIs", async () => { render(<Forecast />); expect(screen.getByRole("status")).toBeInTheDocument(); expect(await screen.findByText("Historical vs predicted units")).toBeInTheDocument(); expect(screen.getByText("20")).toBeInTheDocument(); expect(screen.getByText("Product One")).toBeInTheDocument(); });
  it("refetches when product filter changes", async () => { render(<Forecast />); const select = await screen.findByRole("combobox", { name: "Product filter" }); fireEvent.change(select, { target: { value: "P1" } }); await waitFor(() => expect(api.forecasts).toHaveBeenCalledTimes(2)); expect(api.forecasts.mock.calls[1][0]).toContain("product_id=P1"); });
  it("shows API errors and empty states", async () => { api.forecasts.mockRejectedValueOnce(new Error("offline")); render(<Forecast />); expect(await screen.findByRole("alert")).toHaveTextContent("offline"); api.forecasts.mockResolvedValueOnce({ items: [] }); api.demandHistory.mockResolvedValueOnce({ items: [] }); });
});
