#!/bin/bash
: "${HISTTIMEFORMAT:=}"
set -euo pipefail
[ -f ./a2p_bash_compat.sh ] && source ./a2p_bash_compat.sh
[ -f /tmp/a2p_env.sh ] && source /tmp/a2p_env.sh

# Aim2Build – Buildability / Discover admin commands
# ==================================================
# This file is a runnable cheat‑sheet with descriptions.
#
# Run from repo root:
#   cd ~/aim2build-app
#   bash a2p_buildability_admin.sh help
#
# -------------------------------
# QUICK START
# -------------------------------
# 1) Check DB + filters
#    bash a2p_buildability_admin.sh status
#
# 2) Exclude a noisy THEME
#    bash a2p_buildability_admin.sh theme-search book
#    bash a2p_buildability_admin.sh theme-enable 501 "Books / Manuals"
#
# 3) Exclude a specific SET
#    bash a2p_buildability_admin.sh set-exclude 42141-2 "Duplicate edition"
#
# 4) Verify Discover API exclusion
#    TOKEN='JWT_HERE' bash a2p_buildability_admin.sh discover-check 42141-2
#
# -------------------------------
# DB LOCATION
# -------------------------------
DB="${A2B_CATALOG_DB:-backend/app/data/lego_catalog.db}"

die() { echo "ERROR: $*" >&2; exit 1; }

need_db() {
  [ -f "$DB" ] || die "DB not found at $DB"
}

help() {
  sed -n '1,200p' "$0"
}

# -------------------------------
# STATUS / INSPECTION
# -------------------------------
status() {
  need_db
  echo "== BASIC COUNTS =="
  sqlite3 "$DB" "SELECT COUNT(*) AS sets FROM sets;"
  sqlite3 "$DB" "SELECT COUNT(*) AS set_parts FROM set_parts;"
  echo
  echo "== KEY TABLES =="
  sqlite3 "$DB" "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('themes','theme_filters','set_filters','sets','set_parts') ORDER BY name;"
  echo
  echo "== ENABLED THEME FILTERS =="
  sqlite3 "$DB" "SELECT COUNT(*) FROM theme_filters WHERE enabled=1;" 2>/dev/null || echo "theme_filters missing"
  echo
  echo "== ENABLED SET FILTERS =="
  sqlite3 "$DB" "SELECT COUNT(*) FROM set_filters WHERE enabled=1;" 2>/dev/null || echo "set_filters missing"
}

