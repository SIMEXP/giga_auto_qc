from pkg_resources import resource_filename

from giga_auto_qc.run import main

import pytest


def test_help(capsys):
    try:
        main(["-h"])
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "Quality control metric" in captured.out


@pytest.mark.smoke
def test_smoke_participant(tmp_path, capsys):
    """Somke test on participant level."""
    bids_dir = resource_filename(
        "giga_auto_qc",
        "data/test_data/ds000017-fmriprep22.0.1-downsampled-nosurface",
    )

    # Smoke test the participant level
    main(
        [
            "--participant_label",
            "1",
            "--reindex-bids",
            str(bids_dir),
            str(tmp_path),
            "participant",
        ]
    )
    captured = capsys.readouterr()
    assert "participant_label=['1']" in captured.out
    assert (
        "Use standard template as functional scan reference." in captured.out
    )


@pytest.mark.smoke
def test_smoke_group(tmp_path, capsys):
    """Somke test on group level."""
    bids_dir = resource_filename(
        "giga_auto_qc",
        "data/test_data/ds000017-fmriprep22.0.1-downsampled-nosurface",
    )
    # Smoke test the group level
    main(
        [
            "--reindex-bids",
            str(bids_dir),
            str(tmp_path),
            "group",
        ]
    )
    captured = capsys.readouterr()
    assert "Create dataset level functional brain mask" in captured.out
