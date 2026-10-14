# Category: transistor

Dataset: MVTec AD, category `transistor`. Kind: object (MVTec AD has 10 object and 5 texture categories).

## Defect types in this category
The test folder for `transistor` contains 4 defect folder(s). The plain-language readings below are based on the folder names. Look at the sample images in the MVTec AD paper for the exact appearance.

- `bent_lead`: a bent lead (leg)
- `cut_lead`: a cut lead (leg)
- `damaged_case`: the case of the transistor is damaged
- `misplaced`: the transistor is missing or in the wrong position; name-based reading

## What the classifier does with this category
- The Sentry QC model only answers "good" or "defective". It does not say which defect type is present and it does not show where the defect is.
- Images of `transistor` are part of the training, validation and test data. The test set is the held-out part.
- Category-level accuracy for `transistor` is only available if the file `06_per_category_results.md` is in this knowledge base. If it is not, per-category accuracy has not been measured and must not be guessed.

## Questions this file answers
- What defect types exist for transistor?
- Is transistor an object or a texture category?
- Can the model tell me which defect a transistor has? (No: only good or defective.)
