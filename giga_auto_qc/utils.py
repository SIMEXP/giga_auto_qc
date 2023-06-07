from typing import List
from pathlib import Path
import pandas as pd


def get_subject_lists(
    participant_label: List[str] = None, bids_dir: Path = None
) -> List[str]:
    """
    Parse subject list from user options.

    Parameters
    ----------

    participant_label :

        A list of BIDS competible subject identifiers.
        If the prefix `sub-` is present, it will be removed.

    bids_dir :

        The fMRIPrep derivative output.

    Return
    ------

    List
        BIDS subject identifier without `sub-` prefix.
    """
    if participant_label:
        # TODO: check these IDs exists
        checked_labels = []
        for sub_id in participant_label:
            if "sub-" in sub_id:
                sub_id = sub_id.replace("sub-", "")
            checked_labels.append(sub_id)
        return checked_labels
    # get all subjects, this is quicker than bids...
    subject_dirs = bids_dir.glob("sub-*/")
    return [
        subject_dir.name.split("-")[-1]
        for subject_dir in subject_dirs
        if subject_dir.is_dir()
    ]


def parse_scan_information(metrics: pd.DataFrame) -> pd.DataFrame:
    """
    Parse the identifier into BIDS entities: subject, session, task, run.
    If session and run are not present, the information will not be parsed.

    Parameters
    ----------

    metrics:
        Quality assessment output with identifier as index.

    Returns
    -------
    pandas.DataFrame
        Quality assessment with BIDS entity separated.
    """
    metrics.index.name = "identifier"
    examplar = metrics.index[0].split("_")
    headers = [e.split("-")[0] for e in examplar]
    identifiers = pd.DataFrame(
        metrics.index.tolist(), index=metrics.index, columns=["identifier"]
    )
    identifiers[headers] = identifiers["identifier"].str.split(
        "_", expand=True
    )
    identifiers = identifiers.drop("identifier", axis=1)
    for h in headers:
        identifiers[h] = identifiers[h].str.replace(f"{h}-", "")
    identifiers = identifiers.rename(columns={"sub": "participant_id"})
    metrics = pd.concat((identifiers, metrics), axis=1)
    return metrics
