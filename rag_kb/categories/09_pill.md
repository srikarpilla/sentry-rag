# Category: pill

Dataset: MVTec AD, category `pill`. Kind: object (MVTec AD has 10 object and 5 texture categories).

## Defect types in this category
The test folder for `pill` contains 7 defect folder(s). The plain-language readings below are based on the folder names. Look at the sample images in the MVTec AD paper for the exact appearance.

- `color`: a color defect
- `combined`: more than one defect on the same item
- `contamination`: foreign material on the pill
- `crack`: a crack in the pill
- `faulty_imprint`: the imprint is wrong or damaged
- `pill_type`: a different type of pill than expected; name-based reading
- `scratch`: a scratch on the surface

## What the classifier does with this category
- The Sentry QC model only answers "good" or "defective". It does not say which defect type is present and it does not show where the defect is.
- Images of `pill` are part of the training, validation and test data. The test set is the held-out part.
- Category-level accuracy for `pill` is only available if the file `06_per_category_results.md` is in this knowledge base. If it is not, per-category accuracy has not been measured and must not be guessed.

## Questions this file answers
- What defect types exist for pill?
- Is pill an object or a texture category?
- Can the model tell me which defect a pill has? (No: only good or defective.)
