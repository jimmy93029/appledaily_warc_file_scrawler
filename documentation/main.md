# Apple Daily Taiwan Dataset Documentation

This directory documents the Apple Daily Taiwan Web Archive Dataset as a set of linked objects. It follows the dimensions in the *Datasheet for Digital Cultural Heritage Datasets, Version 2* and the recommendations in *Dataset Context(ualisation) in Documentation: Best Practices, Recommendations and Open Questions*.

## Status vocabulary

| Status | Meaning |
| --- | --- |
| `VERIFIED` | Supported by repository code, Git history, a local comparison report, or a cited public source. |
| `PARTIAL` | Some evidence is available, but the field is not complete for a formal dataset release. |
| `UNKNOWN` | The information is not available in the repository or reviewed sources. It must not be inferred. |
| `NOT APPLICABLE` | The field does not apply to this dataset. |
| `DEFERRED (>30 min)` | The field exists, but completing it requires a full-data or full-WARC audit estimated to exceed 30 minutes. The audit was not run. |
| `HUMAN DECISION REQUIRED` | The value requires an authorised person or institution to make a policy or rights decision. |

## DatasetDocumentation object

```text
DatasetDocumentation
├── description: Description
│   ├── identity
│   ├── people and organisations
│   └── references
├── applications: SupportedApplications
│   ├── supported tasks
│   ├── AI categories
│   └── cultural-heritage applications
├── distribution: Distribution
│   ├── access
│   ├── rights and licensing
│   ├── formats
│   └── citation
├── composition: Composition
│   ├── categories and object types
│   ├── structure and fields
│   ├── standards and language
│   └── descriptive statistics
├── collectionProcess: CollectionProcess
│   ├── source and selection
│   ├── digitisation and extraction
│   ├── preprocessing and generated metadata
│   └── provenance and vocabularies
├── lifecycle: Lifecycle
│   ├── versions and releases
│   ├── checksums
│   └── maintenance
└── responsibleUse: ResponsibleUse
    ├── sensitive information
    ├── biases and limitations
    ├── societal impact
    └── known and unanticipated uses
```

## Child documents

| Object | Scope | Document |
| --- | --- | --- |
| `Description` | Title, summary, homepage, publisher, curators, contributors, contact, and references | [description.md](description.md) |
| `SupportedApplications` | Intended tasks, AI categories, cultural-heritage applications, and examples | [applications.md](applications.md) |
| `Distribution` | Data access, licensing, file formats, restrictions, and citation | [distribution.md](distribution.md) |
| `Composition` | Dataset category, media, object types, schema, fields, language, splits, and statistics | [composition.md](composition.md) |
| `CollectionProcess` | Source data, ArchiveBot collection, extraction, cleaning, generated metadata, and provenance | [collection-process.md](collection-process.md) |
| `Lifecycle` | Version history, release dates, checksums, maintenance, and update periodicity | [lifecycle.md](lifecycle.md) |
| `ResponsibleUse` | Sensitive content, biases, societal impact, suitable uses, limitations, and reuse | [responsible-use.md](responsible-use.md) |

## High-level completeness

The technical description, extraction pipeline, field structure, historical code versions, and general limitations are substantially documented. Formal publication metadata remains incomplete: there is no verified dataset access URL, dataset licence, publisher, persistent dataset identifier, release checksum set, maintenance commitment, or designated dataset contact.

No task marked `DEFERRED (>30 min)` was executed while producing these documents.

## Framework references

- Alkemade et al., *Datasheet for Digital Cultural Heritage Datasets, Version 2*, DOI: <https://doi.org/10.5281/zenodo.15828222>
- Alkemade et al., *Dataset Context(ualisation) in Documentation: Best Practices, Recommendations and Open Questions*, DOI: <https://doi.org/10.5334/johd.571>
- Alkemade et al., *Datasheets for Digital Cultural Heritage Datasets*, DOI: <https://doi.org/10.5334/johd.124>

