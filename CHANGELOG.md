# Changelog

## 2026-09-30 — Reproducibility audit

Every number in the README was re-run from the notebook. All of them reproduce, and the
committed CSVs match a fresh run exactly. `tests/verify_published_numbers.py` now checks
them (18 checks).

**Validation reframed.** The data is synthetic and is generated from the same structure the
forecast uses (location base x day-of-week x season x 7% noise); the December prediction also
applies the generator's own holiday factor. The 5.6% MAPE equals the expected size of the
injected noise (about 5.6%), so the holdout is a correctness check, not evidence of real-world
accuracy. The README and notebook now say so, and lead with the result that does carry over:
the comparison with a naive trailing-7-day rule on the same task (72-hour error 3.4% vs 13.8%;
recall 0.989 vs 0.947). No model code changed.

**Labels clarified.** "Critical" was used for two different things: 25 ATMs projected below
their critical cash threshold, and 5 ATMs in the CRITICAL risk tier (score 140+). Both are now
labeled. "Avg days to failure" now states it covers CRITICAL + HIGH tier machines, and the
revenue-at-risk figure states it covers the 25 below-threshold machines.

**README.** Rebuilt as markdown (headings, tables, links) — the previous version was plain text
and rendered as one block on GitHub. Seasonal multipliers are described as stated assumptions
from operations experience rather than "not assumed." Universal claims about what "standard
reporting" cannot see are narrowed to balance-only reporting, and the lead example now matches
the model (casinos are the highest-volume machines; Tunica has 0.9 days of cash).

**SQL.** `atm_sql_foundation.sql` filtered on `CURDATE()`, which returns no rows against the
2024 dataset; it now uses the dataset's own dates, matching the individual query files. The
tax-proximity premium in Query 3 now keys off the forecast date instead of today's month. The
foundation file's depletion score is now capped at 60, matching the Python model and Query 3.

**Removed.** `index (1).html` (an old WFM Decision Lab build committed here by mistake),
duplicate notebooks `ATM_Predictive_Demand_Model (3).ipynb` and `(4).ipynb`, the outdated
`README (8).md`, and the unused `scikit-learn` dependency. All remain in git history.

**Not supported by this repository.** Figures from earlier versions — recall 97.3%,
F1 0.973, "39 flagged critical", "$839,520 revenue at risk" — came from a prior version of the
model and are not produced by the current code.
