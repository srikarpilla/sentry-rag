# Project overview: Sentry QC

## What it is
Sentry QC is an image classifier that labels a photo of an industrial part as good or defective. It is served through a FastAPI backend and a web page where a user can upload one image or a batch of up to 16.

## How it works: how an image is preprocessed, scored and decided
1. The user uploads an image.
2. The backend resizes it to 288x288 RGB and passes raw pixel values (0 to 255) to the model.
3. The model, an EfficientNetB0 network, outputs two probabilities: P(defective) and P(good).
4. If P(good) is at or above the decision threshold of 0.58, the result is PASS (good). Otherwise it is FAIL (defective).
5. If P(good) is close to the threshold, the result is marked UNCERTAIN and a person should review the image.

## What it was trained on
The MVTec AD benchmark, which contains images of 15 types of industrial products and textures. See `05_dataset_overview.md`.

## What it is not
It is a benchmark project, not a certified inspection system. See `04_limitations_and_risks.md`.
