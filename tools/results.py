"""Write the central run to results/: results.csv, the in-between tables, run.json and figures.json (the
one results file the paper reads by key). Frozen on the cut-off date in stage 7."""
from billtocome.figures import FILE
from billtocome.model import run

if __name__ == "__main__":
    run().save(FILE.parent)
    print(FILE)
