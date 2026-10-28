# Versioning and maintenance

Parent: [Dataset documentation](README.md)

## Code versions

Git tags identify code snapshots, not formal dataset releases. Record the tag and commit actually used to produce or analyse a dataset.

| Version | Code reference | Snapshot date | Main changes |
| --- | --- | --- | --- |
| V1 | `dataset-v1` / [`f747ffd`](https://github.com/jimmy93029/appledaily_warc_file_scrawler/commit/f747ffd6478369bbee0022035bf05ac2b8f02094) | 2024-03-21 | Text extraction and advertising cleanup; ninjs 2.1-style field names. |
| V2 | `dataset-v2` / [`da0438d`](https://github.com/jimmy93029/appledaily_warc_file_scrawler/commit/da0438d2439016511d2fb63b3852fc404dc40174) | 2025-03-23 | Image extraction and SQLite/Datasette display tools. The tag description refers to 2025-04-01. |
| V3 | `dataset-v3` / [`4acdaa1`](https://github.com/jimmy93029/appledaily_warc_file_scrawler/commit/4acdaa18db98c701ba90ce3a2a9beb191f0a7f40) | 2026-07-22 | WARC decoding, date recovery, image association, ninjs 3.2, and date-tree deduplication. |

V3 is the current documented code version. The `master` branch may change independently. V1 and V2 remain historical references; no formal deprecation policy is documented.

## Dataset release status

No authoritative release manifest yet connects a distributed dataset with its version, release date, record counts, checksums, licence, and persistent identifier. Formal release and last-modification dates are therefore unconfirmed. A complete release file list and SHA-256 checksums are not available.

The [historical statistics](composition.md#descriptive-statistics) describe specific comparison inputs, not a reconciled current release. Processing and duplicate-selection behavior are described in [Collection and processing](collection-process.md).

## Maintenance and corrections

The source crawl is static, while code and derived datasets may change. A long-term dataset maintainer, maintenance level, update schedule, and correction/version-notification policy have not been formally established. The technical contact does not imply a response-time or permanent maintenance commitment.

Report code problems through [GitHub Issues](https://github.com/jimmy93029/appledaily_warc_file_scrawler/issues). Direct dataset access, rights, and privacy enquiries to the [administrative contact](distribution.md#point-of-contact).

The formal datasheet is planned for depositar. The final data deposit and rules for synchronising documentation with dataset releases remain to be confirmed; see [Distribution and licensing](distribution.md).
