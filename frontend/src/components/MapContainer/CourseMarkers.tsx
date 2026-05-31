import type { Curso } from '../../types/course'
import { CourseMarker } from './CourseMarker'

interface CourseMarkersProps {
  cursos: Curso[]
  selectedId: number | null
  selectGeneration: number
  onMarkerOpen: (curso: Curso) => void
}

export function CourseMarkers({
  cursos,
  selectedId,
  selectGeneration,
  onMarkerOpen,
}: CourseMarkersProps) {
  return (
    <>
      {cursos.map((curso) => {
        const { latitud, longitud } = curso.coordenadas ?? {}
        if (typeof latitud !== 'number' || typeof longitud !== 'number') {
          return null
        }

        return (
          <CourseMarker
            key={curso.id}
            curso={curso}
            position={[latitud, longitud]}
            selectedId={selectedId}
            selectGeneration={selectGeneration}
            onMarkerOpen={onMarkerOpen}
          />
        )
      })}
    </>
  )
}
