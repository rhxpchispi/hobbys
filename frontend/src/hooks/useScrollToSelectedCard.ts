import { useEffect } from 'react'

export function useScrollToSelectedCard(selectedId: number | null) {
  useEffect(() => {
    if (selectedId == null) return

    const el = document.getElementById(`course-card-${selectedId}`)
    el?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [selectedId])
}
