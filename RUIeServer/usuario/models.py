from django.db import models
from django.conf import settings
from django.contrib.auth.hashers import make_password, identify_hasher
import base64
import hashlib
import hmac
import secrets

ENCRYPTED_PREFIX = "enc$v1$"


def _get_encryption_key() -> bytes:
    raw_secret = getattr(settings, "STR_PASS_ENCRYPTION_KEY", "") or settings.SECRET_KEY
    return hashlib.sha256(str(raw_secret).encode("utf-8")).digest()


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < length:
        block = hmac.new(key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest()
        out.extend(block)
        counter += 1
    return bytes(out[:length])


def is_str_pass_encrypted(value: str) -> bool:
    return bool(value) and str(value).startswith(ENCRYPTED_PREFIX)


def is_password_hashed(value: str) -> bool:
    if not value:
        return False
    try:
        identify_hasher(value)
        return True
    except Exception:
        return False


def encrypt_str_pass(plaintext: str) -> str:
    """Cifra str_pass usando una llave derivada de STR_PASS_ENCRYPTION_KEY (.env.dev)."""
    if not plaintext:
        return ""
    plaintext_str = str(plaintext)
    if is_str_pass_encrypted(plaintext_str):
        return plaintext_str
    # Evitar guardar un hash PBKDF2 accidentalmente dentro de str_pass
    if is_password_hashed(plaintext_str):
        return plaintext_str
    key = _get_encryption_key()
    nonce = secrets.token_bytes(12)
    pt_bytes = plaintext_str.encode("utf-8")
    ks = _keystream(key, nonce, len(pt_bytes))
    ct_bytes = bytes(a ^ b for a, b in zip(pt_bytes, ks))
    mac = hmac.new(key, nonce + ct_bytes, hashlib.sha256).digest()[:16]
    token = base64.urlsafe_b64encode(nonce + mac + ct_bytes).decode("ascii")
    return f"{ENCRYPTED_PREFIX}{token}"


def decrypt_str_pass(ciphertext: str, user=None) -> str:
    """Descifra str_pass automáticamente solo si user es superusuario (o desde shell con is_superuser=True)."""
    if not ciphertext:
        return ""
    if user is not None and not getattr(user, "is_superuser", False):
        return "••••••••"
    ciphertext_str = str(ciphertext)
    if not is_str_pass_encrypted(ciphertext_str):
        return ciphertext_str
    try:
        token = ciphertext_str[len(ENCRYPTED_PREFIX):]
        raw = base64.urlsafe_b64decode(token.encode("ascii"))
        if len(raw) < 28:
            return ciphertext_str
        nonce, mac, ct_bytes = raw[:12], raw[12:28], raw[28:]
        key = _get_encryption_key()
        expected_mac = hmac.new(key, nonce + ct_bytes, hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(mac, expected_mac):
            return ciphertext_str
        ks = _keystream(key, nonce, len(ct_bytes))
        pt_bytes = bytes(a ^ b for a, b in zip(ct_bytes, ks))
        return pt_bytes.decode("utf-8")
    except Exception:
        return ciphertext_str


# Create your models here.

class Usuario(models.Model):
    types_ORS = [
        ("1", "AGUASCALIENTES"),
        ("2", "BAJA CALIFORNIA"),
        ("3", "BAJA CALIFORNIA SUR"),
        ("4", "CAMPECHE"),
        ("5", "COAHUILA"),
        ("6", "COLIMA"),
        ("7", "CHIAPAS"),
        ("8", "CHIHUAHUA"),
        ("9", "CDMX"),
        ("10", "DURANGO"),
        ("11", "GUANAJUATO"),
        ("12", "GUERRERO"),
        ("13", "HIDALGO"),
        ("14", "JALISCO"),
        ("15", "EDOMEX"),
        ("16", "MICHOACÁN"),
        ("17", "MORELOS"),
        ("18", "NAYARIT"),
        ("19", "NUEVO LEÓN"),
        ("20", "OAXACA"),
        ("21", "PUEBLA"),
        ("22", "QUERÉTARO"),
        ("23", "QUINTANA ROO"),
        ("24", "SAN LUIS POTOSÍ"),
        ("25", "SINALOA"),
        ("26", "SONORA"),
        ("27", "TABASCO"),
        ("28", "TAMAULIPAS"),
        ("29", "TLAXCALA"),
        ("30", "VERACRUZ"),
        ("31", "YUCATÁN"),
        ("32", "ZACATECAS"),
    ]
    types_user = [
        ("1" , "Administrador"),
        ("2", "Validador"),
        ("3", "Capturador"),
    ]
    types_disp = [
        ("1" , "Android"),
        ("2", "IPhone"),
        ("3", "Otro"),
    ]
    idUser = models.AutoField(primary_key=True)
    nickname = models.CharField(max_length = 30)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=200)
    password = models.CharField(max_length=250)
    str_pass = models.CharField(max_length=250, blank=True, default="")
    estado = models.CharField(max_length=2, choices=types_ORS, default="9")
    tipo = models.CharField(max_length=1, choices=types_user, default="3")
    tipo_disp = models.CharField(max_length=1, choices=types_disp, default="1")

    def get_plain_str_pass(self, user=None) -> str:
        """Retorna la contraseña descifrada únicamente si el usuario es superusuario."""
        return decrypt_str_pass(self.str_pass, user=user)

    def save(self, *args, **kwargs):
        # Si str_pass viene vacío pero password está en texto plano, conservarlo cifrado en str_pass
        if not self.str_pass and self.password and not is_password_hashed(self.password):
            self.str_pass = encrypt_str_pass(self.password)
        elif self.str_pass:
            self.str_pass = encrypt_str_pass(self.str_pass)

        # Evitar doble hash si la instancia se guarda más de una vez
        if self.password and not is_password_hashed(self.password):
            self.password = make_password(self.password)
        super(Usuario, self).save(*args, **kwargs)

    def __str__(self):
        return  " {id}, {nickname}, {state}, {type}".format(id = self.idUser, nickname = self.nickname, state = self.estado, type = self.tipo)

class Paises(models.Model):
    idPais = models.AutoField(primary_key=True)
    nombre_pais = models.CharField(max_length=250)
    iso3 = models.CharField(max_length=3, null=True)

    def __str__(self):
        return " {id}, {pais}, {iso3}".format(id = self.idPais, pais = self.nombre_pais, iso3 = self.iso3)
    
class Frases(models.Model):
    quote = models.CharField(max_length=250)
    author = models.CharField(max_length=250)

    def __str__(self):
        return " {quote}, {author}".format(
            quote = self.quote[0:30], 
            author = self.author)
    
class MsgUpdate(models.Model):
    idMsg = models.AutoField(primary_key=True)
    version = models.CharField(max_length=25)
    info = models.BooleanField(default=False)
    msg = models.CharField(max_length=500,blank=True)

    def __str__(self):
        return "{id} -> {version}v, {msg}".format(
            id = self.idMsg,
            version = self.version,
            msg = self.msg[0:25]) 
    
class Municipios(models.Model):
    idMunicipio = models.AutoField(primary_key=True)
    estado = models.CharField(max_length=250)
    estadoAbr = models.CharField(max_length=50)
    nomMunicipio = models.CharField(max_length=250)

    def __str__(self):
        return " {estadoAbr}, {nomMunicipio}".format(
            estadoAbr = self.estadoAbr, 
            nomMunicipio = self.nomMunicipio)


class PuntosInternacion(models.Model):
    idPuntoInter = models.AutoField(primary_key=True)
    nombrePunto = models.CharField(max_length=100)
    estadoPunto = models.CharField(max_length=100)
    tipoPunto = models.CharField(max_length=50)

    def __str__(self):
        return " {nombrePunto}, {estadoPunto}, {tipoPunto}".format(
            nombrePunto = self.nombrePunto, 
            estadoPunto = self.estadoPunto, 
            tipoPunto = self.tipoPunto)

class Inadmitido(models.Model):
    GENERO_CHOICES = [
        ('H', 'Hombre'),
        ('M', 'Mujer'),
        ('X', 'No especificado'),
    ]

    fecha_hora = models.DateTimeField(db_index=True)
    oficina = models.CharField(max_length=50, db_index=True)
    puntoInter = models.CharField(max_length=100)
    nac = models.CharField(max_length=100, db_index=True)
    nombreCompleto = models.CharField(max_length=250)
    nacimiento = models.DateField()
    genero = models.CharField(
        max_length=1,
        choices=GENERO_CHOICES,
        db_index=True,
        default="X"
    )
    edad = models.IntegerField( null=True, verbose_name="Edad")

    def __str__(self):
        return "{fecha}: {oficina} -->[{nac}={adulto},{genero}]".format(
            fecha = self.fecha_hora.strftime("%d/%m/%Y"),
            oficina = self.oficina,
            nac = self.nac, 
            adulto = "A" if self.edad >= 18 else "M",
            genero=self.genero)

class EstadoFuerza(models.Model):
    idEdoFuerza = models.AutoField(primary_key=True)
    oficinaR = models.CharField(max_length=50)
    numPunto = models.IntegerField()
    nomPuntoRevision = models.CharField(max_length=350)
    tipoP = models.CharField(max_length=50)
    ubicacion = models.CharField(max_length=300)
    coordenadasTexto = models.CharField(max_length=300)
    latitud = models.FloatField(default=0.0)
    longitud = models.FloatField(default=0.0)
    personalINM = models.IntegerField()
    personalSEDENA = models.IntegerField()
    personalMarina = models.IntegerField()
    personalGuardiaN = models.IntegerField()
    personalOTROS = models.IntegerField()
    vehiculos = models.IntegerField()
    seccion = models.IntegerField()

    def __str__(self):
        return "{id}, {oficina}, {nomPuntoRevision} --> {tipoP}".format(id = self.idEdoFuerza, 
                                                                      oficina = self.oficinaR, 
                                                                      nomPuntoRevision = self.nomPuntoRevision[0:25], 
                                                                      tipoP = self.tipoP)


class RescatePunto(models.Model):
    idRescate = models.AutoField(primary_key=True)
    oficinaRepre = models.CharField(max_length=50, db_index=True)
    fecha = models.CharField(max_length=10, db_index=True)
    hora = models.CharField(max_length=5)
    
    nombreAgente = models.CharField(max_length=300,blank=True)

    aeropuerto = models.BooleanField(default=False)
    carretero = models.BooleanField(default=False)
    tipoVehic = models.CharField(max_length=30, blank=True)
    lineaAutobus = models.CharField(max_length=50, blank=True)
    numeroEcono = models.CharField(max_length=50, blank=True)
    placas = models.CharField(max_length=20, blank=True)

    vehiculoAseg = models.BooleanField(default=False)
    casaSeguridad = models.BooleanField(default=False)
    centralAutobus = models.BooleanField(default=False)
    ferrocarril = models.BooleanField(default=False)
    empresa = models.CharField(max_length=150, blank=True)
    hotel = models.BooleanField(default=False)
    nombreHotel = models.CharField(max_length=100, blank=True)
    
    puestosADispo = models.BooleanField(default=False)
    juezCalif = models.BooleanField(default=False)
    reclusorio = models.BooleanField(default=False)
    policiaFede = models.BooleanField(default=False)
    dif = models.BooleanField(default=False)
    policiaEsta = models.BooleanField(default=False)
    policiaMuni = models.BooleanField(default=False)
    guardiaNaci = models.BooleanField(default=False)
    fiscalia = models.BooleanField(default=False)
    otrasAuto = models.BooleanField(default=False)

    voluntarios = models.BooleanField(default=False)
    otro = models.BooleanField(default=False)
    presuntosDelincuentes = models.BooleanField(default=False)
    numPresuntosDelincuentes = models.IntegerField()
    municipio = models.CharField(max_length=200, blank=True)
    puntoEstra = models.CharField(max_length=250, blank=True, db_index=True)
    
    nacionalidad = models.CharField(max_length=100)
    iso3 = models.CharField(max_length=3)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=150)
    noIdentidad = models.CharField(max_length=50)
    parentesco = models.CharField(max_length=50, blank=True)
    fechaNacimiento = models.CharField(max_length=10)
    sexo = models.BooleanField(default=False)
    embarazo = models.BooleanField(default=False)
    numFamilia = models.IntegerField(blank=True)
    edad = models.IntegerField()

    def __str__(self):
        tipoE = ""
        tipo= ""
        if(self.edad > 18):
            tipoE = "A"
        else:
            tipoE = "NNA"

        if(self.aeropuerto):
            tipo = "Aeropuerto"
        elif(self.carretero):
            tipo= "Carretero"
        elif(self.casaSeguridad):
            tipo= "Casa de Seguridad"
        elif(self.centralAutobus):
            tipo= "Central de Autobús"
        elif(self.ferrocarril):
            tipo= "Ferrocarril"
        elif(self.hotel):
            tipo= "Hotel"
        elif(self.puestosADispo):
            tipo= "Puestos a Disposición"
        elif(self.voluntarios):
            tipo= "Voluntarios"
        elif(self.otro):
            tipo= "Otro"
        else:
            tipo = ""
        return "{id}.- OR: {oficinaRepre}, Fecha: {fecha} {hora}, Tipo: {tipo} --> {iso3}, {tipoE}".format(id = self.idRescate, 
                                                                      oficinaRepre = self.oficinaRepre, 
                                                                      fecha = self.fecha, 
                                                                      hora = self.hora, 
                                                                      tipo = tipo, 
                                                                      iso3 = self.iso3, 
                                                                      tipoE = tipoE)

