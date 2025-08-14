from typing import Union, List, Tuple, Optional

from pathlib import Path
from tqdm import tqdm
import numpy as np
import pandas as pd

from nibabel import Nifti1Image

from nilearn.image import load_img, resample_to_img
from nilearn.masking import intersect_masks, load_mask_img

from bids import BIDSLayout

TEMPLATE = "MNI152NLin2009cAsym"


def get_reference_mask(
    analysis_level: str,
    subjects: List[str],
    task: List[str],
    fmriprep_bids_layout: BIDSLayout,
    verbose: int = 1,
) -> Tuple[dict, Optional[dict]]:
    """
    Find the correct target mask for dice coefficient.

    Parameters
    ----------

    analysis_level : {"group", "participant"}
        BIDS app analyisi level.

    subjects :
        Participant IDs in a BIDS dataset.

    task :
        Task name in a BIDS dataset.

    fmriprep_bids_layout :
        BIDS layout of a fMRIPrep derivative.

    verbose :
        Level of verbosity.

    Returns
    -------

    Dict
        Reference brain masks for anatomical and functional scans.

    Dict
        Identidiers of scans with a different affine by task. If all
        scans in one task have the same affine, the task will not
        be included in the dictionary. If all scans have the same
        affine, return None.
    """
    import templateflow

    template_mask = templateflow.api.get(
        [TEMPLATE], desc="brain", suffix="mask", resolution="01"
    )
    reference_masks = {"anat": template_mask}
    if verbose > 0:
        print("Retrieved anatomical reference mask")

    if analysis_level == "group" and len(subjects) > 1:
        if verbose > 0:
            print("Create dataset level functional brain mask")
        # create a group level mask
        func_filter = {
            "subject": subjects,
            "task": task,
            "space": TEMPLATE,
            "desc": ["brain"],
            "suffix": ["mask"],
            "extension": "nii.gz",
            "datatype": "func",
        }
        func_masks = fmriprep_bids_layout.get(
            **func_filter, return_type="file"
        )
        if verbose > 1:
            print(f"Got reference template {TEMPLATE}.")
            print(f"Found {len(func_masks)} masks")

        if exclude := _check_mask_affine(func_masks, verbose):
            func_masks, weird_mask_identifiers_by_task = _get_consistent_masks(
                func_masks, exclude
            )
            if verbose > 1:
                print(f"Remaining: {len(func_masks)} masks")
        else:
            weird_mask_identifiers_by_task = None
        group_func_map = intersect_masks(func_masks, threshold=0.5)
        reference_masks["func"] = group_func_map
    else:
        if verbose > 0:
            print("Use standard template as functional scan reference.")
        reference_masks["func"] = template_mask
        weird_mask_identifiers_by_task = None
    return reference_masks, weird_mask_identifiers_by_task


def _get_consistent_masks(
    mask_imgs: List[Union[Path, str, Nifti1Image]], exclude: List[int]
) -> Tuple[List[int], dict]:
    """Create a list of masks that has the same affine.

    Parameters
    ----------

    func_masks :
        The original list of functional masks

    exclude :
        List of index to exclude.

    Returns
    -------
    List of str
        Functional masks with the same affine.

    Dict
        Identidiers of scans with a different affine by task.
    """
    weird_mask_identifiers = []
    odd_masks = np.array(mask_imgs)[np.array(exclude)]
    odd_masks = odd_masks.tolist()
    for odd_file in odd_masks:
        identifier = Path(odd_file).name.split("_space")[0]
        weird_mask_identifiers.append(identifier)
    cleaned_func_masks = set(mask_imgs) - set(odd_masks)
    cleaned_func_masks = list(cleaned_func_masks)

    # group identifier by task
    weird_mask_identifiers_by_task = {}
    for identifier in weird_mask_identifiers:
        task = identifier.split("_task-")[-1].split("_")[0]
        if task not in weird_mask_identifiers_by_task:
            weird_mask_identifiers_by_task[task] = []
        weird_mask_identifiers_by_task[task].append(identifier)
    return cleaned_func_masks, weird_mask_identifiers_by_task


