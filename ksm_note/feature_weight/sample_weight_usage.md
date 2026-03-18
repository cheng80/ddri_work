# sample_weight usage

Train file:
- `ksm_note/data/ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3_with_sample_weight.csv`

Concept:
- `sample_weight` is not a model feature.
- Use it only as the training weight for each row.
- Exclude `sample_weight` from `X`.

Example:

```python
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

df = pd.read_csv(
    "ksm_note/data/ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3_with_sample_weight.csv"
)

target_col = "bike_change_raw"
weight_col = "sample_weight"

X = df.drop(columns=[target_col, weight_col])
y = df[target_col]
sample_weight = df[weight_col]

model = RandomForestRegressor(random_state=42)
model.fit(X, y, sample_weight=sample_weight)
```

Notes:
- If your model does not support `sample_weight`, this column should not be used.
- For validation/test data, do not add `sample_weight` unless you explicitly need weighted evaluation.
