export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(168,88,34,0.18),_transparent_35%),radial-gradient(circle_at_80%_20%,_rgba(22,114,90,0.16),_transparent_28%),linear-gradient(180deg,_rgba(247,241,232,0.96),_rgba(239,230,216,0.94))]" />
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-6 py-8 sm:px-10 lg:px-12">
        <header className="flex items-center justify-between gap-4 border-b border-border pb-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-accent">
              ECOS
            </p>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
              Early Control and Observation System
            </h1>
          </div>
          <a
            href="http://localhost:8000/docs"
            className="rounded-full border border-border bg-surface/80 px-4 py-2 text-sm font-medium text-foreground shadow-sm backdrop-blur transition hover:border-foreground/20 hover:bg-surface"
          >
            API Docs
          </a>
        </header>

        <section className="grid flex-1 items-center gap-10 py-12 lg:grid-cols-[1.3fr_0.7fr] lg:py-16">
          <div className="max-w-3xl">
            <p className="inline-flex rounded-full border border-accent-soft bg-surface px-4 py-2 text-sm font-medium text-accent">
              Alerta temprana para dengue, chikungunya, zika y malaria
            </p>
            <h2 className="mt-6 text-5xl font-semibold tracking-tight text-foreground sm:text-6xl lg:text-7xl">
              Predicción, explicación y respuesta en una sola capa.
            </h2>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-foreground-muted sm:text-xl">
              ECOS une datos abiertos, señales tempranas y asistencia conversacional para
              anticipar brotes por municipio y departamento, explicar el riesgo y facilitar
              decisiones operativas con contexto sanitario real.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href="http://localhost:8000/api/predict"
                className="rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-contrast transition hover:opacity-90"
              >
                Ver predicción
              </a>
              <a
                href="http://localhost:8000/api/signals"
                className="rounded-full border border-border bg-surface/80 px-6 py-3 text-sm font-semibold text-foreground transition hover:border-foreground/20 hover:bg-surface"
              >
                Explorar señales
              </a>
            </div>

            <div className="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {[
                {
                  title: "Predicción",
                  body: "Horizonte de 1 a 4 semanas con salida por municipio y enfermedad.",
                },
                {
                  title: "Señales tempranas",
                  body: "Clima, vacunación, movilidad, RIPS y señales web agregadas.",
                },
                {
                  title: "RAG",
                  body: "Consulta guiada sobre riesgo, contexto y fuentes de soporte.",
                },
                {
                  title: "API y dashboard",
                  body: "Servicios listos para consumir desde analítica y visualización.",
                },
              ].map((item) => (
                <article
                  key={item.title}
                  className="rounded-3xl border border-border bg-surface/80 p-5 shadow-[0_10px_30px_rgba(77,50,22,0.08)] backdrop-blur"
                >
                  <h3 className="text-base font-semibold text-foreground">{item.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-foreground-muted">{item.body}</p>
                </article>
              ))}
            </div>
          </div>

          <aside className="rounded-[2rem] border border-border bg-primary p-6 text-primary-contrast shadow-2xl shadow-stone-950/20">
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-accent-soft">
              Estado final
            </p>
            <div className="mt-6 space-y-5">
              <div>
                <p className="text-sm text-primary-contrast/70">Cobertura</p>
                <p className="mt-1 text-2xl font-semibold">Nacional</p>
              </div>
              <div>
                <p className="text-sm text-primary-contrast/70">Modelo</p>
                <p className="mt-1 text-2xl font-semibold">XGBoost + señales</p>
              </div>
              <div>
                <p className="text-sm text-primary-contrast/70">Explicabilidad</p>
                <p className="mt-1 text-2xl font-semibold">SHAP + trazabilidad</p>
              </div>
              <div>
                <p className="text-sm text-primary-contrast/70">Canal conversacional</p>
                <p className="mt-1 text-2xl font-semibold">RAG asistido</p>
              </div>
            </div>

            <div className="mt-8 rounded-2xl border border-primary-contrast/10 bg-primary-contrast/5 p-4 text-sm leading-6 text-primary-contrast/80">
              Diseñado para demo técnica local con FastAPI, dataset curado en Parquet/CSV y una
              interfaz web que concentra predicción, contexto y lectura operativa.
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}
