#!/usr/bin/env python3
"""blink_tables.py — splice generated evidence tables into results/
blink_vetting.md (replaces <!--TABLE_*--> markers and the
{{N_PROM_2MASS}} placeholder from results/blink_vetting.csv).
Run AFTER scripts/blink_vet.py finalize.
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
MD = os.path.join(RES, "blink_vetting.md")

with open(os.path.join(RES, "blink_vetting.csv")) as f:
    rows = sorted(csv.DictReader(f), key=lambda r: -float(r["pm_tot"]))

n_prom_2mass = sum(1 for r in rows if r["twomass_verdict"] == "2mass-corroborated")

t2mass = ["| source_id | 2MASS designation | epoch | sep2000 as | J | J-H | implied pm | Gaia pm | dp +/- sig (z) |",
          "|---|---|---|---|---|---|---|---|---|"]
tcw = ["| source_id | sep as | W1-W2 | CW pm mas/yr | dp +/- sig (z) | verdict |",
       "|---|---|---|---|---|---|"]
tver = ["| source_id | pm mas/yr | G | dist pc | 2MASS verdict | CatWISE verdict | verdict | flags |",
        "|---|---|---|---|---|---|---|---|"]
tbase = ["| source_id | 2MASS epoch | implied pm mas/yr | Gaia pm mas/yr | dp ± sig mas/yr (z) |",
         "|---|---|---|---|---|"]

for r in rows:
    sid = r["source_id"]
    if r["twomass_verdict"] == "2mass-corroborated":
        t2mass.append("| {sid} | {des} | {ep} | {sep} | {j} | {jh} | {impl} | {gaia} | {dp} ± {sig} ({z}) |".format(
            sid=sid, des=r["twomass_des"], ep=r["twomass_epoch"],
            sep=r["twomass_sep2000_as"], j=r["twomass_jm"], jh=r["twomass_jh"],
            impl=r["twomass_impl_pm"], gaia=r["pm_tot"], dp=r["twomass_dp_mas"],
            sig=r["twomass_sig"], z=round(float(r["twomass_dp_mas"]) / float(r["twomass_sig"]), 2)))
    tver.append("| {sid} | {pm} | {g} | {d} | {tv} | {cv} | {v} | {fl} |".format(
        sid=sid, pm=r["pm_tot"], g=r["G"], d=r["dist_pc"],
        tv=r["twomass_verdict"], cv=r["catwise_verdict"], v=r["verdict"],
        fl=r["flags"] or "-"))
    if r["catwise_verdict"] == "catwise-pm-consistent":
        z = round(float(r["catwise_dp_mas"]) / float(r["catwise_sig"]), 2) if r["catwise_dp_mas"] else ""
        tcw.append("| {sid} | {sep} | {w} | {pm} | {dp} ± {sig} ({z}) | ok |".format(
            sid=sid, sep=r["catwise_sep_as"], w=r["catwise_w1w2"],
            pm=r["catwise_pm_mas"], dp=r["catwise_dp_mas"], sig=r["catwise_sig"], z=z))
    if r["verdict"] == "PROMOTED":
        tbase.append("| {sid} | {ep} ({des}) | {impl} | {gaia} | {dp} ± {sig} ({z}) |".format(
            sid=sid, ep=r["twomass_epoch"], des=r["twomass_des"],
            impl=r["twomass_impl_pm"], gaia=r["pm_tot"], dp=r["twomass_dp_mas"],
            sig=r["twomass_sig"],
            z=round(float(r["twomass_dp_mas"]) / float(r["twomass_sig"]), 2)))

md = open(MD).read()
md = md.replace("<!--TABLE_2MASS-->", "\n".join(t2mass))
md = md.replace("<!--TABLE_CATWISE-->", "\n".join(tcw))
md = md.replace("<!--TABLE_VERDICT-->", "\n".join(tver))
md = md.replace("<!--TABLE_BASELINE-->", "\n".join(tbase))
md = md.replace("{{N_PROM_2MASS}}", str(n_prom_2mass))
open(MD, "w").write(md)
print(f"tables spliced: {n_prom_2mass} 2MASS-corroborated rows, "
      f"{len(tver)-2} verdict rows, {len(tbase)-2} baseline rows")
