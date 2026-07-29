"""
Siembra el catálogo Estado con las 32 entidades de México, usando los
nombres EXACTOS que ya usa el GeoJSON del mapa
(mapa/static/mapa/data/inegi_latlon_mexico.geojson) — así los conteos
que arma mapa_interactivo() sí se enganchan correctamente a cada estado
en el mapa.

Uso:
    docker compose exec web python manage.py sembrar_estados

Es seguro correrlo varias veces (usa get_or_create, no duplica nada).
"""

from django.core.management.base import BaseCommand

from mapa.models import Estado

# Nombres tal como aparecen en el GeoJSON real del proyecto — confirmado
# directamente del archivo, no adivinado.
ESTADOS_MEXICO = [
    "Aguascalientes", "Baja California", "Baja California Sur", "Campeche",
    "Chiapas", "Chihuahua", "Ciudad de México", "Coahuila", "Colima",
    "Durango", "Estado de México", "Guanajuato", "Guerrero", "Hidalgo",
    "Jalisco", "Michoacán", "Morelos", "Nayarit", "Nuevo León", "Oaxaca",
    "Puebla", "Querétaro", "Quintana Roo", "San Luis Potosí", "Sinaloa",
    "Sonora", "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz", "Yucatán",
    "Zacatecas",
]


class Command(BaseCommand):
    help = "Siembra el catálogo Estado con las 32 entidades de México (nombres del GeoJSON real)."

    def handle(self, *args, **options):
        creados = 0
        existentes = 0
        for nombre in ESTADOS_MEXICO:
            _, creado = Estado.objects.get_or_create(nombre=nombre)
            if creado:
                creados += 1
            else:
                existentes += 1

        self.stdout.write(self.style.SUCCESS(
            f"{creados} estados creados, {existentes} ya existían. Total en catálogo: {Estado.objects.count()}."
        ))
