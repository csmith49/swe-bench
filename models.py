from __future__ import annotations

import requests
import yaml

from pydantic import BaseModel, HttpUrl


class Prediction(BaseModel):
    instance_id: str
    model_patch: str
    model_name_or_path: str


class Results(BaseModel):
    no_generation: list[str]
    no_logs: list[str]
    resolved: list[str]

    def is_resolved(self, instance_id: str) -> bool:
        return instance_id in self.resolved


class Metadata(BaseModel):
    name: str
    oss: bool
    verified: bool
    site: HttpUrl | None = None

    logs: str | None = None
    trajs: str | None = None


class Evaluation(BaseModel):
    predictions: list[Prediction]
    results: Results
    metadata: Metadata

    @staticmethod
    def from_github(split: str, entry: str, timeout: int = 100) -> Evaluation:
        """
        Generate an evaluation directly from the data on GitHub.
        """
        GH_URL = "https://raw.githubusercontent.com"
        EVAL_DIR = "swe-bench/experiments/refs/heads/main/evaluation"

        raw_predictions = requests.get(
            f"{GH_URL}/{EVAL_DIR}/{split}/{entry}/all_preds.jsonl",
            timeout=timeout,
        ).text.strip()

        predictions = [
            Prediction.model_validate_json(line)
            for line in raw_predictions.split("\n")
            if line
        ]

        results = Results.model_validate_json(
            requests.get(
                f"{GH_URL}/{EVAL_DIR}/{split}/{entry}/results/results.json",
                timeout=timeout,
            ).text
        )

        metadata = Metadata.model_validate(
            yaml.safe_load(
                requests.get(
                    f"{GH_URL}/{EVAL_DIR}/{split}/{entry}/metadata.yaml",
                    timeout=timeout,
                ).text
            )
        )

        return Evaluation(predictions=predictions, results=results, metadata=metadata)
