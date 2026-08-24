# Lifecycle Object

Parent: [DatasetDocumentation](main.md)

## Object schema

```text
Lifecycle
├── currentVersion
├── versions[]
├── releaseDate
├── modificationDate
├── checksums[]
└── maintenance
    ├── plan
    ├── level
    ├── updatePeriodicity
    └── correctionPolicy
```

## Version information

The repository uses Git tags for code snapshots. A code snapshot date is not automatically a formal dataset release date.

| Dataset/code generation | Status | Reference | Code snapshot date | Description |
| --- | --- | --- | --- | --- |
| V1 | `VERIFIED` | `dataset-v1` / `f747ffd6478369bbee0022035bf05ac2b8f02094` | 2024-03-21 | Historical text-extraction and advertising-cleanup workflow; project output used ninjs 2.1-style names. |
| V2 | `VERIFIED` | `dataset-v2` / `da0438d2439016511d2fb63b3852fc404dc40174` | 2025-03-23 commit date; tag description refers to 2025-04-01 | Expanded image and Datasette/SQLite display tooling. |
| V3 | `VERIFIED` | `dataset-v3` / `4acdaa18db98c701ba90ce3a2a9beb191f0a7f40` | 2026-07-22 | Current WARC decoding, date recovery, media association, project-profile ninjs 3.2, and date-tree deduplication code. |

| Field | Status | Value |
| --- | --- | --- |
| Current code version | `VERIFIED` | V3 / `dataset-v3` / `4acdaa1`. |
| Current formal dataset release | `UNKNOWN` / `HUMAN DECISION REQUIRED` | No release manifest ties a public distribution, version string, counts, checksums, licence, and PID together. |
| Formal release dates | `UNKNOWN` | Git snapshot dates are known; formal dataset release dates are not. |
| Last dataset modification date | `UNKNOWN` | No authoritative release manifest records it. |
| Previous-version deprecation | `UNKNOWN` / `HUMAN DECISION REQUIRED` | V1 and V2 remain historically relevant, but no policy declares them active or deprecated. |
| V3 addendum status | `UNKNOWN` | The repository does not provide sufficient evidence that a separately described V3 addendum was completed and merged into a formal release. |

## Deduplication policy in current code

- Canonicalise the article URI by removing query and fragment.
- Extract the article ID from the final 26-character path component.
- Use `YEAR/MONTH/DAY/ARTICLE_ID` as the output key.
- For an existing key, prefer newer `versionCreated`.
- On ties, compare body length, number of associations, and shard number deterministically.
- Write duplicate and error reports outside the year tree.

Limitation: because the key includes the date, the same article ID placed under different parsed dates will not collide at this stage. A global ID/URI release audit remains necessary.

## Checksums and manifests

| Field | Status | Value |
| --- | --- | --- |
| Release file manifest | `UNKNOWN` | No authoritative release manifest is present. |
| SHA-256 checksums | `DEFERRED (>30 min)` | Computing checksums for a complete multi-file release requires identifying and scanning the final release tree. Not run. |
| Aggregate counts tied to checksums | `DEFERRED (>30 min)` | Requires reconciliation of article files, images, reports, and combined artefacts. Not run. |

## Maintenance

| Field | Status | Value |
| --- | --- | --- |
| Maintenance plan | `UNKNOWN` / `HUMAN DECISION REQUIRED` | No approved plan is published. |
| Maintenance level | `UNKNOWN` / `HUMAN DECISION REQUIRED` | Must be designated as actively maintained, limited maintenance, or no maintenance by the responsible organisation. |
| Update periodicity | `UNKNOWN` / `HUMAN DECISION REQUIRED` | No schedule is stated. The source crawl is static, while processing code and derived releases may change. |
| Maintainer | `UNKNOWN` / `HUMAN DECISION REQUIRED` | Git history identifies the primary code contributor, but does not establish a formal long-term dataset maintainer. |
| Issue reporting | `PARTIAL` | GitHub Issues may be used for technical reports. No response commitment is specified. |
| Data correction policy | `UNKNOWN` / `HUMAN DECISION REQUIRED` | No policy defines correction review, release replacement, tombstones, or version notification. |
| Long-term repository | `UNKNOWN` / `HUMAN DECISION REQUIRED` | DepositAR is a candidate or related repository, but a final dataset deposit is not verified. |
| Documentation update policy | `PARTIAL` | This documentation is versioned with the code repository. No required synchronization rule with dataset releases exists. |

