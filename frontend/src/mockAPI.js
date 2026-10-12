
const evaluations = new Map();

export async function createEvaluation(payload) {
  const id = `mock-${Date.now()}`;

  evaluations.set(id, {
    id,
    status: "pending",
    error: null,
    payload,
    createdAt: Date.now(),
  });

  // Simulate the backend accepting the request.
  return { evaluation_id: id, status: "pending" };
}

export async function getEvaluationStatus(id) {
  const evaluation = evaluations.get(id);

  if (!evaluation) {
    throw new Error("Evaluation not found.");
  }

  const elapsed = Date.now() - evaluation.createdAt;

  if (evaluation.payload.simulateFailure) {
    if (elapsed >= 2000) {
      evaluation.status = "failed";
      evaluation.error = "Mock evaluation failed for testing.";
    } else if (elapsed >= 1000) {
      evaluation.status = "running";
    }
  } else {
    if (elapsed >= 4000) {
      evaluation.status = "completed";
    } else if (elapsed >= 1000) {
      evaluation.status = "running";
    }
  }

  return {
    evaluation_id: evaluation.id,
    status: evaluation.status,
    error: evaluation.error,
  };
}
