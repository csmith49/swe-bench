"""
Models for representing SWE-bench evaluation results.
"""

from __future__ import annotations

from enum import Enum
from datetime import datetime
import ast

import yaml
import requests

import datasets  # type: ignore
from pydantic import BaseModel, HttpUrl, AnyUrl, field_validator, Field


InstanceID = str
"""
Type alias for instance identifiers.
"""


class Split(str, Enum):
    """
    Collection of SWE-bench problem instances being considered.
    """

    LITE = "lite"
    TEST = "test"
    VERIFIED = "verified"

    @staticmethod
    def from_str(value: str) -> Split:
        """
        Get a split from a string.

        Raises:
            ValueError: if the string does not correspond to a valid split.
        """
        try:
            return Split[value.upper()]
        except KeyError as e:
            raise ValueError(f"{value} is not a valid split.") from e

    @property
    def dataset_identifier(self) -> str:
        """
        Identifier (compatible with `datasets`) containing the problem instances given by the split.
        """
        dataset_ids = {
            Split.LITE: "princeton-nlp/SWE-bench_Lite",
            Split.TEST: "princeton-nlp/SWE-bench",
            Split.VERIFIED: "princeton-nlp/SWE-bench_Verified",
        }
        return dataset_ids[self]


class Prediction(BaseModel):
    """
    The per-instance output of a model.
    """

    instance_id: InstanceID
    """
    Identifier for the problem instance being solved.
    """

    patch: str = Field(alias="model_patch")
    """
    Git patch produced by the model.
    """

    name_or_path: str = Field(alias="model_name_or_path")
    """
    Name or path to the model used for prediction.
    """


class Results(BaseModel):
    """
    Summarized results of a leaderboard entry.
    """

    no_generation: list[InstanceID]
    """
    Instance identifiers for which the model generated no patch.
    """

    no_logs: list[InstanceID]
    """
    Instance identifiers for which the evaluation harness produced no logs.
    """

    resolved: list[InstanceID]
    """
    Instance identifiers for all issues resolved by the model.
    """

    def is_resolved(self, instance_id: InstanceID) -> bool:
        """
        Check if an instance is resolved.
        """
        return instance_id in self.resolved


class Metadata(BaseModel):
    """
    Metadata about the leaderboard entry.
    """

    name: str
    """
    Name of the model used.
    """

    oss: bool
    """
    Whether the model is open-source or not.
    """

    verified: bool
    """
    Whether the results have been verified by SWE-bench leaderboard maintainers.
    """

    site: HttpUrl | None = None
    """
    URL for the model site.
    """

    logs: AnyUrl | None = None
    """
    S3 identifier for build/test logs.
    """

    trajs: AnyUrl | None = None
    """
    S3 identifier for model trajectories.
    """


def get_gh_file(split: Split, entry: str, path: str, timeout: int = 100) -> str:
    """
    Get a file from the SWE-bench Github repository.

    Args:
        split (Split): The split of the leaderboard entry containing the file.

        entry (str): The name of the leaderboard entry containing the file.

        path (str): Path to the file.

        timeout (int, default=100): Timeout for the HTTP request.
    """
    GH_URL = "https://raw.githubusercontent.com"  # pylint: disable=invalid-name
    EVAL_DIR = "swe-bench/experiments/refs/heads/main/evaluation"  # pylint: disable=invalid-name

    return requests.get(
        f"{GH_URL}/{EVAL_DIR}/{split.value}/{entry}/{path}",
        timeout=timeout,
    ).text.strip()


class Evaluation(BaseModel):
    """
    Summary of a model's evaluation on a SWE-bench problem set.
    """

    split: Split
    """
    The problem split being evaluated.
    """

    predictions: list[Prediction]
    """
    A list of predictions made by the model.
    """

    results: Results
    """
    Results summarizing prediction performance.
    """

    metadata: Metadata
    """
    Metadata about the leaderboard entry.
    """

    @staticmethod
    def from_github(split: Split, entry: str) -> Evaluation:
        """
        Generate an evaluation directly from the data on GitHub.
        """

        predictions = [
            Prediction.model_validate_json(line)
            for line in get_gh_file(split, entry, "all_preds.jsonl").split("\n")
            if line
        ]

        results = Results.model_validate_json(
            get_gh_file(split, entry, "results/results.json")
        )

        metadata = Metadata.model_validate(
            yaml.safe_load(get_gh_file(split, entry, "metadata.yaml"))
        )

        return Evaluation(
            split=split, predictions=predictions, results=results, metadata=metadata
        )


class Dataset(BaseModel):
    """
    Collection of problem instances.
    """

    split: Split
    """
    Split identifying the subset of problem instances.
    """

    instances: list[Instance]
    """
    Problem instances in the dataset.
    """

    @staticmethod
    def from_split(split: Split) -> Dataset:
        """
        Load the collection of problem instances from the indicated split.
        """
        data = datasets.load_dataset(split.dataset_identifier, split="test")
        return Dataset(
            split=split, instances=[Instance.model_validate(row) for row in data]
        )


class Instance(BaseModel):
    """
    SWE-bench problem instance.
    """

    repo: str
    instance_id: InstanceID
    base_commit: str
    patch: str
    test_patch: str
    problem_statement: str
    hints_text: str
    created_at: datetime
    version: str
    fail_to_pass: list[str] = Field(alias="FAIL_TO_PASS")
    pass_to_pass: list[str] = Field(alias="PASS_TO_PASS")
    environment_setup_commit: str

    @field_validator("fail_to_pass", "pass_to_pass", mode="before")
    @classmethod
    def validate_to_pass_lists(cls, value: str | list[str]) -> list[str]:
        """
        Validation that converts string represntation of a list to a list.
        """
        if isinstance(value, str):
            return ast.literal_eval(value)

        return value
