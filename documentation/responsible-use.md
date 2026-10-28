# Responsible use

Parent: [Dataset documentation](README.md)

The dataset preserves access to historical news and supports research on media, language, and digital preservation. Its contents reflect both editorial choices and the limitations of web archiving. See [Research applications](applications.md) for potential uses.

## Personal and sensitive information

Articles and images may identify people and cover crime, accidents, health, sexuality, politics, religion, ethnicity, finances, minors, and other sensitive subjects. Historical reporting may include harmful or outdated framing.

**The pipeline does not anonymise the content.** No item-level sensitivity labels are provided, and consent for redistribution or AI training is not established by this documentation. Re-exposing historical material can affect privacy, dignity, and reputation.

No documented institutional privacy assessment, ethics-review determination, or affected-community consultation is available; rights-holder consultation records are incomplete. These gaps should be considered in any proposed reuse.

## Biases and interpretation limits

| Source of bias or error | Implication for users |
| --- | --- |
| Newspaper editorial choices | The collection reflects one commercial news organisation, not a neutral or representative account of society. |
| Archive coverage | Missing periods, pages, or resources affect inclusion. Article counts are not direct measures of real-world event frequency. |
| Page layouts and extraction | Some periods and formats are easier to parse. Text may be missing, truncated, duplicated, or reduced to metadata descriptions. |
| Cleaning rules | Advertising may remain, and legitimate text may be removed. |
| Duplicate handling | Historical versions use different rules; current date-and-ID keys can retain the same ID under different dates. Do not assume `altIds` is universally unique. |
| Missing or inferred metadata | Empty bylines or locations may reflect parser failure, not absence in the source. Dates may rely on fallbacks. |
| Image selection | Only captured and matched images are available; complete page reconstruction is not supported. |
| Language labels | `zh-Hant-TW` is assigned uniformly, without item-level language detection. |

Bias has not been quantified across the full release, and the pipeline does not rebalance the collection or remove editorial bias. Historical quality estimates may not describe the latest output. See [Composition and fields](composition.md) for field definitions and version-specific statistics.

## Reuse considerations

- Validate samples against archived pages and account for missingness, duplicates, and uneven coverage in the research design.
- Preserve source and version information, and distinguish publication dates from capture and processing dates.
- Do not treat extracted metadata as verified facts about a person, or infer sensitive attributes from names or images without an appropriate ethical basis.
- Avoid consequential decisions, individual risk scores, or political profiling based on this collection.
- Assess rights and privacy before redistributing content or training models. The code's MIT licence does not license the news material; see [Distribution and licensing](distribution.md).

## Reporting concerns and reuse

Send rights, privacy, or sensitive-content concerns to [data.contact@depositar.io](mailto:data.contact@depositar.io). Technical issues can be reported through [GitHub Issues](https://github.com/jimmy93029/appledaily_warc_file_scrawler/issues); do not include personal or sensitive information in public reports.

A formal takedown and incident-response procedure is not yet established. There is no verified register or systematic monitoring of downstream or unexpected uses; users are encouraged to report reuse to the project contacts.
