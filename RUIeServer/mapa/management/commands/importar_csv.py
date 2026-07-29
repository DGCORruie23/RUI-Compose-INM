"""
Comando de gestión: importa los CSV de prueba (vehiculos_prueba.csv y
bitacora_kilometraje.csv) a la base de datos real, ya normalizada.

Uso:
    docker compose exec web python manage.py importar_csv
    docker compose exec web python manage.py importar_csv --reemplazar

Requiere que ya exista la base de datos (haber corrido
database/schema_postgres.sql) y que settings.py ya apunte a PostgreSQL.
"""

import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from vehiculos.models import (
    Asignacion,
    CombustibleExterno,
    Kilometraje,
    Situacion,
    Tarjeta,
    TipoVehiculo,
    Vehiculo,
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


class Command(BaseCommand):
    help = "Importa vehiculos_prueba.csv y bitacora_kilometraje.csv a la base de datos real."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reemplazar",
            action="store_true",
            help="Borra los vehículos existentes antes de importar. Úsalo solo con datos de prueba.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        vehiculos_path = DATA_DIR / "vehiculos_prueba.csv"
        bitacora_path = DATA_DIR / "bitacora_kilometraje.csv"

        if not vehiculos_path.exists():
            self.stderr.write(self.style.ERROR(f"No se encontró {vehiculos_path}"))
            return

        if options["reemplazar"]:
            self.stdout.write("Borrando vehículos existentes...")
            Vehiculo.objects.all().delete()

        with open(vehiculos_path, newline="", encoding="utf-8") as f:
            filas_vehiculos = list(csv.DictReader(f))

        creados = 0
        for fila in filas_vehiculos:
            tipo_vehiculo, _ = TipoVehiculo.objects.get_or_create(nombre=fila["tipo_vehiculo"])
            asignacion, _ = Asignacion.objects.get_or_create(nombre=fila["tipo_asignacion"])
            situacion, _ = Situacion.objects.get_or_create(nombre=fila["situacion"])

            tarjeta = None
            if fila.get("tarjeta"):
                tarjeta, _ = Tarjeta.objects.get_or_create(numero=fila["tarjeta"])

            _, creado = Vehiculo.objects.update_or_create(
                placa=fila["placa"],
                defaults={
                    "marca": fila["marca"],
                    "modelo": fila["modelo"],
                    "anio": int(fila["anio"]),
                    "no_motor": fila["no_motor"],
                    "tipo_vehiculo": tipo_vehiculo,
                    "asignacion": asignacion,
                    "situacion": situacion,
                    "tarjeta": tarjeta,
                },
            )
            if creado:
                creados += 1

        self.stdout.write(self.style.SUCCESS(
            f"{creados} vehículos nuevos ({len(filas_vehiculos)} procesados en total)."
        ))

        if not bitacora_path.exists():
            self.stdout.write(self.style.WARNING(
                f"No se encontró {bitacora_path} — se omite la bitácora de kilometraje."
            ))
            return

        with open(bitacora_path, newline="", encoding="utf-8") as f:
            filas_bitacora = list(csv.DictReader(f))

        km_creados = 0
        comb_creados = 0
        omitidos = 0

        for fila in filas_bitacora:
            try:
                vehiculo = Vehiculo.objects.get(placa=fila["placa"])
            except Vehiculo.DoesNotExist:
                omitidos += 1
                continue

            _, creado_km = Kilometraje.objects.get_or_create(
                vehiculo=vehiculo,
                fecha=fila["fecha"],
                defaults={"tipo": "Carga de gasolina", "odometro": int(fila["km"])},
            )
            km_creados += int(creado_km)

            monto = float(fila.get("monto") or 0)
            if monto > 0:
                tarjeta = None
                if fila.get("tarjeta"):
                    tarjeta, _ = Tarjeta.objects.get_or_create(numero=fila["tarjeta"])
                _, creado_comb = CombustibleExterno.objects.get_or_create(
                    vehiculo=vehiculo,
                    fecha=fila["fecha"],
                    monto=monto,
                    defaults={"tarjeta": tarjeta},
                )
                comb_creados += int(creado_comb)

        self.stdout.write(self.style.SUCCESS(
            f"{km_creados} lecturas de kilometraje y {comb_creados} registros de "
            f"combustible importados. ({omitidos} filas omitidas por placa no encontrada)"
        ))
