# Clearinghouse Scripts

Utility scripts for data management and testing.

## Scripts

### `transform_mock_data.py`
Transforms rich demo track data (like `tracks_all.json`) into the format expected by the bulk import API.

```bash
python transform_mock_data.py /path/to/tracks_all.json
# Output: import_ready.json in same directory
```

### `seed_demo_data.py`
Seeds demo data into the database. Two modes:

**API Mode** (recommended):
```bash
python seed_demo_data.py \
  --api-url https://clearinghouse-api.onrender.com \
  --token YOUR_JWT_TOKEN \
  --data-file test_data/kpop_sample.json
```

**Direct Database Mode**:
```bash
python seed_demo_data.py --direct \
  --database-url postgresql://... \
  --user-id YOUR_USER_UUID \
  --data-file test_data/kpop_sample.json
```

## Test Data

### `test_data/simple_tracks.csv`
Minimal CSV for testing the CSV upload endpoint.

### `test_data/kpop_sample.json`
3 sample tracks with full metadata for testing JSON bulk import.

## Workflow

### 1. Test the Upload Flow
```bash
# Test with minimal data first
curl -X POST https://your-api/api/v1/catalogs/{id}/import \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d @test_data/kpop_sample.json
```

### 2. Transform Full Mock Data
```bash
python transform_mock_data.py ~/Downloads/files/tracks_all.json
```

### 3. Seed Full Demo Catalog
```bash
python seed_demo_data.py \
  --api-url https://clearinghouse-api.onrender.com \
  --token YOUR_TOKEN \
  --data-file ~/Downloads/files/import_ready.json
```

## Dependencies

```bash
pip install httpx asyncpg
```
