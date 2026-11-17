# Deliverable 2: Sprint 2 demo

| | |
|---|---|
| **[Sprint2_Demo.mp4](Sprint2_Demo.mp4)** | A screen recording of the working product (1:32, 1916×874, 79 MB, with an audio track) |
| [demo-inputs/](demo-inputs/) | Six good models and datasets and nine bad inputs, each verified against the real application. See its README for what each one shows |
| [video/record_demo.py](video/record_demo.py) | The script that recorded an earlier, silent 2:00 automated take of the video (the video in this folder is a later recording) |

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
