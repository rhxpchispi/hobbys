import { SUGGESTION_CHIPS } from '../../constants/suggestions'
import styles from './Suggestions.module.css'

interface SuggestionsProps {
  onSelect: (query: string) => void
  visible: boolean
}

export function Suggestions({ onSelect, visible }: SuggestionsProps) {
  if (!visible) return null

  return (
    <div className={styles.wrapper} role="group" aria-label="Sugerencias de búsqueda">
      {SUGGESTION_CHIPS.map((text) => (
        <button
          key={text}
          type="button"
          className={styles.chip}
          onClick={() => onSelect(text)}
        >
          {text}
        </button>
      ))}
    </div>
  )
}
