// Calls the backend API described in the Architecture document (section 10).
// In development Vite proxies /api to the backend (see vite.config.js). Set VITE_USE_MOCK=true to use the
// in-memory mock instead, e.g. when the backend is not running.
import * as mock from "./mockAPI";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

async function readJson(response) {
  let body = null;
  try {
    body = await response.json();
  } catch {
    // The body was empty or not JSON; fall through to the generic message below.
  }
  if (!response.ok) {
    // The backend always answers errors as { error: { code, message } }.
    throw new Error(body?.error?.message || `The request failed (HTTP ${response.status}).`);
  }
  return body;
}

async function request(url, options) {
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new Error("Could not reach the server. Check that the backend is running.");
  }
  return readJson(response);
}

export function createEvaluation({ modelFile, datasetFile, taskType, targetColumn }) {
  if (USE_MOCK) {
    return mock.createEvaluation({
      modelFilename: modelFile.name,
      datasetFilename: datasetFile.name,
      taskType,
      targetColumn,
    });
  }

  const form = new FormData();
  form.append("model", modelFile);
  form.append("dataset", datasetFile);
  form.append("task_type", taskType);
  form.append("target_column", targetColumn);
  return request("/api/evaluations", { method: "POST", body: form });
}

export function getEvaluationStatus(evaluationId) {
  if (USE_MOCK) return mock.getEvaluationStatus(evaluationId);
  return request(`/api/evaluations/${encodeURIComponent(evaluationId)}`);
}
