import { useEffect, useRef } from 'react'
import { Marker, Popup } from 'react-leaflet'
import type { Marker as LeafletMarker } from 'leaflet'
import type { Curso } from '../../types/course'
import { MapPopupContent } from './MapPopupContent'

const FLY_TO_MS = 650

interface CourseMarkerProps {
  curso: Curso
  position: [number, number]
  selectedId: number | null
  selectGeneration: number
  onMarkerOpen: (curso: Curso) => void
}

export function CourseMarker({
  curso,
  position,
  selectedId,
  selectGeneration,
  onMarkerOpen,
}: CourseMarkerProps) {
  const markerRef = useRef<LeafletMarker>(null)

  useEffect(() => {
    if (selectedId !== curso.id) return

    const timer = window.setTimeout(() => {
      markerRef.current?.openPopup()
    }, FLY_TO_MS)

    return () => window.clearTimeout(timer)
  }, [selectedId, selectGeneration, curso.id])

  return (
    <Marker
      ref={markerRef}
      position={position}
      eventHandlers={{
        popupopen: () => onMarkerOpen(curso),
      }}
    >
      <Popup closeButton minWidth={160}>
        <MapPopupContent curso={curso} />
      </Popup>
    </Marker>
  )
}
