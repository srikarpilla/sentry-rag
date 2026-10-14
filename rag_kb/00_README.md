# Sentry QC knowledge base

Documents for a question-answering assistant about the Sentry QC defect classifier.

- `01_project_overview.md`: what the project is and how it works end to end.
- `02_model_card.md`: model, training setup, data splits, all measured results.
- `03_how_to_read_results.md`: how to interpret a prediction (P(good), threshold, uncertain).
- `04_limitations_and_risks.md`: what the model cannot do and where numbers can mislead.
- `05_dataset_overview.md`: facts about the MVTec AD dataset.
- `categories/`: one file per product category (15 files).
- `06_per_category_results.md`: added by running `per_category_report.py` (not included until you do).
- `90_sources.md`: where the facts come from.

Chunking tip: split on `##` headings, keep the file name and heading as metadata, and show the file name as the source in every answer.
