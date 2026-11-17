"""Write the central run to results/: results.csv, the in-between tables, run.json, tornado.csv and
figures.json (the one results file the paper reads by key, with every bracket's ends, the range and the checks).
About five minutes: every bracket end is a full run. Frozen on the cut-off date in stage 7.

`--reuse-tornado` reads the brackets from results/tornado.csv instead of rerunning them (one run, about a
minute): for a version that adds keys and changes no input, as 1.0.1 did (aios-harness#221)."""
import sys

import pandas as pd

from billtocome import brackets, figures
from billtocome.model import run

if __name__ == "__main__":
    r = run()
    r.save(figures.FILE.parent)
    tornado = figures.FILE.parent / "tornado.csv"
    if "--reuse-tornado" in sys.argv[1:]:
        t = pd.read_csv(tornado)
    else:
        t = brackets.tornado()
        t.to_csv(tornado, index=False)
    price_case = next(b for b in brackets.BRACKETS if b.name == "Price after 2050").high  # ruling 11b, 1.3.0
    figures.write(r, figures.FILE, tornado=t, checks=True, price_case=run(price_case))
    print(figures.FILE)
