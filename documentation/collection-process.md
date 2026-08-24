# CollectionProcess Object

Parent: [DatasetDocumentation](main.md)

## Object schema

```text
CollectionProcess
├── curationRationale
├── sourceData
├── initialCollection
├── sourceDataProducers
├── digitisationPipeline
├── preprocessingAndCleaning
├── generatedMetadata
│   ├── process
│   ├── annotators
│   └── crowdLabour
├── provenance
└── linkedDataAndVocabularies
```

## Curation rationale

| Field | Status | Value |
| --- | --- | --- |
| Motivation | `VERIFIED` | Preserve and enable computational access to Taiwan Apple Daily news after the source website became unavailable. |
| Major design choice | `VERIFIED` | Transform page-level web captures into article-level structured JSON while retaining provenance dates and conservative extraction evidence. |
| Representativeness claim | `VERIFIED` | None. The dataset must not be treated as the complete population of all Taiwan Apple Daily publications from 2003–2022. |

## Source data

| Field | Status | Value |
| --- | --- | --- |
| Source objects | `VERIFIED` | HTTP responses, HTML pages, images, redirects, and other resources stored in an ArchiveBot WARC job for `appledaily.com.tw`. |
| Archive job | `VERIFIED` | `202209030158271bpf8`: <https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8> |
| Numbered shards | `VERIFIED` | 804 numbered WARC shards, `00000`–`00803`, plus an unnumbered `meta.warc.gz`. |
| Approximate archive size | `PARTIAL` | Approximately 4.33 TB according to the existing archive description; unit convention and exact bytes are not recorded here. |
| Collection start | `PARTIAL` | The job identifier encodes `2022-09-03 01:58:27`; timezone and exact semantic meaning require ArchiveBot metadata confirmation. |
| Collection end | `UNKNOWN` | Not verified. |
| Crawl seeds, scope, and exclusions | `DEFERRED (>30 min)` | A complete reconstruction requires ArchiveBot job metadata and/or a full WARC metadata audit. It was not run. |
| Archive completeness | `UNKNOWN` | No completeness guarantee exists. The archive may omit pages and resources and may contain failed responses, duplicates, redirects, and non-news content. |

## Initial data collection

The project obtains the WARC URL list from the live ArchiveBot viewer. If the viewer is unavailable, the current downloader falls back to a saved Wayback snapshot of the same job page. WARC shards are downloaded one at a time. A shard is deleted only after processing completes without fatal or write errors; otherwise it is retained for diagnosis or retry.

Selection performed by the current converter includes:

- accepted Apple Daily hostnames and true subdomains;
- article paths whose final component is an exactly 26-character alphanumeric article ID;
- decodable HTML responses that pass article-content validation;
- images whose URL contains the article ID or whose relationship is supported by OG/JSON-LD evidence.

The complete original ArchiveBot harvesting criteria are not present in this repository.

## Source data producers

| Field | Status | Value |
| --- | --- | --- |
| Newspaper content producers | `PARTIAL` | Taiwan Apple Daily journalists, editors, photographers, contributors, and other original publishers produced the source content. A complete creator registry is not available. |
| Machine-generated source elements | `PARTIAL` | Website templates, metadata, tracking parameters, and ArchiveBot/WARC metadata were produced by publishing and archival systems. |
| Producer demographics or identity attributes | `UNKNOWN` | No self-reported demographic register is included. Such attributes must not be inferred from names or content. |

## Digitisation and extraction pipeline

This is a born-digital web-archive transformation rather than scanning/OCR digitisation.

1. Retrieve the WARC URL inventory.
2. Download one WARC shard.
3. Decode HTTP chunked transfer encoding, gzip/deflate content encoding, and declared character sets.
4. Read WARC records with FastWARC and filter candidate article responses.
5. Extract text and metadata with Trafilatura and Beautiful Soup fallbacks.
6. Extract image URLs and captions from HTML elements, OG metadata, and JSON-LD.
7. Scan the WARC again to match and save archived image responses.
8. Clean text, parse bylines and locations, and construct project-profile ninjs 3.2.
9. Write records to the date/ID tree and log duplicate and error decisions.
10. Remove the temporary WARC only after a successful shard summary.

