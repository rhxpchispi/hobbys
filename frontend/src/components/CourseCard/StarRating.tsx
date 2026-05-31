import styles from './CourseCard.module.css'

interface StarRatingProps {
  rating: number
  showValue?: boolean
  size?: 'sm' | 'md'
}

export function StarRating({
  rating,
  showValue = false,
  size = 'md',
}: StarRatingProps) {
  const clamped = Math.min(5, Math.max(0, rating))
  const full = Math.round(clamped)
  const stars = Array.from({ length: 5 }, (_, i) => i < full)
  const sizeClass = size === 'md' ? styles.starsMd : styles.starsSm

  return (
    <span
      className={`${styles.stars} ${sizeClass}`}
      aria-label={`Valoración ${clamped.toFixed(1)} de 5`}
    >
      {stars.map((filled, i) => (
        <span key={i} className={filled ? styles.starFilled : styles.starEmpty}>
          ★
        </span>
      ))}
      {showValue && (
        <span className={styles.ratingValue}>{clamped.toFixed(1)}</span>
      )}
    </span>
  )
}
