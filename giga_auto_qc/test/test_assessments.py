import numpy as np
from nibabel import Nifti1Image
from giga_auto_qc import assessments


def test_dice_coefficient():
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
