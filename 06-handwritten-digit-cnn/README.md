# Handwritten Digit Recognition with a Convolutional Neural Network

A deep learning project building a CNN from scratch in Keras to classify handwritten digits,
reaching 97% test accuracy.

## Problem

Image classification requires a model that understands spatial structure. A standard dense network
flattens an image into a vector and throws away the fact that neighboring pixels are related — a
convolutional network preserves it. This project builds a CNN end to end on the standard benchmark
for the task and evaluates it per-class rather than on headline accuracy alone.

## Data

**MNIST** — 70,000 grayscale images of handwritten digits (60,000 train / 10,000 test), each
28×28 pixels, labeled 0–9. Loaded directly through the Keras datasets API, so there is no data file
to commit and the notebook runs anywhere.

## Approach

**Preprocessing**

1. Reshaped images to `(28, 28, 1)` — adding the explicit single channel dimension the convolutional
   layer expects.
2. Rescaled pixel intensity from 0–255 to 0–1, so gradients stay in a usable range during training.
3. One-hot encoded the labels for multi-class output.
4. Set a fixed random seed for reproducibility.

**Architecture**

A sequential CNN:

| Layer | Configuration | Purpose |
|---|---|---|
| Conv2D | 64 filters, 5×5 kernel, ReLU | Learn local spatial features |
| MaxPooling2D | 2×2 pool | Downsample, add translation tolerance |
| Dropout | 0.5 | Regularize against overfitting |
| Dense output | 10 units, softmax | Class probabilities |

**Evaluation** — full precision, recall, and F1 per digit class, not just overall accuracy.

## Key findings

- **97% test set accuracy**, with predictions matching true labels across the large majority of
  cases.
- Per-class metrics are consistently strong: digits 0, 1, and 3 reach **0.98–0.99 F1**, with the
  lowest-performing classes still around 0.97.
- The per-class breakdown is the part worth looking at. Headline accuracy on a balanced dataset
  hides which digits the model actually confuses — reporting the full classification report shows
  where the remaining error lives rather than averaging it away.
- Dropout at 0.5 after pooling was the main regularization lever; the gap between training and test
  performance stayed small.

## What's in this folder

```
code/    CNN notebook — preprocessing, architecture, training, per-class evaluation
```

## Tools

Python · TensorFlow / Keras (Sequential, Conv2D, MaxPooling2D, Dropout, Dense) · NumPy · scikit-learn
(classification report) · matplotlib

## Notes and limitations

- **MNIST is a solved benchmark.** 97% is a solid result for a simple architecture, but the dataset
  is clean, centered, and balanced — nothing like real-world image data. This project demonstrates
  CNN mechanics and correct evaluation practice, not a hard modeling problem.
- Single architecture, no hyperparameter search, no comparison against a dense baseline.
- No data augmentation, which is where meaningful gains on harder image tasks usually come from.
