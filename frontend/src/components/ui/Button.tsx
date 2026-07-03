'use client';

import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/cn';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  icon?: ReactNode;
  isLoading?: boolean;
}

const variants: Record<ButtonVariant, string> = {
  primary: 'border-cyan-400/50 bg-cyan-400/15 text-cyan-100 hover:border-cyan-300 hover:bg-cyan-400/25',
  secondary: 'border-slate-600/70 bg-slate-900/65 text-slate-100 hover:border-slate-400 hover:bg-slate-800/80',
  ghost: 'border-transparent bg-transparent text-slate-400 hover:bg-slate-800/70 hover:text-slate-100',
  danger: 'border-red-400/40 bg-red-500/15 text-red-200 hover:border-red-300 hover:bg-red-500/25',
};

export default function Button({
  children,
  className,
  variant = 'secondary',
  icon,
  isLoading,
  disabled,
  type = 'button',
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || isLoading}
      className={cn(
        'inline-flex min-h-10 items-center justify-center gap-2 rounded-lg border px-4 text-sm font-semibold transition-all',
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-300',
        'disabled:pointer-events-none disabled:opacity-50',
        variants[variant],
        className,
      )}
      {...props}
    >
      {isLoading ? <span className="h-2 w-2 rounded-full bg-current animate-pulse" aria-hidden="true" /> : icon}
      {children}
    </button>
  );
}
