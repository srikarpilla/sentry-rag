# How to read a prediction

## The fields
- Label: `good` or `defective`.
- P(good): the model's probability that the part is good, from 0 to 1.
- P(defective): the model's probability that it is defective. P(good) + P(defective) = 1.
- Threshold: 0.58. The label is `good` only if P(good) is at least 0.58.
- Status: `ok`, or `uncertain` when P(good) is within a set distance of the threshold. The default distance is 0.10, so about 0.48 to 0.68.

## What to do with each outcome
- PASS with P(good) well above the threshold: the model is confident the part looks like the good parts it was trained on.
- FAIL with P(good) well below the threshold: the model is confident it sees something unlike the good parts.
- UNCERTAIN: the model is close to its decision line. A person should look at the image.

## Why the threshold is 0.58 and not 0.50
The threshold was tuned on the validation set to maximize balanced accuracy. It makes the model slightly more cautious about calling a part good.

## A probability is not a guarantee
P(good) = 0.95 does not mean a 95% chance the part is good in the real world. It is the model's score on images similar to its training data. See `04_limitations_and_risks.md`.

## Common questions
- Does the model say which defect it found? No. It only says good or defective.
- Does it show where the defect is? No.
- What should I do with an uncertain result? Have a person inspect the part.
- Can I use it on photos of other things? No. It was trained only on MVTec-style industrial product images, and results on other images are not reliable.
