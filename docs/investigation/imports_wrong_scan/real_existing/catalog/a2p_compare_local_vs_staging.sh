#!/bin/bash
: "${HISTTIMEFORMAT:=}"
set -euo pipefail
[ -f ./a2p_bash_compat.sh ] && source ./a2p_bash_compat.sh
[ -f /tmp/a2p_env.sh ] && source /tmp/a2p_env.sh

CMD="${1:-}"

die() { echo "ERROR: $*" >&2; exit 1; }

need() { command -v "$1" >/dev/null 2>&1 || die "Missing dependency: $1"; }

hash_file() {
  local f="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$f" | awk '{print $1}'
  else
    shasum -a 256 "$f" | awk '{print $1}'
  fi
}

ts() { date +"%Y%m%d_%H%M%S"; }

repo_root() { git rev-parse --show-toplevel 2>/dev/null || pwd; }

CATALOG_DB_REL="backend/app/data/lego_catalog.db"
APP_DB_REL="backend/app/data/aim2build_app.db"

SQL_SETS_COUNT='SELECT COUNT(*) AS sets_count FROM sets;'
SQL_YEAR_RANGE='SELECT MIN(year) AS min_year, MAX(year) AS max_year FROM sets;'
SQL_2026_SAMPLE='SELECT set_num, year FROM sets WHERE year=2026 ORDER BY set_num LIMIT 20;'

fingerprint_one_db() {
  local label="$1"
  local db_path="$2"
  local out_txt="$3"
  local out_schema="$4"

  if [ ! -f "$db_path" ]; then
    echo "== $label ==" >> "$out_txt"
    echo "MISSING: $db_path" >> "$out_txt"
    echo >> "$out_txt"
    return 0
  fi

  echo "== $label ==" >> "$out_txt"
  echo "path: $db_path" >> "$out_txt"
  echo "size: $(ls -lh "$db_path" | awk '{print $5}')" >> "$out_txt"
  echo "sha256: $(hash_file "$db_path")" >> "$out_txt"
  echo >> "$out_txt"

  echo "-- schema ($label) --" > "$out_schema"
  sqlite3 "$db_path" ".schema" >> "$out_schema" 2>/dev/null || true

  echo "-- indices ($label) --" >> "$out_txt"
  sqlite3 "$db_path" "SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' ORDER BY tbl_name, name;" >> "$out_txt" 2>/dev/null || true
  echo >> "$out_txt"
}

fingerprint_catalog_extras() {
  local db_path="$1"
  local out_txt="$2"
  if [ ! -f "$db_path" ]; then return 0; fi

  echo "== catalog quick stats ==" >> "$out_txt"
  sqlite3 "$db_path" "$SQL_SETS_COUNT" >> "$out_txt" 2>/dev/null || true
  sqlite3 "$db_path" "$SQL_YEAR_RANGE" >> "$out_txt" 2>/dev/null || true
  sqlite3 "$db_path" "$SQL_2026_SAMPLE" >> "$out_txt" 2>/dev/null || true
  echo >> "$out_txt"

  echo "== tables (catalog) ==" >> "$out_txt"
  sqlite3 "$db_path" "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;" >> "$out_txt" 2>/dev/null || true
  echo >> "$out_txt"
}

snapshot_local() {
  need git
  need sqlite3
  need python3

  local root outdir
  root="$(repo_root)"
  outdir="$root/_compare_out/$(ts)"
  mkdir -p "$outdir/db"

  echo "Snapshot dir: $outdir"
  echo "Repo root: $root"

  (cd "$root" && find backend/app/data -maxdepth 2 -name "*.db" -print 2>/dev/null || true) | while read -r rel; do
    [ -f "$root/$rel" ] || continue
    local base
    base="$(echo "$rel" | sed 's#/#__#g')"
    cp -a "$root/$rel" "$outdir/db/$base"
  done

  echo "OK: copied DB candidates into $outdir/db"
  echo "$outdir"
}

fingerprint_local() {
  need git
  need sqlite3
  need python3

  local root outdir
  root="$(repo_root)"
  outdir="$root/_compare_out/$(ts)"
  mkdir -p "$outdir"

  local out_txt="$outdir/local_fingerprint.txt"
  local out_schema_catalog="$outdir/local_schema_catalog.sql"
  local out_schema_app="$outdir/local_schema_app.sql"

  : > "$out_txt"
  echo "== local fingerprint ==" >> "$out_txt"
  echo "when: $(date -Is)" >> "$out_txt"
  echo "git branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)" >> "$out_txt"
  echo >> "$out_txt"

  fingerprint_one_db "catalog_db" "$root/$CATALOG_DB_REL" "$out_txt" "$out_schema_catalog"
  fingerprint_catalog_extras "$root/$CATALOG_DB_REL" "$out_txt"
  fingerprint_one_db "app_db" "$root/$APP_DB_REL" "$out_txt" "$out_schema_app"

  echo "== backend reported constants (best-effort) ==" >> "$out_txt"
  python3 - <<'PY' >> "$out_txt" 2>/dev/null || true
try:
    from app.catalog_db import CATALOG_DB_PATH
    print("CATALOG_DB_PATH =", CATALOG_DB_PATH)
except Exception as e:
    print("CATALOG_DB_PATH import failed:", e)

try:
    from app.core.image_resolver import DEFAULT_IMAGE_BASE
    print("DEFAULT_IMAGE_BASE =", DEFAULT_IMAGE_BASE)
except Exception as e:
    print("image_resolver import failed:", e)
PY
  echo >> "$out_txt"

  echo "Wrote:"
  echo "  $out_txt"
  echo "  $out_schema_catalog"
  echo "  $out_schema_app"
  echo "$outdir"
}

