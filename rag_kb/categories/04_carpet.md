# Category: carpet

Dataset: MVTec AD, category `carpet`. Kind: texture (MVTec AD has 10 object and 5 texture categories).

## Defect types in this category
The test folder for `carpet` contains 5 defect folder(s). The plain-language readings below are based on the folder names. Look at the sample images in the MVTec AD paper for the exact appearance.

- `color`: a color stain or discoloration
- `cut`: a cut in the carpet
- `hole`: a hole in the carpet
- `metal_contamination`: a metal foreign object
- `thread`: a loose or stray thread

## What the classifier does with this category
- The Sentry QC model only answers "good" or "defective". It does not say which defect type is present and it does not show where the defect is.
- Images of `carpet` are part of the training, validation and test data. The test set is the held-out part.
- Category-level accuracy for `carpet` is only available if the file `06_per_category_results.md` is in this knowledge base. If it is not, per-category accuracy has not been measured and must not be guessed.

## Questions this file answers
- What defect types exist for carpet?
- Is carpet an object or a texture category?
- Can the model tell me which defect a carpet has? (No: only good or defective.)
