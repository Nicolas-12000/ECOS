import datetime
import io
from fastapi import APIRouter, Query, HTTPException, Response
from fpdf import FPDF
from app.services.epidemiology import get_history, VALID_DISEASES

# Importación opcional de predict_cases (evita cargar dependencias pesadas de ML)
try:
    from app.services.prediction import predict_cases
    PREDICT_AVAILABLE = True
except Exception:
    PREDICT_AVAILABLE = False
    predict_cases = None

router = APIRouter()

class EcosReport(FPDF):
    def header(self):
        self.set_font("Arial", "B", 15)
        self.cell(0, 10, "ECOS - Sistema de Alerta Temprana", 0, 1, "C")
        self.set_font("Arial", "", 10)
        self.cell(0, 10, f"Reporte Generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, "C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", 0, 0, "C")

@router.get("/report/pdf", summary="Genera un reporte epidemiológico en PDF")
def generate_report_pdf(
    municipio_code: str = Query(..., description="Código DANE municipio"),
    disease: str = Query(..., description="Enfermedad (dengue, etc.)"),
    weeks_ahead: int = Query(4, ge=1, le=4)
):
    if disease not in VALID_DISEASES:
        raise HTTPException(status_code=422, detail="Disease not supported")

    try:
        # Gather data
        history = get_history(municipio_code, disease, limit=8)
        predictions = predict_cases(municipio_code, disease, weeks_ahead=weeks_ahead)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    pdf = EcosReport()
    pdf.add_page()
    
    # Summary Section
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Resumen para {disease.capitalize()} - Municipio {municipio_code}", 0, 1)
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 10)
    if not history.empty:
        latest = history.iloc[0]
        pdf.multi_cell(0, 10, f"En la última semana epidemiológica registrada ({latest['epi_year']}-W{latest['epi_week']}), se reportaron {int(latest['cases_total'])} casos confirmados.")
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, "Predicciones a Corto Plazo", 0, 1)
    pdf.set_font("Arial", "", 10)
    
    for p in predictions:
        risk_label = p.get("endemic_risk", "N/A")
        pdf.cell(0, 8, f"- Semana {p['epi_year']}-W{p['epi_week']}: {p['predicted_cases']} casos (Riesgo: {risk_label})", 0, 1)

    pdf.ln(10)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 8, "Este reporte es generado automáticamente por la plataforma ECOS. Las predicciones son estimaciones basadas en modelos de IA y señales tempranas (clima, movilidad, tendencias) y deben ser validadas por personal técnico oficial.")

    # Output to buffer
    pdf_output = pdf.output(dest='S')
    
    return Response(
        content=pdf_output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=reporte_ecos_{municipio_code}_{disease}.pdf"}
    )
