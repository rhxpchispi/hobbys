import { SearchBar } from './SearchBar'
import { Suggestions } from '../Suggestions/Suggestions'
import styles from './SearchHome.module.css'

interface SearchHomeProps {
  query: string
  onQueryChange: (value: string) => void
  onSearch: () => void
  onSuggestionSelect: (query: string) => void
  isResultsMode: boolean
}

export function SearchHome({
  query,
  onQueryChange,
  onSearch,
  onSuggestionSelect,
  isResultsMode,
}: SearchHomeProps) {
  return (
    <header
      className={`${styles.shell} ${isResultsMode ? styles.shellResults : ''}`}
    >
      <h1 className={`${styles.brand} ${isResultsMode ? styles.brandCompact : ''}`}>
        Proyecto <span className={styles.brandAccent}>Hobbys</span>
      </h1>

      <div className={styles.searchWrap}>
        <SearchBar
          value={query}
          onChange={onQueryChange}
          onSubmit={onSearch}
          compact={isResultsMode}
        />
      </div>

      <Suggestions
        visible={!isResultsMode}
        onSelect={(text) => {
          onQueryChange(text)
          onSuggestionSelect(text)
        }}
      />
    </header>
  )
}
