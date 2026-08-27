from django import forms
from django.contrib.admin import widgets
import django.forms.widgets 
from usuario.models import RescatePunto, Paises, EstadoFuerza, PuntosInternacion, Municipios, Usuario
import datetime


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

types_Puntos = [
        ("aeropuerto", "aeropuerto"),
        ("carretero", "carretero"),
        ("central de autobus", "central de autobus"),
        ("disuadidos", "disuadidos"),
        ("ferrocarril", "ferrocarril"),
        ("visitas de verificación", "visitas de verificación"),
        ("puestos a disposición", "puestos a disposición"),
        ("voluntarios", "voluntarios"),
    ]

year = (datetime.date.today()).strftime("%Y")
YEARS = []
for i in range(10):
    f = int(year) - i
    YEARS.append(str(f))

choice_sexo = (
    ('True', 'Hombre'),
    ('False', 'Mujer')
)

choice_embarazo = (
    ('True', 'Si'),
    ('False', 'No')
)

types_paises = []

## Segunda parte para comentar

for paises_I in Paises.objects.all():
    nomPS = str(paises_I.nombre_pais)
    types_paises.append((nomPS, nomPS))

## hasta aqui

class ExcelForm(forms.Form):    
    fechaDescarga = forms.DateField(
    widget=forms.SelectDateWidget(
        years=YEARS
    ), initial=datetime.date.today )
    # fechaDescarga2 = forms.DateField(widget=forms.SelectDateWidget)

class ExcelFormORs(forms.Form):
    fechaDescarga = forms.DateField(
    widget=forms.SelectDateWidget(
        years=YEARS
    ))
    oficina = forms.ChoiceField(choices=types_ORS)

class RegistroForm(forms.ModelForm):
    # hora = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'hrs:mins','type': 'time'}), label="Hora:")
    # puntoEstra = forms.CharField(widget=forms.TextInput(attrs={}), label="Punto de Rescate:")
    # fechaNacimiento = forms.CharField(widget=forms.TextInput(attrs={}), label="Fecha de Nacimiento:")
    class Meta:
        model = RescatePunto
        fields = [
            'hora',
            'aeropuerto','carretero', 'casaSeguridad', 'centralAutobus', 'ferrocarril', 'hotel', 'puestosADispo', 'voluntarios',
            'municipio', 'puntoEstra',
            'nacionalidad', 'iso3', 'nombre', 'apellidos', 'parentesco', 'fechaNacimiento', 'sexo', 'embarazo', 'numFamilia',
                  ]
        labels = {
            'hora' : 'Hora:',
            'puestosADispo': 'Puestos a disposición',
            'puntoEstra': 'Punto de Rescate',
            'fechaNacimiento': 'Fecha de Nacimiento:',
            'numFamilia': 'Numero de Familia:',
        }

    # oficinaRepre = forms.ChoiceField(choices=types_ORS)
    # fecha = forms.DateField(widget=forms.SelectDateWidget(years=YEARS ))
    # hora = forms.CharField(max_length=5)
    
    # nombreAgente = forms.CharField(max_length=300)

    # aeropuerto = forms.BooleanField()
    # carretero = forms.BooleanField()
    # tipoVehic = forms.CharField(max_length=30)
    # lineaAutobus = forms.CharField(max_length=50)
    # numeroEcono = forms.CharField(max_length=50)
    # placas = forms.CharField(max_length=20)
    # vehiculoAseg = forms.BooleanField()
    
    # casaSeguridad = forms.BooleanField()
    # centralAutobus = forms.BooleanField()
    # ferrocarril = forms.BooleanField()
    # empresa = forms.CharField(max_length=150)
    # hotel = forms.BooleanField()
    # nombreHotel = forms.CharField(max_length=100)
    
    # puestosADispo = forms.BooleanField()
    # juezCalif = forms.BooleanField()
    # reclusorio = forms.BooleanField()
    # policiaFede = forms.BooleanField()
    # dif = forms.BooleanField()
    # policiaEsta = forms.BooleanField()
    # policiaMuni = forms.BooleanField()
    # guardiaNaci = forms.BooleanField()
    # fiscalia = forms.BooleanField()
    # otrasAuto = forms.BooleanField()

    # voluntarios = forms.BooleanField()
    # otro = forms.BooleanField()
    # presuntosDelincuentes = forms.BooleanField()
    # numPresuntosDelincuentes = forms.IntegerField()
    # municipio = forms.CharField(max_length=200)
    # puntoEstra = forms.CharField(max_length=250)
    
    # nacionalidad = forms.CharField(max_length=100)
    # iso3 = forms.CharField(max_length=3)
    # nombre = forms.CharField(max_length=100)
    # apellidos = forms.CharField(max_length=150)
    # noIdentidad = forms.CharField(max_length=50)
    # parentesco = forms.CharField(max_length=50)
    # fechaNacimiento = forms.CharField(max_length=10)
    # sexo = forms.BooleanField()
    # embarazo = forms.BooleanField()
    # numFamilia = forms.IntegerField()
    # edad = forms.IntegerField()