# -------------------------------
# THEME FILTERS
# -------------------------------
theme_list() {
  need_db
  sqlite3 -header -column "$DB" \
    "SELECT theme_id, name FROM themes ORDER BY name;"
}
theme_search() {
  need_db
  local q="${1:-}"
  [ -n "$q" ] || die "theme-search <text>"

  sqlite3 -header -column "$DB" \
    "SELECT theme_id, name
     FROM themes
     WHERE lower(name) LIKE '%' || lower('$(echo "$q" | sed "s/'/''/g")') || '%'
     ORDER BY name;"
}
theme_enabled() {
  need_db
  sqlite3 -header -column "$DB"     "SELECT tf.theme_id, t.name, tf.enabled, COALESCE(tf.reason,'') AS reason
     FROM theme_filters tf
     LEFT JOIN themes t ON t.id=tf.theme_id
     WHERE tf.enabled=1
     ORDER BY t.name;"
}

theme_enable() {
  need_db
  local id="${1:-}"
  local reason="${2:-Manual exclude}"
  [ -n "$id" ] || die "theme-enable <theme_id> [reason]"
  sqlite3 "$DB"     "INSERT OR REPLACE INTO theme_filters(theme_id, enabled, reason)
     VALUES($id, 1, '$(echo "$reason" | sed "s/'/''/g")');"
  echo "Theme excluded: $id"
}

theme_disable() {
  need_db
  local id="${1:-}"
  [ -n "$id" ] || die "theme-disable <theme_id>"
  sqlite3 "$DB" "UPDATE theme_filters SET enabled=0 WHERE theme_id=$id;"
  echo "Theme re-enabled: $id"
}

# -------------------------------
# SET FILTERS
# -------------------------------
set_ensure() {
  need_db
  sqlite3 "$DB" "
  CREATE TABLE IF NOT EXISTS set_filters (
    set_num TEXT PRIMARY KEY,
    enabled INTEGER NOT NULL DEFAULT 1,
    reason TEXT
  );"
}

set_enabled() {
  need_db
  sqlite3 -header -column "$DB"     "SELECT set_num, enabled, COALESCE(reason,'') AS reason
     FROM set_filters WHERE enabled=1 ORDER BY set_num;" 2>/dev/null || true
}

set_exclude() {
  need_db
  set_ensure
  local sn="${1:-}"
  local reason="${2:-Manual exclude}"
  [ -n "$sn" ] || die "set-exclude <set_num> [reason]"
  sqlite3 "$DB"     "INSERT OR REPLACE INTO set_filters(set_num, enabled, reason)
     VALUES('$(echo "$sn" | sed "s/'/''/g")', 1, '$(echo "$reason" | sed "s/'/''/g")');"
  echo "Set excluded: $sn"
}

set_include() {
  need_db
  set_ensure
  local sn="${1:-}"
  [ -n "$sn" ] || die "set-include <set_num>"
  sqlite3 "$DB" "UPDATE set_filters SET enabled=0 WHERE set_num='$(echo "$sn" | sed "s/'/''/g")';"
  echo "Set re-enabled: $sn"
}

# -------------------------------
# PERFORMANCE HELPERS
# -------------------------------
add_indexes() {
  need_db
  sqlite3 "$DB" <<'SQL'
CREATE INDEX IF NOT EXISTS idx_set_parts_part_color_set ON set_parts(part_num, color_id, set_num);
CREATE INDEX IF NOT EXISTS idx_set_parts_set_num ON set_parts(set_num);
CREATE INDEX IF NOT EXISTS idx_sets_set_num ON sets(set_num);
ANALYZE;
SQL
  echo "Indexes ensured + ANALYZE done"
}

# -------------------------------
# API CHECKS
# -------------------------------
discover_raw() {
  [ -n "${TOKEN:-}" ] || die "Set TOKEN env var first"
  curl -sS -H "Authorization: Bearer $TOKEN"     "http://127.0.0.1:8000/api/buildability/discover?min_coverage=0.0&limit=50" | head -c 800; echo
}

discover_check() {
  local sn="${1:-}"
  [ -n "$sn" ] || die "discover-check <set_num>"
  [ -n "${TOKEN:-}" ] || die "Set TOKEN env var first"
  if curl -sS -H "Authorization: Bearer $TOKEN"       "http://127.0.0.1:8000/api/buildability/discover?min_coverage=0.0&limit=5000"       | jq -r '.[].set_num' 2>/dev/null | grep -F "$sn" >/dev/null; then
    echo "FOUND (bad): $sn"
  else
    echo "NOT FOUND (good): $sn"
  fi
}

# -------------------------------
# DISPATCH
# -------------------------------
cmd="${1:-help}"
shift || true

case "$cmd" in
  help) help ;;
  status) status ;;
  theme-list) theme_list ;;
  theme-search) theme_search "${1:-}" ;;
  theme-enabled) theme_enabled ;;
  theme-enable) theme_enable "${1:-}" "${2:-Manual exclude}" ;;
  theme-disable) theme_disable "${1:-}" ;;
  set-ensure) set_ensure ;;
  set-enabled) set_enabled ;;
  set-exclude) set_exclude "${1:-}" "${2:-Manual exclude}" ;;
  set-include) set_include "${1:-}" ;;
  add-indexes) add_indexes ;;
  discover-raw) discover_raw ;;
  discover-check) discover_check "${1:-}" ;;
  *) die "Unknown command: $cmd (run help)" ;;
esac
