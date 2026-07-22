"""
Serializers de Django REST Framework — convierten los modelos de
models.py a/desde JSON, para que otros sistemas (u otros equipos) puedan
consumir estos datos por API, no solo por el HTML que ya construimos.
"""

from rest_framework import serializers

from .models import (
    Asignacion,
    Capufe,
    CombustibleExterno,
    Estado,
    FotoVehiculo,
    Inmueble,
    Kilometraje,
    Situacion,
    Tarjeta,
    TipoVehiculo,
    Vehiculo,
)


# --- Catálogos: solo id + nombre, no necesitan mucho más ---------------

class CatalogoSerializer(serializers.Serializer):
    """Serializer genérico de solo lectura para catálogos simples
    (id, nombre) — evita repetir la misma clase 5 veces."""
    id = serializers.IntegerField()
    nombre = serializers.CharField()


class TarjetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarjeta
        fields = ["id", "numero", "banco", "activa"]


# --- Fotos e historial ---------------------------------------------------

class FotoVehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FotoVehiculo
        fields = ["frente", "lateral", "trasera", "actualizado_en"]


class KilometrajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kilometraje
        fields = ["id", "fecha", "tipo", "odometro", "evidencia"]


class CombustibleExternoSerializer(serializers.ModelSerializer):
    tarjeta_numero = serializers.CharField(source="tarjeta.numero", read_only=True, default=None)

    class Meta:
        model = CombustibleExterno
        fields = ["id", "fecha", "monto", "tarjeta_numero"]


class CapufeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Capufe
        fields = ["id", "fecha_inicio", "fecha_termino"]


# --- Vehículo: listado (ligero) vs. detalle (completo) -----------------

class VehiculoListaSerializer(serializers.ModelSerializer):
    """Para el endpoint de listado — solo lo necesario para una tabla,
    sin cargar todo el historial de cada vehículo (sería lento)."""
    tipo_vehiculo = serializers.CharField(source="tipo_vehiculo.nombre", read_only=True)
    asignacion = serializers.CharField(source="asignacion.nombre", read_only=True)
    situacion = serializers.CharField(source="situacion.nombre", read_only=True)

    class Meta:
        model = Vehiculo
        fields = [
            "id", "placa", "marca", "modelo", "anio",
            "tipo_vehiculo", "asignacion", "situacion",
        ]


class VehiculoDetalleSerializer(serializers.ModelSerializer):
    """Para el endpoint de detalle — incluye catálogos resueltos y todo
    el historial relacionado (fotos, kilometraje, combustible, capufe)."""
    tipo_vehiculo = serializers.CharField(source="tipo_vehiculo.nombre", read_only=True)
    asignacion = serializers.CharField(source="asignacion.nombre", read_only=True)
    situacion = serializers.CharField(source="situacion.nombre", read_only=True)
    estado = serializers.CharField(source="estado.nombre", read_only=True, default=None)
    inmueble = serializers.CharField(source="inmueble.nombre", read_only=True, default=None)
    tarjeta = TarjetaSerializer(read_only=True)

    fotos = serializers.SerializerMethodField()
    lecturas_km = KilometrajeSerializer(many=True, read_only=True)
    combustible = CombustibleExternoSerializer(many=True, read_only=True)
    capufe = CapufeSerializer(many=True, read_only=True)

    def get_fotos(self, obj):
        # OneToOne: si el vehículo aún no tiene fotos capturadas, Django
        # levanta FotoVehiculo.DoesNotExist al acceder a obj.fotos — pero
        # esa excepción hereda también de AttributeError a propósito, así
        # que getattr(...) con default sí funciona sin necesidad de try/except.
        foto = getattr(obj, "fotos", None)
        return FotoVehiculoSerializer(foto).data if foto else None

    class Meta:
        model = Vehiculo
        fields = [
            "id", "placa", "marca", "modelo", "anio", "no_motor",
            "tipo_vehiculo", "asignacion", "situacion", "estado", "inmueble", "tarjeta",
            "fotos", "lecturas_km", "combustible", "capufe",
            "creado_en", "actualizado_en",
        ]