def _check_mask_affine(
    mask_imgs: List[Union[Path, str, Nifti1Image]], verbose: int = 1
) -> Union[list, None]:
    """Given a list of input mask images, show the most common affine matrix
    and subjects with different values.

    Parameters
    ----------
    mask_imgs : :obj:`list` of Niimg-like objects
        See :ref:`extracting_data`.
        3D individual masks with same shape and affine.

    verbose :
        Level of verbosity.

    Returns
    -------

    List or None
        Index of masks with odd affine matrix. Return None when all masks have
        the same affine matrix.
    """
    # save all header and affine info in hashable type...
    header_info = {"affine": []}
    key_to_header = {}
    for this_mask in mask_imgs:
        _, affine = load_mask_img(this_mask, allow_empty=True)
        affine_hashable = str(affine)
        header_info["affine"].append(affine_hashable)
        if affine_hashable not in key_to_header:
            key_to_header[affine_hashable] = affine

    if isinstance(mask_imgs[0], Nifti1Image):
        mask_imgs = np.arange(len(mask_imgs))
    else:
        mask_imgs = np.array(mask_imgs)
    # get most common values
    common_affine = max(
        set(header_info["affine"]), key=header_info["affine"].count
    )
    if verbose > 0:
        print(
            f"We found {len(set(header_info['affine']))} unique affine "
            f"matrices. The most common one is "
            f"{key_to_header[common_affine]}"
        )
    odd_balls = set(header_info["affine"]) - {common_affine}
    if not odd_balls:
        return None

    exclude = []
    for ob in odd_balls:
        ob_index = [
            i for i, aff in enumerate(header_info["affine"]) if aff == ob
        ]
        if verbose > 1:
            print(
                "The following subjects has a different affine matrix "
                f"({key_to_header[ob]}) comparing to the most common value: "
                f"{mask_imgs[ob_index]}."
            )
        exclude += ob_index
    if verbose > 0:
        print(
            f"{len(exclude)} out of {len(mask_imgs)} has "
            "different affine matrix. Ignore when creating group mask."
        )
    return sorted(exclude)


def calculate_functional_metrics(
    subjects: List[str],
    task: List[str],
    fmriprep_bids_layout: BIDSLayout,
    reference_masks: dict,
    qulaity_control_standards: dict,
    verbose: int = 1,
) -> pd.DataFrame:
    """
    Calculate functional scan quality metrics:
        mean framewise displacement of original scan
        mean framewise displacement after scrubbing
        proportion of scan remained after scrubbing
        dice coefficient.

    The default scrubbing criteria is set to 0.2 mm.

    Parameters
    ----------
    subjects :
        Participant IDs in a BIDS dataset.

    task :
        Task name in a BIDS dataset.

    fmriprep_bids_layout :
        BIDS layout of a fMRIPrep derivative.

    reference_masks :
        Reference brain masks for anatomical and functional scans.

    Returns
    -------
    pandas.DataFrame
        Functional scan quality metrics
    """
    metrics = {}

    confounds_filter = {
        "subject": subjects,
        "task": task,
        "desc": "confounds",
        "extension": "tsv",
    }

    confounds = fmriprep_bids_layout.get(
        **confounds_filter, return_type="file"
    )
    if verbose > 0:
        print("Calculate motion QC...")
    for confound_file in tqdm(confounds):
        # compute fds score
        framewise_displacements = pd.read_csv(confound_file, sep="\t")[
            "framewise_displacement"
        ].to_numpy()
        timeseries_length = len(framewise_displacements)
        fds_mean_raw = np.nanmean(framewise_displacements)
        kept_volumes = (
            framewise_displacements < qulaity_control_standards["scrubbing_fd"]
        )
        fds_mean_scrub = np.nanmean(framewise_displacements[kept_volumes])
        proportion_kept = sum(kept_volumes) / timeseries_length
        identifier = Path(confound_file).name.split("_desc-confounds")[0]

        metrics[identifier] = {
            "mean_fd_raw": fds_mean_raw,
            "mean_fd_scrubbed": fds_mean_scrub,
            "proportion_kept": proportion_kept,
            "total_frames": timeseries_length,
        }

    func_filter = {
        "subject": subjects,
        "task": task,
        "space": TEMPLATE,
        "desc": ["brain"],
        "suffix": ["mask"],
        "extension": "nii.gz",
        "datatype": "func",
    }
    func_images = fmriprep_bids_layout.get(**func_filter, return_type="file")
    if verbose > 0:
        print("Calculate EPI mask dice...")
    for func_file in tqdm(func_images):
        identifier = Path(func_file).name.split(f"_space-{TEMPLATE}")[0]
        functional_dice = _dice_coefficient(func_file, reference_masks["func"])
        if identifier in metrics:
            metrics[identifier].update({"functional_dice": functional_dice})
        else:
            metrics[identifier] = {"functional_dice": functional_dice}
    metrics = pd.DataFrame(metrics).T
    return metrics.sort_index()


