import type { FormEvent } from 'react'

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  compact?: boolean
}

export function SearchBar({ value, onChange, onSubmit, compact = false }: SearchBarProps) {
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    onSubmit()
  }

  return (
    <form
      className={compact ? 'searchBar searchBar--compact' : 'searchBar'}
      onSubmit={handleSubmit}
      role="search"
    >
      <input
        type="search"
        className="searchBar__input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="¿Qué te gustaría aprender hoy?"
        autoComplete="off"
        aria-label="Buscar cursos"
      />
    </form>
  )
}
