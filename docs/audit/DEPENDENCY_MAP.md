# Dependency Map

Expected direction:

api/
  imports models, r2, azure, workers

workers/
  imports r2, azure, image, catalog, models

image/
  imports no project modules unless required

catalog/
  imports sqlite/path config only

r2/
  imports boto3 or S3-compatible client only

azure/
  imports Azure SDK only

models/
  imports pydantic/dataclasses only

Forbidden:
- r2 importing api
- azure importing api
- catalog writing to lego_catalog.db
- workers importing mobile/frontend code
- circular imports between api and workers
