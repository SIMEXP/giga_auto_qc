import argparse
from pathlib import Path

from giga_auto_qc.workflow import workflow
from giga_auto_qc import __version__


def main(argv=None):
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
        "-v", "--version", action="version", version=__version__
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
    parser.add_argument(
        "--quality_control_parameters",
        type=Path,
        help="The path to customised quality control parameters. When no file "
        "is supplied, we will filter with the default parameters. It should "
        "include the following fields: mean_fd (default=0.55), scrubbing_fd "
        "(default=0.2), proportion_kept (default=0.5), anatomical_dice "
        "(default=0.99), functional_dice (default=0.89)",
    )
    parser.add_argument(
        "--reindex-bids",
        help="Reindex BIDS data set, even if layout has already been created.",
        action="store_true",
    )
    parser.add_argument(
        "--verbose",
        help="Verbrosity. 0 for minimal, 1 for more details. Default to 1.",
        type=int,
        default=1,
    )
    args = parser.parse_args(argv)

    workflow(args)
