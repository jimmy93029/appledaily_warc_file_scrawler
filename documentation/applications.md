# Research applications

Parent: [Dataset documentation](README.md)

The collection supports exploratory research on archived news. Suitability depends on the research question, data quality, and applicable rights; listing a use here does not grant permission to use the content.

## Potential uses

| Application | What the data supports | Main limitation |
| --- | --- | --- |
| Search and information retrieval | Keyword search, indexing, ranking, and browsing by metadata. | Coverage and extracted text are incomplete. |
| Historical, media, and corpus research | Study of news language, topics, people, organisations, and events. | One newspaper and an incomplete archive are not representative of Taiwanese society. |
| Classification and topic modelling | Exploration using article text and URL-derived section labels. | Section labels are not validated gold annotations. |
| Information extraction and NLP | Named-entity extraction, question answering, summarisation, and related experiments. | No gold entity annotations or benchmark evaluation sets are provided. |
| Image-text research | Retrieval and analysis of articles with associated images. | Image coverage and association quality are incomplete. |
| Digital preservation and metadata research | Study of WARC extraction, cleaning, metadata enrichment, and data quality. | Derived metadata requires validation against archived source pages. |

The dataset supplies no official train/validation/test splits, evaluation metrics, recommended models, or formal shared task. Researchers must design and document their own evaluation. Generative AI training is not an endorsed use; rights, privacy, memorisation, attribution, and bias require assessment. See [Responsible use](responsible-use.md).

## Demonstrations and reuse

The repository includes [SQLite/Datasette display tools](../dataset/) for browsing the collection; no stable public deployment is documented. The [WAC 2025 presentation](https://digital.library.unt.edu/ark:/67531/metadc2472454/) and [COSCUP 2025 talk](https://pretalx.coscup.org/coscup-2025/talk/EJDGTD/) describe the project, rather than demonstrating independent downstream reuse.

No verified register of downstream publications, derivative datasets, or trained models is available. Reuse reports may be sent to the [project contacts](distribution.md#point-of-contact).