class RegistroNewForm(forms.Form):

    idRescate = forms.IntegerField(widget=forms.NumberInput(attrs={'type' : 'hidden'}), label="id")
    fecha = forms.CharField(widget=forms.TextInput(attrs={}), label="Fecha:")
    hora = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'hrs:mins','type': 'time'}), label="Hora:")
    tipo_punto = forms.ChoiceField(choices=types_Puntos, label="Tipo de punto de Rescate:")
    puntoEstra = forms.ChoiceField(choices=[], label="Nombre punto de Rescate:")
    nacionalidad = forms.ChoiceField(choices=[], label="Nacionalidad")
    nombre = forms.CharField(max_length=100)
    apellidos = forms.CharField(max_length=150)
    parentesco = forms.CharField(max_length=50, required=False)
    fechaNacimiento = forms.CharField(widget=forms.TextInput(attrs={}), label="Fecha de Nacimiento:")
    sexo = forms.ChoiceField(choices=choice_sexo, label="Sexo: ")
    embarazo = forms.ChoiceField(choices=choice_embarazo, label="Embarazo: ")
    numFamilia = forms.IntegerField(label="Numero de Familia")
    oficinaR = forms.CharField(widget=forms.TextInput(attrs={}), label="Oficina:")

    def __init__(self, *args, **kwargs):
        super(RegistroNewForm, self).__init__(*args, **kwargs)
        
        # 1. Población dinámica de Nacionalidades al vuelo (evita problemas si DB no está lista al importar)
        paises_choices = [(p.nombre_pais.strip(), p.nombre_pais.strip()) for p in Paises.objects.all()]
        if not paises_choices:
            paises_choices = [("GUATEMALA", "GUATEMALA"), ("HONDURAS", "HONDURAS"), ("EL SALVADOR", "EL SALVADOR")]
        
        # Buscar nacionalidad en kwargs['data'] (POST) o kwargs['initial'] (GET) o args[0] (POST posicional)
        data_obj = kwargs.get('data') or (args[0] if len(args) > 0 else None) or {}
        initial_obj = kwargs.get('initial') or {}
        
        selected_nacion = data_obj.get('nacionalidad') or initial_obj.get('nacionalidad', '')
        if selected_nacion and not any(selected_nacion == choice[0] for choice in paises_choices):
            paises_choices.append((selected_nacion, selected_nacion))
            
        self.fields['nacionalidad'].choices = paises_choices

        # 2. Población dinámica del puntoEstra
        selected_val = data_obj.get('puntoEstra') or initial_obj.get('puntoEstra', '') or "Sin Información"
        
        # Limpiar espacios en blanco
        selected_val = str(selected_val).strip()
        
        # Agregamos dinámicamente el valor actual como una opción válida
        self.fields['puntoEstra'].choices = [(selected_val, selected_val), ("Sin Información", "Sin Información")]

    def save(self, commit=True):
        
        db_aerop = False
        db_carre = False
        db_centralA = False
        db_casaS = False
        db_ferro = False
        db_hotel = False
        db_puestos = False
        db_volunt = False

        puntoEstra = self.cleaned_data['puntoEstra']
        tipo_punto = self.cleaned_data['tipo_punto']

        if(tipo_punto == 'aeropuerto'):
            db_aerop = True
        elif(tipo_punto == 'carretero'):
            db_carre = True
        elif(tipo_punto == 'central de autobus'):
            db_centralA = True
        elif(tipo_punto == 'disuadidos'):
            db_casaS = True
        elif(tipo_punto == 'ferrocarril'):
            db_ferro = True
        elif(tipo_punto == 'visitas de verificación'):
            db_hotel = True
        elif(tipo_punto == 'puestos a disposición'):
            db_puestos = True
            puntoEstra = ""
        else:
            db_volunt = True
            puntoEstra = ""

        db_nacionalid = self.cleaned_data['nacionalidad']
        paisI = Paises.objects.filter(nombre_pais=db_nacionalid)
        db_iso3 = paisI[0].iso3 if paisI.exists() else ""

        # Manejo más seguro de la fecha de nacimiento
        try:
            fecha_nacimiento = datetime.datetime.strptime(self.cleaned_data['fechaNacimiento'], '%Y-%m-%d')
            db_edad = datetime.datetime.now().year - fecha_nacimiento.year
            fecha_nacimiento_str = fecha_nacimiento.strftime('%d/%m/%Y')
        except Exception:
            # Fallback en caso de que ya venga en formato dd/mm/yyyy
            try:
                fecha_nacimiento = datetime.datetime.strptime(self.cleaned_data['fechaNacimiento'], '%d/%m/%Y')
                db_edad = datetime.datetime.now().year - fecha_nacimiento.year
                fecha_nacimiento_str = self.cleaned_data['fechaNacimiento']
            except Exception:
                fecha_nacimiento_str = self.cleaned_data['fechaNacimiento']
                db_edad = 0

        sexo1 = self.cleaned_data['sexo'] 
        embarazo1 = self.cleaned_data['embarazo']

        # Conversiones booleanas explícitas ya que ChoiceField devuelve string 'True' o 'False'
        is_hombre = (sexo1 == 'True' or sexo1 is True)
        is_embarazada = (embarazo1 == 'True' or embarazo1 is True)

        if is_hombre:
            db_embarazo = False
        else:
            db_embarazo = is_embarazada

        datosActualizados = RescatePunto.objects.filter(pk=self.cleaned_data['idRescate']).update(
            
            fecha=self.cleaned_data['fecha'],
            hora=self.cleaned_data['hora'],

            puntoEstra=puntoEstra.upper(),

            aeropuerto=db_aerop,
            carretero=db_carre,
            casaSeguridad=db_casaS,
            centralAutobus=db_centralA,
            ferrocarril=db_ferro,
            hotel=db_hotel,
            puestosADispo=db_puestos,
            voluntarios=db_volunt,

            nacionalidad=str(db_nacionalid).upper(),
            iso3=str(db_iso3),
            nombre=str(self.cleaned_data['nombre']).upper(),
            apellidos=str(self.cleaned_data['apellidos']).upper(),
            parentesco=str(self.cleaned_data['parentesco'] or ''),
            fechaNacimiento=fecha_nacimiento_str,
            sexo=is_hombre,
            embarazo=db_embarazo,
            numFamilia=self.cleaned_data['numFamilia'],
            edad=db_edad,
            oficinaRepre = self.cleaned_data['oficinaR'],
            )
        return datosActualizados


