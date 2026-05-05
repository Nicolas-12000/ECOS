import joblib
import pandas as pd
import shap
from pathlib import Path

class EcosHybridModel:
    """
    Unified wrapper for the ECOS hybrid model (Prophet + XGBoost).
    Handles loading, recursive forecasting, and SHAP explainability.
    """
    def __init__(self, model_path: Path):
        if not model_path.exists():
            raise FileNotFoundError(f"Model artifact not found at {model_path}")
        
        artifact = joblib.load(model_path)
        self.xgb_model = artifact["xgb_model"]
        self.prophet_models = artifact.get("prophet_models", {})
        self.feature_columns = artifact.get("feature_columns", [])
        self.uses_prophet = artifact.get("uses_prophet", False)
        self.trained_on_residuals = artifact.get("trained_on_residuals", False)
        
        # Initialize SHAP explainer
        self.explainer = shap.TreeExplainer(self.xgb_model)

    def predict_residual(self, X: pd.DataFrame) -> tuple[float, pd.DataFrame]:
        """Predicts the residual using XGBoost and returns (prediction, shap_values)."""
        # Ensure columns match
        X_aligned = X.reindex(columns=self.feature_columns, fill_value=0)
        
        pred = float(self.xgb_model.predict(X_aligned)[0])
        shap_values = self.explainer.shap_values(X_aligned)
        
        # Format SHAP as a dict for easy API consumption
        shap_dict = dict(zip(self.feature_columns, shap_values[0].tolist()))
        
        return pred, shap_dict

    def get_prophet_baseline(self, municipio_code: str, disease: str, ds: pd.Timestamp) -> float:
        """Gets the Prophet baseline for a specific series and date."""
        key = f"{municipio_code}:{disease}"
        if key not in self.prophet_models:
            return 0.0
            
        model = self.prophet_models[key]
        frame = pd.DataFrame({"ds": [ds]})
        try:
            forecast = model.predict(frame)
            return float(forecast["yhat"].iloc[0])
        except Exception:
            return 0.0
