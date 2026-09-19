"""Data pipeline: load the dataset, split it, and preprocess it for training."""

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder

from hotelprice.config import (
    CATEGORICAL_FEATURES,
    FEATURES,
    NUMERICAL_FEATURES,
    TARGET,
    get_data_path,
    get_preprocessor_path,
    get_random_seed,
    get_test_size,
)


def run_data_pipeline():
    """Return X_train, X_test, y_train, y_test (preprocessed) and the fitted preprocessor."""
    # 1. Load the CSV from the configured path.
    df = pd.read_csv(get_data_path())

    # 2. Select the feature columns and the target.
    X = df[FEATURES]
    y = df[TARGET]

    # 3. Split into train/test with the configured seed and test size.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=get_test_size(), random_state=get_random_seed()
    )

    # 4. Ordinal-encode categoricals (unseen categories become NaN, which XGBoost treats
    #    as missing) and pass numerics through unscaled (trees don't need scaling).
    preprocessor = ColumnTransformer(
        [
            (
                "categorical",
                OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=np.nan),
                CATEGORICAL_FEATURES,
            ),
            ("numerical", "passthrough", NUMERICAL_FEATURES),
        ],
        verbose_feature_names_out=False,
    )
    preprocessor.set_output(transform="pandas")

    # 5. Fit on the training split only, then transform both splits.
    X_train = preprocessor.fit_transform(X_train)
    X_test = preprocessor.transform(X_test)

    # 6. Save the fitted preprocessor so inference can load it later.
    preprocessor_path = get_preprocessor_path()
    preprocessor_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(preprocessor, preprocessor_path)

    return X_train, X_test, y_train, y_test, preprocessor


if __name__ == "__main__":
    X_train, X_test, y_train, y_test, _ = run_data_pipeline()
    print(f"X_train {X_train.shape}, X_test {X_test.shape}")
    print(f"Preprocessor saved to {get_preprocessor_path()}")
