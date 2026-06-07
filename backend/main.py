"""
Backend API para búsqueda híbrida de cursos.
Implementa: extracción de intención, filtrado duro por categoría y público,
similitud semántica con Qdrant sobre título + descripción y soft boosting por nivel.

Arquitectura:
- Persistencia: Qdrant Vector DB (colección "cursos_hobby")
- Vectores: Asimétricos (título: 384 dims @ 70%, descripción: 384 dims @ 30%)
- Distancia: Cosine similarity
- Pipeline: Intención → Búsqueda Qdrant → Ponderación asimétrica → Soft Boosting → Ordenamiento
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client import models

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ============================================================================
# SCHEMAS PYDANTIC
# ============================================================================

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)


class CursoResponse(BaseModel):
    id: int
    titulo: str
    descripcion: str
    barrio: str
    coordenadas: dict
    precio: float
    modalidad_pago: str
    valoracion: float
    docente: Optional[str] = None
    whatsapp: Optional[str] = None
    instagram: Optional[str] = None
    similarity_score: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    total_resultados: int
    cursos: List[CursoResponse]


# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================

app = FastAPI(
    title="API de Búsqueda Híbrida",
    description="Motor de búsqueda con filtros lógicos, ranking semántico y persistencia en Qdrant",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales
qdrant_client: Optional[QdrantClient] = None
model: Optional[SentenceTransformer] = None
cursos_data: List[dict] = []
categorias_disponibles: List[str] = []

# Configuración Qdrant (lee desde variables de entorno)
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "cursos_hobby"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2 dimension

# Ponderación asimétrica para búsqueda semántica
TITLE_WEIGHT = 0.70
DESCRIPTION_WEIGHT = 0.30
MIN_TITLE_SIMILARITY = 0.35

# Identificadores de campos vectoriales en Qdrant
TITLE_VECTOR_NAME = "titulo_vector"
DESCRIPTION_VECTOR_NAME = "descripcion_vector"


# ============================================================================
# FUNCIONES AUXILIARES DE NORMALIZACIÓN
# ============================================================================

def normalize_text(text: str) -> str:
    """Normaliza texto: minúsculas, quita acentos, caracteres especiales y espacios múltiples."""
    if not text:
        return ""
    normalized = text.lower()
    normalized = normalized.translate(str.maketrans("áéíóúüñ", "aeiouun"))
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def extract_unique_values(cursos: List[dict], key: str) -> List[str]:
    """Extrae valores únicos de un campo en la lista de cursos."""
    values = {str(curso.get(key, "")).strip() for curso in cursos if str(curso.get(key, "")).strip()}
    return sorted(values, key=lambda item: item.lower())


# ============================================================================
# FUNCIONES DE DETECCIÓN DE INTENCIÓN
# ============================================================================

def detect_exact_category(query: str, categories: List[str]) -> Optional[str]:
    """Detecta si la query menciona explícitamente una categoría exacta."""
    query_norm = normalize_text(query)
    
    # Mapeo inteligente de raíces verbales o sinónimos comunes
    raiz_map = {
        "cocin": "cocina",
        "bord": "bordado",
        "pint": "pintura",
        "tejid": "tejido",
        "tejer": "tejido",
        "marcial": "artes marciales",
        "judo": "artes marciales",
        "karate": "artes marciales"
    }
    
    for raiz, cat_destino in raiz_map.items():
        if raiz in query_norm:
            for category in categories:
                if normalize_text(category) == normalize_text(cat_destino):
                    return category

    for category in categories:
        cat_norm = normalize_text(category)
        if re.search(rf"\b{re.escape(cat_norm)}\b", query_norm):
            return category
            
    return None


def detect_explicit_public(query: str) -> Optional[str]:
    """Detecta si el usuario está pidiendo un público específico en su frase."""
    query_norm = normalize_text(query)
    tokens = set(query_norm.split())

    infantil_tokens = {"nino", "ninos", "nina", "ninas", "nene", "nenes", "nena", "nenas", "infantil", "kids", "chicos", "chico"}
    adultos_tokens = {"adulto", "adultos", "grande", "grandes", "mayor", "mayores"}
    juvenil_tokens = {"joven", "jovenes", "juvenil", "adolescente", "adolescentes"}

    if tokens & infantil_tokens:
        return "infantil"
    if tokens & adultos_tokens:
        return "adultos"
    if tokens & juvenil_tokens:
        return "juvenil"
        
    return None


def course_belongs_to_category(curso: dict, categoria: str) -> bool:
    """Verifica si un curso pertenece a una categoría exacta."""
    course_value = normalize_text(curso.get("categoria", ""))
    expected = normalize_text(categoria)
    if not course_value or not expected:
        return False
    return course_value == expected or bool(re.search(rf"\b{re.escape(expected)}\b", course_value))


def course_matches_label(curso: dict, query_text: str, field: str) -> bool:
    """
    Compara normalizado si el curso hace match con lo que el usuario busca en un campo específico.
    Soporta aliases inteligentes (ej: "niño" → "infantil").
    """
    if not query_text:
        return False
        
    course_value = str(curso.get(field, "")).strip().lower()
    if not course_value:
        return False
        
    query_norm = normalize_text(query_text)
    course_norm = normalize_text(course_value)

    if course_norm in query_norm:
        return True

    query_tokens = set(query_norm.split())
    
    # Diccionario de equivalencias: lo que escribe el usuario ↔ valor del JSON
    alias_map = {
        "nino": "infantil", "ninos": "infantil", "nina": "infantil", "ninas": "infantil",
        "nene": "infantil", "nenes": "infantil", "nena": "infantil", "nenas": "infantil",
        "kids": "infantil", "chicos": "infantil", "chico": "infantil", "infantil": "infantil",
        "adulto": "adultos", "adultos": "adultos", "grandes": "adultos", "grande": "adultos",
        "joven": "juvenil", "jovenes": "juvenil", "juvenil": "juvenil",
        "principiante": "inicial", "principiantes": "inicial", "basico": "inicial", 
        "basica": "inicial", "cero": "inicial", "nada": "inicial"
    }
    
    expanded_query_tokens = set()
    for token in query_tokens:
        expanded_query_tokens.add(token)
        if token in alias_map:
            expanded_query_tokens.add(alias_map[token])

    course_tokens = set(course_norm.split())
    normalized_course_tokens = set()
    for token in course_tokens:
        normalized_course_tokens.add(token)
        if token in alias_map:
            normalized_course_tokens.add(alias_map[token])

    return bool(expanded_query_tokens & normalized_course_tokens)


# ============================================================================
# FUNCIONES DE GESTIÓN QDRANT
# ============================================================================

def initialize_qdrant_collection() -> None:
    """Inicializa la colección Qdrant 'cursos_hobby' si no existe."""
    try:
        collections = qdrant_client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if COLLECTION_NAME not in collection_names:
            logger.info(f"Creando colección '{COLLECTION_NAME}' en Qdrant...")
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config={
                    TITLE_VECTOR_NAME: models.VectorParams(
                        size=VECTOR_SIZE,
                        distance=models.Distance.COSINE
                    ),
                    DESCRIPTION_VECTOR_NAME: models.VectorParams(
                        size=VECTOR_SIZE,
                        distance=models.Distance.COSINE
                    )
                }
            )
            logger.info(f"Colección '{COLLECTION_NAME}' creada exitosamente.")
        else:
            logger.info(f"Colección '{COLLECTION_NAME}' ya existe.")
    except Exception as exc:
        logger.error(f"Error al inicializar colección Qdrant: {exc}", exc_info=True)
        raise


def upsert_courses_to_qdrant(cursos: List[dict]) -> None:
    """
    Inserta/actualiza cursos en Qdrant con embeddings de título y descripción.
    Cada punto tiene dos vectores named: titulo_vector y descripcion_vector.
    """
    if not cursos:
        logger.warning("No hay cursos para insertar en Qdrant.")
        return
    
    try:
        logger.info(f"Generando embeddings para {len(cursos)} cursos...")
        
        titulos = [str(curso.get("titulo", "")).strip() for curso in cursos]
        descripciones = [str(curso.get("descripcion", "")).strip() for curso in cursos]
        
        embeddings_titulo = model.encode(titulos, convert_to_numpy=True)
        embeddings_descripcion = model.encode(descripciones, convert_to_numpy=True)
        
        logger.info("Preparando puntos para Qdrant...")
        points = []
        
        for idx, curso in enumerate(cursos):
            punto = models.PointStruct(
                id=curso["id"],
                vector={
                    TITLE_VECTOR_NAME: embeddings_titulo[idx].tolist(),
                    DESCRIPTION_VECTOR_NAME: embeddings_descripcion[idx].tolist()
                },
                payload={
                    "id": curso["id"],
                    "titulo": curso.get("titulo", ""),
                    "descripcion": curso.get("descripcion", ""),
                    "barrio": curso.get("barrio", ""),
                    "categoria": curso.get("categoria", ""),
                    "nivel": curso.get("nivel", ""),
                    "publico": curso.get("publico", ""),
                    "precio": curso.get("precio", 0),
                    "modalidad_pago": curso.get("modalidad_pago", ""),
                    "valoracion": curso.get("valoracion", 0.0),
                    "coordenadas": curso.get("coordenadas", {}),
                    "docente": curso.get("docente", ""),
                    "whatsapp": curso.get("whatsapp", ""),
                    "instagram": curso.get("instagram", "")
                }
            )
            points.append(punto)
        
        logger.info(f"Insertando {len(points)} puntos en Qdrant...")
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        logger.info(f"Insertados {len(points)} cursos en Qdrant exitosamente.")
        
    except Exception as exc:
        logger.error(f"Error al insertar cursos en Qdrant: {exc}", exc_info=True)
        raise


def cargar_datos() -> List[dict]:
    """Carga datos de cursos desde data.json."""
    data_path = Path(__file__).parent / "data.json"
    if not data_path.exists():
        raise FileNotFoundError(f"El archivo {data_path} no existe")

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("cursos", [])


# ============================================================================
# EVENTOS DE CICLO DE VIDA
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Inicializa el servidor: conexión a Qdrant, carga de datos, embeddings."""
    global qdrant_client, model, cursos_data, categorias_disponibles
    
    max_retries = 5
    retry_delay = 2
    
    try:
        logger.info("Iniciando servidor...")
        
        # 1. Conectar a Qdrant con reintentos
        logger.info(f"Conectando a Qdrant en {QDRANT_HOST}:{QDRANT_PORT}...")
        for attempt in range(max_retries):
            try:
                qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, api_key=QDRANT_API_KEY)
                # Verificar conectividad
                qdrant_client.get_collections()
                logger.info("✓ Conexión a Qdrant exitosa.")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Intento {attempt + 1}/{max_retries} fallido: {e}. Reintentando en {retry_delay}s...")
                    import time
                    time.sleep(retry_delay)
                else:
                    raise
        
        # 2. Cargar modelo SentenceTransformer
        logger.info("Cargando modelo de embeddings 'all-MiniLM-L6-v2'...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("✓ Modelo cargado.")
        
        # 3. Cargar datos desde data.json
        logger.info("Cargando datos de cursos desde data.json...")
        cursos_data = cargar_datos()
        logger.info(f"✓ {len(cursos_data)} cursos cargados.")
        
        # 4. Extraer categorías disponibles
        categorias_disponibles = extract_unique_values(cursos_data, "categoria")
        logger.info(f"✓ Categorías disponibles: {categorias_disponibles}")
        
        # 5. Inicializar colección Qdrant
        initialize_qdrant_collection()
        
        # 6. Insertar cursos en Qdrant
        upsert_courses_to_qdrant(cursos_data)
        
        logger.info("✓ Servidor iniciado correctamente.")
        
    except Exception as exc:
        logger.critical(f"Error fatal al iniciar servidor: {exc}", exc_info=True)
        raise


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Verifica el estado del servidor."""
    try:
        collections = qdrant_client.get_collections()
        qdrant_status = "ok"
    except Exception:
        qdrant_status = "error"
    
    return {
        "status": "ok",
        "cursos_cargados": len(cursos_data),
        "qdrant": qdrant_status,
        "modelo": "all-MiniLM-L6-v2"
    }


@app.post("/api/search")
async def buscar_cursos(
    request: SearchRequest,
    sort: Optional[str] = Query(None, description="Campo para ordenar: 'similitud' o 'valoracion'")
):
    """
    Busca cursos con pipeline híbrido:
    1. Extrae intención (categoría + público explícito)
    2. Busca en Qdrant con vectores de título y descripción
    3. Aplica ponderación asimétrica (70% título, 30% descripción)
    4. Aplica soft boosting (infantil +20%, inicial +10%)
    5. Ordena por similitud o valoración
    """
    try:
        if not qdrant_client or not model or not cursos_data:
            raise HTTPException(status_code=503, detail="El servidor no está completamente inicializado")

        query = request.query.strip().lower()
        logger.info(f"Búsqueda recibida: '{query}'")

        # ===== PASO 1: EXTRACCIÓN DE INTENCIÓN =====
        categoria_exacta = detect_exact_category(query, categorias_disponibles)
        intent_publico = detect_explicit_public(query)

        if categoria_exacta:
            logger.info(f"Filtro estricto de CATEGORÍA detectado: {categoria_exacta}")
        if intent_publico:
            logger.info(f"Filtro estricto de PÚBLICO detectado: {intent_publico}")

        # ===== PASO 2: BÚSQUEDA EN QDRANT =====
        logger.info("Generando embedding de query...")
        query_embedding = model.encode(query, convert_to_numpy=True).tolist()

        # Construir filtro Qdrant si hay categoría exacta detectada
        qdrant_filter = None
        if categoria_exacta:
            qdrant_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="categoria",
                        match=models.MatchValue(value=categoria_exacta)
                    )
                ]
            )
            logger.info(f"Aplicando filtro duro de categoría: {categoria_exacta}")

        # Búsqueda en vector de título
        logger.info("Buscando por similitud de título...")
        search_results_titulo = qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            query_filter=qdrant_filter,
            using=TITLE_VECTOR_NAME,
            limit=100,  # Traemos más para aplicar filtros posteriores
            with_payload=True
        )

        # Búsqueda en vector de descripción
        logger.info("Buscando por similitud de descripción...")
        search_results_descripcion = qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            query_filter=qdrant_filter,
            using=DESCRIPTION_VECTOR_NAME,
            limit=100,
            with_payload=True
        )

        # ===== PASO 3: CONSOLIDAR RESULTADOS CON PONDERACIÓN ASIMÉTRICA =====
        # Crear diccionarios para acceso rápido
        scores_titulo = {result.id: result.score for result in search_results_titulo.points}
        scores_descripcion = {result.id: result.score for result in search_results_descripcion.points}

        # Todos los IDs únicos encontrados
        all_ids = set(scores_titulo.keys()) | set(scores_descripcion.keys())

        resultados = []
        for course_id in all_ids:
            sim_titulo = scores_titulo.get(course_id, 0.0)
            sim_descripcion = scores_descripcion.get(course_id, 0.0)

            # Ponderación asimétrica
            score_base = (sim_titulo * TITLE_WEIGHT) + (sim_descripcion * DESCRIPTION_WEIGHT)

            # Escudo de ruido: descartar si similitud de título es muy baja
            # (solo si NO hay categoría o público explícito detectado)
            if not categoria_exacta and not intent_publico and sim_titulo < MIN_TITLE_SIMILARITY:
                continue

            # Obtener payload del curso (usamos el primero disponible)
            payload = None
            if course_id in scores_titulo:
                for result in search_results_titulo.points:
                    if result.id == course_id:
                        payload = result.payload
                        break
            if payload is None and course_id in scores_descripcion:
                for result in search_results_descripcion.points:
                    if result.id == course_id:
                        payload = result.payload
                        break

            if payload is None:
                continue

            # ===== PASO 4: SOFT BOOSTING =====
            boost = 1.0
            
            # Boost para público infantil
            if course_matches_label(payload, query, "publico"):
                boost += 0.20
            
            # Boost para nivel inicial
            if course_matches_label(payload, query, "nivel"):
                boost += 0.10

            score_final = score_base * boost

            # ===== PASO 5: HARD FILTER POR PÚBLICO (si se detectó explícitamente) =====
            if intent_publico and not course_matches_label(payload, query, "publico"):
                continue

            # Mapear payload a CursoResponse
            item = {
                "id": int(payload.get("id", 0)),
                "titulo": payload.get("titulo", ""),
                "descripcion": payload.get("descripcion", ""),
                "barrio": payload.get("barrio", ""),
                "coordenadas": payload.get("coordenadas", {}),
                "precio": float(payload.get("precio", 0)),
                "modalidad_pago": payload.get("modalidad_pago", ""),
                "valoracion": float(payload.get("valoracion", 0.0)),
                "docente": payload.get("docente", ""),
                "whatsapp": payload.get("whatsapp", ""),
                "instagram": payload.get("instagram", ""),
                "similarity_score": round(score_final, 4)
            }
            resultados.append(item)

        # ===== PASO 6: ORDENAMIENTO =====
        if sort == "valoracion":
            resultados.sort(key=lambda item: item.get("valoracion", 0), reverse=True)
        else:
            resultados.sort(key=lambda item: item.get("similarity_score", 0.0), reverse=True)

        logger.info(f"Búsqueda completada: {len(resultados)} resultados.")
        
        return SearchResponse(
            query=query,
            total_resultados=len(resultados),
            cursos=resultados
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error en búsqueda: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(exc)}")


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)