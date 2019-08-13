#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2018 Malcolm Ramsay <malramsay64@gmail.com>
#
# Distributed under terms of the MIT license.

"""Helper functions for the creation and analysis of defects."""

import logging
from typing import List, Tuple

import gsd.hoomd
import hoomd
import joblib
import numpy as np
from bokeh.layouts import gridplot
from bokeh.plotting import Figure
from hoomd.data import SnapshotParticleData, make_snapshot
from sdanalysis import HoomdFrame
from sdanalysis.figures import configuration
from sdanalysis.order import compute_ml_order
from sdrun import SimulationParams, initialise, simulation

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def remove_molecule(snapshot: SnapshotParticleData, index: int) -> SnapshotParticleData:
    """Remove an arbitrary molecule from a Hoomd snapshot.

    Args
    ----
        snapshot: Snapshot from which a particle will be removed.
        index: The index of the molecule to remove. This index is the zero indexed body of the
            particle. All particles with the same body index will also be removed from the snapshot.

    Returns
    -------
        A new snapshot with one less molecule.

    The removal of a molecule is done by creating a new snapshot with N fewer particles, where N is
    the number of particles in a molecule. This approach is simpler than modifying the existing
    snapshot, and ensures a valid configuration once the molecule has been removed.

    ... note:
        The index of molecules changes when this function is applied. All molecule ids need to be
        contiguous, so on the removal of a molecule the largest molecule id is removed, so all molecule
        IDs between ``index`` and the number of bodies will have shifted by 1.

    """
    mask = snapshot.particles.body != index
    num_particles = int(np.sum(mask))
    if num_particles == snapshot.particles.N:
        raise IndexError(f"Index {index} does not match a molecule in the snapshot")

    # Hoomd snapshot
    new_snapshot = make_snapshot(
        num_particles, snapshot.box, snapshot.particles.types, snapshot.pairs.types
    )

    # All the attributes from the old snapshot which need to be applied to the new one.
    snapshot_attributes = [
        "position",
        "angmom",
        "velocity",
        "body",
        "orientation",
        "acceleration",
        "image",
        "mass",
        "moment_inertia",
        "typeid",
    ]

    for attr in snapshot_attributes:
        try:
            getattr(new_snapshot.particles, attr)[:] = getattr(
                snapshot.particles, attr
            )[mask]
        except AttributeError:
            pass
    # Remove the tag of the largest
    body_mask = snapshot.particles.body != max(snapshot.particles.body)
    new_snapshot.particles.body[:] = snapshot.particles.body[body_mask]
    return new_snapshot


def central_molecule(cell_dimensions: Tuple[int, int], cell_molecules: int) -> int:
    """Find the molecule closest to the center of the simulation.

    Args
    ----
        cell_dimensions: This is the number of unit cells in each direction of the crystal
        cell_molecules: The number of molecules within each unit cell

    Returns
    -------
        Index of the most central molecule in the simulation.

    This uses the crystal lattice dimensions to find the unit cell halfway along each of the axes,
    then multiplies by the number of molecules in each unit cell.

    """
    x, y = cell_dimensions
    return int((x / 2 * y + y / 2) * cell_molecules)


