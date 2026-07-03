'use client';

import { motion } from 'framer-motion';
import type { ReactNode } from 'react';
import { cn } from '@/lib/cn';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  id?: string;
  disableMotion?: boolean;
  as?: 'section' | 'div' | 'article';
  variant?: 'glass' | 'solid';
}

export default function GlassCard({
  children,
  className,
  hover = true,
  id,
  disableMotion = false,
  as = 'section',
  variant = 'glass',
}: GlassCardProps) {
  const Tag = as;
  const classes = cn(variant === 'glass' ? 'glass-card p-4 sm:p-5' : 'solid-card p-4 sm:p-5', className);

  if (disableMotion) {
    return (
      <Tag id={id} className={classes}>
        {children}
      </Tag>
    );
  }

  return (
    <motion.section
      id={id}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, ease: 'easeOut' }}
      whileHover={hover ? { y: -2 } : undefined}
      className={classes}
    >
      {children}
    </motion.section>
  );
}
