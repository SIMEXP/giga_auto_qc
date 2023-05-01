import argparse
from pathlib import Path

from giga_auto_qc.workflow import workflow


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=(
            "Quality control metric in one tsv file for fmriprep "
            "processed datasets."
        ),
    )
    parser.add_argument(
        "bids_dir",
        action="store",
        type=Path,
        help="The directory with the input dataset (e.g. fMRIPrep derivative)"
        "formatted according to the BIDS standard.",
    )
    parser.add_argument(
        "output_dir",
        action="store",
        type=Path,
        help="The directory where the output files should be stored.",
    )
    parser.add_argument(
        "analysis_level",
        help="Level of the analysis that will be performed.",
        choices=["participant", "group"],
    )
    parser.add_argument(
        "--participant_label",
        help="The label(s) of the participant(s) that should be analyzed. The "
        "label corresponds to sub-<participant_label> from the BIDS spec (so "
        "it does not include 'sub-'). If this parameter is not provided all "
        "subjects should be analyzed. Multiple participants can be specified "
        "with a space separated list.",
        nargs="+",
    )
    parser.add_argument(
        "--session",
        help="The label(s) of the sessions that should be analyzed. The "
        "label corresponds to ses-<session_label> from the BIDS spec (so "
        "it does not include 'ses-'). ",
        nargs="+",
    )
    parser.add_argument(
        "--task",
        help="The name of the task that you want to calculate metric with. "
        "The label corresponds to task-<task_label> from the BIDS spec (so "
        "it does not include 'task-'). ",
        nargs="+",
    )
    args = parser.parse_args()

    workflow(args)
