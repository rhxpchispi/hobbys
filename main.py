"""
Backend API para búsqueda híbrida de cursos.
Implementa: extracción de intención, filtrado duro por categoría y público,
similitud semántica sobre título + descripción y soft boosting por nivel.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


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
    similarity_score: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    total_resultados: int
    cursos: List[CursoResponse]


app = FastAPI(title="API de Búsqueda Híbrida", description="Motor de búsqueda con filtros lógicos y ranking semántico", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cursos_data: List[dict] = []
model: Optional[SentenceTransformer] = None
categorias_disponibles: List[str] = []

# Embeddings separados por campo para el pipeline híbrido
embeddings_titulo: Optional[np.ndarray] = None
embeddings_descripcion: Optional[np.ndarray] = None

TITLE_WEIGHT = 0.70
DESCRIPTION_WEIGHT = 0.30
MIN_TITLE_SIMILARITY = 0.35


def cargar_datos() -> List[dict]:
    data_path = Path(__file__).parent / "data.json"
    if not data_path.exists():
        raise FileNotFoundError(f"El archivo {data_path} no existe")

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("cursos", [])


def normalize_text(text: str) -> str:
    if not text:
        return ""
    normalized = text.lower()
    normalized = normalized.translate(str.maketrans("áéíóúüñ", "aeiouun"))
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def extract_unique_values(cursos: List[dict], key: str) -> List[str]:
    values = {str(curso.get(key, "")).strip() for curso in cursos if str(curso.get(key, "")).strip()}
    return sorted(values, key=lambda item: item.lower())


def detect_exact_category(query: str, categories: List[str]) -> Optional[str]:
    query_norm = normalize_text(query)
    
    # Mapeo inteligente de raíces verbales o sinónimos comunes para robustez
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
    """
    Detecta si el usuario está pidiendo un público específico en su frase.
    """
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
    course_value = normalize_text(curso.get("categoria", ""))
    expected = normalize_text(categoria)
    if not course_value or not expected:
        return False
    return course_value == expected or bool(re.search(rf"\b{re.escape(expected)}\b", course_value))


def course_matches_label(curso: dict, query_text: str, field: str) -> bool:
    """
    Compara de forma normalizada y con soporte de alias si el curso
    hace match con lo que el usuario está buscando en su query.
    """
    if not query_text:
        return False
        
    course_value = str(curso.get(field, "")).strip().lower()
    if not course_value:
        return False
        
    query_norm = normalize_text(query_text)
    course_norm = normalize_text(course_value)

    # Match directo normalizado (ej: "adultos" en "cursos para adultos")
    if course_norm in query_norm:
        return True

    query_tokens = set(query_norm.split())
    
    # Diccionario unificado de equivalencias (Mapea lo que escribe el usuario al valor del JSON)
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

    # El valor del curso también lo pasamos por el mapa por si acaso
    course_tokens = set(course_norm.split())
    normalized_course_tokens = set()
    for token in course_tokens:
        normalized_course_tokens.add(token)
        if token in alias_map:
            normalized_course_tokens.add(alias_map[token])

    return bool(expanded_query_tokens & normalized_course_tokens)


def generar_embeddings_separados(cursos: List[dict]) -> tuple[np.ndarray, np.ndarray]:
    titulos = [str(curso.get("titulo", "")).strip() for curso in cursos]
    descripciones = [str(curso.get("descripcion", "")).strip() for curso in cursos]

    logger.info("Generando embeddings separados para título y descripción...")
    embeddings_titulo_local = model.encode(titulos, convert_to_numpy=True)
    embeddings_descripcion_local = model.encode(descripciones, convert_to_numpy=True)
    return embeddings_titulo_local, embeddings_descripcion_local


def calcular_similitud(query_embedding: np.ndarray, embeddings_field: np.ndarray) -> np.ndarray:
    query_reshaped = query_embedding.reshape(1, -1)
    return cosine_similarity(query_reshaped, embeddings_field)[0]


@app.on_event("startup")
async def startup_event():
    global cursos_data, model, categorias_disponibles, embeddings_titulo, embeddings_descripcion
    try:
        logger.info("Iniciando servidor...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        cursos_data = cargar_datos()
        categorias_disponibles = extract_unique_values(cursos_data, "categoria")
        embeddings_titulo, embeddings_descripcion = generar_embeddings_separados(cursos_data)
        logger.info("Servidor iniciado correctamente")
    except Exception as exc:
        logger.critical(f"Error fatal al iniciar servidor: {exc}", exc_info=True)
        raise


@app.get("/health")
async def health_check():
    return {"status": "ok", "cursos_cargados": len(cursos_data)}


@app.post("/api/search")
async def buscar_cursos(request: SearchRequest, sort: Optional[str] = Query(None, description="Campo para ordenar: 'similitud' o 'valoracion'")):
    try:
        if not cursos_data or embeddings_titulo is None or embeddings_descripcion is None or model is None:
            raise HTTPException(status_code=503, detail="El servidor no está completamente inicializado")

        query = request.query.strip().lower()
        logger.info(f"Búsqueda recibida: '{query}'")

        # 1. Extracción de intención (Categoría y Público)
        categoria_exacta = detect_exact_category(query, categorias_disponibles)
        intent_publico = detect_explicit_public(query)

        if categoria_exacta:
            logger.info(f"Filtro estricto de CATEGORÍA detectado: {categoria_exacta}")
        if intent_publico:
            logger.info(f"Filtro estricto de PÚBLICO detectado: {intent_publico}")

        # 2. Pipeline Semántico
        query_embedding = model.encode(query, convert_to_numpy=True)
        sim_titulo_scores = calcular_similitud(query_embedding, embeddings_titulo)
        sim_descripcion_scores = calcular_similitud(query_embedding, embeddings_descripcion)

        resultados = []
        for index, curso in enumerate(cursos_data):
            
            # HARD FILTER 1: Si hay categoría explícita y el curso no pertenece, se descarta.
            if categoria_exacta and not course_belongs_to_category(curso, categoria_exacta):
                continue

            # HARD FILTER 2 (CORREGIDO): Si se detectó intención de público, usamos course_matches_label.
            # Si el curso NO coincide con el público pedido por el usuario, se descarta inmediatamente.
            if intent_publico and not course_matches_label(curso, query, "publico"):
                continue

            sim_titulo = float(sim_titulo_scores[index])
            sim_descripcion = float(sim_descripcion_scores[index])
            score_base = (sim_titulo * TITLE_WEIGHT) + (sim_descripcion * DESCRIPTION_WEIGHT)

            # 3. Soft Boosting para atributos de nivel restante (ej: "inicial")
            boost = 1.0
            if course_matches_label(curso, query, "nivel"):
                boost += 0.10

            score_final = score_base * boost

            # ESCUDO DE RUIDO: Solo actúa si el usuario NO buscó una categoría ni un público explícito.
            # Si el usuario escribió "infantil", confiamos plenamente en la lógica dura del Hard Filter 2.
            if not categoria_exacta and not intent_publico and sim_titulo < MIN_TITLE_SIMILARITY:
                continue

            item = dict(curso)
            item["similarity_score"] = round(score_final, 4)
            item["debug_sim_titulo"] = round(sim_titulo, 2)
            resultados.append(item)

        if sort == "valoracion":
            resultados.sort(key=lambda item: item.get("valoracion", 0), reverse=True)
        else:
            resultados.sort(key=lambda item: item.get("similarity_score", 0.0), reverse=True)

        return {"query": query, "total_resultados": len(resultados), "cursos": resultados}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error en búsqueda: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(exc)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)