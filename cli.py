from __future__ import annotations


import click
from models import Split, Evaluation


@click.command()
@click.option(
    "--split",
    type=click.Choice(["lite", "test", "verified"]),
    default="verified",
    callback=lambda _ctx, _param, value: Split.from_str(value),
)
@click.argument("entry", type=str)
def cli(split: Split, entry: str):
    evaluation = Evaluation.from_github(split, entry)
    for prediction in evaluation.predictions:
        if prediction.patch == "":
            print(prediction.instance_id)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