class ConteoRapidoPunto(models.Model):
    IdRescateR = models.AutoField(primary_key=True)
    oficinaRepre = models.CharField(max_length=50)
    fecha = models.CharField(max_length=10)
    hora = models.CharField(max_length=5)

    nombreAgente = models.CharField(max_length=300, blank=True)

    aeropuerto = models.BooleanField(default=False)
    carretero = models.BooleanField(default=False)
    tipoVehic = models.CharField(max_length=30, blank=True)
    lineaAutobus = models.CharField(max_length=50, blank=True)
    numeroEcono = models.CharField(max_length=50, blank=True)
    placas = models.CharField(max_length=20, blank=True)

    vehiculoAseg = models.BooleanField(default=False)
    casaSeguridad = models.BooleanField(default=False)
    centralAutobus = models.BooleanField(default=False)
    ferrocarril = models.BooleanField(default=False)
    empresa = models.CharField(max_length=150, blank=True)
    hotel = models.BooleanField(default=False)
    nombreHotel = models.CharField(max_length=100, blank=True)
    
    puestosADispo = models.BooleanField(default=False)
    juezCalif = models.BooleanField(default=False)
    reclusorio = models.BooleanField(default=False)
    policiaFede = models.BooleanField(default=False)
    dif = models.BooleanField(default=False)
    policiaEsta = models.BooleanField(default=False)
    policiaMuni = models.BooleanField(default=False)
    guardiaNaci = models.BooleanField(default=False)
    fiscalia = models.BooleanField(default=False)
    otrasAuto = models.BooleanField(default=False)

    voluntarios = models.BooleanField(default=False)
    otro = models.BooleanField(default=False)
    presuntosDelincuentes = models.BooleanField(default=False)
    numPresuntosDelincuentes = models.IntegerField()
    municipio = models.CharField(max_length=200, blank=True)
    puntoEstra = models.CharField(max_length=250, blank=True)
    
    nacionalidad = models.CharField(max_length=100)
    iso3 = models.CharField(max_length=3)
    AS_hombres = models.IntegerField()
    AS_mujeresNoEmb = models.IntegerField()
    AS_mujeresEmb = models.IntegerField()
    nucleosFamiliares = models.IntegerField()
    AA_hombres = models.IntegerField()
    AA_mujeresNoEmb = models.IntegerField()
    AA_mujeresEmb = models.IntegerField()
    NNA_A_hombres = models.IntegerField()
    NNA_A_mujeresNoEmb = models.IntegerField()
    NNA_A_mujeresEmb = models.IntegerField()
    NNA_S_hombres = models.IntegerField()
    NNA_S_mujeresNoEmb = models.IntegerField()
    NNA_S_mujeresEmb = models.IntegerField()

    def __str__(self):
        tipo= ""
        total = (self.AS_hombres + self.AS_mujeresNoEmb + self.AS_mujeresEmb 
                 + self.AA_hombres + self.AA_mujeresNoEmb + self.AA_mujeresEmb 
                 + self.NNA_A_hombres + self.NNA_A_mujeresNoEmb + self.NNA_A_mujeresEmb 
                 + self.NNA_S_hombres + self.NNA_S_mujeresNoEmb + self.NNA_S_mujeresEmb)
        
        if(self.aeropuerto):
            tipo = "aeropuerto"
        elif(self.carretero):
            tipo= "carretero"
        elif(self.casaSeguridad):
            tipo= "Casa de Seguridad"
        elif(self.centralAutobus):
            tipo= "Central de Autobús"
        elif(self.ferrocarril):
            tipo= "Ferrocarril"
        elif(self.hotel):
            tipo= "Hotel"
        elif(self.puestosADispo):
            tipo= "Puestos a Disposición"
        elif(self.voluntarios):
            tipo= "Voluntarios"
        elif(self.otro):
            tipo= "Otro"
        else:
            tipo = ""
        return ("{id}.- OR: {oficinaRepre}, Fecha: {fecha} {hora}, Tipo: {tipo} --> {iso3}, #{cuantos}".
                format(id = self.IdRescateR, 
                       oficinaRepre = self.oficinaRepre,
                       fecha = self.fecha,
                       hora = self.hora,
                       tipo = tipo,
                       iso3 = self.iso3,
                       cuantos = total))
    

