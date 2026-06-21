# Aim2Build – Filter Runbook (themes + sets)
# ==========================================
# Keep this file open in VS Code so you never have to remember commands.

## Files you edit
1) backend/app/data/seed_theme_filters.sql
   - List of theme_ids you want Discover to exclude (enabled=1)

2) backend/app/data/seed_set_filters.sql
   - List of specific set_num you want Discover to exclude (enabled=1)

3) a2p_buildability_admin.sh
   - Helper script that runs common commands safely

---

## One-time setup (repo root)
cd ~/aim2build-app
chmod +x a2p_buildability_admin.sh

---

## Check DB status + what is currently excluded
cd ~/aim2build-app
bash ./a2p_buildability_admin.sh status

See enabled theme exclusions:
bash ./a2p_buildability_admin.sh theme-enabled

See enabled set exclusions:
bash ./a2p_buildability_admin.sh set-enabled

---

## Find a theme id by name (search)
cd ~/aim2build-app
bash ./a2p_buildability_admin.sh theme-search book

---

## Exclude a theme (by theme_id)
cd ~/aim2build-app
bash ./a2p_buildability_admin.sh theme-enable 497 "Books clutter"

Re-enable a theme:
bash ./a2p_buildability_admin.sh theme-disable 497

---

## Exclude a specific set (by set_num)
cd ~/aim2build-app
bash ./a2p_buildability_admin.sh set-exclude 42141-2 "Duplicate edition"

Re-enable a set:
bash ./a2p_buildability_admin.sh set-include 42141-2

---

## Apply seed files into the DB (recommended workflow)
# Do this after you edit seed_theme_filters.sql or seed_set_filters.sql

# Apply seed files into the DB (recommended workflow)
# Run ONLY the one you actually edited.

cd ~/aim2build-app

# If you edited seed_set_filters.sql:
sqlite3 backend/app/data/lego_catalog.db < backend/app/data/seed_set_filters.sql

# If you edited seed_theme_filters.sql:
# sqlite3 backend/app/data/lego_catalog.db < backend/app/data/seed_theme_filters.sql

sqlite3 backend/app/data/lego_catalog.db "ANALYZE;"

---

## Verify the API (Discover) is returning JSON and that a set is excluded
# You must provide TOKEN (JWT) when calling the /discover endpoint.

cd ~/aim2build-app
TOKEN='PASTE_JWT_HERE' bash ./a2p_buildability_admin.sh discover-raw

Check one excluded set never appears:
TOKEN='PASTE_JWT_HERE' bash ./a2p_buildability_admin.sh discover-check 42141-2

---

## If you see: "database is locked (5)"
It means something is holding the DB open for writing (common causes):
- sqlite3 session open on the same DB
- VS Code DB viewer extension holding a lock
- backend running with an open write transaction

Fix:
- close the sqlite3 prompt / DB viewer
- stop backend briefly if needed
Then rerun the command.

# ==========================================================
# ⚠️ CATALOG DATABASE SAFETY NOTICE (READ FIRST)
# ==========================================================
#
# The file:
#   backend/app/data/lego_catalog.db
#
# is a LIVE, canonical catalog database.
#
# It contains:
# - Derived tables (element_images, set_parts, instruction_*,
#   truth_* tables, family maps, views, indexes, etc.)
# - Schema that is NOT recreated by the CSV importer.
#
# ----------------------------------------------------------
# 🚫 DO NOT RUN THESE AGAINST A LIVE DB
# ----------------------------------------------------------
#
# catalog_import/import_csv.py
# backend/scripts/a2b_catalog_reimport.sh
# a2b_refresh_catalog.sh
#
# These scripts:
# - DROP TABLES
# - RECREATE ONLY a MINIMAL schema
# - WILL DESTROY derived tables, views, and indexes
#
# They are intended ONLY for:
# - building a brand new catalog DB from scratch
# - offline experiments
#
# ----------------------------------------------------------
# ✅ SAFE OPERATIONS (INTENDED WORKFLOW)
# ----------------------------------------------------------
#
# - Copy a known-good catalog DB from STAGING
# - Apply seed files (theme filters, set filters)
# - Add metadata only (e.g. last_updated timestamp)
#
# NEVER rebuild the catalog DB unless you explicitly intend
# to recreate the entire schema.
#
# ==========================================================
