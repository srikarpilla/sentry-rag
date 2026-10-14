# Category: zipper

Dataset: MVTec AD, category `zipper`. Kind: object (MVTec AD has 10 object and 5 texture categories).

## Defect types in this category
The test folder for `zipper` contains 7 defect folder(s). The plain-language readings below are based on the folder names. Look at the sample images in the MVTec AD paper for the exact appearance.

- `broken_teeth`: broken teeth
- `combined`: more than one defect on the same item
- `fabric_border`: a defect on the fabric border
- `fabric_interior`: a defect on the interior fabric
- `rough`: a rough area
- `split_teeth`: split teeth
- `squeezed_teeth`: squeezed teeth

## What the classifier does with this category
- The Sentry QC model only answers "good" or "defective". It does not say which defect type is present and it does not show where the defect is.
- Images of `zipper` are part of the training, validation and test data. The test set is the held-out part.
- Category-level accuracy for `zipper` is only available if the file `06_per_category_results.md` is in this knowledge base. If it is not, per-category accuracy has not been measured and must not be guessed.

## Questions this file answers
- What defect types exist for zipper?
- Is zipper an object or a texture category?
- Can the model tell me which defect a zipper has? (No: only good or defective.)
