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

# Defect Creation

Defects are a typical part of nearly all crystals, yet we have not observed any in the simulations of the p2 crystal. This notebook introduces defects into the p2 crystals to see how the crystal reacts. The defect we are interested in is a line defect, which runs along one of the crystal axes.

```python
# Import required modules
from sdrun import (
    initialise_snapshot,
    init_from_crystal,
    production,
    equilibrate,
    TrimerP2,
    SimulationParams as RunParams,
)

import numpy as np
import hoomd

import sys

sys.path.append("../src")

from defects import (
    remove_vertical,
    remove_horizontal,
    remove_vertical_cell,
    plot_snapshots,
    plot_snapshot,
    run_sim,
)

import figures

from bokeh.plotting import show, output_notebook
from bokeh.io import export_svgs

output_notebook()
from IPython.display import Image

# def show(plot):
#     export_png(plot, filename=f"{str(hash(plot))}.png")
#     return Image(f"{str(hash(plot))}.png")
```


To create the defects we are going to be removing molecules from the crystal strucutre, introducing a gap between layers which is effectively two line defects in the crystal structure.


For the simulation I am using a pressure of 1.00 with a temperature of 0.40 which is just above our current estimate of the melting point of 0.36. The crystal structure is the p2 structure which appears to be the most stable of the three crystals of this molecule. I am using cell dimensions of 30 x 42 which is the standard number of particles I have been using in the rest of my simulations.

```python
run_params = RunParams(
    temperature=0.20,
    pressure=13.50,
    crystal=TrimerP2(),
    num_steps=20_000,
    cell_dimensions=(30, 42, 1),
    hoomd_args="--notice-level=0",
    outfile="output.gsd",
)

# The number of columns when plotting figures
figure_columns = 2
```

```python
# Create a crystal structure
with run_params.temp_context(init_temp=0.1):
    init_snapshot = run_sim(init_from_crystal(run_params), run_params)
show(plot_snapshot(init_snapshot))
```

The starting crystal structure I am using. I have kept the tilt of the unit cell, since I am not currently interested in a quantitative measure of the structure.


## Vertical Defect

This is the creation of a defect which is approximately half the size of the crystal along the *b* axis of the unit cell. Part of the analysis is understanding how the size of the created defect affects the resulting structure. The cell below creates the sequence of `num_value` from the `min_value` to half the length of the simulation cell.

```python
# The number of linearly spaces values in the sequence
num_values = 4
# Minimum value of the sequence
min_value = 4
mols_removed = np.linspace(
    min_value, run_params.cell_dimensions[1] / 2, num=num_values
).astype(int)
mols_removed
```

In this case we are removing 4, 9, 15 and 21 molecules from the simulation cell to observe the effects.

```python
vert_snapshots = [remove_vertical(init_snapshot, run_params, m) for m in mols_removed]
show(plot_snapshots(vert_snapshots, figure_columns))
```

```python
fig = plot_snapshot(vert_snapshots[-1])
fig = figures.style_snapshot(fig)
fig.output_backend = "svg"
export_svgs(fig, filename="../figures/06_defect_vertical_setup.svg")
```

This is the state of the simulation with the molecules removed. At this point no dynamics have been run, so this is the same as the initial configuration apart from a number of molecules missing.


With the above configurations as starting states, I am running the simulations for 1_000 timesteps since the configuration appeared to be relatively stable after this many steps when [investigating the thermodynamics](07_Defect_thermodynamcs.ipynb). This is an NPT simulation where the pressure tensors for the x and y coordinates are updated separately, and additionally the simulation cell is allowed to tilt. The rest of the simulation conditions are the same as for running any other simulation.

```python
with run_params.temp_context(num_steps=1_000):
    vert_snapshots0 = [run_sim(snap, run_params) for snap in vert_snapshots]
show(plot_snapshots(vert_snapshots0, figure_columns))
```

```python
fig = plot_snapshot(vert_snapshots0[-1])
fig = figures.style_snapshot(fig)
fig.output_backend = "svg"
export_svgs(fig, filename="../figures/06_defect_vertical_thermal.svg")
```

The configurations after 100 000 steps, zoom in on each for more details. Each of the defect sites is now mostly filled with a structure resembling that of the pg crystal, having orientations which are slighly either side of the orientation of the crystal plane. While there is ordering along most of the defect site, at the corners there is some disordering which appears liquid-like in nature.