def remove_vertical(
    snapshot: SnapshotParticleData,
    num_mols: int,
    cell_dimensions: Tuple[int, int],
    cell_molecules: int,
) -> SnapshotParticleData:
    """Remove a number of molecules along a vertical line.

    Args
    ----
        snapshot: The snapshot from which to remove the particles.
        num_mols: The number of molecules to be removed from the simulation. The number of
            molecules actually removed will be rounded to an even number.
        cell_dimensions: The number of unit cells in each direction.
        cell_molecules: The number of molecules within each unit cell.

    Returns
    -------
        A Hoomd snapshot with a number of particles removed from
            the configuration centered around the centre most molecule.

    More important than removing molecules from the exact center or the exact number of molecules
    is the consistency of the removal. This means that the same layer of the crystal lattice
    should be removed regardless of the number of molecules.

    """
    if num_mols < 0:
        raise ValueError("Can't remove a negative number of molecules.")
    if num_mols == 0:
        return snapshot
    center = central_molecule(cell_dimensions, cell_molecules)
    for index in range(center - 2 * num_mols // 2, center):
        snapshot = remove_molecule(snapshot, index)
    return snapshot


def remove_horizontal(
    snapshot: SnapshotParticleData,
    num_mols: int,
    cell_dimensions: Tuple[int, int],
    cell_molecules: int,
) -> SnapshotParticleData:
    """Remove a number of molecules along a horizontal line.

    Args
    ----
        snapshot: The snapshot from which to remove the particles.
        num_mols: The number of molecules to be removed from the simulation. The number of
            molecules actually removed will be rounded to an even number.
        cell_dimensions: The number of unit cells in each direction.
        cell_molecules: The number of molecules within each unit cell.

    Returns
    -------
        A hoomd snapshot with a number of particles removed from
            the configuration centered around the centre most molecule.

    More important than removing molecules from the exact center or the exact number of molecules is
    the consistency of the removal. This means that the same layer of the crystal lattice should be
    removed regardless of the number of molecules and also that the molecules are in the middle of
    the simulation cell. For these reasons the minimum number of molecuels removed is 4, with other
    numbers of molecules removed being multiples of 4.

    """
    if num_mols < 0:
        raise ValueError("Can't remove a negative number of molecules.")
    if num_mols == 0:
        return snapshot
    center = central_molecule(cell_dimensions, cell_molecules)
    _, y = cell_dimensions
    # The minimum number of molecules removed is 4
    extent = max(num_mols // 4 * 2, 2)
    counter = 0

    for count, column in enumerate(range(-extent, extent, 2)):
        # Adjust center by column, then number of molecules removed
        index = center + column * y - count * 2

        snapshot = remove_molecule(snapshot, index)
        snapshot = remove_molecule(snapshot, index + 2)
        counter += 2
    logger.debug("Molecules Removed: %s", counter)
    return snapshot


def remove_vertical_cell(
    snapshot: SnapshotParticleData,
    num_cells: int,
    cell_dimensions: Tuple[int, int],
    cell_molecules: int,
) -> SnapshotParticleData:
    """Remove unit cells in the vertical direction.

    Args
    ----
        snapshot (SnapshotParticleData): The snapshot from which to remove the particles.
        num_mols (int): The number of molecules to be removed from the simulation. The number of
            molecules actually removed will be rounded to an even number.
        cell_dimensions: This is the number of unit cells in each direction of the crystal
        cell_molecules: The number of molecules within each unit cell

    Returns
    -------
        A Hoomd snapshot with a number of particles removed from
            the configuration centered around the centre most molecule.

    Rather than just removing a single layer of molecules like :py:`remove_vertical`, this removes
    both particles from the unit cell, meaning that the remaining layers can come together to form a
    suitable crystal structure.

    """
    if num_cells < 0:
        raise ValueError("Can't remove a negative number of cells.")
    if num_cells == 0:
        return snapshot
    center = central_molecule(cell_dimensions, cell_molecules)
    # This ensures the appropriate molecules are removed
    index = center - num_cells // 2 * 2
    counter = 0
    for i in range(num_cells):
        if i == 0:
            snapshot = remove_molecule(snapshot, index - 2)
        else:
            snapshot = remove_molecule(snapshot, index - 1)
        snapshot = remove_molecule(snapshot, index)
        counter += 2
    logger.debug("Molecules Removed: %s", counter)
    return snapshot


def knn_model():
    return joblib.load("../models/knn-trimer.pkl")


def plot_snapshot(snapshot: SnapshotParticleData, order: bool = False):
    """Helper function to plot a single snapshot."""
    frame = HoomdFrame(snapshot)
    if order:
        from functools import partial

        def order_function(*args, **kwargs):
            result = compute_ml_order(knn_model(), *args, **kwargs)
            return result == "liq"

        return configuration.plot_frame(frame, order_function)
    return configuration.plot_frame(frame)


def plot_snapshots(
    snapshots, num_columns: int = 2, num_rows: int = None, order: bool = False
):
    # Length of sides to make a square
    if num_rows is None:
        num_rows = len(snapshots) // num_columns
    figures = []
    for i in range(num_columns):
        row: List[Figure] = []
        for j in range(num_rows):
            if i * num_rows + j > len(snapshots):
                figures.append(row)
                return gridplot(figures)
            fig = plot_snapshot(snapshots[i * num_rows + j], order=order)
            fig.plot_height = fig.plot_height // num_rows
            fig.plot_width = fig.plot_width // num_rows
            row.append(fig)
        figures.append(row)
    return gridplot(figures)


def run_sim(snapshot: SnapshotParticleData, sim_params: SimulationParams):
    snap = initialise.thermalise(snapshot, sim_params)
    return simulation.equilibrate(snap, sim_params, equil_type="crystal")
