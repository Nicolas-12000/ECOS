import Link from "next/link"
import { Activity } from "lucide-react"

export function Footer() {
  return (
    <footer className="border-t border-(--color-border) bg-(--color-surface) mt-auto">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <Activity className="h-5 w-5 text-(--color-tertiary)" />
              <span className="font-display font-bold uppercase tracking-wider text-sm">ECOS</span>
            </div>
            <p className="text-sm text-(--color-secondary) leading-relaxed max-w-md">
              Early Control and Observation System — Plataforma nacional de alerta temprana 
              para enfermedades de alto impacto en Colombia. Datos abiertos + IA predictiva 
              para anticipar brotes epidemiológicos.
            </p>
            <p className="text-xs text-(--color-muted) mt-4 font-display uppercase tracking-wider">
              Concurso Datos al Ecosistema 2026 — IA para Colombia
            </p>
          </div>

          {/* Navigation */}
          <div>
            <h4 className="font-display text-xs uppercase tracking-wider text-(--color-secondary) mb-4 font-semibold">
              Módulos
            </h4>
            <ul className="space-y-2.5">
              {[
                { href: "/", label: "Inicio" },
                { href: "/tendencias", label: "Tendencias" },
                { href: "/noticias", label: "Monitor de Noticias" },
                { href: "/dashboard", label: "Dashboard" },
              ].map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className="text-sm text-(--color-secondary) hover:text-(--color-tertiary) transition-colors">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Data Sources */}
          <div>
            <h4 className="font-display text-xs uppercase tracking-wider text-(--color-secondary) mb-4 font-semibold">
              Fuentes de datos
            </h4>
            <ul className="space-y-2.5">
              {[
                "datos.gov.co",
                "SIVIGILA — INS",
                "IDEAM",
                "Google Trends",
                "Open-Meteo API",
              ].map((source) => (
                <li key={source} className="text-sm text-(--color-secondary)">
                  {source}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-(--color-border) mt-8 pt-6 flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-xs text-(--color-muted)">
            © 2026 ECOS — Licencia MIT · Código abierto · Transferible al INS y MinSalud
          </p>
          <div className="flex items-center gap-4">
            <span className="text-xs text-(--color-muted) font-display uppercase tracking-wider">
              Stack 100% gratuito
            </span>
            <span className="inline-flex items-center gap-1.5 text-xs font-display uppercase tracking-wider text-(--color-success)">
              <span className="w-1.5 h-1.5 rounded-full bg-(--color-success) animate-pulse" />
              Sistema activo
            </span>
          </div>
        </div>
      </div>
    </footer>
  )
}
