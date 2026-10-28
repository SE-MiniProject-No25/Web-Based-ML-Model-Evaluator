
import { useEffect, useState } from "react";
import { createEvaluation, getEvaluationStatus } from "./api";
import Papa from "papaparse";
import "./App.css";

// Matches the backend's default upload limit (EVALUATOR_MAX_UPLOAD_MB). This is only quick feedback: the server
// enforces the real limit.
const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

function tooLargeMessage(file) {
  return `${file.name} is larger than the ${MAX_UPLOAD_BYTES / (1024 * 1024)} MB upload limit.`;
}

const METRIC_LABELS = {
  accuracy: "Accuracy",
  precision: "Precision",
  recall: "Recall",
  f1: "F1-score",
  mae: "MAE",
  mse: "MSE",
  rmse: "RMSE",
  r2: "R²",
};

function App() {
  const [modelFile, setModelFile] = useState(null);
  const [datasetFile, setDatasetFile] = useState(null);
  const [columns, setColumns] = useState([]);
  const [taskType, setTaskType] = useState("");
  const [targetColumn, setTargetColumn] = useState("");
  const [error, setError] = useState("");
  const [evaluationId, setEvaluationId] = useState("");
  const [evaluationStatus, setEvaluationStatus] = useState("");
  const [evaluationError, setEvaluationError] = useState("");
  const [metrics, setMetrics] = useState(null);
  

  
function handleDatasetChange(event) {
  const file = event.target.files?.[0];

  setDatasetFile(null);
  setColumns([]);
  setTargetColumn("");
  setError("");

  if (!file) return;

  if (!file.name.toLowerCase().endsWith(".csv")) {
    setError("Please select a CSV dataset.");
    event.target.value = "";
    return;
  }

  if (file.size > MAX_UPLOAD_BYTES) {
    setError(tooLargeMessage(file));
    event.target.value = "";
    return;
  }

  Papa.parse(file, {
    preview: 2,
    skipEmptyLines: "greedy",

    complete: (results) => {
      const headers = results.data?.[0];

      if (!headers || !Array.isArray(headers) || headers.length === 0) {
        setError("The CSV is empty or has no readable header row.");
        return;
      }

      const cleanedHeaders = headers.map((header) =>
        String(header).trim()
      );

      if (cleanedHeaders.some((header) => !header)) {
        setError(
          "The CSV contains an empty column name. Please check the header row."
        );
        return;
      }

      const normalizedHeaders = cleanedHeaders.map((header) =>
        header.toLowerCase()
      );

      if (new Set(normalizedHeaders).size !== cleanedHeaders.length) {
        setError(
          "The CSV contains duplicate column names. Please make the headers unique."
        );
        return;
      }

      setDatasetFile(file);
      setColumns(cleanedHeaders);
    },

    error: () => {
      setError("Could not read the CSV file. Please check the file and try again.");
    },
  });
}


  function handleModelChange(event) {
    const file = event.target.files?.[0];
    setError("");

    if (!file) return;

    const allowedExtensions = [".pkl", ".joblib"];
    const isAllowed = allowedExtensions.some((extension) =>
      file.name.toLowerCase().endsWith(extension)
    );

    if (!isAllowed) {
      setModelFile(null);
      setError("Please select a .pkl or .joblib model file.");
      event.target.value = "";
      return;
    }

    if (file.size > MAX_UPLOAD_BYTES) {
      setModelFile(null);
      setError(tooLargeMessage(file));
      event.target.value = "";
      return;
    }

    setModelFile(file);
  }

  const missing = [
    !modelFile && "a model",
    !datasetFile && "a dataset",
    !taskType && "a task type",
    !targetColumn && "a target column",
  ].filter(Boolean);
  const canEvaluate = missing.length === 0;

  async function handleEvaluate() {
  setError("");
  setEvaluationError("");
  setEvaluationId("");
  setMetrics(null);
  setEvaluationStatus("pending");

  try {
    const result = await createEvaluation({
      modelFile,
      datasetFile,
      taskType,
      targetColumn,
    });
    setEvaluationId(result.evaluation_id);
    setEvaluationStatus(result.status);
  } catch (err) {
    // The request was rejected (validation error, server unreachable): no evaluation exists, so show the
    // message next to the form instead of in the status panel.
    setEvaluationStatus("");
    setError(err.message || "Could not start evaluation.");
  }
}
useEffect(() => {
  if (!evaluationId) return;

  let stopped = false;
  let timer;

  async function pollStatus() {
    try {
      const result = await getEvaluationStatus(evaluationId);

      if (stopped) return;

      setEvaluationStatus(result.status);

      if (result.status === "failed") {
        // The API returns an error object ({ code, message }); the mock returns a plain string.
        setEvaluationError(result.error?.message || result.error || "Evaluation failed.");
        return;
      }

      if (result.status === "completed") {
        setMetrics(result.metrics || {});
        return;
      }

      if (result.status !== "completed") {
        timer = setTimeout(pollStatus, 1000);
      }
    } catch (err) {
      if (stopped) return;

      setEvaluationStatus("failed");
      setEvaluationError(err.message || "Unable to retrieve evaluation status.");
    }
  }

  timer = setTimeout(pollStatus, 1000);

  return () => {
    stopped = true;
    clearTimeout(timer);
  };
}, [evaluationId]);

  return (
    <main className="app">
      <header className="header">
        <div>
          <p className="eyebrow">MACHINE LEARNING TOOLS</p>
          <h1>ML Model Evaluator</h1>
          <p className="subtitle">
            Evaluate your model with your own dataset.
          </p>
        </div>
        <span className="status-pill">Evaluation workspace</span>
      </header>

      <nav className="steps" aria-label="Evaluation workflow">
        <span className="active">01 Upload</span>
        <span>02 Configure</span>
        <span>03 Run</span>
        <span>04 Results</span>
      </nav>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">STEP 01</p>
            <h2>Upload your files</h2>
            <p className="subtitle">
              Select a trained model and the CSV dataset to evaluate.
            </p>
          </div>
        </div>

        <div className="upload-grid">
          <label className="upload-card">
            <span className="file-icon">01</span>
            <strong>Trained model</strong>
            <span className="help">
              Supported formats: .pkl, .joblib
            </span>
            <input
              type="file"
              accept=".pkl,.joblib"
              onChange={handleModelChange}
            />
            {modelFile && (
              <span className="file-info">
                {modelFile.name} · {(modelFile.size / 1024).toFixed(1)} KB
              </span>
            )}
          </label>

          <label className="upload-card">
            <span className="file-icon">02</span>
            <strong>Dataset (CSV)</strong>
            <span className="help">
              Choose a CSV containing your evaluation data. Accepted format: .csv
            </span>
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={handleDatasetChange}
            />
            {datasetFile && (
              <span className="file-info">
                {datasetFile.name} · {(datasetFile.size / 1024).toFixed(1)} KB
              </span>
            )}
          </label>
        </div>

        {error && <p className="error" role="alert">{error}</p>}

        <div className="section-heading configure-heading">
          <div>
            <p className="eyebrow">STEP 02</p>
            <h2>Configure evaluation</h2>
            <p className="subtitle">
              Choose the machine learning task and the column to predict.
            </p>
          </div>
        </div>

        <div className="form-grid">
          <label>
            <span>Task type</span>
            <select
              value={taskType}
              onChange={(event) => setTaskType(event.target.value)}
            >
              <option value="">Select task type</option>
              <option value="classification">Classification</option>
              <option value="regression">Regression</option>
            </select>
          </label>

          <label>
            <span>Target column</span>
            <select
              value={targetColumn}
              onChange={(event) => setTargetColumn(event.target.value)}
              disabled={!columns.length}
            >
              <option value="">Select target column</option>
              {columns.map((column, index) => (
                <option key={`${column}-${index}`} value={column}>
                  {column}
                </option>
              ))}
            </select>
          </label>
        </div>

        {columns.length > 0 && (
          <p className="help">
            {columns.length} column(s) detected: {columns.join(", ")}
          </p>
        )}
        


        <div className="actions">
          <span className="help">
            {canEvaluate
              ? "Your inputs are ready."
              : `Still needed: ${missing.join(", ")}.`}
          </span>
          <button
            type="button"
            disabled={!canEvaluate}
            onClick={handleEvaluate}
          >
            Evaluate model →
          </button>
        </div>
        {evaluationId && (
  <div className="evaluation-status" aria-live="polite">
    <h3>Evaluation status</h3>

    <p>
      <strong>Evaluation ID:</strong> {evaluationId}
    </p>

    <p>
      <strong>Status:</strong>{" "}
      <span className={`status-badge ${evaluationStatus}`}>
        {evaluationStatus.toUpperCase()}
      </span>
    </p>

    {evaluationStatus === "completed" && metrics && (
      <>
        <h3>Results</h3>
        {Object.keys(metrics).length === 0 ? (
          <p className="help">The evaluation completed but reported no metrics.</p>
        ) : (
          <table className="metrics-table">
            <thead>
              <tr>
                <th>Metric</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(metrics).map(([name, value]) => (
                <tr key={name}>
                  <td>{METRIC_LABELS[name] || name}</td>
                  <td>{Number(value).toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </>
    )}

    {evaluationStatus === "failed" && (
      <p className="error" role="alert">{evaluationError}</p>
    )}
  </div>
)}
      </section>

      <footer>
        Web-Based ML Model Evaluator · Development version
      </footer>
    </main>
  );
}

export default App;
