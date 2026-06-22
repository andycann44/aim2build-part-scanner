# Rulebook

1. Phase 1 only supports black LEGO parts.
2. color_id 0 is valid LEGO Black and must never be remapped.
3. lego_catalog.db is read-only.
4. R2 stores original scan images and thumbnails.
5. Azure / ML metadata stores labels, confidence, and staff confirmation.
6. Staff confirmation is source of truth for training labels.

## Catalog Safety

- lego_catalog.db is read-only.
- Scanner code must never INSERT, UPDATE, DELETE, DROP, ALTER, VACUUM, or CREATE inside lego_catalog.db.
- Catalog access is lookup-only for:
  - part metadata
  - set metadata
  - element images
  - color data
- Scanner-generated data must be stored only in:
  - R2 for images/crops/thumbnails
  - Azure/metadata store for sessions and labels
  - scanner/training database if added later
