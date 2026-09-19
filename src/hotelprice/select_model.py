"""List the registered model versions and set the "champion" alias on one of them.

Usage: python -m hotelprice.select_model [VERSION]   (no VERSION = the latest version)
"""

import sys

import mlflow

from hotelprice.config import get_mlflow_tracking_uri, get_registered_model_name

ALIAS = "champion"

# 1. Connect to the MLflow store and read all versions of the registered model.
mlflow.set_tracking_uri(get_mlflow_tracking_uri())
client = mlflow.MlflowClient()
name = get_registered_model_name()
versions = sorted(client.search_model_versions(f"name='{name}'"), key=lambda v: int(v.version))
if not versions:
    sys.exit(f"No versions of '{name}' found. Run `python -m hotelprice.train` first.")

# 2. Print each version with its run ID, metrics and current aliases.
#    (search_model_versions does not fill in aliases, so read them from the registered model.)
alias_versions = client.get_registered_model(name).aliases
print(f"Registered model: {name}")
for v in versions:
    metrics = client.get_run(v.run_id).data.metrics
    aliases = ",".join(a for a, ver in alias_versions.items() if str(ver) == str(v.version)) or "-"
    print(
        f"  v{v.version}  run_id={v.run_id}  mae={metrics['mae']:.2f}  "
        f"rmse={metrics['rmse']:.2f}  r2={metrics['r2']:.4f}  aliases={aliases}"
    )

# 3. Pick the version from the command line (default: the latest) and set the alias on it.
#    An alias points to one version at a time, so this moves it if it was on another version.
version = sys.argv[1] if len(sys.argv) > 1 else versions[-1].version
client.set_registered_model_alias(name, ALIAS, version)
print(f"Alias '{ALIAS}' now points to version {version} (load with models:/{name}@{ALIAS})")
