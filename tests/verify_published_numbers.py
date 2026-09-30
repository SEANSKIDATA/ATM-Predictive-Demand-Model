"""
Re-runs the notebook's own code and checks every number published in the README.
Run from the repo root:  python tests/verify_published_numbers.py
Exits non-zero on any failure. Needs pandas, numpy, matplotlib.
"""
import contextlib, io, json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.show = lambda *a, **k: None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
nb = json.load(open("atm_predictive_demand_model.ipynb", encoding="utf-8"))
g = {}
for cell in nb["cells"]:
    src = "".join(cell["source"])
    if cell["cell_type"] != "code" or "plt.subplots(2, 3" in src or ".to_csv(" in src:
        continue                      # skip the dashboard render and the file exports
    with contextlib.redirect_stdout(io.StringIO()):
        exec(src, g)

np, pd, f, ev, err = g["np"], g["pd"], g["f"], g["ev"], g["err"]
dec = g["december"]
pct = err.abs() / dec.daily_cash_dispensed
reg = f.sort_values("priority_rank")
crit_status = f[f.risk_status == "CRITICAL"]
fs = g["flag_scores"]
pm, rm, f1m = fs(ev.actual_critical, ev.pred_critical)
pn, rn, f1n = fs(ev.actual_critical, ev.naive_critical)
mape72 = ((ev.fwd3_pred - ev.fwd3_actual).abs() / ev.fwd3_actual).mean() * 100
mape72n = ((ev.fwd3_naive - ev.fwd3_actual).abs() / ev.fwd3_actual).mean() * 100
sigma = g["DAILY_NOISE_SIGMA"]
z = np.random.default_rng(0).normal(0, sigma, 2_000_000)
noise_floor = np.mean(np.abs(np.exp(z) - 1)) * 100
committed = pd.read_csv("atm_forecast.csv")

checks = [
    ("18,300 transaction rows (50 ATMs x 366 days)",          len(g["atm_transactions"]) == 18300),
    ("Revenue at risk, below-threshold ATMs = $634,320",      crit_status.revenue_at_risk_72hr.sum() == 634320),
    ("25 ATMs projected below critical threshold",            len(crit_status) == 25),
    ("5 ATMs in CRITICAL risk tier / immediate dispatch",     (f.risk_tier == "CRITICAL").sum() == 5 and (f.dispatch_action == "IMMEDIATE DISPATCH").sum() == 5),
    ("6 Over The Road terminals below threshold",             (crit_status.terminal_type == "Over The Road").sum() == 6),
    ("Avg days until empty, CRITICAL + HIGH = 0.9",           round(f[f.risk_tier.isin(["CRITICAL", "HIGH"])].days_until_empty.mean(), 1) == 0.9),
    ("Top 5 register: ATM038, 008, 007, 010, 009",            list(reg.atm_id.head(5)) == ["ATM038", "ATM008", "ATM007", "ATM010", "ATM009"]),
    ("Committed atm_forecast.csv matches this run",           list(committed.atm_id) == list(reg.atm_id) and np.allclose(committed.composite_risk_score, reg.composite_risk_score)),
    ("1,550 December predictions",                            len(dec) == 1550),
    ("MAE = $880/day",                                        round(err.abs().mean()) == 880),
    ("RMSE = $1,439/day",                                     round(np.sqrt((err ** 2).mean())) == 1439),
    ("MAPE = 5.6%",                                           round(pct.mean() * 100, 1) == 5.6),
    ("Within 10% = 84.2%, within 20% = 99.7%",                round((pct <= .10).mean() * 100, 1) == 84.2 and round((pct <= .20).mean() * 100, 1) == 99.7),
    ("1,400 machine-days scored for critical flags",          len(ev) == 1400),
    ("Model: precision 0.985, recall 0.989, F1 0.987",        (round(pm, 3), round(rm, 3), round(f1m, 3)) == (0.985, 0.989, 0.987)),
    ("Naive: precision 0.949, recall 0.947, F1 0.948",        (round(pn, 3), round(rn, 3), round(f1n, 3)) == (0.949, 0.947, 0.948)),
    ("72-hour MAPE: model 3.4%, naive 13.8%",                 round(mape72, 1) == 3.4 and round(mape72n, 1) == 13.8),
    ("MAPE sits at the injected-noise floor (within 0.2 pt)", abs(pct.mean() * 100 - noise_floor) < 0.2),
]
fail = 0
for name, ok in checks:
    print(("PASS  " if ok else "FAIL  ") + name); fail += (not ok)
print(f"\nInjected noise sigma {sigma:.0%} -> expected absolute error {noise_floor:.2f}%; measured MAPE {pct.mean()*100:.2f}%")
print(f"{len(checks) - fail}/{len(checks)} checks passed")
sys.exit(1 if fail else 0)
