# SequenceModel-HAR-Lab

**Subject-disjoint human activity recognition with traceable data preparation.**

[简体中文](README.md) · English

[![Documentation checks](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab/actions/workflows/docs.yml/badge.svg)](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab/actions/workflows/docs.yml)

This repository develops a time-series classification workflow using smartphone accelerometer and gyroscope signals from UCI HAR. The current milestone covers data acquisition, auditing, subject-disjoint splits, training-only standardization, and real signal inspection. Model training and comparisons are planned; no classification results are reported yet.

## Data at a glance

- **Input:** 128 time steps × 9 channels per window, sampled at 50 Hz.
- **Activities:** walking, walking upstairs, walking downstairs, sitting, standing, and laying.
- **Dataset:** 10,299 windows from 30 participants, using the official preprocessed inertial signals rather than the 561 engineered features.

| Split | Participants | Windows | Selection |
| --- | ---: | ---: | --- |
| Training | 17 | 6,037 | Official training participants excluding validation IDs |
| Validation | 4 | 1,315 | First four sorted official training IDs: 1, 3, 5, 6 |
| Test | 9 | 2,947 | Official test participants, row order, and labels preserved |

The participant sets are disjoint. Channel-wise means and population standard deviations are fitted on the final training windows only and applied unchanged to validation and test. Arrays use the `N × time × channels` layout; original label IDs 1–6 are retained.

See the [data protocol](docs/data_protocol.md), [published split metadata](docs/day01/split_metadata.json), and [standardization parameters](docs/day01/standardization_train_only.json). Most detailed documents are currently in Chinese.

## What has been verified

The data workflow checks official archives using member CRCs and local SHA-256 hashes, reads all 18 signal files, validates window/label/subject alignment, and independently compares saved standardized values with their original rows and training parameters. Publisher-provided hashes were unavailable; local checks are not presented as publisher authentication.

Two documented training windows illustrate the nine channels for WALKING and STANDING. They are examples, not evidence of population-wide activity differences or model performance. [Signal figures and provenance](docs/day01/README.md).

## Getting started

```sh
git clone https://github.com/wzhikun-helper/SequenceModel-HAR-Lab.git
cd SequenceModel-HAR-Lab
python -B scripts/check_public_docs.py
```

The documentation check uses only the Python standard library and does not access the network or raw data. The [reproduction guide](docs/reproducing_day01.md) describes the complete data workflow, tested dependency versions, and fresh run IDs. It does not require a GPU or PyTorch.

## Verification levels

Lightweight CI runs the documentation checks and 25 synthetic shared-contract tests without site packages, raw data, or a GPU. This is separate from the full real-data reproduction completed on 2026-10-31 in a fresh Python virtual environment and fresh run directories. The latter reran the official download, audit, preprocessing, plotting, and value-by-value verification; arrays matched the earlier valid run exactly and PNG pixels matched. PDF/SVG bytes differ, with different creation dates recorded.

See the [remediation report](reports/remediation_round1_20261031/README.md) and [verification scope](docs/verification.md). A passing lightweight CI run is not a claim that CI downloaded or reproduced the full dataset.

## Repository guide

| Location | Purpose |
| --- | --- |
| [docs/](docs/README.md) | Protocol, reproduction instructions, signal figures, and small metadata files |
| [scripts/](scripts/README.md) | Download, audit, plot, and verify entry points |
| [reports/](reports/README.md) | Audit results and historical execution evidence |
| [learning_notes/](learning_notes/day01/README.md) | Learning notes, corrections, and available teaching records |

Raw datasets, processed arrays, model weights, credentials, and local logs are excluded from version control. Historical records are preserved with their original dates and limitations. See [contribution guidelines](CONTRIBUTING.md) and the [changelog](CHANGELOG.md).

## Roadmap

The data foundation is complete. CNN, GRU, Transformer, and Mamba implementations, unified evaluation, and ablation studies remain future work. The project has not entered its model-training stage. [Current progress](PROGRESS.md).

## Dataset reference

Reyes-Ortiz et al. (2013). *Human Activity Recognition Using Smartphones*. UCI Machine Learning Repository. [DOI: 10.24432/C54S4K](https://doi.org/10.24432/C54S4K). [Official dataset page](https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones).
