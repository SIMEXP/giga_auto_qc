import numpy as np
import pandas as pd
from nibabel import Nifti1Image
from giga_auto_qc import assessments
from bids import BIDSLayout
from pkg_resources import resource_filename
import pytest
import templateflow


def test_quality_accessments():
    functional_metrics = pd.DataFrame(
        [0.2, 0.99, 0.88],
        columns=["sub-001_task-rest"],
        index=["mean_fd_raw", "proportion_kept", "functional_dice"],
    ).T
    anatomical_metrics = pd.DataFrame(
        [0.99, True], columns=["001"], index=["anatomical_dice", "pass_qc"]
    ).T
    qc = {
        "mean_fd": 0.55,
        "scrubbing_fd": 0.2,
        "proportion_kept": 0.5,
        "anatomical_dice": 0.97,
        "functional_dice": 0.87,
    }
    metrics = assessments.quality_accessments(
        functional_metrics=functional_metrics,
        anatomical_metrics=anatomical_metrics,
        qulaity_control_standards=qc,
    )
    assert metrics["pass_all_qc"].astype(int).sum() == 1

    metrics = assessments.quality_accessments(
        functional_metrics=functional_metrics,
        anatomical_metrics=pd.DataFrame(),
        qulaity_control_standards=qc,
    )
    assert (
        metrics["pass_all_qc"].astype(int).sum()
        == metrics["pass_func_qc"].astype(int).sum()
    )
    assert metrics["pass_anat_qc"].isnull().all() == True


def test_dice_coefficient():
    """Check the dice coefficient is calculated correctly."""
    # test image of (5, 5, 6)
    img_base = np.zeros([5, 5, 6])
    processed_vol = img_base.copy()
    processed_vol[2:4, 2:4, 2:4] += 1
    processed = Nifti1Image(processed_vol, np.eye(4))
    # two identical image should give you perfect overlap
    assert (
        assessments._dice_coefficient(
            processed_img=processed, template_mask=processed
        )
        == 1
    )

    # no overlap
    template_mask = img_base.copy()
    template_mask[0:1, 0:2, 0:2] += 1
    template_mask = Nifti1Image(template_mask, np.eye(4))
    assert (
        assessments._dice_coefficient(
            processed_img=processed, template_mask=template_mask
        )
        == 0
    )


def test_check_mask_affine():
    """Check odd affine detection."""

    img_base = np.zeros([5, 5, 6])
    processed_vol = img_base.copy()
    processed_vol[2:4, 2:4, 2:4] += 1
    processed = Nifti1Image(processed_vol, np.eye(4))
    weird = Nifti1Image(processed_vol, np.eye(4) * np.array([1, 1, 1.5, 1]).T)
    weird2 = Nifti1Image(processed_vol, np.eye(4) * np.array([1, 1, 1.6, 1]).T)
    exclude = assessments._check_mask_affine(
        [processed, processed, processed, processed, weird, weird, weird2],
        verbose=2,
    )
    assert len(exclude) == 3
    assert exclude == [4, 5, 6]


def test_get_consistent_masks():
    """Check odd affine detection."""
    # mix in different tasks
    mask_imgs = [
        f"sub-{i + 1:2d}_task-rest_space-MNI_desc-brain_mask.nii.gz"
        for i in range(7)
    ] + [
        f"sub-{i + 1:2d}_task-stuff_space-MNI_desc-brain_mask.nii.gz"
        for i in range(7)
    ]
    exclude = [1, 2, 10]
    (
        cleaned_func_masks,
        weird_mask_identifiers,
    ) = assessments._get_consistent_masks(mask_imgs, exclude)
    assert len(cleaned_func_masks) == len(mask_imgs) - len(exclude)
    assert len(weird_mask_identifiers["rest"]) == 2
    assert len(weird_mask_identifiers["stuff"]) == 1

    exclude = [1, 2, 3]
    (
        cleaned_func_masks,
        weird_mask_identifiers,
    ) = assessments._get_consistent_masks(mask_imgs, exclude)
    assert len(weird_mask_identifiers["rest"]) == 3
    assert weird_mask_identifiers.get("stuff") is None


@pytest.mark.smoke
def test_calculate_anat_metrics():
    bids_dir = resource_filename(
        "giga_auto_qc",
        "data/test_data/ds000017-fmriprep22.0.1-downsampled-nosurface",
    )
    fmriprep_bids_layout = BIDSLayout(
        root=bids_dir,
        database_path=bids_dir,
        validate=False,
        derivatives=True,
        reset_database=True,
    )
    template_mask = templateflow.api.get(
        ["MNI152NLin2009cAsym"], desc="brain", suffix="mask", resolution="01"
    )
    df = assessments.calculate_anat_metrics(
        ["1", "2"],
        fmriprep_bids_layout,
        {"anat": template_mask},
        {"anatomical_dice": 0.97},
    )

    assert df.shape == (2, 2)
