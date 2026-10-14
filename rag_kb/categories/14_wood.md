# Category: wood

Dataset: MVTec AD, category `wood`. Kind: texture (MVTec AD has 10 object and 5 texture categories).

## Defect types in this category
The test folder for `wood` contains 5 defect folder(s). The plain-language readings below are based on the folder names. Look at the sample images in the MVTec AD paper for the exact appearance.

- `color`: a color stain or discoloration
- `combined`: more than one defect on the same item
- `hole`: a hole in the wood
- `liquid`: a liquid stain
- `scratch`: a scratch on the surface

## What the classifier does with this category
- The Sentry QC model only answers "good" or "defective". It does not say which defect type is present and it does not show where the defect is.
- Images of `wood` are part of the training, validation and test data. The test set is the held-out part.
- Category-level accuracy for `wood` is only available if the file `06_per_category_results.md` is in this knowledge base. If it is not, per-category accuracy has not been measured and must not be guessed.

## Questions this file answers
- What defect types exist for wood?
- Is wood an object or a texture category?
- Can the model tell me which defect a wood has? (No: only good or defective.)
