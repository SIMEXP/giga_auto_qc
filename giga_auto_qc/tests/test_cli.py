from pathlib import Path
from pkg_resources import resource_filename

import argparse
from giga_auto_qc.workflow import workflow

import pytest
import os

IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


@pytest.mark.skipif(
    IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions."
)
def test_smoke(tmp_path):
    bids_dir = resource_filename(
        "giga_auto_qc", "data/test_data/ds000017-fmriprep22.0.1-downsampled"
    )

    args = argparse.Namespace(
        reindex_bids=False,
        verbose=1,
        participant_label=[],
        task=None,
        quality_control_parameters=None,
        analysis_level="participant",
        bids_dir=Path(bids_dir),
        output_dir=tmp_path,
    )

    # Smoke test the participant level
    workflow(args)

    # Smoke test the group level
    args.analysis_level = "group"
    workflow(args)
