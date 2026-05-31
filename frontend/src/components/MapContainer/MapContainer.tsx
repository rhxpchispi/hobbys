import L from 'leaflet'
import { MapContainer as LeafletMap, TileLayer } from 'react-leaflet'
import type { Curso } from '../../types/course'
import { MapController } from './MapController'
import { CourseMarkers } from './CourseMarkers'
import styles from './MapContainer.module.css'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

import 'leaflet/dist/leaflet.css'

delete (L.Icon.Default.prototype as { _getIconUrl?: unknown })._getIconUrl
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
})

interface MapContainerProps {
  cursos: Curso[]
  selectedId: number | null
  selectGeneration: number
  isLoading: boolean
  visible: boolean
  onMarkerOpen: (curso: Curso) => void
}

const CABA_CENTER: [number, number] = [-34.6037, -58.3816]

export function MapContainer({
  cursos,
  selectedId,
  selectGeneration,
  isLoading,
  visible,
  onMarkerOpen,
}: MapContainerProps) {
  return (
    <div className={styles.wrap}>
      {isLoading && (
        <div className={styles.loadingOverlay} aria-live="polite">
          <span className={styles.spinner} aria-hidden="true" />
          Cargando mapa...
        </div>
      )}
      <LeafletMap
        className={styles.map}
        center={CABA_CENTER}
        zoom={12}
        scrollWheelZoom
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <CourseMarkers
          cursos={cursos}
          selectedId={selectedId}
          selectGeneration={selectGeneration}
          onMarkerOpen={onMarkerOpen}
        />
        <MapController cursos={cursos} selectedId={selectedId} visible={visible} />
      </LeafletMap>
    </div>
  )
}