Verified local software environment: Ubuntu 22.04.4 LTS, Python 3.10.12, FastWARC 0.3.2, Beautiful Soup 4.12.3, Trafilatura 2.0.0, ftfy 6.3.1, and requests 2.31.0. The repository does not yet provide a complete pinned dependency lock file for the download pipeline.

## Preprocessing and cleaning

| Operation | Status | Description |
| --- | --- | --- |
| URI canonicalisation | `VERIFIED` | Removes query parameters and fragments. |
| Article identification | `VERIFIED` | Uses only the final 26-character article path component. |
| Text extraction | `VERIFIED` | Uses Trafilatura with `<article>` and metadata fallbacks; candidates must pass content validation. |
| Advertising cleanup | `PARTIAL` | Rule-based removal of known promotional or membership text. False removal and residual advertisements remain possible. |
| Character cleanup | `VERIFIED` | Repairs likely mojibake with ftfy, unescapes HTML entities, normalises special spaces, and removes selected format/control characters. |
| Date normalisation | `VERIFIED` | Chooses evidenced publication metadata in a documented order and converts accepted timestamps to Taiwan time. |
| Byline/location parsing | `PARTIAL` | Deterministic parsing supports multiple separators and exclusion rules. Missing or ambiguous credits remain empty. |
| Image filtering | `PARTIAL` | Retains images supported by article-ID ownership or trusted OG/JSON-LD evidence. Incomplete captures and false associations remain possible. |

No anonymisation, tokenisation, stemming, machine translation, or semantic balancing is performed by the extraction pipeline.

## Generated metadata and annotations

These values are machine-generated metadata, not human-verified gold annotations.

| Field | Status | Producer and validation |
| --- | --- | --- |
| `subjects` | `PARTIAL` | Generated from the URL section. No release-wide comparison with the original editorial taxonomy exists. |
| `firstCreated` | `PARTIAL` | Generated through a deterministic evidence hierarchy. Tests cover representative fallbacks, but a release-wide audit is deferred. |
| `by` and `located` | `PARTIAL` | Generated by deterministic rules from the extracted credit line. No inter-annotator agreement applies. |
| `associations` and captions | `PARTIAL` | Generated from HTML/metadata evidence and matched WARC image responses. Smoke tests and targeted diagnostics exist; full validation is deferred. |
| Annotation process documentation | `VERIFIED` | Rules are implemented in `downloads/` and described in its README and format-difference document. |
| Human annotators | `NOT APPLICABLE` | The current pipeline does not use a human annotation workforce. Targeted developer review is quality assurance, not a published annotation campaign. |
| Crowd labour | `NOT APPLICABLE` | No crowdsourcing platform or paid crowd annotation was used. |
| Full annotation-quality statistics | `DEFERRED (>30 min)` | Requires sampling or full-data validation against archived pages. |

## Provenance and rights

The provenance chain is:

```text
Taiwan Apple Daily publication
    -> ArchiveBot/Archive Team crawl
        -> WARC records and archival hosting
            -> repository extraction and cleaning code
                -> ninjs article records and associated image files
```

Each layer can introduce selection, transformation, technical error, or rights obligations. The repository documents technical provenance but does not establish that the project holds copyright in article text or images.

## Linked open data and controlled vocabularies

| Field | Status | Value |
| --- | --- | --- |
| Linked open data | `NOT APPLICABLE` | No item-level links to external authority files or knowledge graphs are generated. |
| Controlled subject vocabulary | `NOT APPLICABLE` | `subjects.name` stores website sections, not identifiers from a published controlled vocabulary. |
| Structural standard | `PARTIAL` | The project uses a conservative subset based on ninjs 3.2. |
| Language vocabulary | `VERIFIED` structurally | Uses the BCP 47 tag `zh-Hant-TW`, assigned uniformly. |

