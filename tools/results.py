"""Write the central run to results/: results.csv, the in-between tables, run.json, tornado.csv and
figures.json (the one results file the paper reads by key, with every bracket's ends and the range).
About five minutes: every bracket end is a full run. Frozen on the cut-off date in stage 7."""
from billtocome import brackets, figures
from billtocome.model import run

if __name__ == "__main__":
    r = run()
    r.save(figures.FILE.parent)
    t = brackets.tornado()
    t.to_csv(figures.FILE.parent / "tornado.csv", index=False)
    figures.write(r, figures.FILE, tornado=t)
    print(figures.FILE)
