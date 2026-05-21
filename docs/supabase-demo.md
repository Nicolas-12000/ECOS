# Supabase Demo (ECOS)

## Objetivo
Usar Supabase Free como base operativa para la demo:
- `public.curated_weekly`
- `public.predictions_demo`

No cargar `data/raw` completo en Supabase Free.

## 1) Crear esquema

```bash
cd /home/nicolas/proyectos/Ecos
psql "$SUPABASE_DB_URL" -f infra/sql/supabase_demo_schema.sql
```

## 2) Cargar dataset curado

Asegura que exista `data/processed/curated_weekly_csv/part-*.csv`.

```bash
cd /home/nicolas/proyectos/Ecos
.venv/bin/python scripts/load_curated_to_supabase.py --truncate
```

Opcional (ruta explícita):

```bash
cd /home/nicolas/proyectos/Ecos
.venv/bin/python scripts/load_curated_to_supabase.py \
  --database-url "$SUPABASE_DB_URL" \
  --csv data/processed/curated_weekly_csv
```

## 3) Verificar carga

```sql
select count(*) from public.curated_weekly;

select disease, count(*)
from public.curated_weekly
group by disease
order by count(*) desc;

select
  sum(case when humidity_avg_pct is null then 1 else 0 end) as humidity_nulls,
  sum(case when mobility_index is null then 1 else 0 end) as mobility_nulls,
  sum(case when trends_score is null then 1 else 0 end) as trends_nulls
from public.curated_weekly;
```

## 4) Recomendación para demo
- Backend FastAPI local o desplegado leyendo Supabase.
- Dashboard/Power BI consumiendo API o SQL read-only en Supabase.
- Mantener Spark para generación de curado; Supabase solo sirve datos de demo.
