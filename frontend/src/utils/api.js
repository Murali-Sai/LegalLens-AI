import axios from "axios";

const api = axios.create({
  baseURL: "/api",
});

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/upload", formData);
  return data;
}

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
