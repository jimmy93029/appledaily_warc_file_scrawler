# Collection and processing

Parent: [Dataset documentation](main.md)

The dataset transforms archived Taiwan Apple Daily web pages into structured news records and associated images. It supports preservation and research access after the source website became unavailable. The source material was born digital; no scanning or OCR is involved.

## Processing overview

```mermaid
flowchart TD
    A["Archived Apple Daily web pages"] --> B["Select article pages"]
    B --> C["Extract text and metadata"]
    B --> D["Identify images and captions"]
    C --> E["Clean text and standardise fields"]
    D --> F["Match images in the archive"]
    E --> G["Combine article records and images"]
    F --> G
    G --> H["Resolve duplicates and organise by date"]
    H --> I["ninjs JSON records and image files"]
```

This overview describes the V3 pipeline. The diagram shows the main data transformations; implementation details and the applicable code version are linked at the end.

**The result is not a complete collection of all Taiwan Apple Daily news.** Missing captures, extraction errors, and cleaning rules affect which articles and images are available.

## Source and collection

| Item | Description |
| --- | --- |
| Original material | Taiwan Apple Daily news pages, images, and related web resources. |
| Archive provider | ArchiveBot / Archive Team. |
| Source archive | [ArchiveBot job `202209030158271bpf8`](https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8). |
| Archive format | WARC files containing captured web responses. |
| Archive inventory | 804 numbered WARC shards, plus `meta.warc.gz`. |
| Approximate size | About 4.33 TB according to the existing archive description; exact bytes and unit convention have not been confirmed. |
| Capture period | The job identifier contains `2022-09-03 01:58:27`; its timezone and meaning require confirmation. The collection end is not verified. |
| Coverage | Incomplete. The original crawl seeds, scope, and exclusion rules have not been fully established. |

The project retrieves the archive file list from the ArchiveBot viewer, with a saved Wayback snapshot as a fallback. It selects supported Apple Daily article pages and extracts their content from the archived responses.

### Who produced the source material?

| Contributor | Role |
| --- | --- |
| Journalists, editors, photographers, and other contributors | Produced the original news text and images. A complete creator registry is unavailable. |
| Website publishing systems | Generated page layouts and embedded metadata. |
| ArchiveBot / Archive Team | Captured web resources and recorded archival metadata. |

No self-reported demographic register of source creators is included. Identity attributes should not be inferred from names or content.

## Preprocessing and cleaning

| What is processed? | What changes? | What should users know? |
| --- | --- | --- |
| Article URLs and IDs | Tracking parameters and fragments are removed; article IDs are extracted from supported URL paths. | Selection depends on recognised website and URL structures. |
| Article text | Text is extracted from page content, with alternative extraction sources when needed. | Some records may contain only a metadata description rather than the full article. |
| Promotional text | Known promotional or membership text is removed using rules. | Some advertising may remain, and legitimate text may be removed. |
| Characters and spacing | Likely encoding errors, HTML entities, unusual spaces, and selected control characters are cleaned. | These operations repair text artifacts; they do not guarantee error-free transcription. |
| Dates | Publication evidence is prioritised and accepted timestamps are normalised to Taiwan time. | A valid URL date may supply a fallback publication date. Capture time is distinct from publication time. |
| Bylines and locations | Rules parse the source credit line into separate fields. | Missing or ambiguous values remain empty; parsing errors are possible. |
| Images and captions | Page evidence identifies candidate images, which are matched to archived image responses. | Matching is limited to the same WARC shard. Missing captures and incorrect associations remain possible. |
| Duplicate articles | Repeated article responses are merged within a shard; competing records at the same date-and-ID output location are resolved. | The same ID under different dates can remain in the dataset. |

The pipeline does not anonymise, translate, tokenise, stem, or semantically balance the article content.

## Output and generated metadata

Each article is stored as a project-profile ninjs 3.2 JSON record, with available images, under `YEAR/MONTH/DAY/ARTICLE_ID/`.

The directory date may fall back to the capture date when publication evidence is unavailable. This does not turn the capture date into an asserted publication date.

| Field | Source | Validation limit |
| --- | --- | --- |
| `subjects` | Website section in the article URL. | Not a validated editorial taxonomy or gold topic label. |
| `firstCreated` | Prioritised publication evidence, with a URL-date fallback. | No release-wide validation is available. |
| `by`, `located` | Rules applied to the extracted credit line. | Not manually verified for every article. |
| `associations` and captions | Page metadata and matched archived images. | Image coverage and caption accuracy are not guaranteed. |
| `language` | Uniformly assigned `zh-Hant-TW`. | No item-level language detection was performed. |

These are automatically generated metadata, not human-verified gold annotations. There is no human annotation workforce or crowdsourcing process. Targeted developer checks do not constitute full-dataset validation.

The output uses a subset based on ninjs 3.2. It does not add item-level links to external authority files or knowledge graphs, and website sections are not mapped to a controlled subject vocabulary.

## Provenance and rights

| Stage | Role in the dataset |
| --- | --- |
| Taiwan Apple Daily publication | Source of the original text, images, and editorial context. |
| ArchiveBot capture | Preserves a subset of web resources and capture metadata. |
| Extraction and cleaning | Selects and transforms archived content into structured records. |
| Derived dataset | Contains ninjs article records and associated archived images. |

Selection and transformation at each stage affect the final dataset. Documenting this provenance does not establish that the project holds copyright in the original article text or images.

## Version and technical references

This description applies to **V3**, tag **`dataset-v3`**, commit [`4acdaa18db98c701ba90ce3a2a9beb191f0a7f40`](https://github.com/jimmy93029/appledaily_warc_file_scrawler/tree/4acdaa18db98c701ba90ce3a2a9beb191f0a7f40). A dataset release should separately record the code version actually used to produce it.

- [Pipeline documentation and software requirements](../downloads/README.md)
- [ninjs format and field differences](../downloads/NINJS_FORMAT_DIFF.md)
- [Tests and diagnostic tools](../smoke-test/README.md)
- [Extraction and image matching](../downloads/extract_warc2.py)
- [Text cleaning and date rules](../downloads/final_cleaning_rules.py)
- [Output organisation and duplicate selection](../downloads/organize_deduplicate.py)

The download pipeline does not yet provide a complete pinned dependency lock file.
