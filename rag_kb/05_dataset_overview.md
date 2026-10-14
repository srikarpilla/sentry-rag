# Dataset: MVTec AD

## What the MVTec AD dataset is
- Name: MVTec Anomaly Detection dataset (MVTec AD), from MVTec Software GmbH.
- Original purpose: benchmarking unsupervised anomaly detection (training on good images only).
- It contains high-resolution color images of 15 types of industrial products and textures.

## Size and categories
- Size: 5,354 images, 3,629 for training and 1,725 for testing.
- Categories: 15 (10 object categories and 5 texture categories). Textures: carpet, grid, leather, tile, wood. Objects: bottle, cable, capsule, hazelnut, metal nut, pill, screw, toothbrush, transistor, zipper.
- Training images are all defect-free. Test images include defect-free images and images with defects.
- Test set: 467 defect-free and 1,258 defective images (1,725 in total).

## Defect types and annotations
- Over 70 defect types, such as scratches, dents, contaminations and structural changes. A listing of the defect folders by category is in the `categories/` files.
- The dataset also provides pixel-precise ground-truth regions for defects. The Sentry QC classifier does not use them.

## How Sentry QC uses the dataset
- Sentry QC trains a supervised good-vs-defective classifier, which is a different setup from the original unsupervised benchmark. Its numbers must not be compared with published anomaly-detection scores.
- How the splits were built is described in `02_model_card.md`.

## License and usage
- The dataset is not allowed for commercial use. Check the terms on the MVTec page.
