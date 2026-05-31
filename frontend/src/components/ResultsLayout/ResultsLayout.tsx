import type { Curso } from '../../types/course'
import type { SearchStatus } from '../../hooks/useCourseSearch'
import { useScrollToSelectedCard } from '../../hooks/useScrollToSelectedCard'
import { CourseCard } from '../CourseCard/CourseCard'
import { CourseCardSkeleton } from '../CourseCard/CourseCardSkeleton'
import { MapContainer } from '../MapContainer/MapContainer'
import styles from './ResultsLayout.module.css'

interface ResultsLayoutProps {
  cursos: Curso[]
  totalResultados: number
  status: SearchStatus
  error: string | null
  selectedId: number | null
  selectGeneration: number
  onSelectCourse: (curso: Curso) => void
  onMarkerOpen: (curso: Curso) => void
  visible: boolean
}

export function ResultsLayout({
  cursos,
  totalResultados,
  status,
  error,
  selectedId,
  selectGeneration,
  onSelectCourse,
  onMarkerOpen,
  visible,
}: ResultsLayoutProps) {
  const isLoading = status === 'loading'
  useScrollToSelectedCard(selectedId)

  const countLabel = () => {
    if (isLoading) return 'Buscando talleres perfectos para vos...'
    if (status === 'error') return error ?? 'Error al buscar'
    if (totalResultados === 0) {
      return 'No encontramos opciones exactas. Probá describiendo tu hobby de otra manera.'
    }
    return `Cerca de ${totalResultados} resultados encontrados`
  }

  return (
    <section
      className={`${styles.layout} ${visible ? styles.layoutVisible : ''}`}
      aria-hidden={!visible}
    >
      <aside className={styles.sidebar}>
        <p className={styles.count} role="status">
          {countLabel()}
        </p>

        <div className={styles.list}>
          {isLoading &&
            Array.from({ length: 4 }).map((_, i) => <CourseCardSkeleton key={i} />)}

          {!isLoading &&
            status !== 'error' &&
            cursos.map((curso) => (
              <CourseCard
                key={curso.id}
                curso={curso}
                isSelected={selectedId === curso.id}
                onSelect={onSelectCourse}
              />
            ))}
        </div>
      </aside>

      <div className={styles.mapPane}>
        <MapContainer
          cursos={cursos}
          selectedId={selectedId}
          selectGeneration={selectGeneration}
          isLoading={isLoading}
          visible={visible}
          onMarkerOpen={onMarkerOpen}
        />
      </div>
    </section>
  )
}
