import json
import os
import sys

STATS_PATH = "mutants/mutmut-cicd-stats.json"

if not os.path.exists(STATS_PATH):
    print(f"No {STATS_PATH} found (mutmut run may have failed before producing stats).")
    sys.exit(0)

with open(STATS_PATH) as f:
    stats = json.load(f)

killed = stats["killed"]
survived = stats["survived"]
scored = killed + survived
score = (killed / scored * 100) if scored else 0.0

summary = (
    "### Mutation testing (report only)\n\n"
    f"- Mutation score: **{score:.1f}%** ({killed}/{scored} killed)\n"
    f"- Survived: {survived}\n"
    f"- No tests covering: {stats['no_tests']}\n"
    f"- Timeout: {stats['timeout']}\n\n"
    "Run `tox -e mutmut` locally, then `mutmut results` / `mutmut browse` to "
    "inspect survivors.\n"
)
print(summary)

summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
if summary_path:
    with open(summary_path, "a") as f:
        f.write(summary)
