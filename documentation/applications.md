# SupportedApplications Object

Parent: [DatasetDocumentation](main.md)

## Object schema

```text
SupportedApplications
├── supportedTasks[]
├── taskMetrics[]
├── suggestedModels[]
├── sharedTasks[]
├── aiCategories[]
├── culturalHeritageApplicationTypes[]
└── applicationExamples[]
```

## Supported tasks

| Field | Status | Value |
| --- | --- | --- |
| Full-text search and information retrieval | `VERIFIED` | Article headlines and bodies can support keyword search, indexing, ranking experiments, and exploratory retrieval. The repository contains a Datasette/SQLite FTS demonstration pipeline. |
| Corpus and discourse analysis | `VERIFIED` | Suitable for exploratory studies of historical news language, topics, people, organisations, and events, subject to archival and editorial biases. |
| Text classification and topic modelling | `PARTIAL` | URL-derived `subjects` can provide weak section labels. They have not been validated as a benchmark gold standard. |
| Named-entity recognition and information extraction | `PARTIAL` | Article text may be used as research material, but the dataset does not provide gold entity annotations. |
| Multimodal retrieval and analysis | `PARTIAL` | Records may associate text with archived images. Image coverage and association quality are incomplete and not benchmarked. |
| Web-archive processing research | `VERIFIED` | The repository documents WARC decoding, extraction fallbacks, media matching, cleaning, and deduplication behaviour. |
| Dataset metrics | `UNKNOWN` | No official task-specific metrics are prescribed. Researchers must define metrics appropriate to their task. |
| Suggested models | `UNKNOWN` | No model is endorsed by the dataset curators. |
| Shared tasks | `NOT APPLICABLE` | The dataset is not documented as part of a formal shared task or challenge. |

## AI categories

| Field | Status | Value |
| --- | --- | --- |
| Natural-language processing | `PARTIAL` | Potential Hugging Face-style tasks include text classification, token classification, question answering, summarisation, and feature extraction. Suitability varies because no benchmark splits or gold labels are supplied. |
| Information retrieval | `VERIFIED` | Full-text and metadata search are direct supported uses. |
| Multimodal and image-text processing | `PARTIAL` | Potential tasks include image-text retrieval and multimodal representation learning, limited by incomplete image capture and association quality. |
| Generative AI training | `PARTIAL` / caution | Technically possible but not an endorsed use. Rights, privacy, memorisation, attribution, and editorial-bias risks must be resolved first. |

## Cultural-heritage application types

| Field | Status | Value |
| --- | --- | --- |
| Collection search | `VERIFIED` | Search and browse over archived newspaper articles. |
| Digital preservation research | `VERIFIED` | Study extraction and transformation from WARC web archives into article-level research data. |
| Metadata enrichment | `PARTIAL` | The pipeline derives publication dates, sections, bylines, locations, and image associations. Derived values are not all manually validated. |
| Historical and media research | `VERIFIED` | Supports contextual and computational study of a major Taiwanese newspaper, without a claim of representativeness. |

## Application examples

| Example | Status | Value |
| --- | --- | --- |
| Datasette demonstration | `PARTIAL` | The repository includes code for a SQLite/Datasette news browser. A stable public deployment URL is not documented. |
| WAC 2025 presentation | `VERIFIED` | The project was presented as a case study in transforming archived webpages into reusable datasets: <https://digital.library.unt.edu/ark:/67531/metadc2472454/>. |
| COSCUP 2025 presentation | `VERIFIED` | A public talk described the preservation and dataset-production work: <https://pretalx.coscup.org/coscup-2025/talk/EJDGTD/>. |
| Published downstream research or trained models | `UNKNOWN` | No verified registry of downstream publications, derivative datasets, notebooks, or models is available. |

