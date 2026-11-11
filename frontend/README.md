# Frontend

The web interface of the ML Model Evaluator: React and Vite, in four steps (Upload → Configure → Run → Results). It talks to the backend only through the API in [Architecture §10](../deliverable-1/03_Architecture_and_Design.md#10-api-design).

```bash
npm install
npm run dev        # http://localhost:5173, with /api forwarded to the backend on port 8000
npm test           # component and API tests (Vitest, React Testing Library)
npm run coverage   # the same, with line and branch coverage in coverage/
npm run lint
npm run build
```

| File | What it does |
|---|---|
| `src/App.jsx` | The four-step workflow, its checks (file type, size, CSV header and separator), status polling, results table, chart and download |
| `src/api.js` | Calls the three endpoints and turns errors into `ApiError` (code, message, network failure) |
| `src/metrics.js` | Metric names, plain-language explanations and how the chart scales each metric |
| `src/mockAPI.js` | An in-memory stand-in for the backend: start with `VITE_USE_MOCK=true` |
| `src/test/` | The tests |

`VITE_API_TARGET` sends `/api` to another backend address, for example a backend on another port (the browser tests in `../e2e/` use this).
