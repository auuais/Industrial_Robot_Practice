# Intelligent Robot Practice — English translations and study notes

English versions of the Korean lecture slides for 지능로봇실제 (Intelligent Robot Practice, Department of Intelligent Robot Engineering, Chungbuk National University), and study notes made from them.

## Contents

| Lecture | Topic | Korean original | English | Notes |
|---|---|---|---|---|
| 1 | Course introduction | `Lecture 1.pdf` | — | in the Lectures 1–7 notes |
| 2 | System modeling and motion analysis | `Lecture 2.pdf` | `Lecture 2 (English).pdf` | `Exam Prep Notes (Lectures 1-7).pdf` |
| 3 | Sensor calibration | `Lecture 3.pdf` | `Lecture 3 (English).pdf` | 〃 |
| 4 | Wheel odometry and the Kalman filter | `Lecture 4.pdf` | `Lecture 4 (English).pdf` | 〃 |
| 6 | EKF, UKF and pose-graph optimization | `Lecture 6.pdf` | `Lecture 6 (English).pdf` | 〃 |
| 7 | Optimization | `Lecture 7.pdf` | `Lecture 7 (English).pdf` | 〃 |
| 8 | Global planning and route execution | `Lecture 8.pdf` | `Lecture 8 (English).pdf` | `Lecture 8 Study Notes.pdf` |
| 9 | Local trajectory planning | `Lecture9.pdf` | `Lecture 9 (English).pdf` | `Lecture 9 Study Notes.pdf` |
| 10 | Tracking control: Pure Pursuit, Stanley, speed control, Kanayama | `Lecture 10.pdf` | `Lecture 10 (English).pdf` | `Lecture 10 Study Notes.pdf` |

`Concept Question Bank (Lectures 1-7).pdf` has ten intuition questions with answers per lecture. Lecture 5 was not supplied.

## How the files are made

- **`translation_build/`** — layout-preserving translator (PyMuPDF). It removes only the Korean text spans, redraws the English in the deck's own fonts, erases Korean that is baked into figures by inpainting, and checks that nothing outside the replaced text changed. Run `python engine.py spec_l10` (or `spec_l8`, `spec_l9`) from that folder. Lectures 2–7 were translated before the engine moved into this repository, so their specs are not included.
- **`exam_prep_build/`** — study notes. HTML content with TeX math (converted to MathML by `tex2mml.py`) is printed by headless Chromium through Playwright, in two passes so the table of contents gets page numbers. Figures come from `figures*.py` and every number is recomputed by `verify*.py`. Build with `python build.py` (Lectures 1–7), `python build_q.py` (question bank), `python build_l8.py`, `python build_l9.py` or `python build_l10.py`.

Requirements: Python 3.9 with PyMuPDF, fontTools, numpy, opencv-python, matplotlib and Playwright (with Chromium), plus the Windows fonts Malgun Gothic, Cambria and Segoe UI.

## Note

The Korean slides are the course instructor's material. Keep this repository private unless you have permission to share them.
