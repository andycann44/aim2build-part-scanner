#!/bin/bash
: "${HISTTIMEFORMAT:=}"
set -euo pipefail
[ -f ./a2p_bash_compat.sh ] && source ./a2p_bash_compat.sh
[ -f /tmp/a2p_env.sh ] && source /tmp/a2p_env.sh

cd ~/aim2build-app

CAT_DB="backend/app/data/lego_catalog.db"
REB_DIR="backend/app/data/rebrickable"

echo "==> Catalog rebuild contract"
echo "  CSV source: $REB_DIR"
echo "  Output DB : $CAT_DB"
echo
echo "This script is a CONTRACT wrapper."
echo "It does NOT guess schema."
echo "Next: we wire it to your existing importer/rebuild module (or create one)."
echo

# Smoke: verify required CSVs exist
need=(sets parts colors inventories inventory_parts inventory_sets elements)
for f in "${need[@]}"; do
  [ -s "$REB_DIR/$f.csv" ] || { echo "Missing $REB_DIR/$f.csv"; exit 2; }
done

echo "==> CSVs present."

# Smoke: show current DB tables (if exists)
if [ -f "$CAT_DB" ]; then
  echo "==> Existing DB tables:"
  sqlite3 "$CAT_DB" ".tables" || true
else
  echo "==> No DB found yet at $CAT_DB (expected if not built)."
fi

echo
echo "NEXT STEP:"
echo "1) Point this contract at your existing rebuild/import script (if you already have one)."
echo "2) Or we generate a new importer that builds:"
echo "   - base tables: sets, parts, colors, inventories, inventory_parts, inventory_sets, elements"
echo "   - derived: set_parts, element_images, top_common_parts*, indexes"
echo
echo "Tell me which importer file currently builds lego_catalog.db in your repo and I’ll wire it in."
