# SAFE SCRIPT
# -----------
# Refreshes element_images URLs from Rebrickable API.
# Does NOT rebuild catalog.
# Does NOT delete tables.
# Requires REBRICKABLE_API_KEY.


#!/bin/bash
: "${HISTTIMEFORMAT:=}"
set -euo pipefail
[ -f ./a2p_bash_compat.sh ] && source ./a2p_bash_compat.sh
[ -f /tmp/a2p_env.sh ] && source /tmp/a2p_env.sh

cd ~/aim2build-app

: "${REBRICKABLE_API_KEY:?Please export REBRICKABLE_API_KEY before running this script.}"

python3 backend/scripts/a2b_refresh_inventory_images_from_rebrickable.py
