# Aim2Build Part Scanner - Structure Audit

## Current production layout

backend/
- api/        FastAPI routes and upload/session endpoints
- r2/         Cloudflare R2 upload helpers
- azure/      Metadata/session label storage
- workers/    Background processing jobs
- image/      Thumbnail, crop, background removal, geometry helpers
- catalog/    Read-only lego_catalog.db lookup
- models/     Shared request/response/session models

## Baseline files

- backend/r2/r2_client.py
- backend/azure/metadata_store.py
- backend/image/thumbnails.py
- backend/catalog/catalog_lookup.py
- backend/workers/process_session.py
- docs/migration/PHASE_PLAN.md
- requirements.txt

## Rules

- Do not modify live Aim2Build repos.
- Do not write ML/scanner data into lego_catalog.db.
- lego_catalog.db is read-only.
- R2 stores originals, thumbnails, and processed crops.
- Azure metadata stores session records and labels.
- Phase 1 colour is black only: color_id = 0.
