// Names, plain-language explanations and chart scales for the metrics the backend returns.

export const METRIC_LABELS = {
  accuracy: "Accuracy",
  precision: "Precision",
  recall: "Recall",
  f1: "F1-score",
  mae: "MAE",
  mse: "MSE",
  rmse: "RMSE",
  r2: "R²",
};

// Plain-language explanations for people who are new to machine learning (usability finding, US-18).
export const METRIC_HELP = {
  accuracy: "The share of predictions that were correct. Higher is better; 1 is perfect.",
  precision:
    "Of everything the model labelled positive, how much really was positive. Higher means fewer false alarms.",
  recall:
    "Of everything that really was positive, how much the model found. Higher means fewer missed cases.",
  f1: "One score that balances precision and recall. Higher is better; 1 is perfect.",
  mae: "The average size of the model's mistakes, in the same units as the value being predicted. Lower is better; 0 is perfect.",
  mse: "The average of the squared mistakes. Squaring makes big mistakes count much more. Lower is better.",
  rmse: "The square root of MSE, so it is in the same units as the value being predicted. Like MAE, but it punishes big mistakes more. Lower is better.",
  r2: "How much of the variation in the data the model explains. 1 is perfect; 0 is no better than always guessing the average; below 0 is worse than that.",
};

// How each metric's bar is scaled. Scores between 0 and 1 are drawn on that range; MAE and RMSE are in
// the units of the predicted value, so they share a scale; MSE (squared units) is left out of the chart.
export const CHART_SCALES = {
  accuracy: "unit",
  precision: "unit",
  recall: "unit",
  f1: "unit",
  r2: "unit",
  mae: "error",
  rmse: "error",
};

export function chartWidth(name, value, metrics) {
  if (typeof value !== "number" || !Number.isFinite(value)) return 0;
  if (CHART_SCALES[name] === "unit") return Math.min(Math.max(value, 0), 1) * 100;
  const largest = Math.max(
    ...Object.entries(metrics)
      .filter(([other, v]) => CHART_SCALES[other] === "error" && Number.isFinite(v))
      .map(([, v]) => Math.abs(v)),
    0
  );
  return largest > 0 ? (Math.abs(value) / largest) * 100 : 0;
}
