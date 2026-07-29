"""
Carga el dataset de prueba (un vehículo por cada una de las 32 entidades
de México) directo a la tabla real VehiculosOR de la app 'mapa'.

Uso:
    docker compose exec web python manage.py cargar_vehiculos_prueba
    docker compose exec web python manage.py cargar_vehiculos_prueba --limpiar

IMPORTANTE — decisiones de seguridad de este comando:
- NUNCA crea registros de Estado. Solo los busca (deben existir ya, son
  parte del catálogo geográfico real de 'mapa'). Si un estado del CSV no
  se encuentra, esa fila se omite y se reporta al final — así no hay
  riesgo de ensuciar el catálogo de estados que ya usa todo el sistema.
- Si crea catálogos nuevos, son SOLO los específicos de vehículos
  (TipoVeh, TipoAsignacionVeh, SituacionVeh) — nunca toca tablas de
  personal, inmuebles, ni ninguna otra parte de 'mapa'.
- Usa `update_or_create` por placa, así que correrlo varias veces no
  duplica vehículos — actualiza los que ya existan con ese mismo dato.
- Con --limpiar, borra ÚNICAMENTE los vehículos cuya placa empiece con
  "EST-" (el prefijo que usa este dataset de prueba) — nunca toca
  vehículos reales que ya hayan sido capturados por el equipo.
"""

import csv
import unicodedata
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from mapa.models import Estado, Inmueble, SituacionVeh, TipoAsignacionVeh, TipoVeh, VehiculosOR

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def normalizar_nombre(texto):
    """Misma normalización que ya usa mapa/views.py (sin acentos, mayúsculas),
    para que la búsqueda de estado sea consistente con el resto del sistema."""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto.strip().upper()


class Command(BaseCommand):
    help = "Carga el CSV de prueba (32 entidades) a la tabla real VehiculosOR."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help='Antes de cargar, borra los vehículos de prueba previos (placa que empieza con "EST-").',
        )
        parser.add_argument(
            "--archivo",
            default=str(DATA_DIR / "vehiculos_prueba.csv"),
            help="Ruta al CSV a cargar (por defecto: data/vehiculos_prueba.csv de este mismo módulo).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        ruta_csv = Path(options["archivo"])
        if not ruta_csv.exists():
            self.stderr.write(self.style.ERROR(f"No se encontró el archivo: {ruta_csv}"))
            return

        if options["limpiar"]:
            borrados, _ = VehiculosOR.objects.filter(placa__startswith="EST-").delete()
            self.stdout.write(f"Vehículos de prueba anteriores eliminados: {borrados}")

        with open(ruta_csv, newline="", encoding="utf-8") as f:
            filas = list(csv.DictReader(f))

        # Índice de estados existentes, normalizado — NUNCA se crean estados nuevos aquí.
        estados_por_nombre = {normalizar_nombre(e.nombre): e for e in Estado.objects.all()}

        # Índice de inmuebles existentes por estado (uno por estado, sembrado
        # con "sembrar_inmuebles_prueba") — si no existe, el vehículo se
        # crea igual pero sin inmueble (no aparecerá en el mapa de íconos).
        inmuebles_por_estado_id = {}
        for inmueble in Inmueble.objects.filter(latitud__isnull=False, longitud__isnull=False):
            inmuebles_por_estado_id.setdefault(inmueble.estado_id, inmueble)

        creados = 0
        actualizados = 0
        sin_inmueble = 0
        omitidos = []

        for fila in filas:
            estado_obj = estados_por_nombre.get(normalizar_nombre(fila["estado"]))
            if not estado_obj:
                omitidos.append(f"{fila['placa']} -> estado '{fila['estado']}' no encontrado en el catálogo")
                continue

            inmueble_obj = inmuebles_por_estado_id.get(estado_obj.id)
            if inmueble_obj is None:
                sin_inmueble += 1

            tipo_veh_obj, _ = TipoVeh.objects.get_or_create(tipo_veh=fila["tipo_vehiculo"])
            asignacion_obj, _ = TipoAsignacionVeh.objects.get_or_create(tipo=fila["tipo_asignacion"])
            situacion_obj, _ = SituacionVeh.objects.get_or_create(situacion=fila["situacion"])

            anio_int = int(fila["anio"]) if fila.get("anio") else None
            anio_date = date(anio_int, 1, 1) if anio_int else None

            monto_val = float(fila["monto"]) if fila.get("monto") else 0.0

            _, creado = VehiculosOR.objects.update_or_create(
                placa=fila["placa"],
                defaults={
                    "marca": fila["marca"],
                    "modelo": fila["modelo"],
                    "anio": anio_date,
                    "no_motor": fila["no_motor"],
                    "tarjeta_asig": fila.get("tarjeta") or None,
                    "monto": monto_val,
                    "tipoVeh": tipo_veh_obj,
                    "asignacion": asignacion_obj,
                    "estado": estado_obj,
                    "inmueble": inmueble_obj,
                    "situacion": situacion_obj,
                },
            )
            if creado:
                creados += 1
            else:
                actualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f"{creados} vehículos creados, {actualizados} actualizados, "
            f"{len(omitidos)} omitidos (de {len(filas)} en el CSV)."
        ))
        if sin_inmueble:
            self.stdout.write(self.style.WARNING(
                f"{sin_inmueble} vehículos se crearon SIN inmueble (no hay uno con coordenadas para su estado — "
                f"corre 'sembrar_inmuebles_prueba' primero si quieres verlos en el mapa)."
            ))
        if omitidos:
            self.stdout.write(self.style.WARNING("Omitidos:"))
            for linea in omitidos:
                self.stdout.write(f"  - {linea}")