class RegistroCreateForm(RegistroNewForm):
    idRescate = forms.IntegerField(widget=forms.NumberInput(attrs={'type' : 'hidden'}), label="id", required=False)
    nombreAgente = forms.CharField(max_length=300, required=False, label="Nombre del Agente:")

    def __init__(self, *args, **kwargs):
        super(RegistroCreateForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        db_aerop = False
        db_carre = False
        db_centralA = False
        db_casaS = False
        db_ferro = False
        db_hotel = False
        db_puestos = False
        db_volunt = False

        puntoEstra = self.cleaned_data['puntoEstra']
        tipo_punto = self.cleaned_data['tipo_punto']

        if(tipo_punto == 'aeropuerto'):
            db_aerop = True
        elif(tipo_punto == 'carretero'):
            db_carre = True
        elif(tipo_punto == 'central de autobus'):
            db_centralA = True
        elif(tipo_punto == 'disuadidos'):
            db_casaS = True
        elif(tipo_punto == 'ferrocarril'):
            db_ferro = True
        elif(tipo_punto == 'visitas de verificación'):
            db_hotel = True
        elif(tipo_punto == 'puestos a disposición'):
            db_puestos = True
            puntoEstra = ""
        else:
            db_volunt = True
            puntoEstra = ""

        db_nacionalid = self.cleaned_data['nacionalidad']
        paisI = Paises.objects.filter(nombre_pais=db_nacionalid)
        db_iso3 = paisI[0].iso3 if paisI.exists() else ""

        try:
            fecha_nacimiento = datetime.datetime.strptime(self.cleaned_data['fechaNacimiento'], '%Y-%m-%d')
            db_edad = datetime.datetime.now().year - fecha_nacimiento.year
            fecha_nacimiento_str = fecha_nacimiento.strftime('%d/%m/%Y')
        except Exception:
            try:
                fecha_nacimiento = datetime.datetime.strptime(self.cleaned_data['fechaNacimiento'], '%d/%m/%Y')
                db_edad = datetime.datetime.now().year - fecha_nacimiento.year
                fecha_nacimiento_str = self.cleaned_data['fechaNacimiento']
            except Exception:
                fecha_nacimiento_str = self.cleaned_data['fechaNacimiento']
                db_edad = 0

        sexo1 = self.cleaned_data['sexo'] 
        embarazo1 = self.cleaned_data['embarazo']

        is_hombre = (sexo1 == 'True' or sexo1 is True)
        is_embarazada = (embarazo1 == 'True' or embarazo1 is True)

        if is_hombre:
            db_embarazo = False
        else:
            db_embarazo = is_embarazada

        nuevoRescate = RescatePunto.objects.create(
            fecha=self.cleaned_data['fecha'],
            hora=self.cleaned_data['hora'],
            nombreAgente=str(self.cleaned_data.get('nombreAgente') or '').upper(),
            puntoEstra=puntoEstra.upper(),
            aeropuerto=db_aerop,
            carretero=db_carre,
            casaSeguridad=db_casaS,
            centralAutobus=db_centralA,
            ferrocarril=db_ferro,
            hotel=db_hotel,
            puestosADispo=db_puestos,
            voluntarios=db_volunt,
            nacionalidad=str(db_nacionalid).upper(),
            iso3=str(db_iso3),
            nombre=str(self.cleaned_data['nombre']).upper(),
            apellidos=str(self.cleaned_data['apellidos']).upper(),
            parentesco=str(self.cleaned_data['parentesco'] or ''),
            fechaNacimiento=fecha_nacimiento_str,
            sexo=is_hombre,
            embarazo=db_embarazo,
            numFamilia=self.cleaned_data['numFamilia'],
            edad=db_edad,
            oficinaRepre=self.cleaned_data['oficinaR'],
            numPresuntosDelincuentes=0,
        )
        return nuevoRescate


class EstadoFuerzaForm(forms.ModelForm):
    class Meta:
        model = EstadoFuerza
        fields = '__all__'

    
class puntosIForm(forms.ModelForm):
    class Meta:
        model = PuntosInternacion
        fields = '__all__'

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = '__all__'

