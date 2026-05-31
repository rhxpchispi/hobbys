export interface Coordenadas {
  latitud: number
  longitud: number
}

export interface Curso {
  id: number
  titulo: string
  descripcion: string
  barrio: string
  coordenadas: Coordenadas
  precio: number
  modalidad_pago: string
  valoracion: number
  similarity_score?: number | null
  whatsapp?: string | null
  instagram?: string | null
}

export interface SearchResponse {
  query: string
  total_resultados: number
  cursos: Curso[]
}

export interface SearchRequest {
  query: string
}
