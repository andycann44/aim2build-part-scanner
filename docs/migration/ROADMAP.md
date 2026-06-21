# Scanner Roadmap

## Phase 1
Photo Session -> Upload -> R2 -> Azure Metadata

- Mobile captures 3+ photos.
- Backend creates session_id.
- Upload originals to R2.
- Save metadata to Azure.
- Mark session as uploaded.

## Phase 2
Background Removal -> Crop -> Thumbnail

- Worker loads originals.
- Removes/crops background.
- Creates thumbnails.
- Uploads crops/thumbs to R2.
- Updates metadata.

## Phase 3
Geometry Extraction

- Detect studs.
- Estimate stud count.
- Estimate width/length.
- Estimate height from side/angled shots.
- Save geometry metadata.

## Phase 4
Catalog Candidate Search

- Read lego_catalog.db only.
- Restrict Phase 1 to color_id 0.
- Query candidates by geometry and known black availability.
- Return top candidates.

## Phase 5
User Confirmation -> Training Dataset

- Staff confirms part_num.
- Save confirmed label.
- Training record links:
  - original R2 image
  - crop R2 image
  - thumbnail R2 image
  - part_num
  - color_id
  - geometry metadata
  - camera/light metadata
