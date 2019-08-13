#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2019 Malcolm Ramsay <malramsay64@gmail.com>
#
# Distributed under terms of the MIT license.

"""Run simulations with crystal defects.

These are a collation of simulations which are aimed at understanding
defects within the crystal of the trimer molecule.

"""

import argparse
import sys

import hoomd

import defects


def main(infile, outfile, cell_dimensions, cell_molecules, direction, remove, layers):
    with hoomd.context.initialize(""):
        sys = hoomd.init.read_gsd(infile)
        snap = sys.take_snapshot()

        snap_out = create_defect(
            snap, cell_dimensions, cell_molecules, direction, remove, layers
        )

    with hoomd.context.initialize(""):
        hoomd.init.read_snapshot(snap_out)
        hoomd.dump.gsd(outfile, period=None, group=hoomd.group.all())


def create_defect(snap, cell_dimensions, cell_molecules, direction, remove, layers):

    if direction == "H":
        print("direction")
        return defects.remove_horizontal(snap, remove, cell_dimensions, cell_molecules)
    elif direction == "V":
        if layers == 1:
            return defects.remove_vertical(
                snap, remove, cell_dimensions, cell_molecules
            )
        elif layers == 2:
            return defects.remove_vertical_cell(
                snap, remove, cell_dimensions, cell_molecules
            )


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="File containing crystal structure.")
    parser.add_argument("outfile", help="File to output resulting structure to.")
    parser.add_argument(
        "--cell-dimensions",
        nargs=2,
        required=True,
        type=int,
        help="The number of unit cells of each dimension within the configuration.",
    )
    parser.add_argument(
        "--cell-molecules",
        required=True,
        type=int,
        help="The number of molecules within each unit cell.",
    )
    parser.add_argument(
        "--direction",
        required=True,
        choices=["H", "V"],
        help="The direction of the defect.",
    )
    parser.add_argument(
        "--remove", required=True, type=int, help="The number of molecules to remove"
    )
    parser.add_argument(
        "--layers", type=int, default=1, help="The number of layers to remove"
    )
    return parser


if __name__ == "__main__":
    my_parser = create_parser()
    args = my_parser.parse_args()
    sys.argv = [sys.argv[0]]
    main(**vars(args))
