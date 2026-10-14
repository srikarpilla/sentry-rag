# Category: bottle

Dataset: MVTec AD, category `bottle`. Kind: object (MVTec AD has 10 object and 5 texture categories).

## Defect types in this category
The test folder for `bottle` contains 3 defect folder(s). The plain-language readings below are based on the folder names. Look at the sample images in the MVTec AD paper for the exact appearance.

- `broken_large`: a large piece broken off the bottle
- `broken_small`: a small piece broken off the bottle
- `contamination`: foreign material on the bottle

## What the classifier does with this category
- The Sentry QC model only answers "good" or "defective". It does not say which defect type is present and it does not show where the defect is.
- Images of `bottle` are part of the training, validation and test data. The test set is the held-out part.
- Category-level accuracy for `bottle` is only available if the file `06_per_category_results.md` is in this knowledge base. If it is not, per-category accuracy has not been measured and must not be guessed.

## Questions this file answers
- What defect types exist for bottle?
- Is bottle an object or a texture category?
- Can the model tell me which defect a bottle has? (No: only good or defective.)
