# Description Object

Parent: [DatasetDocumentation](main.md)

## Object schema

```text
Description
├── title
├── summary
├── homepage
├── publisher
├── datasetCurators[]
├── otherContributors[]
├── pointOfContact
└── references[]
```

## Identity

| Field | Status | Value |
| --- | --- | --- |
| Title | `VERIFIED` | Apple Daily Taiwan Web Archive Dataset |
| Alternative title | `VERIFIED` | Taiwan Apple Daily Web Archive Dataset |
| Brief description | `VERIFIED` | A research dataset produced by extracting news text, metadata, and associated images from ArchiveBot WARC captures of the Taiwan Apple Daily website and serialising article records as project-profile ninjs JSON. |
| Domain | `VERIFIED` | Digital cultural heritage, web archives, newspapers, news data, and research data management. |
| Topics and genres | `PARTIAL` | Taiwan and international news, politics, society, local news, finance, entertainment, sport, lifestyle, and other website sections. A controlled topic inventory has not been published. |
| Temporal coverage | `VERIFIED` | 2003–2022, based on the documented publication-year range. Exact minimum and maximum timestamps for the current release require a full audit. |
| Geographic coverage | `PARTIAL` | The publisher and primary context are Taiwanese. Article content includes international coverage. No normalised item-level geographic coverage is provided. |
| Homepage | `UNKNOWN` | No formal dataset homepage has been designated. The GitHub repository is a code and documentation location, not a verified dataset landing page. |

## Motivation and creation context

| Field | Status | Value |
| --- | --- | --- |
| Purpose | `VERIFIED` | Preserve and make computationally usable historical Taiwan Apple Daily news recovered from a web archive after the source website became unavailable. |
| Intended audience | `PARTIAL` | Digital-humanities researchers, journalism and media researchers, information-retrieval researchers, NLP and multimodal researchers, archivists, educators, and students. No formal user-needs study is recorded. |
| Gap addressed | `VERIFIED` | The source website is no longer reliably accessible, and the ArchiveBot WARC collection is not directly convenient for article-level research. |
| Funding interests | `UNKNOWN` | No funding statement for dataset production is recorded in the repository. |
| Creating entity | `PARTIAL` | Public presentations associate the work with the Institute of Information Science, Academia Sinica, and Hung-Yen Wu also with National Yang Ming Chiao Tung University. The formal entity responsible for publishing the dataset has not been designated. |

## People and organisations

| Field | Status | Value |
| --- | --- | --- |
| Publisher | `UNKNOWN` / `HUMAN DECISION REQUIRED` | No individual or organisation has been formally identified as the dataset publisher. |
| Dataset curator: Hung-Yen (Jimmy) Wu | `PARTIAL` | Repository history supports responsibility for WARC processing, extraction code, data processing, and technical documentation. Affiliation reported publicly: Institute of Information Science, Academia Sinica; College of Computer Science, National Yang Ming Chiao Tung University. A curator-approved positionality statement is not available. |
| Dataset curator: Chia-Hsun Ally Wang | `PARTIAL` | Co-author of the WAC 2025 presentation; publicly affiliated with the Institute of Information Science, Academia Sinica. Exact dataset-curation responsibilities require confirmation. |
| Dataset curator: Tyng-Ruey Chuang | `PARTIAL` | Co-author of the WAC 2025 presentation; publicly affiliated with Academia Sinica. Exact dataset-curation and supervision responsibilities require confirmation. |
| Other contributor: Weiqi | `UNKNOWN` | The supplied draft attributes dataset checking, version comparison, and dataset description work, but a complete name, affiliation, and approved contribution statement are unavailable. |
| Other contributors | `UNKNOWN` | No complete contributor register or CRediT-style statement exists. |
| Point of contact | `UNKNOWN` / `HUMAN DECISION REQUIRED` | GitHub Issues can receive code-related reports. No reliable dataset, rights, privacy, or takedown contact has been designated. |

## Papers and other references

| Reference | Status | URL |
| --- | --- | --- |
| Source repository | `VERIFIED` | <https://github.com/jimmy93029/appledaily_warc_file_scrawler> |
| ArchiveBot job | `VERIFIED` | <https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8> |
| Work log | `VERIFIED` | <https://hackmd.io/@jimmywupika/HyfuxFiF6> |
| Dataset comparison report | `VERIFIED` | <https://hackmd.io/mSNYQ4PjT1-MjO9IztENLw> |
| WAC 2025 presentation PID | `VERIFIED` | <https://pid.depositar.io/ark:37281/k5p3h9k37> |
| WAC 2025 presentation record | `VERIFIED` | <https://digital.library.unt.edu/ark:/67531/metadc2472454/> |
| WAC 2025 video | `VERIFIED` | <https://digital.library.unt.edu/ark:/67531/metadc2537183/> |
| COSCUP 2025 talk | `VERIFIED` | <https://pretalx.coscup.org/coscup-2025/talk/EJDGTD/> |

The WAC presentation PID identifies presentation materials and related code. It is not currently verified as the persistent identifier of the complete dataset.

