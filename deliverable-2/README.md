# Deliverable 2: Sprint 2 demo

| | |
|---|---|
| **[Sprint2_Demo.mp4](Sprint2_Demo.mp4)** | A 2-minute screen recording of the working product, made in a real browser (2:00, 1280×720, 7 MB, no sound so it can be narrated live or recorded over) |
| [demo-inputs/](demo-inputs/) | Six good models and datasets and nine bad inputs, each verified against the real application. See its README for what each one shows |
| [video/record_demo.py](video/record_demo.py) | The script that recorded the video, so the take can be repeated after a change |

## What the video shows

| Time | Scene |
|---|---|
| 0:00 | Upload a churn model and its CSV through the Open window, pick the task and target column from the menus, review and run |
| 0:22 | The target column was a feature by mistake: the evaluation fails and names the missing and unused columns |
| 0:27 | Back to configuration, pick the right column, run again |
| 0:36 | The results: status, the metrics table with a plain-language explanation of each metric, and the chart |
| 0:46 | **Download Results**, then the downloaded JSON file opened in the browser |
| 0:51 | A different kind of model: house-price regression, with MAE, MSE, RMSE and R² |
| 1:15 | A corrupt model file is rejected |
| 1:25 | A malformed CSV (ragged rows) is rejected before anything runs, with the message next to the field |
| 1:41 | A `.txt` file is refused as soon as it is chosen |
| 1:47 | The interactive API documentation at `/docs`, with the fields of `POST /api/evaluations` |

## Recording it again

Start the backend and the frontend (see the [main README](../README.md#getting-started)), then:

```bash
pip install playwright
cd deliverable-2/video
python record_demo.py
```

The script drives Microsoft Edge in the background (it does not take over the screen): it picks files through the browser's own file chooser, chooses from the menus, clicks the buttons and scrolls the page at a human pace, with a visible cursor. Edge records itself, and ffmpeg converts the recording to MP4.

A browser recording only contains the page, and the Windows Open window and an opened drop-down list are drawn outside it. So while the real file chooser is open the script draws a picture of the Open window listing the real `demo-inputs` folder, and it draws the opened list when it picks a menu option; the file and the option are then set for real. Waiting for evaluations takes real time, so a take longer than two minutes is sped up evenly to fit. It needs Edge and ffmpeg on the PATH.

## Re-creating the demo inputs

```bash
cd deliverable-2/demo-inputs
python make_demo_inputs.py --verify
```

This needs the backend dependencies (`pip install -r backend/requirements-dev.txt`).
