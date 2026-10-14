# Category: capsule

Dataset: MVTec AD, category `capsule`. Kind: object (MVTec AD has 10 object and 5 texture categories).

## Defect types in this category
The test folder for `capsule` contains 5 defect folder(s). The plain-language readings below are based on the folder names. Look at the sample images in the MVTec AD paper for the exact appearance.

- `crack`: a crack in the capsule
- `faulty_imprint`: the printed imprint is wrong or damaged
- `poke`: the capsule is poked or punctured
- `scratch`: a scratch on the surface
- `squeeze`: the capsule is squeezed or deformed

## What the classifier does with this category
- The Sentry QC model only answers "good" or "defective". It does not say which defect type is present and it does not show where the defect is.
- Images of `capsule` are part of the training, validation and test data. The test set is the held-out part.
- Category-level accuracy for `capsule` is only available if the file `06_per_category_results.md` is in this knowledge base. If it is not, per-category accuracy has not been measured and must not be guessed.

## Questions this file answers
- What defect types exist for capsule?
- Is capsule an object or a texture category?
- Can the model tell me which defect a capsule has? (No: only good or defective.)
