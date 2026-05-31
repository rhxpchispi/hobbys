import { useCallback, useState } from 'react'
import type { Curso } from '../types/course'

export function useSelectedCourse() {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [selectGeneration, setSelectGeneration] = useState(0)

  const selectCourse = useCallback((curso: Curso) => {
    setSelectedId(curso.id)
    setSelectGeneration((g) => g + 1)
  }, [])

  const clearSelection = useCallback(() => {
    setSelectedId(null)
  }, [])

  return { selectedId, selectCourse, selectGeneration, clearSelection }
}
