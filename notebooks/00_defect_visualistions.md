---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.1'
      jupytext_version: 1.2.1
  kernelspec:
    display_name: defects
    language: python
    name: defects
---

# Defect Visualisations

This is a visualisation of the defects created by the defect visualisation experiment.

```python
import sys

sys.path.append("../src")
import defects
import sdanalysis
import gsd.hoomd
from bokeh.io import show, output_notebook
from pathlib import Path
import ipywidgets

output_notebook()
```

```python
files = sorted(list(Path("../data/simulations/output").glob("*.gsd")))


@ipywidgets.interact(file=files)
def plot(file):
    with gsd.hoomd.open(str(file)) as trj:
        snap = trj[0]
        show(defects.plot_snapshot(snap))
```


```python

```
