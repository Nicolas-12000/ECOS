const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface SignalsItem {
  epi_year: number;
  epi_week: number;
  week_start_date: string;
  departamento_code: string;
  disease: string;
  vaccination_coverage_pct: number | null;
  rips_visits_total: number | null;
  mobility_index: number | null;
  trends_score: number | null;
  rss_mentions: number | null;
  signals_score: number | null;
}

export interface SignalsResponse {
  departamento_code: string;
  disease: string;
  records: SignalsItem[];
}

export interface ChatResponse {
  answer: string;
  sources: Array<{
    title: string;
    excerpt: string;
    source_type: string;
  }>;
}

export interface PredictionItem {
  epi_year: number;
  epi_week: number;
  week_start_date: string;
  disease: string;
  municipio_code: string;
  departamento_code: string;
  predicted_cases: number;
  outbreak_flag: boolean;
  outbreak_threshold: number;
}

export interface PredictResponse {
  municipio_code: string;
  disease: string;
  predictions: PredictionItem[];
}

export interface HistoryItem {
  epi_year: number;
  epi_week: number;
  week_start_date: string;
  disease: string;
  municipio_code: string;
  departamento_code: string;
  cases_total: number;
  temp_avg_c: number | null;
  humidity_avg_pct: number | null;
  precipitation_mm: number | null;
}

export interface HistoryResponse {
  municipio_code: string;
  disease: string;
  records: HistoryItem[];
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `API error: ${response.status}`);
  }
  return response.json();
}

export async function chat(message: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: message }),
  });
  return handleResponse<ChatResponse>(response);
}

export async function getHistory(municipio_code: string, disease: string, limit: number = 52): Promise<HistoryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/history?municipio_code=${municipio_code}&disease=${disease}&limit=${limit}`);
  return handleResponse<HistoryResponse>(response);
}

export async function getSignals(departamento_code: string, disease: string, limit: number = 52): Promise<SignalsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/signals?departamento_code=${departamento_code}&disease=${disease}&limit=${limit}`);
  return handleResponse<SignalsResponse>(response);
}

export async function predict(municipio_code: string, disease: string, weeks_ahead: number = 4): Promise<PredictResponse> {
  const response = await fetch(`${API_BASE_URL}/api/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ municipio_code, disease, weeks_ahead }),
  });
  return handleResponse<PredictResponse>(response);
}
