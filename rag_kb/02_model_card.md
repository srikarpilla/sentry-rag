# Model card

## Model architecture
- Architecture: EfficientNetB0, pretrained on ImageNet, used through transfer learning.
- Input: RGB image resized to 288x288. Raw pixel values 0 to 255 (EfficientNet rescales internally).
- Head: global average pooling, dropout 0.3, dense layer with 256 units (ReLU, L2 regularization 1e-4), dropout 0.3, dense layer with 2 units (softmax).
- Output order: index 0 is `defective`, index 1 is `good`.
- Decision rule: PASS (good) if P(good) >= 0.58, otherwise FAIL (defective).

## Training setup
- Task: binary classification, good vs defective.
- Phase 1: 10 epochs with the backbone frozen, learning rate 1e-3, training only the head.
- Phase 2: up to 40 epochs fine-tuning the backbone at learning rate 3e-5, with BatchNorm layers kept frozen.
- Loss: categorical cross-entropy with label smoothing 0.05.
- Class imbalance: class-balanced sample weights on both training and validation, so reported accuracy is balanced accuracy.
- Augmentation (training only): horizontal and vertical flips, small rotation, zoom, translation, contrast and brightness changes.
- Early stopping on validation loss with patience 8, and learning-rate reduction on plateau.
- The decision threshold 0.58 was tuned on the validation set to maximize balanced accuracy. It was not tuned on the test set.

## Data splits
| Split | Images | Defective | Good |
|---|---|---|---|
| Train | 3,615 | 531 | 3,084 |
| Validation | 639 | 94 | 545 |
| Test (held out) | 1,100 | 633 | 467 |

How the splits were made: all defect-free MVTec training images are "good". MVTec's anomalous test images are "defective" and were split 50/50 per product category between train and test. The validation set was carved out of the training set with stratification. No file appears in more than one split (checked in code).

## Results
| Metric | Train | Val | Test |
|---|---|---|---|
| Balanced accuracy | 98.2% | 96.9% | 95.0% |
| Plain accuracy | 97.5% | 97.0% | 94.8% |
| Recall, defective | 99.2% | 96.8% | 93.8% |
| Recall, good | 97.2% | 97.1% | 96.1% |
| Precision, defective | 85.8% | 85.0% | 97.1% |
| Precision, good | 99.9% | 99.4% | 92.0% |

Test is the honest number. Train and val are about 15% defective, test is 57% defective, which is why defective precision is much higher on test.

## Confusion matrices (rows = true class, columns = predicted)
Test: true defective 633 -> 594 predicted defective, 39 predicted good. True good 467 -> 18 predicted defective, 449 predicted good.
Validation: true defective 94 -> 91 predicted defective, 3 predicted good. True good 545 -> 16 predicted defective, 529 predicted good.
Train: true defective 531 -> 527 predicted defective, 4 predicted good. True good 3,084 -> 87 predicted defective, 2,997 predicted good.

## Why balanced accuracy
In the training data about 85% of images are good. A model that always says "good" would get about 85% plain accuracy and catch no defects. Balanced accuracy is the average of the two recalls, so that model would score about 50%.
