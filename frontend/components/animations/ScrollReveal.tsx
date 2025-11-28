'use client'

import React from 'react'
import { cn } from '@/lib/utils'
import { useScrollAnimation, UseScrollAnimationOptions } from '@/hooks/useScrollAnimation'

export type AnimationType =
  | 'fade-in'
  | 'fade-in-up'
  | 'fade-in-down'
  | 'fade-in-left'
  | 'fade-in-right'
  | 'scale-in'

interface ScrollRevealProps extends React.HTMLAttributes<HTMLDivElement> {
  animation?: AnimationType
  delay?: number
  duration?: number
  children: React.ReactNode
  as?: React.ElementType
  options?: UseScrollAnimationOptions
}

export function ScrollReveal({
  animation = 'fade-in-up',
  delay = 0,
  duration = 500,
  children,
  className,
  as: Component = 'div',
  options = {},
  style,
  ...props
}: ScrollRevealProps) {
  const { ref, isVisible } = useScrollAnimation(options)

  return (
    <Component
      ref={ref as React.RefObject<HTMLDivElement>}
      className={cn(
        isVisible ? `animate-${animation}` : 'opacity-0',
        className
      )}
      style={{
        animationDelay: `${delay}ms`,
        animationDuration: `${duration}ms`,
        animationFillMode: 'both',
        ...style,
      }}
      {...props}
    >
      {children}
    </Component>
  )
}

// Staggered list component
interface StaggeredListProps extends React.HTMLAttributes<HTMLDivElement> {
  animation?: AnimationType
  staggerDelay?: number
  children: React.ReactNode
}

export function StaggeredList({
  animation = 'fade-in-up',
  staggerDelay = 75,
  children,
  className,
  ...props
}: StaggeredListProps) {
  const childArray = React.Children.toArray(children)

  return (
    <div className={className} {...props}>
      {childArray.map((child, index) => (
        <ScrollReveal
          key={index}
          animation={animation}
          delay={index * staggerDelay}
        >
          {child}
        </ScrollReveal>
      ))}
    </div>
  )
}
