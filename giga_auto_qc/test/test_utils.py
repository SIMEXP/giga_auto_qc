import pandas as pd
import numpy as np
from giga_auto_qc import utils


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

    bids_specifier_index = [
        "sub-test_task-rest_run-001",
        "sub-test_task-rest_run-002",
        "sub-test_task-finger",
    ]
    metrics = pd.DataFrame(
        np.random.random((3, 4)), index=bids_specifier_index
    )
    parsed = utils.parse_scan_information(metrics=metrics)
    assert list(parsed.columns[:3]) == ["participant_id", "task", "run"]
