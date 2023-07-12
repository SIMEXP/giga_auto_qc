from pathlib import Path
import pandas as pd
import numpy as np
from bids.tests import get_test_data_path
from giga_auto_qc import utils


def test_get_subject_lists():
    bids_test = Path(get_test_data_path())
    # strip the sub- prefix
    subjects = utils.get_subject_lists(participant_label=["sub-01"])
    assert len(subjects) == 1
    assert subjects[0] == "01"
    subjects = utils.get_subject_lists(
        participant_label=None, bids_dir=bids_test / "ds005_derivs/dummy"
    )
    assert len(subjects) == 1
    assert subjects[0] == "01"


def test_parse_scan_information():
    bids_specifier_index = [
        "sub-test_ses-baseline_task-rest_run-001",
        "sub-test_ses-baseline_task-rest_run-002",
        "sub-test_ses-baseline_task-rest_run-003",
    ]
    metrics = pd.DataFrame(
        np.random.random((3, 4)), index=bids_specifier_index
    )
    parsed = utils.parse_scan_information(metrics=metrics)
    assert list(parsed.columns[:4]) == ["participant_id", "ses", "task", "run"]
    assert (
        parsed.loc["sub-test_ses-baseline_task-rest_run-002", "participant_id"]
        == "test"
    )

    # specifiers with different entities
    bids_specifier_index = [
        "sub-test_task-finger",
        "sub-test_task-rest_run-001",
        "sub-test_task-rest_run-002",
    ]
    metrics = pd.DataFrame(
        np.random.random((3, 4)), index=bids_specifier_index
    )
    parsed = utils.parse_scan_information(metrics=metrics)
    assert list(parsed.columns[:3]) == ["participant_id", "task", "run"]
