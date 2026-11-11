import { describe, expect, it } from 'vitest'

import { CHART_SCALES, METRIC_HELP, METRIC_LABELS, chartWidth } from '../metrics'

describe('metric names and explanations', () => {
  it('has a label and a plain-language explanation for every metric the backend returns', () => {
    for (const name of ['accuracy', 'precision', 'recall', 'f1', 'mae', 'mse', 'rmse', 'r2']) {
      expect(METRIC_LABELS[name]).toBeTruthy()
      expect(METRIC_HELP[name].length).toBeGreaterThan(20)
    }
  })
})

describe('chart scaling', () => {
  it('draws scores between 0 and 1 on that range, clamped', () => {
    expect(chartWidth('accuracy', 0.75, {})).toBe(75)
    expect(chartWidth('r2', -0.4, {})).toBe(0)
    expect(chartWidth('f1', 1.2, {})).toBe(100)
  })

  it('draws MAE and RMSE on one shared scale and leaves MSE out of the chart', () => {
    const metrics = { mae: 30, mse: 1268, rmse: 40, r2: 0.9 }
    expect(chartWidth('rmse', 40, metrics)).toBe(100)
    expect(chartWidth('mae', 30, metrics)).toBe(75)
    expect(CHART_SCALES.mse).toBeUndefined()
  })

  it('draws nothing for a missing or non-finite value, or when every error is zero', () => {
    expect(chartWidth('accuracy', undefined, {})).toBe(0)
    expect(chartWidth('mae', Number.NaN, { mae: Number.NaN })).toBe(0)
    expect(chartWidth('mae', 0, { mae: 0, rmse: 0 })).toBe(0)
  })
})
