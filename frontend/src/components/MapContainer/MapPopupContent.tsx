import type { Curso } from '../../types/course'
import { buildGoogleMapsDirectionsUrl } from '../../utils/mapsLinks'
import styles from './MapPopupContent.module.css'

interface MapPopupContentProps {
  curso: Curso
}

export function MapPopupContent({ curso }: MapPopupContentProps) {
  const { latitud, longitud } = curso.coordenadas ?? {}
  const hasCoords =
    typeof latitud === 'number' && typeof longitud === 'number'
  const directionsUrl = hasCoords
    ? buildGoogleMapsDirectionsUrl(latitud, longitud)
    : null

  return (
    <div className={styles.popup}>
      <p className={styles.title}>{curso.titulo}</p>
      <p className={styles.barrio}>{curso.barrio}</p>

      <p className={styles.hint}>
        <span className={styles.hintArrow} aria-hidden="true">
          ←
        </span>
        Más info en la lista
      </p>

      {directionsUrl && (
        <a
          className={styles.directions}
          href={directionsUrl}
          target="_blank"
          rel="noopener noreferrer"
        >
          Cómo llegar
        </a>
      )}
    </div>
  )
}
