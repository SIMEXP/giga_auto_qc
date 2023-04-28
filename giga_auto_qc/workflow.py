from typing import List

from pathlib import Path

from bids import BIDSLayout

from giga_auto_qc import assessments


def workflow(args):
    print(args)
    # set file paths
    bids_dir = args.bids_dir
    output_dir = args.output_dir
    analysis_level = args.analysis_level
    participant_label = args.participant_label

    if not bids_dir.is_dir():
        raise FileNotFoundError(
            "fMRIPrep directory does not exist: " f"{str(bids_dir)}"
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
        subjects, fmriprep_bids_layout, reference_masks
    )

    for task in tasks:
        print(f"task-{task}")
        metrics = assessments.calculate_functional_metrics(
            subjects,
            task,
            fmriprep_bids_layout,
            reference_masks,
        )
        metrics = assessments.quality_accessments(metrics, anatomical_metrics)
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
