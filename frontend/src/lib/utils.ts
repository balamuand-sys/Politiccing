import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return 'Ukjent dato'
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('nb-NO', { year: 'numeric', month: 'long', day: 'numeric' })
  } catch {
    return dateStr
  }
}

export function docTypeLabel(type: string | null | undefined): string {
  const map: Record<string, string> = {
    innkalling: 'Innkalling',
    saksdokument: 'Saksdokument',
    protokoll: 'Protokoll',
    vedlegg: 'Vedlegg',
  }
  return type ? (map[type] || type) : 'Ukjent type'
}

export function docTypeBadgeColor(type: string | null | undefined): string {
  const map: Record<string, string> = {
    innkalling: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
    saksdokument: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
    protokoll: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
    vedlegg: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
  }
  return type ? (map[type] || 'bg-gray-100 text-gray-600') : 'bg-gray-100 text-gray-600'
}

export function enrichmentTypeLabel(type: string): string {
  const map: Record<string, string> = {
    law: 'Lover og forskrifter',
    news: 'Nyhetsartikler',
    research: 'Forskning og rapporter',
    municipal_comparison: 'Andre kommuner',
    budget: 'Budsjett og økonomi',
  }
  return map[type] || type
}

export function truncate(text: string, max: number): string {
  if (text.length <= max) return text
  return text.slice(0, max) + '…'
}
