'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { FolderKanban, Activity, Menu, X, Settings } from 'lucide-react'
import { BackendHealthIndicator } from './BackendHealthIndicator'
import { cn } from '@/lib/utils'

export function Navigation() {
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navLinks = [
    {
      href: '/taiga',
      label: 'Taiga',
      icon: FolderKanban,
      isActive: pathname === '/' || pathname?.startsWith('/taiga'),
    },
    {
      href: '/gauges',
      label: 'Gauges',
      icon: Activity,
      isActive: pathname?.startsWith('/gauges'),
    },
    {
      href: '/settings',
      label: 'Settings',
      icon: Settings,
      isActive: pathname?.startsWith('/settings'),
    },
  ]

  return (
    <nav className="bg-neo-black border-b-neo border-neo-blue sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16 md:h-20">
          {/* Logo */}
          <Link href="/taiga" className="flex items-center gap-3 group">
            {/* Logo Icon */}
            <div className="w-10 h-10 md:w-12 md:h-12 bg-neo-blue border-neo-sm border-white flex items-center justify-center transform -rotate-3 group-hover:rotate-3 transition-transform duration-200">
              <span className="font-display font-bold text-xl md:text-2xl text-white">F</span>
            </div>
            {/* Logo Text */}
            <div className="hidden sm:block">
              <div className="font-display font-bold text-xl md:text-2xl text-white tracking-tight">
                F.O.C.U.S.
              </div>
              <div className="font-mono text-[10px] md:text-xs text-neo-blue uppercase tracking-widest">
                MOMENTUM
              </div>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-3">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "flex items-center gap-2 px-4 py-2",
                  "font-display font-bold uppercase text-sm tracking-wide",
                  "border-neo-sm transition-all duration-150",
                  link.isActive
                    ? "bg-neo-blue text-white border-white shadow-[3px_3px_0px_0px_#ffffff]"
                    : "bg-white text-neo-black border-neo-black hover:bg-neo-blue-light hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-[4px_4px_0px_0px_#ffffff]"
                )}
              >
                <link.icon className="h-4 w-4" />
                {link.label}
              </Link>
            ))}

            {/* Health Indicator */}
            <div className="ml-2">
              <BackendHealthIndicator />
            </div>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 bg-white border-neo-sm border-neo-black shadow-neo-sm hover:shadow-none hover:translate-x-0.5 hover:translate-y-0.5 transition-all"
            aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
          >
            {mobileMenuOpen ? (
              <X className="h-6 w-6 text-neo-black" />
            ) : (
              <Menu className="h-6 w-6 text-neo-black" />
            )}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden pb-4 animate-fade-in-down">
            <div className="bg-white border-neo border-neo-black shadow-neo">
              {navLinks.map((link, index) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-4 py-4",
                    "font-display font-bold uppercase text-sm tracking-wide",
                    "transition-colors",
                    index > 0 && "border-t border-neo-lightgrey",
                    link.isActive
                      ? "bg-neo-blue-light text-neo-blue"
                      : "text-neo-black hover:bg-neo-offwhite"
                  )}
                >
                  <link.icon className="h-5 w-5" />
                  {link.label}
                </Link>
              ))}

              {/* Mobile Health Indicator */}
              <div className="px-4 py-4 border-t border-neo-lightgrey">
                <BackendHealthIndicator />
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}
