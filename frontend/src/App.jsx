import { useEffect, useState } from "react";
import { ApiError, createEvaluation, getEvaluationStatus } from "./api";
import Papa from "papaparse";
import "./App.css";

// Matches the backend's default upload limit. This is only quick feedback: the server enforces the real limit.
const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

function tooLargeMessage(file) {
  return `${file.name} is larger than ${MAX_UPLOAD_BYTES / (1024 * 1024)} MB upload limit.`;
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
  const [fieldErrors, setFieldErrors] = useState({});
  const [retryable, setRetryable] = useState(false);
  const [pollAttempt, setPollAttempt] = useState(0);

  const [currentStep, setCurrentStep] = useState(1);
  const [furthestStep, setFurthestStep] = useState(1);

  const [evaluationId, setEvaluationId] = useState("");
  const [evaluationStatus, setEvaluationStatus] = useState("");
  const [evaluationError, setEvaluationError] = useState("");
  const [metrics, setMetrics] = useState(null);
  const [resultTaskType, setResultTaskType] = useState("");

  const isEvaluating =
    evaluationStatus === "pending" || evaluationStatus === "running";

  const canUpload = Boolean(modelFile && datasetFile);

  const canConfigure = Boolean(
    canUpload && taskType && targetColumn
  );

  // Map backend errors to the relevant form control.
  function mapApiError(err) {
    const message = err?.message || "An unexpected error occurred.";
    const code = err?.code || "";

    if (code === "INVALID_MODEL") {
      return { modelFile: message };
    }

    if (code === "MALFORMED_DATASET") {
      return { datasetFile: message };
    }

    if (code === "INVALID_TARGET_COLUMN") {
      return { targetColumn: message };
    }

    if (code === "INVALID_TASK_TYPE") {
      return { taskType: message };
    }

    if (
      code === "UNSUPPORTED_FILE_TYPE" ||
      code === "FILE_TOO_LARGE"
    ) {
      if (/\bmodel\b/i.test(message)) {
        return { modelFile: message };
      }

      if (/\bdataset\b/i.test(message)) {
        return { datasetFile: message };
      }

      return {};
    }

    if (
      code === "MISSING_REQUIRED_FIELD" ||
      code === "VALIDATION_ERROR"
    ) {
      const fieldMatch = message.match(
        /(?:field\s*['"]?|required field(?:\(s\))?:?\s*)(model|dataset|task_type|target_column)/i
      );

      if (fieldMatch) {
        const fieldMap = {
          model: "modelFile",
          dataset: "datasetFile",
          task_type: "taskType",
          target_column: "targetColumn",
        };

        const fieldName = fieldMap[fieldMatch[1].toLowerCase()];

        if (fieldName) {
          return { [fieldName]: message };
        }
      }
    }

    return {};
  }

  function resetEvaluation() {
    setEvaluationId("");
    setEvaluationStatus("");
    setEvaluationError("");
    setRetryable(false);
    setFieldErrors({});
    setMetrics(null);
    setResultTaskType("");
    setCurrentStep(1);
    setFurthestStep(1);
  }

  function handleDatasetChange(event) {
    const file = event.target.files?.[0];

    setDatasetFile(null);
    setColumns([]);
    setTargetColumn("");
    setError("");
    setFieldErrors({});
    resetEvaluation();

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
        setError(
          "Could not read the CSV file. Please check the file and try again."
        );
      },
    });
  }

  function handleModelChange(event) {
    const file = event.target.files?.[0];

    setError("");
    setFieldErrors({});
    resetEvaluation();

    if (!file) {
      setModelFile(null);
      return;
    }

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

  function goToStep(step) {
    if (step < 1 || step > 4) return;
    if (step > furthestStep) return;

    setCurrentStep(step);
    setError("");
  }

  function nextStep() {
    setError("");

    if (currentStep === 1) {
      if (!canUpload) {
        setError("Please upload both a model and a dataset first.");
        return;
      }

      setFurthestStep((previous) => Math.max(previous, 2));
      setCurrentStep(2);
      return;
    }

    if (currentStep === 2) {
      if (!canConfigure) {
        setError("Please select a task type and target column.");
        return;
      }

      setFurthestStep((previous) => Math.max(previous, 3));
      setCurrentStep(3);
    }
  }

  async function handleEvaluate() {
    if (!canConfigure || isEvaluating) return;

    setError("");
    setFieldErrors({});
    setRetryable(false);
    setEvaluationError("");
    setEvaluationId("");
    setEvaluationStatus("pending");
    setMetrics(null);
    setResultTaskType("");

    try {
      const result = await createEvaluation({
        modelFile,
        datasetFile,
        taskType,
        targetColumn,
      });

      setEvaluationId(result.evaluation_id);
      setEvaluationStatus(result.status);
      setFurthestStep(4);
      setCurrentStep(4);
    } catch (err) {
      setEvaluationStatus("");

      const mappedErrors = mapApiError(err);
      setFieldErrors(mappedErrors);
      setRetryable(false);

      if (mappedErrors.modelFile || mappedErrors.datasetFile) {
        setCurrentStep(1);
      } else if (
        mappedErrors.taskType ||
        mappedErrors.targetColumn
      ) {
        setCurrentStep(2);
      }

      setError(
        Object.keys(mappedErrors).length === 0
          ? err.message ||
            "Could not start evaluation. Please check your inputs and try again."
          : "Please correct the highlighted field(s) and try again."
      );
    }
  }
    // Poll the backend for evaluation status.
  useEffect(() => {
    if (!evaluationId) return;

    let stopped = false;
    let timer;

    async function pollStatus() {
      try {
        const result = await getEvaluationStatus(evaluationId);

        if (stopped) return;

        setEvaluationStatus(result.status);

        if (result.status === "completed") {
          setMetrics(result.metrics || {});
          setResultTaskType(result.task_type || "");
          setRetryable(false);
          return;
        }

        if (result.status === "failed") {
          setEvaluationError(
            result.error?.message ||
              result.error ||
              "Evaluation failed."
          );
          setRetryable(false);
          return;
        }

        timer = setTimeout(pollStatus, 1000);
      } catch (err) {
        if (stopped) return;

        setEvaluationStatus("failed");
        setRetryable(true);

        setEvaluationError(
          err instanceof ApiError && err.isNetworkError
            ? "Unable to reach the evaluation server. Check your connection and retry."
            : err.message || "Unable to retrieve evaluation status."
        );
      }
    }

    timer = setTimeout(pollStatus, 1000);

    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [evaluationId, pollAttempt]);

  function retryStatusCheck() {
    setRetryable(false);
    setEvaluationError("");
    setEvaluationStatus("pending");
    setPollAttempt((attempt) => attempt + 1);
  }

  function formatMetric(value) {
    if (typeof value === "number" && Number.isFinite(value)) {
      return value.toFixed(4);
    }

    return String(value);
  }

  const steps = [
    { number: 1, label: "Upload" },
    { number: 2, label: "Configure" },
    { number: 3, label: "Run" },
    { number: 4, label: "Results" },
  ];

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

      {/* WORKFLOW NAVIGATION */}
      <nav className="steps" aria-label="Evaluation workflow">
        {steps.map((step) => (
          <button
            key={step.number}
            type="button"
            className={`step-button ${
              currentStep === step.number ? "active" : ""
            } ${
              step.number < currentStep ? "completed" : ""
            }`}
            disabled={step.number > furthestStep}
            onClick={() => goToStep(step.number)}
            aria-current={
              currentStep === step.number ? "step" : undefined
            }
          >
            {`0${step.number} ${step.label}`}
          </button>
        ))}
      </nav>

      <section className="panel">

        {/* STEP 1: UPLOAD */}
        {currentStep === 1 && (
          <>
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
                  aria-invalid={Boolean(fieldErrors.modelFile)}
                />

                {fieldErrors.modelFile && (
                  <span className="error field-error" role="alert">
                    {fieldErrors.modelFile}
                  </span>
                )}

                {modelFile && (
                  <span className="file-info">
                    {modelFile.name} ·{" "}
                    {(modelFile.size / 1024).toFixed(1)} KB
                  </span>
                )}
              </label>

              <label className="upload-card">
                <span className="file-icon">02</span>
                <strong>Dataset (CSV)</strong>
                <span className="help">
                  Choose a CSV containing your evaluation data.
                  Accepted format: .csv
                </span>

                <input
                  type="file"
                  accept=".csv,text/csv"
                  onChange={handleDatasetChange}
                  aria-invalid={Boolean(fieldErrors.datasetFile)}
                />

                {fieldErrors.datasetFile && (
                  <span className="error field-error" role="alert">
                    {fieldErrors.datasetFile}
                  </span>
                )}

                {datasetFile && (
                  <span className="file-info">
                    {datasetFile.name} ·{" "}
                    {(datasetFile.size / 1024).toFixed(1)} KB
                  </span>
                )}
              </label>
            </div>

            {canUpload && Object.keys(fieldErrors).length === 0 && (
  <p className="success-message">
    Both files uploaded successfully.
  </p>
)}

            {error && (
              <p className="error" role="alert">{error}</p>
            )}

            <div className="actions">
              <span className="help">
                {canUpload
                  ? "Your files are ready. Continue to configuration."
                  : "Upload both files to continue."}
              </span>

              <button
                type="button"
                disabled={!canUpload}
                onClick={nextStep}
              >
                Next: Configure →
              </button>
            </div>
          </>
        )}

        {/* STEP 2: CONFIGURE */}
        {currentStep === 2 && (
          <>
            <div className="section-heading">
              <div>
                <p className="eyebrow">STEP 02</p>
                <h2>Configure evaluation</h2>
                <p className="subtitle">
                  Choose the machine learning task and the column to predict.
                </p>
              </div>
            </div>

            <div className="file-summary">
              <p><strong>Model:</strong> {modelFile?.name}</p>
              <p><strong>Dataset:</strong> {datasetFile?.name}</p>
            </div>

            <div className="form-grid">
              <label>
                <span>Task type</span>
                <select
                  value={taskType}
                  aria-invalid={Boolean(fieldErrors.taskType)}
                  aria-describedby={
                    fieldErrors.taskType
                      ? "task-type-error"
                      : undefined
                  }
                  onChange={(event) => {
                    setTaskType(event.target.value);
                    setFieldErrors((previous) => ({
                      ...previous,
                      taskType: "",
                    }));
                  }}
                >
                  <option value="">Select task type</option>
                  <option value="classification">Classification</option>
                  <option value="regression">Regression</option>
                </select>

                {fieldErrors.taskType && (
                  <span
                    id="task-type-error"
                    className="error field-error"
                    role="alert"
                  >
                    {fieldErrors.taskType}
                  </span>
                )}
              </label>

              <label>
                <span>Target column</span>
                <select
                  value={targetColumn}
                  aria-invalid={Boolean(fieldErrors.targetColumn)}
                  aria-describedby={
                    fieldErrors.targetColumn
                      ? "target-column-error"
                      : undefined
                  }
                  onChange={(event) => {
                    setTargetColumn(event.target.value);
                    setFieldErrors((previous) => ({
                      ...previous,
                      targetColumn: "",
                    }));
                  }}
                  disabled={!columns.length}
                >
                  <option value="">Select target column</option>
                  {columns.map((column, index) => (
                    <option key={`${column}-${index}`} value={column}>
                      {column}
                    </option>
                  ))}
                </select>

                {fieldErrors.targetColumn && (
                  <span
                    id="target-column-error"
                    className="error field-error"
                    role="alert"
                  >
                    {fieldErrors.targetColumn}
                  </span>
                )}
              </label>
            </div>

            {columns.length > 0 && (
              <p className="help">
                {columns.length} column(s) detected: {columns.join(", ")}
              </p>
            )}

            {error && (
              <p className="error" role="alert">{error}</p>
            )}

            <div className="actions">
              <button
                type="button"
                className="secondary-button"
                onClick={() => goToStep(1)}
              >
                ← Back
              </button>

              <button
                type="button"
                disabled={!canConfigure}
                onClick={nextStep}
              >
                Next: Review →
              </button>
            </div>
          </>
        )}
                {/* STEP 3: RUN */}
        {currentStep === 3 && (
          <>
            <div className="section-heading">
              <div>
                <p className="eyebrow">STEP 03</p>
                <h2>Review and run evaluation</h2>
                <p className="subtitle">
                  Confirm your inputs before submitting the evaluation.
                </p>
              </div>
            </div>

            <div className="review-grid">
              <div className="review-item">
                <span>MODEL FILE</span>
                <strong>{modelFile?.name}</strong>
              </div>

              <div className="review-item">
                <span>DATASET FILE</span>
                <strong>{datasetFile?.name}</strong>
              </div>

              <div className="review-item">
                <span>TASK TYPE</span>
                <strong>
                  {taskType === "classification"
                    ? "Classification"
                    : "Regression"}
                </strong>
              </div>

              <div className="review-item">
                <span>TARGET COLUMN</span>
                <strong>{targetColumn}</strong>
              </div>
            </div>

            <p className="help">
              Your model and dataset will be submitted to the evaluation
              backend. The results will appear in the next step.
            </p>

            {error && (
              <p className="error" role="alert">{error}</p>
            )}

            <div className="actions">
              <button
                type="button"
                className="secondary-button"
                onClick={() => goToStep(2)}
              >
                ← Back
              </button>

              <button
                type="button"
                disabled={!canConfigure || isEvaluating}
                onClick={handleEvaluate}
              >
                {isEvaluating ? "Submitting…" : "Evaluate model →"}
              </button>
            </div>
          </>
        )}

        {/* STEP 4: RESULTS */}
        {currentStep === 4 && (
          <>
            <div className="section-heading">
              <div>
                <p className="eyebrow">STEP 04</p>
                <h2>Evaluation results</h2>
                <p className="subtitle">
                  View the status and performance metrics returned by the backend.
                </p>
              </div>
            </div>

            <div className="evaluation-status" aria-live="polite">
              <h3>Evaluation status</h3>

              {evaluationId && (
                <p>
                  <strong>Evaluation ID:</strong> {evaluationId}
                </p>
              )}

              <p>
                <strong>Status:</strong>{" "}
                <span className={`status-badge ${evaluationStatus}`}>
                  {evaluationStatus
                    ? evaluationStatus.toUpperCase()
                    : "NOT STARTED"}
                </span>
              </p>

              {isEvaluating && (
                <p className="help">
                  Your model is being evaluated. Please wait...
                </p>
              )}

              {evaluationStatus === "completed" && (
                <div className="results">
                  <h3>Evaluation completed successfully</h3>

                  <p>
                    <strong>Task type:</strong> {resultTaskType}
                  </p>

                  <h4>Evaluation metrics</h4>

                  {metrics && Object.keys(metrics).length > 0 ? (
                    <>
                      <h4>Metrics summary</h4>

                      <div className="metrics-table-wrapper">
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
                                <td>{formatMetric(value)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      <h4>Metrics visualization</h4>

                      <div className="metrics-chart">
                        {Object.entries(metrics).map(([name, value]) => {
                          const numericValues = Object.values(metrics).filter(
                            (item) =>
                              typeof item === "number" &&
                              Number.isFinite(item)
                          );

                          const maxValue = Math.max(
                            ...numericValues.map((item) => Math.abs(item)),
                            0
                          );

                          const barWidth =
                            typeof value === "number" &&
                            Number.isFinite(value) &&
                            maxValue > 0
                              ? (Math.abs(value) / maxValue) * 100
                              : 0;

                          return (
                            <div className="chart-row" key={name}>
                              <span className="chart-label">
                                {METRIC_LABELS[name] || name}
                              </span>

                              <div
                                className="chart-track"
                                role="img"
                                aria-label={`${
                                  METRIC_LABELS[name] || name
                                }: ${formatMetric(value)}`}
                              >
                                <div
                                  className="chart-bar"
                                  style={{ width: `${barWidth}%` }}
                                />
                              </div>

                              <strong className="chart-value">
                                {formatMetric(value)}
                              </strong>
                            </div>
                          );
                        })}
                      </div>
                    </>
                  ) : (
                    <p>No metrics were returned by the backend.</p>
                  )}
                </div>
              )}

              {evaluationStatus === "failed" && (
                <>
                  <p className="error" role="alert">
                    {evaluationError}
                  </p>

                  {retryable && (
                    <button
                      type="button"
                      onClick={retryStatusCheck}
                    >
                      Retry connection
                    </button>
                  )}
                </>
              )}
            </div>

            <div className="actions">
              <button
                type="button"
                className="secondary-button"
                onClick={() => goToStep(2)}
                disabled={isEvaluating}
              >
                ← Back to configuration
              </button>

              <button
                type="button"
                onClick={resetEvaluation}
                disabled={isEvaluating}
              >
                New evaluation
              </button>
            </div>
          </>
        )}
      </section>

      <footer>
        Web-Based ML Model Evaluator · Development version
      </footer>
    </main>
  );
}

export default App;