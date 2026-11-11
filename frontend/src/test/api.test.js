import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, createEvaluation, downloadEvaluation, getEvaluationStatus } from '../api'

function reply(status, body, headers = {}) {
  return Promise.resolve(
    new Response(body === undefined ? null : JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json', ...headers },
    })
  )
}

const files = {
  modelFile: new File(['model'], 'model.joblib'),
  datasetFile: new File(['a,b\n1,2\n'], 'data.csv'),
  taskType: 'classification',
  targetColumn: 'b',
}

let fetchMock

beforeEach(() => {
  fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  URL.createObjectURL = vi.fn(() => 'blob:result')
  URL.revokeObjectURL = vi.fn()
})

afterEach(() => vi.unstubAllGlobals())

describe('createEvaluation', () => {
  it('posts the two files and two fields as a form and returns the new id', async () => {
    fetchMock.mockReturnValue(reply(202, { evaluation_id: 'abc', status: 'pending' }))

    await expect(createEvaluation(files)).resolves.toEqual({ evaluation_id: 'abc', status: 'pending' })

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/evaluations')
    expect(options.method).toBe('POST')
    expect(options.body.get('model').name).toBe('model.joblib')
    expect(options.body.get('dataset').name).toBe('data.csv')
    expect(options.body.get('task_type')).toBe('classification')
    expect(options.body.get('target_column')).toBe('b')
  })

  it('passes on the error code and message from the server', async () => {
    fetchMock.mockReturnValue(
      reply(422, { error: { code: 'MALFORMED_DATASET', message: 'The dataset file is empty.' } })
    )

    const error = await createEvaluation(files).catch((e) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 422, code: 'MALFORMED_DATASET', message: 'The dataset file is empty.' })
    expect(error.isNetworkError).toBe(false)
  })

  it('says the server is unavailable for a gateway error', async () => {
    fetchMock.mockReturnValue(reply(503, undefined))

    const error = await createEvaluation(files).catch((e) => e)

    expect(error.isNetworkError).toBe(true)
    expect(error.message).toMatch(/temporarily unavailable/)
  })

  it('names the HTTP status when an error has no body', async () => {
    fetchMock.mockReturnValue(reply(500, undefined))
    await expect(createEvaluation(files)).rejects.toThrow('HTTP 500')
  })

  it('reports a network failure as an ApiError the interface can recognise', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))

    const error = await createEvaluation(files).catch((e) => e)

    expect(error.isNetworkError).toBe(true)
    expect(error.message).toMatch(/Unable to connect/)
  })
})

describe('getEvaluationStatus', () => {
  it('asks for the status with the id escaped', async () => {
    fetchMock.mockReturnValue(reply(200, { status: 'running' }))

    await expect(getEvaluationStatus('a/b')).resolves.toEqual({ status: 'running' })
    expect(fetchMock).toHaveBeenCalledWith('/api/evaluations/a%2Fb', undefined)
  })
})

describe('downloadEvaluation', () => {
  it('saves the file under the name the server gives', async () => {
    fetchMock.mockReturnValue(
      reply(200, { evaluation_id: 'abc' }, { 'Content-Disposition': 'attachment; filename="evaluation-abc.json"' })
    )
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    await downloadEvaluation('abc')

    expect(fetchMock).toHaveBeenCalledWith('/api/evaluations/abc/download')
    expect(click).toHaveBeenCalledOnce()
    expect(click.mock.contexts[0].download).toBe('evaluation-abc.json')
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:result')
  })

  it('falls back to a name built from the id', async () => {
    fetchMock.mockReturnValue(reply(200, {}))
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    await downloadEvaluation('xyz')

    expect(click.mock.contexts[0].download).toBe('evaluation-xyz.json')
  })

  it('passes on the error from the server for an evaluation that has not completed', async () => {
    fetchMock.mockReturnValue(
      reply(409, { error: { code: 'EVALUATION_NOT_COMPLETED', message: 'Evaluation not completed.' } })
    )
    await expect(downloadEvaluation('abc')).rejects.toMatchObject({ code: 'EVALUATION_NOT_COMPLETED' })
  })

  it('reports a network failure', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))
    await expect(downloadEvaluation('abc')).rejects.toThrow(/Unable to connect/)
  })
})
