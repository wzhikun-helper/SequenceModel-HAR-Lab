# SequenceModel-HAR-Lab

**Subject-disjoint activity recognition, parameter-matched ablations, and training variability.**

[简体中文](README.md) · English · [Documentation](docs/README.md) · [Experiment registry](docs/experiment_registry.md) · [Project status](PROGRESS.md)

## Data and evaluation

[UCI HAR](https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones) contains 10,299 inertial windows from 30 participants. Each window is **128 × 9**, sampled at **50 Hz**, with six activity classes. Training, validation, and official test contain **17 / 4 / 9** disjoint participants and **6,037 / 1,315 / 2,947** windows. Channel standardization is fitted on training data only. Validation Macro-F1 selects the checkpoint, with validation loss breaking exact ties. The official test set is reserved for final evaluation. [Frozen protocol, labels, and signals](docs/data_protocol.md)

## Four Seed42 baselines

CNN uses local convolution, GRU uses gated state, Transformer uses self-attention and positional encoding, and Mamba uses a selective state-space block.

| Model | Accuracy | Macro-F1 | Loss | Parameters | Device |
| --- | --- | --- | --- | --- | --- |
| CNN A | 89.7523% | 89.8202% | 0.290570 | 27,270 | CPU |
| GRU B | 91.8222% | 91.9444% | 0.255319 | 14,790 | CPU |
| Transformer C | 88.0896% | 88.0326% | 0.425905 | 34,502 | CPU |
| Mamba D | 88.7004% | 88.8610% | 0.379041 | 33,670 | RTX 3090 |

All four runs use the same official test set. GRU has the highest Macro-F1 among these runs. One seed does not establish a general architecture ranking, and training times across CPU and GPU lack a common hardware basis. [Per-run configurations and evidence](docs/experiment_registry.md)

## Three-seed CNN ablation

Macro-F1 is reported as a percentage. The residual MLP and SE add the same number of parameters.

| Group | Seed42 | Seed43 | Seed44 | Mean |
| --- | --- | --- | --- | --- |
| A · CNN | 89.8202 | 88.5241 | 90.0424 | 89.4623 |
| B · CNN + SE | 89.7161 | 91.1212 | 89.5221 | 90.1198 |
| C · CNN + residual MLP | 89.6185 | 92.1449 | 88.6817 | 90.1484 |

SE averages **+0.6575 pp** over the original CNN and improves only on Seed43. It averages **−0.0286 pp** relative to the parameter-matched residual MLP. These runs provide insufficient evidence of a stable independent gain. [Paired results and sample standard deviations](docs/experiment_registry.md#cnn-三种子消融)

## GRU Task03 GPU three-seed results

| Seed | Accuracy | Macro-F1 | Loss |
| --- | --- | --- | --- |
| 42 | 91.2793% | 91.3919% | 0.362237 |
| 43 | 89.7523% | 89.8447% | 0.313432 |
| 44 | 90.7024% | 90.7504% | 0.352929 |
| Mean | 90.5780% | 90.6623% | 0.342866 |

These are separate RTX 3090 runs. The historical CPU GRU Seed42 remains a separate record; both hardware and software differ. All three seeds share the same participant split and reflect training variability on that split. Sitting has the lowest F1 across all three seeds. [Task03 per-class results](reports/gru_multiseed_task03_20261123/comparison.md)

## Navigation and reproduction

```sh
git clone https://github.com/wzhikun-helper/SequenceModel-HAR-Lab.git
cd SequenceModel-HAR-Lab
python -B scripts/check_public_docs.py
python -I -S -B -m unittest discover -s tests -v
```

The clone checks out the repository's default branch. PR reviewers can find the organization branch in the [release checklist](reports/repository_organization_20261123/final_release_checklist.md). Lightweight CI runs documentation checks, 25 standard-library unit tests, and static checks. A separate job runs eight synthetic Task03 reporting tests under `python -O`. The 16 synthetic PyTorch tests run locally.

For data reproduction, run `python -m pip install -r requirements-data.txt` in an isolated environment. Follow the official download and processing commands in the [Day 01 guide](docs/reproducing_day01.md). Raw files go to `data/raw/<Run>` and standardized artifacts to `data/processed/<Artifacts>`. See [CPU dependencies](requirements-cnn.txt), [training and reporting entry points](scripts/README.md), and the CUDA environments for [Task03](docs/gru_task03_protocol.md) and [Mamba](experiments/mamba_baseline_d_seed42_20261122/docs/environment.md).

| Location | Contents |
| --- | --- |
| [docs/](docs/README.md) | Data protocol, environments, reproduction, experiment registry |
| [src/](src/har_lab) · [scripts/](scripts/README.md) · [configs/](configs/gru_task03) | Models, entry points, versioned configuration |
| [reports/](reports/README.md) · [experiments/](experiments/mamba_baseline_d_seed42_20261122/README.md) | Public records, independent metric checks, figures, Mamba |
| [Learning records](learning_notes/fourth_plan_final_archive.md) · [Project skill](.agents/skills/uci-har-experiment-workflow/SKILL.md) | Teaching assessment and workflow |
| [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) | Run registration and artifact protection |

## Evidence levels and next research steps

**PASS** applies to the scope actually verified. **PARTIAL** indicates missing originals. Of the 60 Task03 manifest entries, 18 public files can be rechecked and 42 rely on historical server verification. The teacher's overall 48/48 assessment is recorded, with item-level transcript coverage marked PARTIAL. [Final report and all 48 questions](reports/fourth_plan_final_archive_20261123/README.md)

Future work covers additional participant splits and training seeds, participant-level sitting/standing error analysis, and runtime measurement in a shared environment. [Project status and evidence gaps](PROGRESS.md)

Dataset reference: [Human Activity Recognition Using Smartphones · DOI 10.24432/C54S4K](https://doi.org/10.24432/C54S4K).
