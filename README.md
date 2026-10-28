# Taiwan Apple Daily Web Archive Dataset Tools

This repository converts Taiwan Apple Daily WARC web archives preserved by ArchiveBot into news text, metadata, and images for research. The current converter produces a project profile based on **ninjs 3.2**, with Git tags preserving the V1, V2, and V3 code history.

> [!IMPORTANT]
> The code in this repository is licensed under the MIT License. This licence does not cover the original WARC files, news text, images, or original content included in the output dataset. Dataset access, usage conditions, and formal citation information are documented separately in [Distribution and licensing](documentation/distribution.md).

## Dataset at a glance

| Item | Value |
| --- | --- |
| Source | [ArchiveBot job `202209030158271bpf8`](https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8) |
| Coverage | 2003–2022 |
| Language tag | Traditional Chinese (`zh-Hant-TW`); assigned uniformly, without item-level language detection |
| Current code | V3 / `dataset-v3` / `4acdaa1` |
| Current output | ninjs 3.2 JSON and archived images |
| Layout | `YEAR/MONTH/DAY/ARTICLE_ID/` |
| Archive inventory | 804 numbered WARC shards (`00000`–`00803`) plus `meta.warc.gz` |

The dataset is reconstructed from archived web pages, not exported from Apple Daily's original database. Archive coverage, page layouts, extraction, cleaning, and deduplication rules affect the results. The dataset should not be described as a complete collection of all historical articles.

## Documentation

The English dataset documentation is organised into linked sections:

- **Documentation index:** [documentation/main.md](documentation/main.md)
- [Description](documentation/description.md)
- [Supported applications](documentation/applications.md)
- [Distribution and licensing](documentation/distribution.md)
- [Composition, fields, and statistics](documentation/composition.md)
- [Collection and processing](documentation/collection-process.md)
- [Versioning and maintenance](documentation/lifecycle.md)
- [Responsible use, ethics, and limitations](documentation/responsible-use.md)

Documentation status labels distinguish `VERIFIED`, `PARTIAL`, `UNKNOWN`, `NOT APPLICABLE`, `DEFERRED (>30 min)`, and `HUMAN DECISION REQUIRED`.

## Repository layout

```text
.
├── documentation/   # Dataset datasheet and responsible-use documentation
├── downloads/       # WARC download, extraction, cleaning, and deduplication
├── smoke-test/      # Pipeline tests, diagnostics, and archive audits
└── dataset/         # Optional Datasette/SQLite presentation tooling
```

See [downloads/README.md](downloads/README.md) for technical details, [downloads/NINJS_FORMAT_DIFF.md](downloads/NINJS_FORMAT_DIFF.md) for ninjs format changes, and [smoke-test/README.md](smoke-test/README.md) for tests and audits.

## Point of Contact

| Contact | Enquiries | Contact method |
| --- | --- | --- |
| **Technical contact: Hung-Yen (Jimmy) Wu** | Code usage, extraction and cleaning workflows, bug reports, and reproducibility. | [GitHub Issues](https://github.com/jimmy93029/appledaily_warc_file_scrawler/issues) |
| **Administrative contact: depositar team** | Dataset access, publication, licensing enquiries, and rights or privacy concerns. | [data.contact@depositar.io](mailto:data.contact@depositar.io) |

Please send enquiries containing personal or other sensitive information by email rather than posting them in public issues.

## AI collaboration

The code and documentation in this project were developed collaboratively by **Jimmy Wu and AI tools**. AI tools contributed to drafting and revising both the code and the documentation.

## Requirements

The verified local environment uses Ubuntu 22.04, Python 3.10, FastWARC 0.3.2, Beautiful Soup 4.12.3, Trafilatura 2.0.0, ftfy 6.3.1, and requests 2.31.0. Downloading WARC files also requires `axel`.

The download pipeline does not yet have a complete dependency lock file. To install the verified package versions:

```bash
python3 -m venv .venv
.venv/bin/pip install \
  FastWARC==0.3.2 beautifulsoup4==4.12.3 requests==2.31.0 \
  trafilatura==2.0.0 ftfy==6.3.1
```

## Quick start

Create a new output root and test with a small number of WARC shards:

```bash
mkdir -p /mnt/data/appledaily_v3_new

PYTHONPATH=downloads .venv/bin/python downloads/main.py \
  --start 0 --end 2 \
  --connect 5 \
  --output /mnt/data/appledaily_v3_new
```

`--end` is exclusive, so this example processes shards 0 and 1. Processing all shards requires `--start 0 --end 804` and substantial time and storage. Before a full run, check the output path, available storage, logging, and restart strategy.

## Versions

| Dataset | Git reference | Summary |
| --- | --- | --- |
| V1 | `dataset-v1` / `f747ffd` | 2024 text extraction and advertising cleanup |
| V2 | `dataset-v2` / `da0438d` | Image and Datasette/SQLite tooling expansion |
| V3 | `dataset-v3` / `4acdaa1` | Current WARC decoding, date recovery, image association, ninjs 3.2, and deduplication |

```bash
git checkout dataset-v3
```

The `master` branch continues to evolve and may differ from the code used to produce a historical dataset. Record both the tag and commit when reproducing or citing a specific version.

## Licence and citation

This repository includes an [MIT License](LICENSE) for the project code. Third-party components remain subject to their respective licences. The code licence does not grant the same permissions for the original WARC files, news text, images, or original content included in the output dataset.

The dataset's formal citation and persistent identifier remain to be confirmed. Code and dataset citations should be handled separately.

When citing the code, include at least the repository, tag, commit, and access date:

```text
jimmy93029/appledaily_warc_file_scrawler,
dataset-v3, commit 4acdaa1, accessed YYYY-MM-DD.
```
