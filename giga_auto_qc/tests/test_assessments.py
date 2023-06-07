import numpy as np
import pandas as pd
from nibabel import Nifti1Image
from giga_auto_qc import assessments


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

    exclude = assessments._check_mask_affine(
        [processed, processed, processed, processed, weird, weird]
    )
    assert len(exclude) == 2
    assert exclude == [4, 5]
