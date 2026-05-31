import { useEffect } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
import type { Curso } from '../../types/course'

const DEFAULT_CENTER: L.LatLngExpression = [-34.6037, -58.3816]
const DEFAULT_ZOOM = 12

interface MapControllerProps {
  cursos: Curso[]
  selectedId: number | null
  visible: boolean
}

function getLatLng(curso: Curso): L.LatLngTuple | null {
  const { latitud, longitud } = curso.coordenadas ?? {}
  if (typeof latitud !== 'number' || typeof longitud !== 'number') return null
  return [latitud, longitud]
}

export function MapController({ cursos, selectedId, visible }: MapControllerProps) {
  const map = useMap()

  useEffect(() => {
    if (!visible) return
    const timer = window.setTimeout(() => {
      map.invalidateSize()
    }, 650)
    return () => window.clearTimeout(timer)
  }, [map, visible])

  useEffect(() => {
    const points = cursos
      .map(getLatLng)
      .filter((p): p is L.LatLngTuple => p !== null)

    if (points.length === 0) {
      map.setView(DEFAULT_CENTER, DEFAULT_ZOOM)
      return
    }

    if (points.length === 1) {
      map.setView(points[0], 14, { animate: true })
      return
    }

    const bounds = L.latLngBounds(points)
    map.fitBounds(bounds, { padding: [50, 50], animate: true })
  }, [cursos, map])

  useEffect(() => {
    if (selectedId == null) return
    const curso = cursos.find((c) => c.id === selectedId)
    if (!curso) return
    const latlng = getLatLng(curso)
    if (!latlng) return
    map.flyTo(latlng, 15, { duration: 0.6 })
  }, [selectedId, cursos, map])

  return null
}
