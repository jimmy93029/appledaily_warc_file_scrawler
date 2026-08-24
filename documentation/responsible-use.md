# ResponsibleUse Object

Parent: [DatasetDocumentation](main.md)

## Object schema

```text
ResponsibleUse
├── ethicalConsiderations
│   ├── personalAndSensitiveInformation
│   ├── biases[]
│   └── societalImpact
├── suitableUses[]
├── unsuitableUses[]
├── knownReuseExamples[]
├── knownNonEthicalLimitations[]
└── unanticipatedUses[]
```

## Personal and sensitive information

| Field | Status | Value |
| --- | --- | --- |
| Identifiable people | `VERIFIED` | News text and images may directly identify living or deceased people by name, image, occupation, location, or event involvement. |
| Sensitive subjects | `VERIFIED` | Content may concern crime, accidents, health, disability, sexual matters, political opinions, religion, ethnicity, labour activity, finances, minors, and vulnerable groups. |
| Identity categories | `PARTIAL` | Source articles may state or imply identity attributes. The extraction pipeline does not create a validated identity-category annotation layer. Users must not infer sensitive attributes from names, images, or indirect signals without an appropriate ethical basis. |
| Anonymisation | `NOT APPLICABLE` as a performed step | The project does not anonymise article text or images. This fact increases privacy and redistribution risk; it does not mean anonymisation is unnecessary for a particular reuse. |
| Consent | `UNKNOWN` | The dataset documentation does not establish consent from people mentioned or depicted for archival redistribution or AI training. |
| Privacy-law assessment | `UNKNOWN` / `HUMAN DECISION REQUIRED` | No documented legal or institutional privacy assessment is available. |
| Difficult history | `PARTIAL` | The collection documents politically and socially sensitive events and may reproduce harmful, sensational, discriminatory, or outdated framing. No item-level sensitivity labels are provided. |

## Biases

| Bias | Status | Description |
| --- | --- | --- |
| Archival coverage bias | `VERIFIED` | The ArchiveBot crawl may omit periods, sections, pages, embedded resources, or failed responses. Crawl frequency and link discovery affect inclusion. |
| Source/editorial bias | `VERIFIED` | The dataset represents one commercial news organisation's editorial priorities, language, framing, audience, and production practices. |
| Temporal and layout bias | `VERIFIED` | Website template changes make some periods and content types easier to extract than others. |
| Parsing bias | `VERIFIED` | URL rules, HTML selectors, extraction fallbacks, and minimum-content checks determine which pages become records. |
| Cleaning bias | `VERIFIED` | Rule-based advertising removal can remove legitimate text or leave promotional text behind. |
| Deduplication bias | `VERIFIED` | Historical title- or ID-based decisions can merge or retain records incorrectly. Current date/ID keys can miss cross-date duplicates. |
| Missing-metadata bias | `VERIFIED` | Empty `by` or `located` values can reflect missing source metadata, layout differences, or parser failure. They must not be interpreted simply as absence in the original article. |
| Image-selection bias | `VERIFIED` | Images are retained only when archived and supported by selected evidence. External or lazily loaded media may be absent. |
| Language-labelling bias | `VERIFIED` | All records receive `zh-Hant-TW`; code-switching, quoted languages, and non-Chinese articles are not detected item by item. |
| Bias quantification | `DEFERRED (>30 min)` | A release-wide and period-stratified analysis requires a full dataset audit and a defined research methodology. Not run. |
| Bias mitigation | `PARTIAL` | The project documents limitations and uses conservative extraction evidence. It does not rebalance historical content or claim to remove editorial bias. |

## Potential societal impact

### Potential benefits

- Preserve access to an unavailable Taiwanese news source.
- Enable research on language, journalism, politics, society, popular culture, and digital preservation.
- Support low-resource Traditional Chinese and Taiwan-focused information-retrieval research.
- Make web-archive transformation methods inspectable and reproducible.

### Potential risks

- Renewed exposure of sensitive or harmful historical reporting.
- Privacy, dignity, reputational, and re-identification harms to people named or pictured.
- Copyright infringement through redistribution or model training without authority.
- Amplification of source editorial biases in search systems, classifiers, or generative models.
- False historical conclusions caused by treating crawl coverage as a representative publication sample.
- Confident but incorrect metadata produced from extraction errors.

| Field | Status | Value |
| --- | --- | --- |
| Impacted-community consultation | `UNKNOWN` | No documented consultation with people or communities represented in the news corpus is available. |
| Institutional ethics review | `UNKNOWN` | No ethics-review determination is recorded. |
| Rights-holder consultation | `UNKNOWN` | No complete record is available. |

## Suitable uses

- Exploratory Taiwan news-text analysis.
- Historical, journalism, media, and digital-humanities research.
- Information retrieval and full-text search research.
- Web-archive extraction, preservation, and data-quality research.
- NLP or multimodal research that explicitly accounts for rights, incompleteness, and bias.
- Teaching about WARC, structured news metadata, provenance, and responsible dataset documentation.

Suitability remains dependent on the research question, legal authority, ethical review, and validation appropriate to the task.

## Unsuitable or high-risk uses

- Claiming complete coverage of all Taiwan Apple Daily publications from 2003–2022.
- Treating article counts as direct measures of real-world event frequency.
- Treating missing metadata as evidence that the source article lacked that information.
- Treating `altIds` as universally unique without release-level deduplication.
- Requiring verbatim reconstruction of the original webpage or complete image coverage.
- Making consequential decisions, risk scores, political profiles, identity inferences, or assessments of named people.
- Publicly redistributing text or images, or training commercial models, without resolving rights and privacy obligations.
- Using the collection as a neutral or representative account of Taiwanese society.

## Known reuse examples

| Field | Status | Value |
| --- | --- | --- |
| WAC 2025 presentation | `VERIFIED` as project documentation | Demonstrated the conversion of archived webpages into reusable article collections. |
| COSCUP 2025 talk | `VERIFIED` as project documentation | Discussed preservation and dataset construction. |
| Downstream publications using the released data | `UNKNOWN` | No verified reuse registry exists. |
| Derived datasets | `UNKNOWN` | No verified public register exists. |
| Models trained on the dataset | `UNKNOWN` | No verified public register exists. |

## Known non-ethical limitations

- Archive coverage is incomplete and not a known statistical sample.
- The dataset combines source content with crawl, extraction, cleaning, and deduplication effects.
- Historical versions use different schemas and processing rules.
- Date fields can be missing or derived from fallbacks.
- Article IDs are not safe as an unconditional primary key across all historical artefacts.
- Text extraction can be empty, truncated, duplicated, or contaminated by boilerplate.
- Image capture and article association are incomplete.
- Historical estimates for missing bylines, locations, replacement characters, and duplicate IDs may not describe the newest output.
- Formal release statistics and checksums are not yet reconciled.

## Unanticipated uses

| Field | Status | Value |
| --- | --- | --- |
| Known unanticipated uses | `UNKNOWN` | No monitoring or user-reporting mechanism records unexpected uses. |
| Positive unforeseen uses | `UNKNOWN` | Users are encouraged to report responsible reuse through a future designated contact. |
| Harmful unforeseen uses | `UNKNOWN` | A takedown and incident-response process has not been established. |

