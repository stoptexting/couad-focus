'use client'

import { useEffect, useRef, useState, useCallback } from 'react'

export interface UseScrollAnimationOptions {
  threshold?: number
  rootMargin?: string
  triggerOnce?: boolean
}

export interface UseScrollAnimationReturn {
  ref: React.RefObject<HTMLElement | null>
  isVisible: boolean
  hasAnimated: boolean
}

export function useScrollAnimation({
  threshold = 0.1,
  rootMargin = '0px 0px -50px 0px',
  triggerOnce = true,
}: UseScrollAnimationOptions = {}): UseScrollAnimationReturn {
  const ref = useRef<HTMLElement | null>(null)
  const [isVisible, setIsVisible] = useState(false)
  const [hasAnimated, setHasAnimated] = useState(false)

  useEffect(() => {
    const element = ref.current
    if (!element) return

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)'
    ).matches

    if (prefersReducedMotion) {
      setIsVisible(true)
      setHasAnimated(true)
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true)
            setHasAnimated(true)

            if (triggerOnce) {
              observer.unobserve(element)
            }
          } else if (!triggerOnce) {
            setIsVisible(false)
          }
        })
      },
      {
        threshold,
        rootMargin,
      }
    )

    observer.observe(element)

    return () => {
      observer.disconnect()
    }
  }, [threshold, rootMargin, triggerOnce])

  return { ref, isVisible, hasAnimated }
}

// Hook for staggered list animations
export function useStaggeredAnimation(itemCount: number, options: UseScrollAnimationOptions = {}) {
  const containerRef = useRef<HTMLElement | null>(null)
  const [visibleItems, setVisibleItems] = useState<boolean[]>(
    new Array(itemCount).fill(false)
  )

  const { threshold = 0.1, rootMargin = '0px', triggerOnce = true } = options

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const prefersReducedMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)'
    ).matches

    if (prefersReducedMotion) {
      setVisibleItems(new Array(itemCount).fill(true))
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // Stagger the visibility of items
            for (let i = 0; i < itemCount; i++) {
              setTimeout(() => {
                setVisibleItems((prev) => {
                  const next = [...prev]
                  next[i] = true
                  return next
                })
              }, i * 75)
            }

            if (triggerOnce) {
              observer.unobserve(container)
            }
          }
        })
      },
      { threshold, rootMargin }
    )

    observer.observe(container)

    return () => observer.disconnect()
  }, [itemCount, threshold, rootMargin, triggerOnce])

  return { containerRef, visibleItems }
}
