from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict
from uuid import UUID, uuid4

app = FastAPI(title="API de Productos - Cooperativa", version="1.0.0")

CATALOGO_CATEGORIAS = {
    "granos", "frutas", "hortalizas", "lacteos", "carnes",
    "procesados", "organicos", "ofertas", "semillas", "bebidas"
}

class ProductoIn(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=60, strip_whitespace=True)
    precio: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    categorias: List[str] = Field(..., min_length=1, max_length=10, description="Lista de categorías")

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v

    @field_validator("precio")
    @classmethod
    def normalizar_precio(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @field_validator("categorias")
    @classmethod
    def validar_categorias(cls, v: List[str]) -> List[str]:
        normalizadas = [c.strip().lower() for c in v if c and c.strip()]
        if not normalizadas:
            raise ValueError("Debe incluir al menos una categoría válida")
        if len(normalizadas) != len(set(normalizadas)):
            raise ValueError("Las categorías no deben repetirse")
        desconocidas = [c for c in normalizadas if c not in CATALOGO_CATEGORIAS]
        if desconocidas:
            raise ValueError(f"Categorías no permitidas: {desconocidas}")
        return normalizadas


class ProductoOut(ProductoIn):
    id: UUID


DB: Dict[UUID, ProductoOut] = {}

@app.get("/categorias-permitidas", response_model=List[str], tags=["utilidad"])
def categorias_permitidas():
    return sorted(CATALOGO_CATEGORIAS)


@app.post("/productos", response_model=ProductoOut, status_code=status.HTTP_201_CREATED, tags=["productos"])
def crear_producto(prod: ProductoIn):
    nuevo = ProductoOut(id=uuid4(), **prod.model_dump())
    DB[nuevo.id] = nuevo
    return nuevo


@app.get("/productos", response_model=List[ProductoOut], tags=["productos"])
def listar_productos():
    return list(DB.values())


@app.get("/productos/{producto_id}", response_model=ProductoOut, tags=["productos"])
def obtener_producto(producto_id: UUID):
    prod = DB.get(producto_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return prod


@app.put("/productos/{producto_id}", response_model=ProductoOut, tags=["productos"])
def actualizar_producto(producto_id: UUID, prod: ProductoIn):
    if producto_id not in DB:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    actualizado = ProductoOut(id=producto_id, **prod.model_dump())
    DB[producto_id] = actualizado
    return actualizado


@app.delete("/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["productos"])
def eliminar_producto(producto_id: UUID):
    if producto_id not in DB:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    del DB[producto_id]
    return None