class DisuadidosPunto(models.Model):
    idDisuadidos = models.AutoField(primary_key=True)
    oficinaRepre = models.CharField(max_length=50)
    fecha = models.DateField()
    hora = models.TimeField()
    nombreAgente = models.CharField(max_length=300, blank=True)

    tipoPuntoRevision = models.CharField(max_length=300, blank=True)
    nombrePuntoRevision = models.CharField(max_length=300, blank=True)
    numDisiadidos = models.IntegerField(default=0)

    def __str__(self):
        stringReturn = "{id}.- OR: {oficinaRepre}, Fecha: {fecha} {hora}, Tipo: {nombrePunto} --> #{cuantos}".format( 
            id = self.idDisuadidos,
            oficinaRepre = self.oficinaRepre,
            fecha = self.fecha,
            hora = self.hora,
            nombrePunto = self.nombrePuntoRevision,
            cuantos = self.numDisiadidos
            )
        return(stringReturn)

class ValidacionServidor(models.Model):
    idValidacion = models.AutoField(primary_key=True)
    servidor_url = models.URLField(max_length=255, help_text="URL base del servidor a consultar")
    servidor_backup_url = models.URLField(max_length=255, blank=True, null=True, help_text="URL del servidor de respaldo")
    activo = models.BooleanField(default=True, help_text="Indica si el servidor está activo")
    version_minima_app = models.CharField(max_length=20, default="1.0.0", help_text="Versión mínima requerida de la app móvil")
    mensaje = models.CharField(max_length=500, blank=True, null=True, help_text="Mensaje informativo para la app")
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.servidor_url} ({'Activo' if self.activo else 'Inactivo'})"


