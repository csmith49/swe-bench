from __future__ import annotations


import click
from swe_bench.models import Split, Evaluation


@click.command()
@click.option(
    "--split",
    type=click.Choice(["lite", "test", "verified"]),
    default="verified",
    callback=lambda _ctx, _param, value: Split.from_str(value),
)
@click.argument("entry", type=str)
def main(split: Split, entry: str):
    evaluation = Evaluation.from_github(split, entry)
    for prediction in evaluation.predictions:
        if prediction.patch == "":
            print(prediction.instance_id)
