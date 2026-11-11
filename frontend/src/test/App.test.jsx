import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import App from '../App'
import * as api from '../api'

vi.mock('../api', async (importOriginal) => {
  const real = await importOriginal()
  return {
    ...real,
    createEvaluation: vi.fn(),
    getEvaluationStatus: vi.fn(),
    downloadEvaluation: vi.fn(),
  }
})

const POLL = { timeout: 4000 } // the interface checks the status once a second

const model = () => new File(['model bytes'], 'churn.joblib')
const csv = (text, name = 'churn.csv') => new File([text], name, { type: 'text/csv' })
const CHURN = 'tenure,charge,churned\n1,20,0\n5,30,1\n'

function fileInputs(container) {
  const [modelInput, datasetInput] = container.querySelectorAll('input[type=file]')
  return { modelInput, datasetInput }
}

async function upload(user, container, modelFile = model(), datasetFile = csv(CHURN)) {
  const { modelInput, datasetInput } = fileInputs(container)
  if (modelFile) await user.upload(modelInput, modelFile)
  if (datasetFile) await user.upload(datasetInput, datasetFile)
}

async function configure(user, task = 'classification', target = 'churned') {
  await user.click(screen.getByRole('button', { name: /Next: Configure/ }))
  const [taskSelect, targetSelect] = screen.getAllByRole('combobox')
  await user.selectOptions(taskSelect, task)
  await user.selectOptions(targetSelect, target)
}

async function runToResults(user, container, status) {
  api.createEvaluation.mockResolvedValue({ evaluation_id: 'eval-1', status: 'pending' })
  api.getEvaluationStatus.mockResolvedValue(status)
  await upload(user, container)
  await configure(user)
  await user.click(screen.getByRole('button', { name: /Next: Review/ }))
  await user.click(screen.getByRole('button', { name: /Evaluate model/ }))
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('upload step', () => {
  it('refuses a model file that is not .pkl or .joblib', async () => {
    const user = userEvent.setup({ applyAccept: false })
    const { container } = render(<App />)

    await upload(user, container, new File(['x'], 'notes.txt'), null)

    expect(screen.getByRole('alert')).toHaveTextContent('Please select a .pkl or .joblib model file.')
  })

  it('refuses a file over the 10 MB upload limit before sending it', async () => {
    const user = userEvent.setup()
    const { container } = render(<App />)
    const big = new File(['x'], 'big.joblib')
    Object.defineProperty(big, 'size', { value: 11 * 1024 * 1024 })

    await upload(user, container, big, null)

    expect(screen.getByRole('alert')).toHaveTextContent('larger than 10 MB')
  })

  it('refuses a dataset that is not a CSV', async () => {
    const user = userEvent.setup({ applyAccept: false })
    const { container } = render(<App />)

    await upload(user, container, null, new File(['x'], 'data.xlsx'))

    expect(screen.getByRole('alert')).toHaveTextContent('Please select a CSV dataset.')
  })

  it('refuses a semicolon-separated CSV and says why', async () => {
    const user = userEvent.setup()
    const { container } = render(<App />)

    await upload(user, container, model(), csv('tenure;charge;churned\n1;20;0\n'))

    expect(await screen.findByRole('alert')).toHaveTextContent('this file uses semicolons')
  })

  it('refuses a CSV with duplicate column names', async () => {
    const user = userEvent.setup()
    const { container } = render(<App />)

    await upload(user, container, model(), csv('a,A,b\n1,2,3\n'))

    expect(await screen.findByRole('alert')).toHaveTextContent('duplicate column names')
  })

  it('enables the next step only when both files are chosen', async () => {
    const user = userEvent.setup()
    const { container } = render(<App />)
    const next = screen.getByRole('button', { name: /Next: Configure/ })
    expect(next).toBeDisabled()

    await upload(user, container)

    expect(await screen.findByText('Both files uploaded successfully.')).toBeInTheDocument()
    expect(next).toBeEnabled()
  })
})

describe('configure and review steps', () => {
  it('lists the columns read from the CSV, trimmed, as target choices', async () => {
    const user = userEvent.setup()
    const { container } = render(<App />)
    await upload(user, container, model(), csv('tenure, charge, churned\n1,20,0\n'))
    await screen.findByText('Both files uploaded successfully.')

    await user.click(screen.getByRole('button', { name: /Next: Configure/ }))

    const target = screen.getAllByRole('combobox')[1]
    const options = within(target).getAllByRole('option').map((o) => o.value)
    expect(options).toEqual(['', 'tenure', 'charge', 'churned'])
  })

  it('shows the chosen files, task and target on the review step', async () => {
    const user = userEvent.setup()
    const { container } = render(<App />)
    await upload(user, container)
    await screen.findByText('Both files uploaded successfully.')
    await configure(user)

    await user.click(screen.getByRole('button', { name: /Next: Review/ }))

    for (const text of ['churn.joblib', 'churn.csv', 'Classification', 'churned']) {
      expect(screen.getByText(text)).toBeInTheDocument()
    }
  })
})

describe('results step', () => {
  it('shows the metrics table with explanations, the chart and the download button when completed', async () => {
    const user = userEvent.setup()
    const { container } = render(<App />)
    await runToResults(user, container, {
      status: 'completed',
      task_type: 'classification',
      metrics: { accuracy: 0.75, precision: 0.5, recall: 1, f1: 0.6667 },
    })

    expect(await screen.findByText('COMPLETED', {}, POLL)).toBeInTheDocument()
    const table = screen.getByRole('table')
    expect(within(table).getByText('Accuracy')).toBeInTheDocument()
    expect(within(table).getByText('0.7500')).toBeInTheDocument()
    expect(within(table).getByText(/The share of predictions that were correct/)).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Accuracy: 0.7500' })).toBeInTheDocument()
    expect(screen.getByText(/the positive class/)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Download Results/ }))
    expect(api.downloadEvaluation).toHaveBeenCalledWith('eval-1')
  })

  it('explains the regression chart scales and leaves MSE out of the chart', async () => {
    const user = userEvent.setup()
    const { container } = render(<App />)
    await runToResults(user, container, {
      status: 'completed',
      task_type: 'regression',
      metrics: { mae: 29.17, mse: 1267.7, rmse: 35.6, r2: 0.8965 },
    })

    expect(await screen.findByText('COMPLETED', {}, POLL)).toBeInTheDocument()
    expect(screen.getByText(/MSE is in squared units/)).toBeInTheDocument()
    expect(screen.queryByRole('img', { name: /^MSE/ })).toBeNull()
    expect(screen.getByRole('img', { name: 'R²: 0.8965' })).toBeInTheDocument()
  })

  it('shows the message of a failed evaluation and no download button', async () => {
    const user = userEvent.setup()
    const { container } = render(<App />)
    await runToResults(user, container, {
      status: 'failed',
      error: { code: 'INCOMPATIBLE_INPUTS', message: 'Missing from the dataset: tenure.' },
    })

    expect(await screen.findByText('FAILED', {}, POLL)).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Missing from the dataset: tenure.')
    expect(screen.queryByRole('button', { name: /Download Results/ })).toBeNull()
  })

  it('offers a retry when the server cannot be reached while waiting', async () => {
    const user = userEvent.setup()
    const { container } = render(<App />)
    api.createEvaluation.mockResolvedValue({ evaluation_id: 'eval-1', status: 'pending' })
    api.getEvaluationStatus.mockRejectedValueOnce(new api.ApiError('down', { isNetworkError: true }))
    await upload(user, container)
    await configure(user)
    await user.click(screen.getByRole('button', { name: /Next: Review/ }))
    await user.click(screen.getByRole('button', { name: /Evaluate model/ }))

    expect(await screen.findByText(/Unable to reach the evaluation server/, {}, POLL)).toBeInTheDocument()
    api.getEvaluationStatus.mockResolvedValue({ status: 'completed', task_type: 'classification', metrics: {} })
    await user.click(screen.getByRole('button', { name: 'Retry connection' }))
    expect(await screen.findByText('No metrics were returned by the backend.', {}, POLL)).toBeInTheDocument()
  })
})