class RegistroMex(models.Model):
    fecha = models.DateField(db_index=True)
    oficina = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    puntoInternación = models.ForeignKey(PuntosInternacion, on_delete=models.CASCADE, null=True, blank=True)
    nacionalidad = models.ForeignKey(Paises, on_delete=models.CASCADE, null=True, blank=True, help_text="Solo aplica si categoria=Extranjero")
    hombres = models.IntegerField(default=0)
    mujeres = models.IntegerField(default=0)
    ninos = models.IntegerField(default=0)
    ninas = models.IntegerField(default=0)
    total = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.fecha} ({self.oficina}) - {self.nacionalidad} - {self.total}"

    class Meta:
        verbose_name = "Registro Mex"
        verbose_name_plural = "Registros Mex"


# class Municipios(models.Model):
#     idMunicipio = models.AutoField(primary_key=True)
#     estado = models.CharField(max_length=250)
#     estadoAbr = models.CharField(max_length=50)
#     nomMunicipio = models.CharField(max_length=250)

# class PuntosInternacion(models.Model):
#     idPuntoInter = models.AutoField(primary_key=True)
#     nombrePunto = models.CharField(max_length=100)
#     estadoPunto = models.CharField(max_length=100)
#     tipoPunto = models.CharField(max_length=50) 

