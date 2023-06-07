[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![codecov](https://codecov.io/github/SIMEXP/giga_auto_qc/branch/main/graph/badge.svg?token=TYE4UURNTQ)](https://codecov.io/github/SIMEXP/giga_auto_qc)
# Giga automatic quality control

Automatic quality control for fMRIPrep outputs aimed for large datasets.

## Description

Quality control for preprocessed fMRI data is important for the subsequent data analysis.
fMRIPrep provides comprehensive visual reports, but when it comes to processing larger datasets,
visual inspection can be an tiresome process. `giga_auto_qc` implemented some basic quality
metrics, calculated using fMRIPrep outputs, to highlight scans that doesn't worth your attention in
further visual qulaity control.

- Dice coefficient: The metric calculate the overlap of the preprocessed full brain mask and the ICBM
nonlinear-asymmetric 2009c MNI template. Higher values are better. We calculate one score for the T1w
mask and one for each functional scan.
    - `anatomical_dice`: Anatomical, threshold at 0.99
    - `functional_dice`: Functional, threshold at 0.89

- Framewise displacement: expresses instantaneous head-motion. Rotational displacements are calculated
as the displacement on the surface of a sphere of radius 50 mm (Power 2012).
    - `mean_fd`: the average of framewise displacement per volume for each functional scan.
    - `mean_fd_scrubbed`: the average of framewise displacement after scrubbing at 0.2 for each functional scan.
    - `proportion_kept`: Proportion of volumes remaining after scrubbing at 0.2 mm

The default thresholds are as followed:

| Metrics   | `anatomical_dice` | `functional_dice` | `mean_fd` | `mean_fd_scrubbed` | `proportion_kept` |
|-----------|-------------------|-------------------|-----------|--------------------|-------------------|
| Threshold | 0.97              | 0.89              | 0.55      | N/A                | 0.5               |

A subject with failed `anatomical_dice` would be marked as failed.
A scan with any functiona metrics failed would be marked as failed.

Users can use the report as is to filter subjects, or perform further visual inspections.

## How to report errors

Please use the GitHub issue to report errors.
Check out the open issues first to see if we're already working on it.
If not, open up a new issue and we will get back to you when we can!

## How to contribute

You can review open issues that we are looking for help with.
If you submit a new pull request please be as detailed as possible in your comments.

## Installation

```
pip install .
```

For development:
```
pip install -e .[dev]
```

## Usage

```
usage: giga_auto_qc [-h] [--participant_label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]]
                    [--session SESSION [SESSION ...]] [--task TASK [TASK ...]]
                    bids_dir output_dir {participant,group}

Quality control metric in one tsv file for fmriprep processed datasets.

positional arguments:
  bids_dir              The directory with the input dataset (e.g. fMRIPrep derivative)formatted according to
                        the BIDS standard.
  output_dir            The directory where the output files should be stored.
  {participant,group}   Level of the analysis that will be performed.

optional arguments:
  -h, --help            show this help message and exit
  --participant_label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]
                        The label(s) of the participant(s) that should be analyzed. The label corresponds to
                        sub-<participant_label> from the BIDS spec (so it does not include 'sub-'). If this
                        parameter is not provided all subjects should be analyzed. Multiple participants can
                        be specified with a space separated list.
  --session SESSION [SESSION ...]
                        The label(s) of the sessions that should be analyzed. The label corresponds to
                        ses-<session_label> from the BIDS spec (so it does not include 'ses-').
  --task TASK [TASK ...]
                        The name of the task that you want to calculate metric with. The label corresponds to
                        task-<task_label> from the BIDS spec (so it does not include 'task-').
  --quality_control_parameters QUALITY_CONTROL_PARAMETERS
                        The path to customised quality control parameters. When no file is supplied, we will
                        filter with the default parameters. It should include the following fields:
                        mean_fd (default=0.55), scrubbing_fd (default=0.2), proportion_kept (default=0.5),
                        anatomical_dice (default=0.99), functional_dice (default=0.89)
  --reindex-bids        Reindex BIDS data set, even if layout has already been created.
  --verbose VERBOSE     Verbrosity. 0 for minimal, 1 for more details. Default to 1.
```

## Acknowledgements

This is a Python project packaged according to [Contemporary Python Packaging - 2023][].

We acknowledge all the BIDS-Apps team
https://github.com/orgs/BIDS-Apps/people

[Contemporary Python Packaging - 2023]: https://effigies.gitlab.io/posts/python-packaging-2023/
