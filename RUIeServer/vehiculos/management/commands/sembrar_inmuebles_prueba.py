"""
Siembra UN inmueble de prueba por cada una de las 32 entidades (requiere
que 'sembrar_estados' ya se haya corrido antes) — usando coordenadas
reales de la capital de cada estado, para que los íconos del mapa tengan
dónde ubicarse.

Uso:
    docker compose exec web python manage.py sembrar_inmuebles_prueba

Es seguro correrlo varias veces (usa get_or_create por nombre, no duplica).
Solo llena los campos obligatorios del modelo real (estado, nombre,
dirección genérica, coordenadas, superficies, niveles) — nada de datos
de personal, PIPC, ni otras relaciones opcionales.
"""

from django.core.management.base import BaseCommand

from mapa.models import Estado, Inmueble

COORDENADAS_CAPITALES = {
    "Aguascalientes": (21.8853, -102.2916),
    "Baja California": (32.6245, -115.4523),
    "Baja California Sur": (24.1426, -110.3128),
    "Campeche": (19.8301, -90.5349),
    "Chiapas": (16.7569, -93.1292),
    "Chihuahua": (28.6353, -106.0889),
    "Ciudad de México": (19.4326, -99.1332),
    "Coahuila": (25.4260, -101.0053),
    "Colima": (19.2433, -103.7250),
    "Durango": (24.0277, -104.6532),
    "Estado de México": (19.2926, -99.6557),
    "Guanajuato": (21.0190, -101.2574),
    "Guerrero": (17.5506, -99.5024),
    "Hidalgo": (20.0911, -98.7624),
    "Jalisco": (20.6597, -103.3496),
    "Michoacán": (19.7069, -101.1950),
    "Morelos": (18.9242, -99.2216),
    "Nayarit": (21.5041, -104.8942),
    "Nuevo León": (25.6866, -100.3161),
    "Oaxaca": (17.0732, -96.7266),
    "Puebla": (19.0414, -98.2063),
    "Querétaro": (20.5888, -100.3899),
    "Quintana Roo": (18.5036, -88.3055),
    "San Luis Potosí": (22.1565, -100.9855),
    "Sinaloa": (24.8091, -107.3940),
    "Sonora": (29.0729, -110.9559),
    "Tabasco": (17.9869, -92.9303),
    "Tamaulipas": (23.7369, -99.1411),
    "Tlaxcala": (19.3139, -98.2400),
    "Veracruz": (19.1738, -96.1342),
    "Yucatán": (20.9674, -89.5926),
    "Zacatecas": (22.7709, -102.5832),
}


class Command(BaseCommand):
    help = "Siembra un inmueble de prueba por estado, con coordenadas reales de su capital."

    def handle(self, *args, **options):
        creados = 0
        existentes = 0
        omitidos = []

        for nombre_estado, (lat, lng) in COORDENADAS_CAPITALES.items():
            try:
                estado_obj = Estado.objects.get(nombre=nombre_estado)
            except Estado.DoesNotExist:
                omitidos.append(nombre_estado)
                continue

            nombre_inmueble = f"Oficina {nombre_estado}"
            _, creado = Inmueble.objects.get_or_create(
                nombre_inmueble=nombre_inmueble,
                defaults={
                    "estado": estado_obj,
                    "calle": "Calle Principal",
                    "numero_exterior": "1",
                    "numero_interior": "",
                    "colonia": "Centro",
                    "municipio": nombre_estado,
                    "codigo_postal": "00000",
                    "latitud": lat,
                    "longitud": lng,
                    "superficie_total": 100.0,
                    "superficie_construida": 80.0,
                    "superficie_utilizada": 80.0,
                    "numero_de_niveles": 1,
                },
            )
            if creado:
                creados += 1
            else:
                existentes += 1

        self.stdout.write(self.style.SUCCESS(
            f"{creados} inmuebles creados, {existentes} ya existían."
        ))
        if omitidos:
            self.stdout.write(self.style.WARNING(
                f"{len(omitidos)} estados no encontrados (corre 'sembrar_estados' primero): {omitidos}"
            ))
