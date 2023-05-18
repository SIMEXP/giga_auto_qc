from typing import List
import json
from pathlib import Path

from bids import BIDSLayout

from giga_auto_qc import assessments


DEFAULT_QC_STANDARD = {
    "mean_fd": 0.55,
    "scrubbing_fd": 0.2,
    "proportion_kept": 0.5,
    "anatomical_dice": 0.97,
    "functional_dice": 0.89,
}


def workflow(args):
    print(args)
    # set file paths
    bids_dir = args.bids_dir
    output_dir = args.output_dir
    analysis_level = args.analysis_level
    participant_label = args.participant_label
    quality_control_parameters = args.quality_control_parameters

    if not bids_dir.is_dir():
        raise FileNotFoundError(
            "fMRIPrep directory does not exist: " f"{str(bids_dir)}"
        )

    if not quality_control_parameters:
        quality_control_parameters = DEFAULT_QC_STANDARD
    else:
        with open(quality_control_parameters, "r") as f:
            quality_control_parameters = json.load(f)
    print(f"Quality control parameters: {quality_control_parameters}")

    if set(quality_control_parameters.keys()) != \
        set(DEFAULT_QC_STANDARD.keys()):
        raise ValueError(
            "The supplied quality control parameter file "
            f"{args.quality_control_parameters} should contain the following"
            f"fields: {DEFAULT_QC_STANDARD.keys()}; the supplied file contains"
            f" {quality_control_parameters.keys()}."
        )

    fmriprep_bids_layout = BIDSLayout(
        root=bids_dir,
        database_path=bids_dir,
        validate=False,
        derivatives=True,
    )
    # check output path
    output_dir.mkdir(parents=True, exist_ok=True)

    # get subject list
    subjects = _get_subject_lists(participant_label, bids_dir)
    # infer task for bids search
    tasks = args.task if args.task else fmriprep_bids_layout.get_tasks()

    reference_masks = assessments.get_reference_mask(
        analysis_level, subjects, tasks, fmriprep_bids_layout
    )

    anatomical_metrics = assessments.calculate_anat_metrics(
        subjects, fmriprep_bids_layout, reference_masks,
        quality_control_parameters
    )

    for task in tasks:
        print(f"task-{task}")
        metrics = assessments.calculate_functional_metrics(
            subjects,
            task,
            fmriprep_bids_layout,
            reference_masks,
            quality_control_parameters
        )
        metrics = assessments.quality_accessments(
            metrics, anatomical_metrics, quality_control_parameters
        )
        # split the index into sub - ses - task - run
        metrics = assessments.parse_scan_information(metrics)
        metrics.to_csv(output_dir / f"task-{task}_report.tsv", sep="\t")


def _get_subject_lists(
    participant_label: List[str], bids_dir: Path
) -> List[str]:
    """Parse subject list from user options"""
    if participant_label:
        return participant_label
    # get all subjects, this is quicker than bids...
    subject_dirs = bids_dir.glob("sub-*/")
    return [
        subject_dir.name.split("-")[-1]
        for subject_dir in subject_dirs
        if subject_dir.is_dir()
    ]
