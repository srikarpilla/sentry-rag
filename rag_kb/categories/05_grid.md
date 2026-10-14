# Category: grid

Dataset: MVTec AD, category `grid`. Kind: texture (MVTec AD has 10 object and 5 texture categories).

## Defect types in this category
The test folder for `grid` contains 5 defect folder(s). The plain-language readings below are based on the folder names. Look at the sample images in the MVTec AD paper for the exact appearance.

- `bent`: part of the grid is bent
- `broken`: part of the grid is broken
- `glue`: glue residue on the grid
- `metal_contamination`: a metal foreign object
- `thread`: a stray thread

## What the classifier does with this category
- The Sentry QC model only answers "good" or "defective". It does not say which defect type is present and it does not show where the defect is.
- Images of `grid` are part of the training, validation and test data. The test set is the held-out part.
- Category-level accuracy for `grid` is only available if the file `06_per_category_results.md` is in this knowledge base. If it is not, per-category accuracy has not been measured and must not be guessed.

## Questions this file answers
- What defect types exist for grid?
- Is grid an object or a texture category?
- Can the model tell me which defect a grid has? (No: only good or defective.)
