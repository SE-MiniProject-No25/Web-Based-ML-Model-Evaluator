const API_BASE_URL = "/api";

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message =
      data.detail ||
      data.error ||
      data.message ||
      `Request failed with status ${response.status}.`;

    throw new Error(
      typeof message === "string" ? message : JSON.stringify(message)
    );
  }

  return data;
}

export async function createEvaluation({
  modelFile,
  datasetFile,
  taskType,
  targetColumn,
}) {
  const formData = new FormData();

  formData.append("model", modelFile);
  formData.append("dataset", datasetFile);
  formData.append("task_type", taskType);
  formData.append("target_column", targetColumn);

  const response = await fetch(`${API_BASE_URL}/evaluations`, {
    method: "POST",
    body: formData,
  });

  return parseResponse(response);
}

export async function getEvaluationStatus(id) {
  const response = await fetch(
    `${API_BASE_URL}/evaluations/${encodeURIComponent(id)}`
  );

  return parseResponse(response);
}