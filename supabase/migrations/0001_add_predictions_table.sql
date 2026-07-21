CREATE TABLE IF NOT EXISTS public.predictions (
    id BIGSERIAL PRIMARY KEY,
    departamento_code VARCHAR(2),
    municipio_code VARCHAR(5),
    disease VARCHAR(20),
    epi_year INTEGER,
    epi_week INTEGER,
    week_start_date DATE,
    predicted_cases DOUBLE PRECISION,
    outbreak_flag BOOLEAN,
    outbreak_threshold DOUBLE PRECISION,
    endemic_risk VARCHAR(20),
    shap_top_factors JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_predictions_dept_disease_week ON public.predictions (departamento_code, disease, epi_year, epi_week);
CREATE INDEX IF NOT EXISTS idx_predictions_municipio_disease_week ON public.predictions (municipio_code, disease, epi_year, epi_week);
