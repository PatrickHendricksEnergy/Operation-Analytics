"""Driver models for supply chain analysis dataset."""
from __future__ import annotations

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    r2_score,
)
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.inspection import partial_dependence

from shared.src.common_metrics import safe_mae, safe_rmse


def _build_preprocessor(df: pd.DataFrame, target: str) -> tuple[ColumnTransformer, list[str], list[str]]:
    X = df.drop(columns=[target])
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = X.select_dtypes(include=["object"]).columns.tolist()

    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
    ])
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_cols),
            ("cat", categorical_pipe, categorical_cols),
        ],
        remainder="drop",
    )
    return preprocessor, numeric_cols, categorical_cols


def _get_feature_names(preprocessor: ColumnTransformer) -> list[str]:
    try:
        return preprocessor.get_feature_names_out().tolist()
    except Exception:
        return []


def run_regression(df: pd.DataFrame, target: str = "revenue_generated"):
    if target not in df.columns:
        return pd.DataFrame(), pd.DataFrame(), {}, pd.DataFrame()

    model_df = df.dropna(subset=[target]).copy()
    preprocessor, numeric_cols, _ = _build_preprocessor(model_df, target)

    X = model_df.drop(columns=[target])
    y = model_df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(n_estimators=300, random_state=42)
    pipeline = Pipeline([
        ("preprocess", preprocessor),
        ("model", model),
    ])
    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)

    metrics = {
        "mae": safe_mae(y_test, preds),
        "rmse": safe_rmse(y_test, preds),
        "r2": float(r2_score(y_test, preds)),
    }

    scores_df = pd.DataFrame({
        "y_actual": y_test.values,
        "y_pred": preds,
    })

    feature_names = _get_feature_names(preprocessor)
    importances = pipeline.named_steps["model"].feature_importances_
    importance_df = pd.DataFrame({
        "feature": feature_names,
        "importance": importances,
    }).sort_values("importance", ascending=False)

    # Partial dependence for top numeric features
    pdp_rows = []
    if numeric_cols:
        # choose top numeric by correlation
        corr = model_df[numeric_cols + [target]].corr(numeric_only=True)[target].drop(target).abs()
        top_numeric = corr.sort_values(ascending=False).head(3).index.tolist()
        for feat in top_numeric:
            try:
                pdp = partial_dependence(pipeline, X_train, [feat], grid_resolution=20)
                values = pdp["values"][0]
                averages = pdp["average"][0]
                for v, a in zip(values, averages):
                    pdp_rows.append({"feature": feat, "value": float(v), "partial_dependence": float(a)})
            except Exception:
                continue

    pdp_df = pd.DataFrame(pdp_rows)
    return scores_df, importance_df, metrics, pdp_df


def _build_classification_target(df: pd.DataFrame) -> tuple[pd.Series, str]:
    if "inspection_results" in df.columns:
        y = df["inspection_results"].astype(str).str.lower().str.contains("fail")
        return y, "inspection_fail"
    if "defect_rate_scaled" in df.columns:
        threshold = df["defect_rate_scaled"].quantile(0.75)
        y = df["defect_rate_scaled"] >= threshold
        return y, "high_defect_rate"
    raise ValueError("No target available for classification")


def run_classification(df: pd.DataFrame):
    try:
        y, target_name = _build_classification_target(df)
    except Exception:
        return pd.DataFrame(), pd.DataFrame(), {}, target_name if "target_name" in locals() else "classification"

    model_df = df.copy()
    model_df = model_df.loc[y.notna()].copy()
    model_df[target_name] = y.astype(int)

    preprocessor, _, _ = _build_preprocessor(model_df, target_name)

    X = model_df.drop(columns=[target_name])
    y = model_df[target_name]

    if y.nunique() < 2:
        return pd.DataFrame(), pd.DataFrame(), {}, target_name

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(n_estimators=300, random_state=42, class_weight="balanced")
    pipeline = Pipeline([
        ("preprocess", preprocessor),
        ("model", model),
    ])
    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)
    probas = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": float(accuracy_score(y_test, preds)),
        "precision": float(precision_score(y_test, preds, zero_division=0)),
        "recall": float(recall_score(y_test, preds, zero_division=0)),
        "f1": float(f1_score(y_test, preds, zero_division=0)),
    }
    try:
        metrics["roc_auc"] = float(roc_auc_score(y_test, probas))
    except Exception:
        metrics["roc_auc"] = None

    scores_df = pd.DataFrame({
        "y_actual": y_test.values,
        "y_pred": preds,
        "y_prob": probas,
    })

    feature_names = _get_feature_names(preprocessor)
    importances = pipeline.named_steps["model"].feature_importances_
    importance_df = pd.DataFrame({
        "feature": feature_names,
        "importance": importances,
    }).sort_values("importance", ascending=False)

    return scores_df, importance_df, metrics, target_name
