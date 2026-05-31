import { useCallback, useState } from 'react'
import { postSearch, SearchApiError } from '../api/search'
import type { Curso } from '../types/course'

export type SearchStatus = 'idle' | 'loading' | 'success' | 'error'

export interface UseCourseSearchResult {
  query: string
  cursos: Curso[]
  totalResultados: number
  status: SearchStatus
  error: string | null
  hasSearched: boolean
  search: (query: string) => Promise<void>
  reset: () => void
}

export function useCourseSearch(): UseCourseSearchResult {
  const [query, setQuery] = useState('')
  const [cursos, setCursos] = useState<Curso[]>([])
  const [totalResultados, setTotalResultados] = useState(0)
  const [status, setStatus] = useState<SearchStatus>('idle')
  const [error, setError] = useState<string | null>(null)
  const [hasSearched, setHasSearched] = useState(false)

  const search = useCallback(async (searchQuery: string) => {
    const trimmed = searchQuery.trim()
    if (!trimmed) return

    setQuery(trimmed)
    setHasSearched(true)
    setStatus('loading')
    setError(null)

    try {
      const data = await postSearch({ query: trimmed })
      setCursos(data.cursos)
      setTotalResultados(data.total_resultados)
      setStatus('success')
    } catch (err) {
      setCursos([])
      setTotalResultados(0)
      setStatus('error')
      if (err instanceof SearchApiError) {
        setError(
          err.status === 503
            ? 'El backend aún no está listo. Verificá que FastAPI esté corriendo.'
            : err.message,
        )
      } else if (err instanceof TypeError) {
        setError('No se pudo conectar con el backend. ¿Está FastAPI en el puerto 8000?')
      } else {
        setError('Ocurrió un error inesperado al buscar.')
      }
    }
  }, [])

  const reset = useCallback(() => {
    setQuery('')
    setCursos([])
    setTotalResultados(0)
    setStatus('idle')
    setError(null)
    setHasSearched(false)
  }, [])

  return {
    query,
    cursos,
    totalResultados,
    status,
    error,
    hasSearched,
    search,
    reset,
  }
}
