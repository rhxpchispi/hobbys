import { useCallback, useState } from 'react'
import { SearchHome } from './components/SearchHome/SearchHome'
import { ResultsLayout } from './components/ResultsLayout/ResultsLayout'
import { useCourseSearch } from './hooks/useCourseSearch'
import { useSelectedCourse } from './hooks/useSelectedCourse'
import './styles/global.css'

export default function App() {
  const [inputQuery, setInputQuery] = useState('')
  const {
    query,
    cursos,
    totalResultados,
    status,
    error,
    hasSearched,
    search,
  } = useCourseSearch()
  const { selectedId, selectCourse, selectGeneration, clearSelection } =
    useSelectedCourse()

  const isResultsMode = hasSearched

  const runSearch = useCallback(
    async (q?: string) => {
      const text = (q ?? inputQuery).trim()
      if (!text) return
      setInputQuery(text)
      clearSelection()
      await search(text)
    },
    [inputQuery, search, clearSelection],
  )

  const handleSuggestion = useCallback(
    async (text: string) => {
      setInputQuery(text)
      clearSelection()
      await search(text)
    },
    [search, clearSelection],
  )

  return (
    <div className={`app ${isResultsMode ? 'app--results' : ''}`}>
      <SearchHome
        query={inputQuery || query}
        onQueryChange={setInputQuery}
        onSearch={() => void runSearch()}
        onSuggestionSelect={(text) => void handleSuggestion(text)}
        isResultsMode={isResultsMode}
      />

      <ResultsLayout
        cursos={cursos}
        totalResultados={totalResultados}
        status={status}
        error={error}
        selectedId={selectedId}
        selectGeneration={selectGeneration}
        onSelectCourse={selectCourse}
        onMarkerOpen={selectCourse}
        visible={isResultsMode}
      />
    </div>
  )
}
