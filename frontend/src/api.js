// Calls the backend API described in the Architecture document (section 10).
// In development Vite proxies /api to the backend (see vite.config.js). Set VITE_USE_MOCK=true to use the
// in-memory mock instead, e.g. when the backend is not running.

import * as mock from "./mockAPI";
const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

// Structured API error containing HTTP and backend details.
export class ApiError extends Error {
  constructor(message, { status = null, code = null, details = null, isNetworkError = false } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
    this.isNetworkError = isNetworkError;
  }
}

async function readJson(response) {
  let body = null;

  try {
    body = await response.json();
  } catch {
    // Response was empty or not JSON.
  }

  if (!response.ok) {
  const apiError = body?.error || {};
  const isServerUnavailable = [502, 503, 504].includes(response.status);

  const message = isServerUnavailable
    ? "The evaluation server is temporarily unavailable. Please check that the backend is running and try again."
    : apiError.message || `The request failed (HTTP ${response.status}).`;

  throw new ApiError(message, {
    status: response.status,
    code: apiError.code || null,
    details: apiError.details || null,
    isNetworkError: isServerUnavailable,
  });
}

  return body;
}

async function request(url, options) {
  let response;

  try {
    response = await fetch(url, options);
  } catch {
    throw new ApiError(
      "Unable to connect to the evaluation server. Please check that the backend is running and try again.",
      { isNetworkError: true }
    );
  }

  return readJson(response);
}

export function createEvaluation({
  modelFile,
  datasetFile,
  taskType,
  targetColumn,
}) {
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

  return request("/api/evaluations", {
    method: "POST",
    body: form,
  });
}

export function getEvaluationStatus(evaluationId) {
  if (USE_MOCK) {
    return mock.getEvaluationStatus(evaluationId);
  }

  return request(
    `/api/evaluations/${encodeURIComponent(evaluationId)}`
  );
}
