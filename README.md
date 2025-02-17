# swe-bench

This module provides some structured representations of [SWE-bench](http://www.swebench.com) data and test results to make exploration and data science a bit easier.

## Usage

The easiest way to use this library is to add it as a dependency to your project using [poetry](). In your `pyconfig.toml`, add the following:

```toml
[tool.poetry.dependencies]
swe-bench = {git = "https://github.com/csmith49/swe-bench.git"}
```
## Examples

To load the SWE-bench datasets:

```python
from swe_bench.models import Dataset, Split

instances = Dataset.from_split(Split.VERIFIED).instances
```

To select the entire benchmark, use `Split.TEST`. To help with scripting use `Split.from_str(...)` for parsing command-line arguments.

To find leaderboard entries, which we structure as `Evaluation` models:

```python
from swe_bench.models import Evaluation, Split
from swe_bench.utilities import get_all_entries

split = Split.VERIFIED

entries = get_all_entries(split=split)
evaluations = [Evaluation.from_github(split=split, entry=entry) for entry in entries]
```

Not all entries are well-formatted, so if you run into `ValidationError` issues wrap each `Evaluation.from_github(...)` call in a try-catch block.
