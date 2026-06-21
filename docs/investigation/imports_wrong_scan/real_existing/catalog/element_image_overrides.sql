-- Aim2Build manual image overrides
-- Truth table: element_images(part_num, color_id, img_url)
-- Rule: do NOT swap colours. Insert exact (part_num, color_id).
--
-- Apply:
--   cd ~/aim2build-app
--   sqlite3 backend/app/data/lego_catalog.db < backend/app/data/element_image_overrides.sql

BEGIN TRANSACTION;

-- Example (your 10197 colour 0 fix):
INSERT OR REPLACE INTO element_images (part_num, color_id, img_url)
VALUES ('10197', 0, 'https://cdn.rebrickable.com/media/thumbs/parts/elements/6099801.jpg/250x250p.jpg');

COMMIT;