def calculate_anat_metrics(
    subjects: List[str],
    fmriprep_bids_layout: BIDSLayout,
    reference_masks: dict,
    qulaity_control_standards: dict,
    verbose: int = 1,
) -> pd.DataFrame:
    """
    Calculate the anatomical dice score.

    Parameters
    ----------
    subjects :
        Participant IDs in a BIDS dataset.

    fmriprep_bids_layout :
        BIDS layout of a fMRIPrep derivative.

    reference_masks :
        Reference brain masks for anatomical and functional scans.

    Returns
    -------
    pandas.DataFrame
        Anatomical scan dice score scan quality metrics.
    """
    if verbose > 0:
        print("Calculate the anatomical dice score.")
    # check if the derivative was created with anatomical fast-track
    check_anat = fmriprep_bids_layout.get(datatype="anat", return_type="file")
    if not check_anat:
        print("`anat/` not present in the derivatives. " "Skip anatomical QC.")
        return pd.DataFrame()

    metrics = {}
    for sub in tqdm(subjects):
        anat_filter = {
            "subject": sub,
            "space": TEMPLATE,
            "desc": ["brain"],
            "suffix": ["mask"],
            "extension": "nii.gz",
            "datatype": "anat",
        }
        anat_image = fmriprep_bids_layout.get(
            **anat_filter, return_type="file"
        )
        # dice
        anat_dice = _dice_coefficient(anat_image[0], reference_masks["anat"])
        metrics[sub] = {
            "anatomical_dice": anat_dice,
        }
    metrics = pd.DataFrame(metrics).T
    metrics["pass_qc"] = (
        metrics["anatomical_dice"]
        > qulaity_control_standards["anatomical_dice"]
    )
    return metrics.sort_index()


def quality_accessments(
    functional_metrics: pd.DataFrame,
    anatomical_metrics: pd.DataFrame,
    qulaity_control_standards: dict,
) -> pd.DataFrame:
    """
    Automatic quality accessments.
    Currently the criteria are a set of preset. Consider allow user providing
    there own.

    Parameters
    ----------

    functional_metrics:
        Functional scan metrics with fMRIPrep file identifier as index.

    anatomical_metrics:
        Anatomical scan metrics with fMRIPrep file identifier as index.

    Returns
    -------
    pandas.DataFrame
        All metric for a set of functional scans and pass / fail assessment.
    """
    keep_fd = (
        functional_metrics["mean_fd_raw"]
        < qulaity_control_standards["mean_fd"]
    )
    keep_proportion = (
        functional_metrics["proportion_kept"]
        > qulaity_control_standards["proportion_kept"]
    )
    keep_func = (
        functional_metrics["functional_dice"]
        > qulaity_control_standards["functional_dice"]
    )
    functional_metrics["pass_func_qc"] = keep_fd * keep_proportion * keep_func
    if anatomical_metrics.empty:
        functional_metrics["pass_anat_qc"] = np.nan
        functional_metrics["pass_all_qc"] = functional_metrics[
            "pass_func_qc"
        ].copy()
        return functional_metrics

    # get the anatomical pass / fail
    pass_anat_qc = {}
    for id in functional_metrics.index:
        sub = id.split("sub-")[-1].split("_")[0]
        pass_anat_qc[id] = {
            "anatomical_dice": anatomical_metrics.loc[sub, "anatomical_dice"],
            "pass_anat_qc": anatomical_metrics.loc[sub, "pass_qc"],
        }
    anat_qc = pd.DataFrame(pass_anat_qc).T
    metrics = pd.concat((functional_metrics, anat_qc), axis=1)
    metrics["pass_all_qc"] = metrics["pass_func_qc"] * metrics["pass_anat_qc"]
    print(
        f"{metrics['pass_all_qc'].astype(int).sum()} out of "
        f"{metrics.shape[0]} functional scans passed automatic QC."
    )
    return metrics


def _dice_coefficient(
    processed_img: Union[str, Path, Nifti1Image],
    template_mask: Union[str, Path, Nifti1Image],
) -> np.array:
    """
    Compute the Sørensen-dice coefficient between two n-d volumes.

    Parameters
    ----------

    processed_img:
        Path to the processed structural or functional mask from fMRIPrep.

    template_mask:
        Path or nifti image object of the reference template.

    Return
    ------
    numpy.array
        The dice coefficient.
    """
    # make sure the inputs are 3d
    processed_img = load_img(processed_img)
    template_mask = load_img(template_mask)

    # resample template to processed image
    if (template_mask.affine != processed_img.affine).any():
        template_mask = resample_to_img(
            template_mask, processed_img, interpolation="nearest"
        )

    # check space, resample target to source space
    processed_img = processed_img.get_fdata().astype(bool)
    template_mask = template_mask.get_fdata().astype(bool)
    intersection = np.sum(np.logical_and(processed_img, template_mask))
    total_elements = np.sum(processed_img) + np.sum(template_mask)
    return 2 * intersection / total_elements
