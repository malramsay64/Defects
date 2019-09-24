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

# Defect Characterisation

This Notebook is about characterising the initial formation of defects. The end goal is to have some idea of what the point defects at the end of each of the created defects intially looks like as a stepping stone to having some idea of how the defect propogates moves and generally just behaves. The creation of the defects is the same process as in [06_Defect_Creation](06_Defect_Creation.ipynb) so check that notebook for more detail on the specifics.

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
from sdrun.initialise import minimize_snapshot

import numpy as np
import hoomd

import sys

sys.path.append("../src")

from defects import (
    remove_molecule,
    remove_vertical,
    remove_horizontal,
    plot_snapshots,
    plot_snapshot,
    central_molecule,
)

from bokeh.plotting import show, output_notebook
from bokeh.io import export_png

from IPython.display import Image

output_notebook()
# def show(plot):
#     export_png(plot, filename=f"{str(hash(plot))}.png")
#     return Image(f"{str(hash(plot))}.png")
```

For the simulation I am using a pressure of 1.00 with a temperature of 0.10 which is really low to have a simulation that prevents melting, only showing the creation of the defects. The crystal structure is the p2 structure which appears to be the most stable of the three crystals of this molecule. I am using cell dimensions of 30 x 42 which is the standard number of particles I have been using in the rest of my simulations.

```python
run_params = RunParams(
    temperature=0.10,
    pressure=1.00,
    crystal=TrimerP2(),
    num_steps=20_000,
    cell_dimensions=(30, 42, 1),
    hoomd_args="--notice-level=0",
    outfile="./dump.gsd",
)
```

```python
# Create a crystal structure
with run_params.temp_context(init_temp=0.1):
    init_snapshot = equilibrate(
        init_from_crystal(run_params), run_params, equil_type="crystal"
    )
```

## Vertical Defect

This is the creation of a defect which is half the size of the crystal along the *b* axis of the unit cell.

```python
mols_removed = int(run_params.cell_dimensions[1] / 2)
vert_snapshot = remove_vertical(init_snapshot, run_params, mols_removed)
```

```python
with run_params.temp_context(num_steps=10_000):
    vert_snapshot0 = equilibrate(vert_snapshot, run_params, "crystal")
```

```python
show(plot_snapshot(vert_snapshot0))
```

The configurations after 10 000 steps, zoom in on each for more details. The colour indicates the orientation of the molecule, with the light colours indicating crystal structure and the darker colours a defect. Each of the removed sites is now mostly filled with a structure which has very little orientational compensation for the missing layer.


## Horizontal Defect

The creation of the horizontal defect is done in much the same way as the vertical defect.

```python
mols_removed = int(run_params.cell_dimensions[0])
horiz_snapshot = remove_horizontal(init_snapshot, run_params, mols_removed)
```

```python
with run_params.temp_context(num_steps=10_000):
    horiz_snapshot0 = equilibrate(horiz_snapshot, run_params, "crystal")
show(plot_snapshot(horiz_snapshot0))
```

The simulation after runnign for 10 000 steps at a temperature of 0.1. The colour indicates orientation while light particles are considered crystalline and dark colours liquid/defects. This horizontal defect proves to be much more mobile than the vertical defect with the right hand defect propogating along the (-1,-1) lattice dimension. It is interesting that not all of the particles along the diagonal are categorised by the algorithm, which is currently not displaying labels for the classification so they could be one of the other crystal structures. In previous simulations at higher temperatuers (see [06_Defect_Creation](06_Defect_Creation.ipynb)) there is propogation from both ends of the removed particles, so it is possible the left hand defect shows the start of the propogation.


## Minimisation

Rather than running a simulation to create the defect, an alternate method is the minimisatiion of the configuraion using a conjugate gradient or similar method. The method used by hoomd is [FIRE](http://hoomd-blue.readthedocs.io/en/stable/module-md-integrate.html#hoomd.md.integrate.mode_minimize_fire), which is how I am minimising the defects.


```python
with run_params.temp_context(pressure=3.0):
    min_vert_snapshot = minimize_snapshot(vert_snapshot, run_params, ensemble="NPH")
```

```python
show(plot_snapshot(min_vert_snapshot))
```

The defect created by the minimisation of the vertical defect is very similar to that obtained through a low temperature thermal method above.

```python
with run_params.temp_context(pressure=3.5):
    min_horiz_snapshot = minimize_snapshot(horiz_snapshot, run_params, ensemble="NPH")
```

```python
show(plot_snapshot(min_horiz_snapshot))
```

At a pressure of 1.0, the horizontal snapshot appears to show no changes from the minimisation, despite there being some particle motions. It does make some sense that there is little motion due to the attractive potential on the particles. When increasing the pressure to 3.0, which is the lowest pressure to observe a change in the crystal structure, we see the start of the defects in the thermal system above, however interestingly there is propogation of the defects along the diagonals. It is also interesting to note that the defect structues here have two fold rotational symmetry within the crystal structure, implying that the direction of the defect propogation is a property of the created defect.
