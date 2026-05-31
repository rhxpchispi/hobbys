import styles from './CourseCard.module.css'

export function CourseCardSkeleton() {
  return (
    <div className={styles.skeleton} aria-hidden="true">
      <div className={`${styles.skeletonLine} ${styles.skeletonTitle}`} />
      <div className={`${styles.skeletonLine} ${styles.skeletonRating}`} />
      <div className={`${styles.skeletonLine} ${styles.skeletonShort}`} />
      <div className={`${styles.skeletonLine} ${styles.skeletonBody}`} />
      <div className={`${styles.skeletonLine} ${styles.skeletonBody}`} />
      <div className={`${styles.skeletonLine} ${styles.skeletonBody}`} />
    </div>
  )
}
