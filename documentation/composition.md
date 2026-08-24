# Composition Object

Parent: [DatasetDocumentation](main.md)

## Object schema

```text
Composition
├── datasetCategory
├── mediaCategories[]
├── objectTypes[]
├── structure
├── dataInstance
├── fields[]
├── standards[]
├── dataSplits[]
├── languages[]
└── descriptiveStatistics
```

## Categories and object types

| Field | Status | Value |
| --- | --- | --- |
| Dataset category | `VERIFIED` | Content and metadata. Article bodies and images are content; dates, headlines, sections, bylines, locations, identifiers, and associations are metadata. |
| Media categories | `VERIFIED` | Text and image. Archived web pages are the source representation. |
| Cultural-heritage object types | `VERIFIED` | Newspaper articles, news photographs, and archived web pages. No controlled AAT or RDA term identifiers have been assigned. |
| Unit of observation | `VERIFIED` | One extracted news article represented by one ninjs JSON object, optionally associated with zero or more images. |

## Technical structure

Current V3 output is organised as:

```text
DATASET_ROOT/
└── YEAR/
    └── MONTH/
        └── DAY/
            └── ARTICLE_ID/
                ├── ARTICLE_ID.json
                └── img/
                    └── archived-image-files
```

`ARTICLE_ID` is the final, exactly 26-character path component of a supported Apple Daily article URL. The directory date is derived from the URL date, evidenced `firstCreated`, or a capture-date directory fallback. A capture-date directory fallback is not written as an invented `firstCreated` value.

## Typical data instance

```json
{
  "uri": "https://www.appledaily.com.tw/entertainment/20220824/724E2C670A6767BFA1ADA8478E",
  "standard": {
    "name": "ninjs",
    "version": "3.2",
    "schema": "https://iptc.org/std/ninjs/ninjs-schema_3.2.json"
  },
  "firstCreated": "2022-08-24T00:00:00+08:00",
  "versionCreated": "2022-09-03T09:58:27+08:00",
  "contentCreated": "2026-08-24T12:00:00+08:00",
  "type": "text",
  "language": "zh-Hant-TW",
  "headlines": [{"role": "main", "value": "Example headline"}],
  "subjects": [{"name": "entertainment"}],
  "bodies": [
    {"role": "main", "contentType": "text/plain", "value": "Example article body"}
  ],
  "associations": [],
  "by": "",
  "located": "",
  "altIds": [
    {"role": "internal", "value": "724E2C670A6767BFA1ADA8478E"}
  ]
}
```

The timestamps and content above illustrate the current schema; they are not asserted as a verified transcription of that specific article.

## Data fields

| Field | Type | Status | Description and limitations |
| --- | --- | --- | --- |
| `uri` | string/URI | `VERIFIED` | Canonical article URI with query and fragment removed. The original page may no longer be accessible. |
| `standard` | object | `VERIFIED` | Declares project-profile ninjs 3.2 and its schema URI. |
| `firstCreated` | ISO 8601 datetime | `PARTIAL` | Original publication time chosen from evidenced HTML metadata; valid URL date at Taiwan midnight is the last fallback. Omitted when no valid evidence exists. |
| `versionCreated` | ISO 8601 datetime | `VERIFIED` | `WARC-Date` converted to Taiwan time (`+08:00`). |
| `contentCreated` | ISO 8601 datetime | `VERIFIED` | Time at which the JSON object was generated, not article publication time. |
| `type` | string | `VERIFIED` | `composite` when image associations exist; otherwise `text`. |
| `profile` | string | `VERIFIED` | Present as `text-photo` for composite records; absent for text-only records in this project profile. |
| `language` | BCP 47 string | `PARTIAL` | Fixed to `zh-Hant-TW`; item-level language detection was not performed. |
| `headlines` | array of objects | `PARTIAL` | Main headline extracted from the page. Missing or incorrect extraction remains possible across historical layouts. |
| `subjects` | array of objects | `PARTIAL` | Website section derived from the article URL. It is not a complete editorial taxonomy. |
| `bodies` | array of objects | `PARTIAL` | Cleaned plain-text body with `contentType: text/plain`; affected by extraction fallbacks and cleaning rules. |
| `associations` | array of objects | `PARTIAL` | Picture associations with `name`, original `uri`, `type: picture`, and optional caption `headlines`. No local `renditions` or creator metadata are emitted. |
| `by` | string | `PARTIAL` | Rule-derived byline; empty when no reliable match exists. |
| `located` | string | `PARTIAL` | Rule-derived reporting location; empty when no reliable match exists. |
| `altIds` | array of objects | `PARTIAL` | Contains the URI-derived 26-character internal article ID. Historical datasets contain duplicate values; consumers must not assume universal uniqueness. |

## Compliance with standards

| Standard | Status | Value |
| --- | --- | --- |
| ninjs | `PARTIAL` | The current converter emits a deliberately small project profile based on ninjs 3.2: <https://iptc.org/std/ninjs/ninjs-schema_3.2.json>. Release-wide schema validation is not documented. |
| WARC | `VERIFIED` as source format | Source data are WARC web-archive files processed with FastWARC. The dataset output itself is not WARC. |
| BCP 47 | `VERIFIED` structurally | `zh-Hant-TW` is used as the language tag. The value is assigned uniformly rather than detected per item. |

## Data splits

| Field | Status | Value |
| --- | --- | --- |
| Train/validation/test splits | `NOT APPLICABLE` | The dataset is an archival collection, not a benchmark release. It provides no recommended ML splits. Researchers creating splits must document date leakage, duplicate IDs, topic imbalance, and image availability. |

## Descriptive statistics

These figures describe existing historical artefacts and comparison inputs. They must not be treated as a single, formally reconciled release.

| Version/artefact | Status | Records | Distinct IDs | Other known statistics |
| --- | --- | ---: | ---: | --- |
| V1 text collection | `VERIFIED` | 953,175 | 952,556 | 13 records lack an ID; 606 ID values are duplicated. The WAC 2025 description reports 4.3 GB for the unique text collection. |
| Local V2 comparison input | `VERIFIED` | 977,305 | 949,704 | 2 records lack an ID; 27,528 ID values are duplicated. A prior image inventory reports 1,156,263 images. |
| Local V3 comparison input | `VERIFIED` | 992,176 | 991,987 | 188 ID values are duplicated. |
| V3 images | `PARTIAL` | — | — | Approximately 1.9 million images were previously reported, but this has not been reconciled with a formal release manifest. |
| Exact release bytes and MIME distribution | `DEFERRED (>30 min)` | — | — | Requires a full release-tree scan. |
| Per-year, per-section, and per-field distributions | `DEFERRED (>30 min)` | — | — | Requires a full dataset audit. |
| Current `by` and `located` missingness | `DEFERRED (>30 min)` | — | — | Historical estimates are about 27% and 44%, respectively; they have not been recomputed for the latest ninjs 3.2 output. |
| Empty text, replacement characters, and association coverage | `DEFERRED (>30 min)` | — | — | Requires a full dataset audit. |