describe('a rejected submission', () => {
  it('puts the error next to the dataset field and returns to the upload step', async () => {
    const user = userEvent.setup()
    const { container } = render(<App />)
    api.createEvaluation.mockRejectedValue(
      new api.ApiError('The dataset file contains ragged rows with inconsistent column counts.', {
        status: 422,
        code: 'MALFORMED_DATASET',
      })
    )
    await upload(user, container)
    await configure(user)
    await user.click(screen.getByRole('button', { name: /Next: Review/ }))
    await user.click(screen.getByRole('button', { name: /Evaluate model/ }))

    const alerts = await screen.findAllByRole('alert')
    expect(alerts.map((a) => a.textContent)).toEqual([
      'The dataset file contains ragged rows with inconsistent column counts.',
      'Please correct the highlighted field(s) and try again.',
    ])
    expect(fileInputs(container).datasetInput).toHaveAttribute('aria-invalid', 'true')
  })

  it('shows a message that names no field on its own', async () => {
    const user = userEvent.setup()
    const { container } = render(<App />)
    api.createEvaluation.mockRejectedValue(new api.ApiError('The evaluation server is temporarily unavailable.'))
    await upload(user, container)
    await configure(user)
    await user.click(screen.getByRole('button', { name: /Next: Review/ }))
    await user.click(screen.getByRole('button', { name: /Evaluate model/ }))

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent('The evaluation server is temporarily unavailable.')
    )
  })
})
