# Limitations and risks

## Missed defects
On the held-out test set the model passed 39 of 633 defective images as good (6.2%). It flagged 18 of 467 good images as defective (3.9%).

## Real production rates change the picture
The test set is 57% defective. On a real line, defects are usually a small share of items. Example with a 1% defect rate on 10,000 items (100 defective, 9,900 good), using the test recalls:
- About 94 of the 100 defective items are caught and about 6 are missed.
- About 382 good items are flagged by mistake (3.9% of 9,900).
- Only about 1 in 5 flagged items (about 20%) would be truly defective.
This is a calculation from the test recalls, not a measurement on a real line.

## Data limits
- Trained and tested only on MVTec AD: the same 15 product types, cameras and lighting. Results on other products, cameras or lighting have not been measured.
- Defect images of the same type were split randomly between train and test, so similar-looking defects can appear on both sides. This tests defects of types the model has seen. It does not test new defect types.
- The test set has 1,100 images, so the test accuracy has an uncertainty of roughly 1 to 2 percentage points.
- The good training images in MVTec are very similar to each other, so validation accuracy on good images is likely easier than real life.

## Model limits
- Only good vs defective. No defect type, no location.
- Images are resized to 288x288. Very small defects can be lost.
- Per-category accuracy is only reported if `06_per_category_results.md` exists.

## Usage limits: is it ready for real factory or production use?
- The MVTec AD dataset is licensed for non-commercial use only.
- This is a benchmark project and has not been validated as a certified inspection system. A person should review uncertain and high-stakes results.
