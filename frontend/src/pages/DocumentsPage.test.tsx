import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../services/api";
import DocumentsPage from "./DocumentsPage";

vi.mock("../services/api", () => ({
  api: { get: vi.fn(), post: vi.fn(), delete: vi.fn() },
  errorMessage: vi.fn(() => "request failed"),
}));

describe("DocumentsPage upload workflow", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockImplementation((url) => Promise.resolve({
      data: url === "/settings"
        ? { max_upload_mb: 50 }
        : { items: [], total: 0, limit: 100, offset: 0 },
    }) as never);
  });

  it("posts valid PDFs and shows the processing outcome", async () => {
    const user = userEvent.setup();
    vi.mocked(api.post).mockResolvedValue({ data: { results: [{
      filename: "paper.pdf",
      duplicate: false,
      error: null,
      document: { page_count: 3 },
    }] } } as never);
    render(<MemoryRouter initialEntries={["/library"]}><DocumentsPage /></MemoryRouter>);

    const file = new File(["%PDF-1.4 test"], "paper.pdf", { type: "application/pdf" });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(input, file);

    await screen.findByText("Upload complete. Each PDF keeps its original page references.");
    expect(api.post).toHaveBeenCalledWith("/documents", expect.any(FormData), expect.objectContaining({
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: expect.any(Function),
    }));
    expect(await screen.findByText("3 pages extracted")).toBeInTheDocument();
  });

  it("rejects a non-PDF before sending it to the API", async () => {
    const user = userEvent.setup({ applyAccept: false });
    render(<MemoryRouter><DocumentsPage /></MemoryRouter>);
    const file = new File(["not a PDF"], "notes.txt", { type: "text/plain" });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(input, file);

    expect(await screen.findByText("Only PDF files are accepted.")).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });
});
