from typing import List
from pathlib import Path
import pandas as pd

BIDS_ENTITIES = {
    "sub": 0,
    "ses": 1,
    "task": 2,
    "acq": 3,
    "run": 4,
}


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
    Parts of the identifier that do not match are ignored.

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

    # get all unique entities
    headers_members = set()
    for id in metrics.index:
        exemplar = id.split("_")
        new_headers = set(
            [
                e.split("-")[0]
                for e in exemplar
                if e.split("-")[0] in BIDS_ENTITIES
            ]
        )
        headers_members.update(new_headers)
    ordered_header = [None] * len(BIDS_ENTITIES)
    for header in headers_members:
        if header in BIDS_ENTITIES:
            ordered_header[BIDS_ENTITIES[header]] = header
    headers = [h for h in ordered_header if h is not None]  # remove none

    identifiers = pd.DataFrame(
        metrics.index.tolist(), index=metrics.index, columns=["identifier"]
    )
    split_data = identifiers["identifier"].str.split("_", expand=True)

    # filter split data to only include columns corresponding to recognised headers
    split_data = split_data.iloc[
        :,
        [
            i
            for i, part in enumerate(identifiers["identifier"][0].split("_"))
            if part.split("-")[0] in BIDS_ENTITIES
        ],
    ]
    identifiers[headers] = split_data

    identifiers = identifiers.drop("identifier", axis=1)
    for h in headers:
        identifiers[h] = identifiers[h].str.replace(f"{h}-", "")
    identifiers = identifiers.rename(columns={"sub": "participant_id"})
    metrics = pd.concat((identifiers, metrics), axis=1)
    return metrics
