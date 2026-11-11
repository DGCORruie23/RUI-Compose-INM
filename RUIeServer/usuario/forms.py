from django import forms
from django.contrib.admin import widgets
import django.forms.widgets 
import datetime

from django import forms
from .models import EstadoFuerza

class CargarArchivoForm(forms.Form):
    archivo = forms.FileField()

class ExcelForm(forms.Form):
    year = (datetime.date.today()).strftime("%Y")
    YEARS = []
    for i in range(10):
        f = int(year) - i
        YEARS.append(str(f))

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
    fechaDescarga = forms.DateField(
    widget=forms.SelectDateWidget(
        years=YEARS
    ))
    oficina = forms.ChoiceField(choices=types_ORS)
    # fechaDescarga2 = forms.DateField(widget=forms.SelectDateWidget)

class ExcelFormOr(forms.Form):
    year = (datetime.date.today()).strftime("%Y")
    YEARS = []
    for i in range(10):
        f = int(year) - i
        YEARS.append(str(f))

    fechaDescarga = forms.DateField(
    widget=forms.SelectDateWidget(
        years=YEARS
    ))

class ExcelFormOrs(forms.Form):
    fechaDescarga = forms.DateField()
    oficina = forms.CharField()
    # fechaDescarga2 = forms.DateField(widget=forms.SelectDateWidget)


class ExcelFormUsers(forms.Form):
    oficina = forms.CharField()