# Category: cable

Dataset: MVTec AD, category `cable`. Kind: object (MVTec AD has 10 object and 5 texture categories).

## Defect types in this category
The test folder for `cable` contains 8 defect folder(s). The plain-language readings below are based on the folder names. Look at the sample images in the MVTec AD paper for the exact appearance.

- `bent_wire`: a wire inside the cable is bent
- `cable_swap`: cables in the wrong arrangement (swapped); name-based reading
- `combined`: more than one defect on the same item
- `cut_inner_insulation`: the inner insulation is cut
- `cut_outer_insulation`: the outer insulation is cut
- `missing_cable`: one of the cables is missing
- `missing_wire`: a wire is missing
- `poke_insulation`: the insulation is poked or punctured

## What the classifier does with this category
- The Sentry QC model only answers "good" or "defective". It does not say which defect type is present and it does not show where the defect is.
- Images of `cable` are part of the training, validation and test data. The test set is the held-out part.
- Category-level accuracy for `cable` is only available if the file `06_per_category_results.md` is in this knowledge base. If it is not, per-category accuracy has not been measured and must not be guessed.

## Questions this file answers
- What defect types exist for cable?
- Is cable an object or a texture category?
- Can the model tell me which defect a cable has? (No: only good or defective.)
