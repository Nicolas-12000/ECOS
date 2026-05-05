"use client"

import React from "react"

export type AnimatedVariant = "loading" | "health" | "empty" | "search" | "error"

interface AnimatedGraphicProps {
  variant?: AnimatedVariant
  size?: number
  className?: string
  message?: string
}

export function LottieLoader({
  variant = "loading",
  size = 160,
  className = "",
  message,
}: AnimatedGraphicProps) {
  
  // A glowing, pulsing medical/data radar for the Hero section
  const HealthAnimation = () => (
    <div className="relative flex items-center justify-center w-full h-full">
      {/* Outer pulsing rings */}
      <div className="absolute inset-0 rounded-full border border-[#B8422E] opacity-20 animate-ping" style={{ animationDuration: '3s' }} />
      <div className="absolute inset-4 rounded-full border border-[#B8422E] opacity-40 animate-pulse" style={{ animationDuration: '2s' }} />
      
      {/* Central rotating element */}
      <div className="relative w-1/2 h-1/2 bg-[#B8422E] rounded-xl rotate-45 animate-spin shadow-lg" style={{ animationDuration: '10s' }}>
        <div className="absolute inset-0 bg-linear-to-br from-background to-transparent opacity-30 rounded-xl" />
        <div className="absolute inset-2 border border-white opacity-50 rounded-lg" />
      </div>

      {/* Floating data dots */}
      <div className="absolute top-0 right-1/4 w-3 h-3 bg-success rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
      <div className="absolute bottom-1/4 left-0 w-2 h-2 bg-[#F59E0B] rounded-full animate-bounce" style={{ animationDelay: '0.5s' }} />
    </div>
  )

  // A floating magnifying glass over a chart for the Trends empty state
  const SearchAnimation = () => (
    <div className="relative flex items-center justify-center w-full h-full">
      {/* Chart bars in background */}
      <div className="absolute bottom-1/4 flex items-end gap-2 h-1/2 w-3/4 opacity-30">
        <div className="w-full bg-primary rounded-t-sm animate-pulse" style={{ height: '40%' }} />
        <div className="w-full bg-primary rounded-t-sm animate-pulse" style={{ height: '70%', animationDelay: '0.2s' }} />
        <div className="w-full bg-primary rounded-t-sm animate-pulse" style={{ height: '50%', animationDelay: '0.4s' }} />
      </div>

      {/* Floating magnifying glass */}
      <div className="absolute inset-0 flex items-center justify-center animate-[float_4s_ease-in-out_infinite]">
        <svg viewBox="0 0 24 24" fill="none" stroke="#B8422E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-1/2 h-1/2 drop-shadow-md">
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      </div>
    </div>
  )

  // A softly floating folded newspaper/document for the News empty state
  const EmptyAnimation = () => (
    <div className="relative flex items-center justify-center w-full h-full">
      <div className="animate-[float_5s_ease-in-out_infinite] w-3/4 h-3/4 text-secondary opacity-50">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
          <path d="M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v4" />
          <polyline points="14 2 14 8 20 8" />
          <path d="M2 15h10" />
          <path d="M2 18h10" />
          <path d="M2 12h10" />
        </svg>
      </div>
    </div>
  )

  const LoadingAnimation = () => (
    <div className="w-full h-full flex items-center justify-center">
      <div className="w-1/4 h-1/4 border-4 border-border border-t-[#B8422E] rounded-full animate-spin" />
    </div>
  )

  const renderAnimation = () => {
    switch (variant) {
      case "health": return <HealthAnimation />
      case "search": return <SearchAnimation />
      case "empty": return <EmptyAnimation />
      case "loading":
      case "error":
      default: return <LoadingAnimation />
    }
  }

  return (
    <div className={`flex flex-col items-center justify-center gap-4 ${className}`}>
      <div style={{ width: size, height: size }}>
        {renderAnimation()}
      </div>
      {message && (
        <p className="text-sm text-secondary font-medium animate-pulse text-center">
          {message}
        </p>
      )}
    </div>
  )
}

/** Simple skeleton shimmer block */
export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`animate-shimmer rounded-md ${className}`} style={{ backgroundColor: "#E5E2DC" }} />
  )
}
