'use client'

export function Footer() {
  return (
    <footer className="bg-neo-black border-t-neo border-neo-blue mt-12">
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-neo-blue border-neo-sm border-white flex items-center justify-center transform -rotate-3">
              <span className="font-display font-bold text-sm text-white">F</span>
            </div>
            <div>
              <span className="font-display font-bold text-white text-sm">F.O.C.U.S.</span>
              <span className="font-mono text-neo-grey text-xs ml-2">MOMENTUM</span>
            </div>
          </div>

          {/* Info */}
          <div className="flex items-center gap-4 text-sm">
            <span className="font-mono text-neo-grey">
              © {new Date().getFullYear()}
            </span>
            <span className="px-3 py-1 bg-neo-blue text-white font-mono text-xs border-neo-sm border-white">
              v1.0.1
            </span>
          </div>
        </div>
      </div>
    </footer>
  )
}
