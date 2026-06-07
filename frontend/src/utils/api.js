import axios from "axios";

const api = axios.create({ baseURL: "/api" });

export async function getAnalysis(documentId) {
  const { data } = await api.get(`/analysis/${documentId}`);
  return data;
}

export async function listAnalyses() {
  const { data } = await api.get("/analyses");
  return data;
}

export async function getStats() {
  const { data } = await api.get("/stats");
  return data;
}

export async function getHealth() {
  const { data } = await api.get("/health");
  return data;
}

/**
 * Upload a file and stream pipeline progress via SSE.
 *
 * @param {File} file
 * @param {{ onStep: (stepIndex: number) => void, onComplete: (result: object) => void, onError: (msg: string) => void }} callbacks
 */
export async function uploadAndStream(file, { onStep, onComplete, onError }) {
  const formData = new FormData();
  formData.append("file", file);
  await _streamSSE("/api/upload-stream", { method: "POST", body: formData }, { onStep, onComplete, onError });
}

/**
 * Stream demo analysis of the bundled sample contract.
 */
export async function streamDemo({ onStep, onComplete, onError }) {
  await _streamSSE("/api/demo-stream", { method: "GET" }, { onStep, onComplete, onError });
}

async function _streamSSE(url, fetchInit, { onStep, onComplete, onError }) {
  let response;
  try {
    response = await fetch(url, fetchInit);
  } catch (err) {
    onError("Network error — is the server running?");
    return;
  }

  if (!response.ok) {
    let detail = "Request failed";
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {}
    onError(detail);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE blocks are separated by double newline
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop(); // Keep incomplete trailing chunk

      for (const block of blocks) {
        if (!block.trim()) continue;
        let event = "message";
        let data = "";
        for (const line of block.split("\n")) {
          if (line.startsWith("event: ")) event = line.slice(7).trim();
          if (line.startsWith("data: ")) data = line.slice(6).trim();
        }
        if (!data) continue;

        if (event === "progress") {
          const { step_index } = JSON.parse(data);
          onStep(step_index);
        } else if (event === "complete") {
          onComplete(JSON.parse(data));
          return;
        } else if (event === "error") {
          onError(JSON.parse(data));
          return;
        }
      }
    }
  } catch (err) {
    onError(err.message || "Streaming interrupted");
  }
}
