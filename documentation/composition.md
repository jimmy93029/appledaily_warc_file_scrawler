# Composition and fields

Parent: [Dataset documentation](README.md)

Each record represents one extracted news article, with text, metadata, and optional images. The current output uses a project profile based on ninjs 3.2.

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

## Data fields

| Field | Type | Description and limitations |
| --- | --- | --- |
| `uri` | string/URI | Canonical article URI with query and fragment removed. The original page may no longer be accessible. |
| `standard` | object | Declares project-profile ninjs 3.2 and its schema URI. |
| `firstCreated` | ISO 8601 datetime | Original publication time chosen from evidenced HTML metadata; valid URL date at Taiwan midnight is the last fallback. Omitted when no valid evidence exists. |
| `versionCreated` | ISO 8601 datetime | `WARC-Date` converted to Taiwan time (`+08:00`). |
| `contentCreated` | ISO 8601 datetime | Time at which the JSON object was generated, not article publication time. |
| `type` | string | `composite` when image associations exist; otherwise `text`. |
| `profile` | string | Present as `text-photo` for composite records; absent for text-only records in this project profile. |
| `language` | BCP 47 string | Fixed to `zh-Hant-TW`; item-level language detection was not performed. |
| `headlines` | array of objects | Main headline extracted from the page. Missing or incorrect extraction remains possible across historical layouts. |
| `subjects` | array of objects | Website section derived from the article URL. It is not a complete editorial taxonomy. |
| `bodies` | array of objects | Cleaned plain-text body with `contentType: text/plain`; affected by extraction fallbacks and cleaning rules. |
| `associations` | array of objects | Picture associations with `name`, original `uri`, `type: picture`, and optional caption `headlines`. No local `renditions` or creator metadata are emitted. |
| `by` | string | Rule-derived byline; empty when no reliable match exists. |
| `located` | string | Rule-derived reporting location; empty when no reliable match exists. |
| `altIds` | array of objects | Contains the URI-derived 26-character internal article ID. Historical datasets contain duplicate values; consumers must not assume universal uniqueness. |

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

## Standards and data splits

The output follows a subset of [ninjs 3.2](https://iptc.org/std/ninjs/ninjs-schema_3.2.json); release-wide schema validation is not documented. WARC is the source format, not the output format. The BCP 47 tag `zh-Hant-TW` is assigned uniformly. No external authority links, controlled subject taxonomy, or AAT/RDA object identifiers are supplied.

This archival collection has no recommended train/validation/test splits. Researchers constructing splits should account for temporal leakage, duplicates, topic imbalance, and image availability.

## Descriptive statistics

These figures describe existing historical artefacts and comparison inputs. They must not be treated as a single, formally reconciled release.

| Version/artefact | Records | Distinct IDs | Other known statistics |
| --- | ---: | ---: | --- |
| V1 text collection | 953,175 | 952,556 | 13 records lack an ID; 606 ID values are duplicated. The WAC 2025 description reports 4.3 GB for the unique text collection. |
| Local V2 comparison input | 977,305 | 949,704 | 2 records lack an ID; 27,528 ID values are duplicated. A prior image inventory reports 1,156,263 images. |
| Local V3 comparison input | 992,176 | 991,987 | 188 ID values are duplicated. |
| V3 images | — | — | Approximately 1.9 million images were previously reported, but this has not been reconciled with a formal release manifest. |

Exact release size, MIME distribution, year/section distributions, current missingness, text quality, and image-association coverage have not been audited across the final release. Historical missingness estimates for `by` and `located` are about 27% and 44%; they have not been recomputed for the latest ninjs 3.2 output.

References: [Dataset comparison report](https://hackmd.io/mSNYQ4PjT1-MjO9IztENLw) and [WAC 2025 presentation](https://digital.library.unt.edu/ark:/67531/metadc2472454/). These existing figures are retained here and have not been recomputed for this documentation revision.
