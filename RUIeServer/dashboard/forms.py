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
    (True, 'Hombre'),
    (False, 'Mujer')
)

choice_embarazo = (
    (True, 'Si'),
    (False, 'No')
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
    nacionalidad = forms.ChoiceField(choices=types_paises, label="Nacionalidad")
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
        ### Comentar para nueva base
        types_PRescate = []
        puntosF_ALL = EstadoFuerza.objects.all()

        for puntos in puntosF_ALL:
            nomS = str(puntos.nomPuntoRevision)
            nomS1 = ""
            if nomS[0]== " ":
                nomS1 = nomS[1:]
            else:
                nomS1 = nomS

            types_PRescate.append((nomS1, nomS1))

        for puntos in PuntosInternacion.objects.all():
            nomS = str(puntos.nombrePunto)
            nomS1 = ""
            if nomS[0]== " ":
                nomS1 = nomS[1:]
            else:
                nomS1 = nomS

            types_PRescate.append((nomS1, nomS1))

        types_PRescate.append(("Sin Información", "Sin Información"))

        for mun in Municipios.objects.all():
            nomS = str(mun.nomMunicipio)
            nomS1 = ""
            if nomS[0]== " ":
                nomS1 = nomS[1:]
            else:
                nomS1 = nomS

            types_PRescate.append((nomS1, nomS1))

        ## hasta aqui

        self.fields['puntoEstra'].choices = types_PRescate

    def save(self, commit=True):
        
        db_aerop = False
        db_carre = False
        db_centralA = False
        db_casaS = False
        db_ferro = False
        db_hotel = False
        db_puestos = False
        db_volunt = False

        puntoEstra = self.data['puntoEstra']

        if(self.data['tipo_punto'] == 'aeropuerto'):
            db_aerop = True
        elif(self.data['tipo_punto'] == 'carretero'):
            db_carre = True
        elif(self.data['tipo_punto'] == 'central de autobus'):
            db_centralA = True
        elif(self.data['tipo_punto'] == 'disuadidos'):
            db_casaS = True
        elif(self.data['tipo_punto'] == 'ferrocarril'):
            db_ferro = True
        elif(self.data['tipo_punto'] == 'visitas de verificación'):
            db_hotel = True
        elif(self.data['tipo_punto'] == 'puestos a disposición'):
            db_puestos = True
            puntoEstra = ""
        else:
            db_volunt = True
            puntoEstra = ""

        db_nacionalid = self.data['nacionalidad']
        paisI = Paises.objects.filter(nombre_pais=db_nacionalid)
        db_iso3 = paisI[0].iso3

        fecha_nacimiento = datetime.datetime.strptime(self.data['fechaNacimiento'], '%Y-%m-%d')
        db_edad = datetime.datetime.now().year - fecha_nacimiento.year
        fecha_nacimiento = fecha_nacimiento.strftime('%d/%m/%Y')

        sexo1 = self.data['sexo'] 
        embarazo1 = self.data['embarazo']

        if sexo1 == "True":
            embarazo1 = False
        elif sexo1 == "False":
            embarazo1 = self.data['embarazo']
        else:
            print(self.data['sexo'])
            print(embarazo1)

        datosActualizados = RescatePunto.objects.filter(pk=self.data['idRescate']).update(
            
            fecha=self.data['fecha'],
            hora=self.data['hora'],

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
            nombre=str(self.data['nombre']).upper(),
            apellidos=str(self.data['apellidos']).upper(),
            parentesco=str(self.data['parentesco']),
            fechaNacimiento=fecha_nacimiento,
            sexo=self.data['sexo'],
            embarazo=embarazo1,
            numFamilia=self.data['numFamilia'],
            edad=db_edad,
            oficinaRepre = self.data['oficinaR'],
            )
        # datosActualizados = RescatePunto.objects.update_or_create(idRescate=self.data['idRescate'], sexo=self.data['sexo'] )
        return datosActualizados
    

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

