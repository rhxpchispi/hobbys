import type { Curso } from '../../types/course'
import { buildInstagramUrl, buildWhatsAppUrl } from '../../utils/contactLinks'
import { InstagramIcon, WhatsAppIcon } from './ContactIcons'
import { StarRating } from './StarRating'
import styles from './CourseCard.module.css'

interface CourseCardProps {
  curso: Curso
  isSelected: boolean
  onSelect: (curso: Curso) => void
}

function formatPrecio(precio: number): string {
  return precio > 0 ? `$${precio.toLocaleString('es-AR')}` : 'Consultar'
}

export function CourseCard({ curso, isSelected, onSelect }: CourseCardProps) {
  const waUrl = buildWhatsAppUrl(curso.whatsapp)
  const igUrl = buildInstagramUrl(curso.instagram)
  const hasContacts = Boolean(waUrl || igUrl)

  return (
    <article
      id={`course-card-${curso.id}`}
      className={`${styles.card} ${isSelected ? styles.cardSelected : ''}`}
      onClick={() => onSelect(curso)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onSelect(curso)
        }
      }}
      role="button"
      tabIndex={0}
      aria-pressed={isSelected}
    >
      <header className={styles.header}>
        <h3 className={styles.title}>{curso.titulo}</h3>
        <div className={styles.ratingBlock}>
          <StarRating rating={curso.valoracion} size="md" showValue />
        </div>
      </header>

      <ul className={styles.facts} aria-label="Detalles del curso">
        <li className={styles.fact}>{curso.barrio}</li>
        <li className={styles.fact}>{formatPrecio(curso.precio)}</li>
        {curso.modalidad_pago ? (
          <li className={styles.fact}>{curso.modalidad_pago}</li>
        ) : null}
      </ul>

      <p className={styles.desc}>{curso.descripcion}</p>

      {hasContacts && (
        <footer className={styles.contactRow}>
          {waUrl && (
            <a
              className={`${styles.contactPill} ${styles.contactPillWa}`}
              href={waUrl}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              aria-label="Contactar por WhatsApp"
            >
              <WhatsAppIcon className={styles.contactIcon} />
              <span>WhatsApp</span>
            </a>
          )}
          {igUrl && (
            <a
              className={`${styles.contactPill} ${styles.contactPillIg}`}
              href={igUrl}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              aria-label="Ver en Instagram"
            >
              <InstagramIcon className={styles.contactIcon} />
              <span>Instagram</span>
            </a>
          )}
        </footer>
      )}
    </article>
  )
}
