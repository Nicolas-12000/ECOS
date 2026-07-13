"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState } from "react"
import { Activity, Menu, X, TrendingUp, Newspaper, BarChart3, Scale, ShieldAlert } from "lucide-react"

const NAV_LINKS = [
  { href: "/", label: "Inicio", icon: Activity },
  { href: "/tendencias", label: "Tendencias", icon: TrendingUp },
  { href: "/noticias", label: "Noticias", icon: Newspaper },
  { href: "/alertas", label: "Alertas", icon: ShieldAlert },
  { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { href: "/anova", label: "ANOVA", icon: Scale },
]

export function Navbar() {
  const pathname = usePathname()
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <>
      <header className="sticky top-0 z-50 w-full border-b border-[--color-border] glass-strong">
        <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="relative">
              <Activity className="h-6 w-6 text-[--color-tertiary] transition-transform group-hover:scale-110" />
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-[--color-success] border-2 border-white" />
            </div>
            <div className="flex flex-col">
              <span className="font-(family-name:--font-display) font-bold uppercase tracking-[0.15em] text-sm leading-none">ECOS</span>
              <span className="text-[9px] text-[--color-muted] font-(family-name:--font-display) uppercase tracking-wider leading-none mt-0.5 hidden sm:block">
                Alerta temprana
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map((link) => {
              const isActive = pathname === link.href || (link.href !== "/" && pathname.startsWith(link.href))
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`relative group flex items-center gap-1.5 px-3.5 py-2 text-sm font-semibold rounded-md transition-all duration-200 ${
                    isActive
                      ? "text-[var(--color-tertiary)] bg-[var(--color-tertiary-alpha)]"
                      : "text-[var(--color-secondary)] hover:text-[var(--color-primary)] hover:bg-[var(--color-surface-hover)]"
                  }`}
                >
                  {link.label}
                  <span
                    className={`absolute bottom-0 left-3.5 right-3.5 h-[2px] bg-[var(--color-tertiary)] rounded-full transition-transform duration-300 origin-center ${
                      isActive ? "scale-x-100" : "scale-x-0 group-hover:scale-x-75"
                    }`}
                  />
                </Link>
              )
            })}
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-3">
            {/* Live indicator */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border border-emerald-500/20 bg-emerald-500/5 shadow-[0_0_8px_rgba(16,185,129,0.05)]">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75 animate-ping" />
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
              </span>
              <span className="text-[9px] font-(family-name:--font-display) uppercase tracking-widest text-emerald-600 font-bold">
                Live
              </span>
            </div>

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden p-2 rounded-sm text-[--color-secondary] hover:text-[--color-primary] hover:bg-[--color-surface-hover] transition-colors"
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm md:hidden animate-fade-in"
            onClick={() => setMobileOpen(false)}
          />
          <div className="fixed top-16 left-0 right-0 z-40 md:hidden animate-slide-down">
            <nav className="mx-4 mt-2 p-3 bg-[--color-surface] border border-[--color-border] rounded-md shadow-lg space-y-1">
              {NAV_LINKS.map((link) => {
                const isActive = pathname === link.href || (link.href !== "/" && pathname.startsWith(link.href))
                const Icon = link.icon
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setMobileOpen(false)}
                    className={`flex items-center gap-3 px-4 py-3 rounded-sm text-sm font-medium transition-colors ${
                      isActive
                        ? "text-[--color-tertiary] bg-[--color-tertiary-alpha]"
                        : "text-[--color-secondary] hover:text-[--color-primary] hover:bg-[--color-surface-hover]"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {link.label}
                  </Link>
                )
              })}
            </nav>
          </div>
        </>
      )}
    </>
  )
}
