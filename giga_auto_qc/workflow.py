import json
from bids import BIDSLayout

from giga_auto_qc import assessments, utils


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

    if set(quality_control_parameters.keys()) != set(
        DEFAULT_QC_STANDARD.keys()
    ):
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
        reset_database=args.reindex_bids,
    )
    if fmriprep_bids_layout is None:
        raise ValueError(
            f"Cannot index directory in {bids_dir}. "
            "Please ensure the path is a fMRIPrep output directory."
        )

    # check output path
    output_dir.mkdir(parents=True, exist_ok=True)

    # get subject list
    subjects = utils.get_subject_lists(participant_label, bids_dir)
    # infer task for bids search
    tasks = args.task if args.task else fmriprep_bids_layout.get_tasks()

    (
        reference_masks,
        weird_func_mask_identifiers,
    ) = assessments.get_reference_mask(
        analysis_level, subjects, tasks, fmriprep_bids_layout, args.verbose
    )

    anatomical_metrics = assessments.calculate_anat_metrics(
        subjects,
        fmriprep_bids_layout,
        reference_masks,
        quality_control_parameters,
        args.verbose,
    )

    for task in tasks:
        print(f"task-{task}")
        metrics = assessments.calculate_functional_metrics(
            subjects,
            task,
            fmriprep_bids_layout,
            reference_masks,
            quality_control_parameters,
            args.verbose,
        )
        metrics = assessments.quality_accessments(
            metrics, anatomical_metrics, quality_control_parameters
        )
        metrics["different_func_affine"] = False
        if (
            weird_func_mask_identifiers is not None
            and task in weird_func_mask_identifiers
        ):
            metrics.loc[
                weird_func_mask_identifiers[task], "different_func_affine"
            ] = True
        # split the index into sub - ses - task - run
        metrics = utils.parse_scan_information(metrics)
        metrics.to_csv(output_dir / f"task-{task}_report.tsv", sep="\t")
