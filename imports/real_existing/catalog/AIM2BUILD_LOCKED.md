🔒 WHAT IS NOW LOCKED (WRITE THIS IN STONE)

1) Images
- Source: lego_catalog.db -> element_images
- No inventory_images
- No URL rewriting
- No fallbacks

2) Inventory
- Key = (part_num, color_id)
- color_id=0 valid
- Printed parts are distinct part_nums
- No family / canonical collapsing at runtime
## Inventory (LOCKED)
- Legacy `/api/inventory/add` is temporarily allowed as a migration bridge.
  All new work must use canonical endpoints.    

- Inventory source of truth is the database table:
  `user_inventory_parts` in `aim2build_app.db`
- `/api/inventory/parts` and `/api/inventory/parts_with_images`
  MUST read from `user_inventory_parts`
- Legacy per-user JSON inventory files are deprecated and MUST NOT
  be used by inventory read endpoints

3) Canonical endpoints (ONLY inventory mutation APIs)
- POST /api/inventory/add-canonical
- POST /api/inventory/set-canonical
- POST /api/inventory/decrement-canonical

- Inventory mutation endpoints allowed: add-canonical, set-canonical, decrement-canonical, clear-canonical

