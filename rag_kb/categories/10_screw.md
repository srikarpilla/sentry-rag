# Category: screw

Dataset: MVTec AD, category `screw`. Kind: object (MVTec AD has 10 object and 5 texture categories).

## Defect types in this category
The test folder for `screw` contains 5 defect folder(s). The plain-language readings below are based on the folder names. Look at the sample images in the MVTec AD paper for the exact appearance.

- `manipulated_front`: the front of the screw has been altered; name-based reading
- `scratch_head`: a scratch on the screw head
- `scratch_neck`: a scratch on the screw neck
- `thread_side`: damage on the side of the thread
- `thread_top`: damage at the top of the thread

## What the classifier does with this category
- The Sentry QC model only answers "good" or "defective". It does not say which defect type is present and it does not show where the defect is.
- Images of `screw` are part of the training, validation and test data. The test set is the held-out part.
- Category-level accuracy for `screw` is only available if the file `06_per_category_results.md` is in this knowledge base. If it is not, per-category accuracy has not been measured and must not be guessed.

## Questions this file answers
- What defect types exist for screw?
- Is screw an object or a texture category?
- Can the model tell me which defect a screw has? (No: only good or defective.)