fingerprint_staging() {
  need ssh
  need sqlite3

  local host="${A2P_STAGING_HOST:-}"
  local path="${A2P_STAGING_PATH:-}"

  [ -n "$host" ] || die "Set A2P_STAGING_HOST (e.g. ubuntu@host)"
  [ -n "$path" ] || die "Set A2P_STAGING_PATH (e.g. /home/ubuntu/aim2build-app)"

  local root outdir
  root="$(repo_root)"
  outdir="$root/_compare_out/$(ts)"
  mkdir -p "$outdir"

  local out_txt="$outdir/staging_fingerprint.txt"
  local out_schema_catalog="$outdir/staging_schema_catalog.sql"
  local out_schema_app="$outdir/staging_schema_app.sql"

  : > "$out_txt"
  echo "== staging fingerprint ==" >> "$out_txt"
  echo "when: $(date -Is)" >> "$out_txt"
  echo "host: $host" >> "$out_txt"
  echo "path: $path" >> "$out_txt"
  echo >> "$out_txt"

  ssh "$host" "cd "$path" && ls -lh backend/app/data/*.db backend/app/data/**/*.db 2>/dev/null || true" >> "$out_txt" || true
  echo >> "$out_txt"

  ssh "$host" "cd "$path" && test -f "$CATALOG_DB_REL" && sqlite3 "$CATALOG_DB_REL" "$SQL_SETS_COUNT" && sqlite3 "$CATALOG_DB_REL" "$SQL_YEAR_RANGE" && sqlite3 "$CATALOG_DB_REL" "$SQL_2026_SAMPLE" || true" >> "$out_txt" || true
  echo >> "$out_txt"

  ssh "$host" "cd "$path" && test -f "$CATALOG_DB_REL" && sqlite3 "$CATALOG_DB_REL" ".schema" || true" > "$out_schema_catalog" || true
  ssh "$host" "cd "$path" && test -f "$APP_DB_REL" && sqlite3 "$APP_DB_REL" ".schema" || true" > "$out_schema_app" || true

  echo "Wrote:"
  echo "  $out_txt"
  echo "  $out_schema_catalog"
  echo "  $out_schema_app"
  echo "$outdir"
}

diff_out() {
  need diff

  local root latest_local latest_staging outdir out
  root="$(repo_root)"
  latest_local="$(ls -1dt "$root/_compare_out/"*/local_fingerprint.txt 2>/dev/null | head -n 1 || true)"
  latest_staging="$(ls -1dt "$root/_compare_out/"*/staging_fingerprint.txt 2>/dev/null | head -n 1 || true)"

  [ -n "$latest_local" ] || die "No local_fingerprint.txt found. Run: ./a2p_compare_local_vs_staging.sh fingerprint-local"
  [ -n "$latest_staging" ] || die "No staging_fingerprint.txt found. Run: ./a2p_compare_local_vs_staging.sh fingerprint-staging"

  outdir="$(dirname "$latest_local")"
  out="$outdir/diff.txt"

  {
    echo "== diff: local vs staging fingerprints =="
    echo "local:   $latest_local"
    echo "staging: $latest_staging"
    echo
    diff -u "$latest_staging" "$latest_local" || true
  } > "$out"

  echo "Wrote: $out"
  echo "$outdir"
}

case "$CMD" in
  snapshot) snapshot_local ;;
  fingerprint-local) fingerprint_local ;;
  fingerprint-staging) fingerprint_staging ;;
  diff) diff_out ;;
  *)
    cat <<USAGE
Usage:
  ./a2p_compare_local_vs_staging.sh snapshot
  ./a2p_compare_local_vs_staging.sh fingerprint-local
  ./a2p_compare_local_vs_staging.sh fingerprint-staging
  ./a2p_compare_local_vs_staging.sh diff

Environment for staging:
  export A2P_STAGING_HOST="ubuntu@host"
  export A2P_STAGING_PATH="/home/ubuntu/aim2build-app"
USAGE
    exit 1
    ;;
esac
