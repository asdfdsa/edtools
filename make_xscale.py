from pathlib import Path, PurePosixPath
from sys import argv
import os, time
from math import radians, cos
import numpy as np
import yaml
from collections import Counter


threshold = 2.0


def parse_xds_ascii(fn):
    d = {"xds_ascii": fn.absolute()}
    with open(fn, "r") as f:
        for line in f:
            if not line.startswith("!"):
                break
            if "UNIT_CELL_CONSTANTS" in line:
                inp = line.split()
                cell = [float(val) for val in inp[-6:]]
            if "SPACE_GROUP_NUMBER" in line:
                inp = line.strip().split("=")
                spgr = int(inp[-1])

        d["space_group"] = spgr
        d["unit_cell"] = cell
    
    return d


def get_xds_ascii_names(lst):
    ret = []
    for d in lst:
        try:
            ret.append(d["xds_ascii"])
        except KeyError:
            ret.append(d["directory"] / "XDS_ASCII.HKL")
    return ret


def write_xscale_inp(fns, unit_cell, space_group):
    cwd = Path(".").resolve()

    cell_str = " ".join((f"{val:.3f}" for val in unit_cell))
    with open("XSCALE.INP", "w") as f:

        print("MINIMUM_I/SIGMA= 2", file=f)
        print("SAVE_CORRECTION_IMAGES= FALSE", file=f)  # prevent local directory being littered with .cbf files
        print(f"SPACE_GROUP_NUMBER= {space_group}", file=f)
        print(f"SPACE_GROUP_NUMBER= {space_group}")
        print(f"UNIT_CELL_CONSTANTS= {cell_str}", file=f)
        print(f"UNIT_CELL_CONSTANTS= {cell_str}")
        print(file=f)
        print("OUTPUT_FILE= MERGED.HKL", file=f)
        print(file=f)
        
        for i, fn in enumerate(fns):
            fn = fn.absolute()
            print(fn.absolute())
            fn = fn.relative_to(cwd)
            print(f"    INPUT_FILE= {fn.as_posix()}", file=f)
            print(f"    INCLUDE_RESOLUTION_RANGE= 20 0.8", file=f)
            print(file=f)

    print(f"Wrote file {f.name}")


def write_xdsconv_inp():
    with open("XDSCONV.INP", "w") as f:
        print("""
INPUT_FILE= MERGED.HKL
INCLUDE_RESOLUTION_RANGE= 20 0.8 ! optional 
OUTPUT_FILE= shelx.hkl  SHELX    ! Warning: do _not_ name this file "temp.mtz" !
FRIEDEL'S_LAW= FALSE             ! default is FRIEDEL'S_LAW=TRUE""", file=f)

    print(f"Wrote file {f.name}")


def main():
    import argparse

    description = "Program to make an input file for XSCALE."
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument("args",
                        type=str, nargs="*", metavar="FILE",
                        help="Path to a cells.yaml / XDS_ASCII.HKL files")

    parser.add_argument("-s","--spgr",
                        action="store", type=int, dest="spgr",
                        help="Space group number (default: most common one)")

    parser.add_argument("-c","--cell",
                        action="store", type=float, nargs=6, dest="cell",
                        help="Override the unit cell parameters (default: mean unit cell)")

    parser.set_defaults(cell=None,
                        spgr=None)
    
    options = parser.parse_args()
    spgr = options.spgr
    cell = options.cell
    args = options.args
    
    if not args:  # attempt to populate args
        if os.path.exists("cells.yaml"):
            args = ["cells.yaml"]
        else:
            args = list(Path(".").glob("*XDS_ASCII.HKL"))
        
    if not args:
        exit()
    else:
        lst = []
        for arg in args:
            fn = Path(arg)
            extension = fn.suffix.lower()
            if extension == ".yaml":
                d = yaml.load(open(fn, "r"))
                lst.extend(d)
            if extension == ".hkl":
                lst.append(parse_xds_ascii(fn))

    print(f"Loaded {len(lst)} cells")

    fns = get_xds_ascii_names(lst)

    cells = np.array([d["unit_cell"] for d in lst])

    if not cell:
        cell = np.mean(cells, axis=0)

    if not spgr:
        c = Counter([d["space_group"] for d in lst])
        for key, count in c.most_common(5):
            print(f"Space group {key} was found {count} times")
        spgr =  c.most_common()[0][0]

    write_xscale_inp(fns, unit_cell=cell, space_group=spgr)
    write_xdsconv_inp()


if __name__ == '__main__':
    main()
