from django.db import models
from django.contrib.auth.models import User 

# Create your models here.

class usuarioL(models.Model):
    types_ORS = [
        ("AGUASCALIENTES", "AGUASCALIENTES"),
        ("BAJA CALIFORNIA", "BAJA CALIFORNIA"),
        ("BAJA CALIFORNIA SUR", "BAJA CALIFORNIA SUR"),
        ("CAMPECHE", "CAMPECHE"),
        ("COAHUILA", "COAHUILA"),
        ("COLIMA", "COLIMA"),
        ("CHIAPAS", "CHIAPAS"),
        ("CHIHUAHUA", "CHIHUAHUA"),
        ("CDMX", "CDMX"),
        ("DURANGO", "DURANGO"),
        ("GUANAJUATO", "GUANAJUATO"),
        ("GUERRERO", "GUERRERO"),
        ("HIDALGO", "HIDALGO"),
        ("JALISCO", "JALISCO"),
        ("EDOMEX", "EDOMEX"),
        ("MICHOACÁN", "MICHOACÁN"),
        ("MORELOS", "MORELOS"),
        ("NAYARIT", "NAYARIT"),
        ("NUEVO LEÓN", "NUEVO LEÓN"),
        ("OAXACA", "OAXACA"),
        ("PUEBLA", "PUEBLA"),
        ("QUERÉTARO", "QUERÉTARO"),
        ("QUINTANA ROO", "QUINTANA ROO"),
        ("SAN LUIS POTOSÍ", "SAN LUIS POTOSÍ"),
        ("SINALOA", "SINALOA"),
        ("SONORA", "SONORA"),
        ("TABASCO", "TABASCO"),
        ("TAMAULIPAS", "TAMAULIPAS"),
        ("TLAXCALA", "TLAXCALA"),
        ("VERACRUZ", "VERACRUZ"),
        ("YUCATÁN", "YUCATÁN"),
        ("ZACATECAS", "ZACATECAS"),
    ]
    user = models.OneToOneField(User, related_name="usuarioL", on_delete=models.CASCADE)
    oficinaR = models.CharField(max_length=20, choices=types_ORS, default="CDMX")

    def __str__(self):
        return "{user} --> {oficinaR}".format(user = self.user, oficinaR = self.oficinaR)