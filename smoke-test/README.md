# Smoke tests and audit tools

This directory contains the useful read-only diagnostics selected from
`venv/codes`.  Production download and conversion code lives in
`../downloads`; old ad-hoc upload, website, and hard-coded investigation
scripts were intentionally not copied.

## Pipeline checks

- `pipeline/test_ninjs_pipeline.py` — fast formatter and disk-backed dedup test.
- `pipeline/diagnose_target_articles.py` — inspect selected WARC article records.
- `pipeline/verify_diagnosed_image_captions.py` — verify image/caption evidence.

Run the fast test from this directory with:

```bash
PYTHONPATH=../downloads python pipeline/test_ninjs_pipeline.py
```

When the repository is checked out elsewhere, use the Python environment that
contains the packages required by the download pipeline.

## Archive audits

- `audit/audit_warc_recoverable_fields.py` — report metadata recoverable from WARC HTML.
- `audit/classify_images_by_article_id.py` — classify image candidates using article IDs and trusted evidence.
- `audit/list_missing_associations_with_images.py` — find records whose image files are not represented in ninjs.
- `audit/check_all_only_v1.py` — audit records found only by the former extraction.
- `audit/classify_missing_articles.py` — classify canonical missing IDs by URL
  rule and by responses found in explicitly available WARC files; absence is
  reported only for those supplied WARCs, never for the full archive.

These tools stream their inputs and write reports; they do not modify the
source WARC or article archive.