## Horizontal Defect

The creation of the horizontal defect is done in much the same way as the vertical defect. I am removing the same number of molecuels as for the vertical defect, which are 4, 9, 15, and 21.

```python
mols_removed
```

```python
horiz_snapshots = [
    remove_horizontal(init_snapshot, run_params, m) for m in mols_removed
]
show(plot_snapshots(horiz_snapshots, figure_columns))
```

```python
fig = plot_snapshot(horiz_snapshots[-1])
fig = figures.style_snapshot(fig)
fig.output_backend = "svg"
export_svgs(fig, filename="../figures/06_defect_horiz_setup.svg")
```

Running the horizontal shapshot with the same properties as the vertical split, a pressure of 1.0, a temperature of 0.40 which is just over the estimated melting point of ~0.36.

```python
with run_params.temp_context(num_steps=1_000):
    horiz_snapshots0 = [run_sim(snap, run_params) for snap in horiz_snapshots]
show(plot_snapshots(horiz_snapshots0, figure_columns))
```

```python
fig = plot_snapshot(horiz_snapshots0[-1])
fig = figures.style_snapshot(fig)
fig.output_backend = "svg"
export_svgs(fig, filename="../figures/06_defect_horiz_thermal.svg")
```

Once run for the 100 000 steps, the horizontal defect proves to be much more mobile than the vertical defect making a diagonal along the (1,1) lattice dimension. Another interesting feature with the bottom left image is that the defect has split in two, creating a lower and upper defect both of which are oriented on the same diagonal. Like the vertical defect, the horizontal defect also exhibits disordering at the edges of the defect, which completely takes up the smallest defect. The defect on the top right is starting to exhibit some of the spliting of the bottom left, although it is somewhat obscured by the melting.


I suspect the melting seen is mostly a result of the lower effective pressure in the areas where the melting occurs. Trying to fill the space left behind by the molecules that were removed.


## Shockley Defects

These are defects where both layers are remove
in the vertical direction.

```python
shockley_snapshots = [
    remove_vertical_cell(init_snapshot, run_params, m) for m in mols_removed
]
show(plot_snapshots(shockley_snapshots, figure_columns))
```

```python
fig = plot_snapshot(shockley_snapshots[-1])
fig = figures.style_snapshot(fig)
fig.output_backend = "svg"
export_svgs(fig, filename="../figures/06_defect_shockley_setup.svg")
```

```python
with run_params.temp_context(num_steps=1_000):
    shockley_snapshots0 = [run_sim(snap, run_params) for snap in shockley_snapshots]
show(plot_snapshots(shockley_snapshots0, figure_columns))
```

```python
fig = plot_snapshot(shockley_snapshots0[-1])
fig = figures.style_snapshot(fig)
fig.output_backend = "svg"
export_svgs(fig, filename="../figures/06_defect_shockley_thermal.svg")
```

## Higher Temperatures

```python
with run_params.temp_context(temperature=1.30, num_steps=500):
    vert_snapshots1 = [run_sim(snap, run_params) for snap in vert_snapshots]
    horiz_snapshots1 = [run_sim(snap, run_params) for snap in horiz_snapshots]
    shockley_snapshots1 = [run_sim(snap, run_params) for snap in shockley_snapshots]
```

```python
show(plot_snapshots(vert_snapshots1, figure_columns))
```

```python
fig = plot_snapshot(vert_snapshots1[-1])
fig = figures.style_snapshot(fig)
fig.output_backend = "svg"
export_svgs(fig, filename="../figures/06_defect_vert_thermal_1.30.svg")
```

```python
show(plot_snapshots(horiz_snapshots1, figure_columns))
```

```python
fig = plot_snapshot(horiz_snapshots1[-1])
fig = figures.style_snapshot(fig)
fig.output_backend = "svg"
export_svgs(fig, filename="../figures/06_defect_horiz_thermal_1.30.svg")
```

```python
show(plot_snapshots(shockley_snapshots1, figure_columns))
```

```python
fig = plot_snapshot(shockley_snapshots1[-1])
fig = figures.style_snapshot(fig)
fig.output_backend = "svg"
export_svgs(fig, filename="../figures/06_defect_shockley_thermal_1.30.svg")
```
