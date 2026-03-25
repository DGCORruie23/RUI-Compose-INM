from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from usuarioL.models import usuarioL
from .forms import ExcelForm, RegistroForm, RegistroNewForm, puntosIForm
from usuario.models import RescatePunto, EstadoFuerza, PuntosInternacion, Municipios, Paises, Usuario
from django.contrib import messages
from datetime import *

from .forms import EstadoFuerzaForm, UsuarioForm
from usuario.forms import CargarArchivoForm
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth.hashers import make_password

import json
# Create your views here.

@login_required
def dashboard(request):
    user_profile = getattr(request.user, 'usuarioL', None)
    userDataI = [user_profile] if user_profile else []

    if request.method == 'GET':
        form = ExcelForm()
        formCargar1 = CargarArchivoForm()
        data = {
            'usuario' : userDataI,
            'form': form,
            'formCargar1': formCargar1
        }
        return render(request, "dashboard/dashboard.html", context=data)
    
    elif request.method == 'POST':
        form = ExcelForm(request.POST)
        valores = []
        if(form.is_valid()):
            dia = request.POST["fechaDescarga_day"]
            mes = request.POST["fechaDescarga_month"]
            year = request.POST["fechaDescarga_year"]

            fechaR = datetime.strptime(f"{dia}/{mes}/{year}", "%d/%m/%Y").strftime('%d-%m-%y')

            oficina = user_profile.oficinaR if user_profile else None
            valores = RescatePunto.objects.filter(fecha=fechaR, oficinaRepre=oficina)

        data = {
            'usuario' : userDataI,
            'form': form,
            'values' : valores,
        }
            
        return render(request, "dashboard/dashboard.html", context=data)

    else: 
        form = ExcelForm()
        data = {
            'usuario' : userDataI,
            'form': form,
        }
        return render(request, "dashboard/dashboard.html", context=data) 

@login_required

def datos_fecha(request):
    if request.method == 'POST':
        form = ExcelForm(request.POST)
        if form.is_valid():
            # Obtiene la fecha seleccionada del formulario
            fecha_seleccionada = form.cleaned_data['fechaDescarga']

            print(fecha_seleccionada)
            # Redirige a la vista de la tabla de productos con la fecha seleccionada
            return redirect('tabla_registros_fecha', year=fecha_seleccionada.year, month=fecha_seleccionada.month, day=fecha_seleccionada.day)
    else:
        return redirect('/dashboard')
    
@login_required
def datos_fechas(request):
    if request.method == 'POST':
        form = ExcelForm(request.POST)
        if form.is_valid():
            user_profile = getattr(request.user, 'usuarioL', None)
            userDataI = [user_profile] if user_profile else []
            
            fechaI = request.POST["fechaInicio"]
            fechaF = request.POST["fechaFin"]

            fechaIN = datetime.strptime(f"{fechaI}", "%Y-%m-%d")
            fechaFN = datetime.strptime(f"{fechaF}", "%Y-%m-%d")
            
            array_fechas = [(fechaIN + timedelta(days=d)).strftime("%d-%m-%y") for d in range((fechaFN - fechaIN).days + 1)]
            form = ExcelForm()
            
            valores = RescatePunto.objects.filter(fecha__in=array_fechas)
                
            if request.user.is_superuser:
                template = "dashboard/datos_diaSU.html"
            else:
                oficina = user_profile.oficinaR if user_profile else None
                valores = valores.filter(oficinaRepre=oficina)
                template = "dashboard/datos_dia.html"

            data = {
                'usuario' : userDataI,
                'form': form,
                'values' : valores,
                'fecha_P' : array_fechas,
            }

            return render(request, template, context=data)
    
    return redirect('/dashboard')
    
@login_required

def eliminar_registros(request):
    if request.method == 'POST':
        # Obtén los IDs de los productos seleccionados
        registros_seleccionados = request.POST.getlist('registros_seleccionados')

        # Elimina los productos seleccionados
        registros_eliminar = RescatePunto.objects.filter(idRescate__in=registros_seleccionados)
        fechaR = registros_eliminar[0].fecha
        registros_eliminar.delete()

        # Redirige a la página de la tabla de productos o a donde desees
        fecha_seleccionada = datetime.strptime(f"{fechaR}", "%d-%m-%y")
                # return redirect('../datos/')
        return redirect('tabla_registros_fecha', year=fecha_seleccionada.year, month=fecha_seleccionada.month, day=fecha_seleccionada.day)

    # Obtén todos los productos para mostrar en la tabla
    return redirect("/dashboard")


@login_required
def tabla_registros(request, year=None, month=None, day=None):
    user_profile = getattr(request.user, 'usuarioL', None)
    userDataI = [user_profile] if user_profile else []

    fechaR = datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y").strftime('%d-%m-%y')
    form = ExcelForm()
    
    valores = RescatePunto.objects.filter(fecha=fechaR)

    if request.user.is_superuser:
        template = "dashboard/datos_diaSU.html"
    else:
        oficina = user_profile.oficinaR if user_profile else None
        valores = valores.filter(oficinaRepre=oficina)
        template = "dashboard/datos_dia.html"

    data = {
        'usuario' : userDataI,
        'form': form,
        'values' : valores,
        'fecha_P' : fechaR,
    }

    return render(request, template, context=data)
    
@login_required
def editarData(request, pk):
    rescate = get_object_or_404(RescatePunto, idRescate=pk)
    
    if request.method == 'GET':
        ofiRep = str(rescate.oficinaRepre)
        
        # Mapeo de tipos de punto para simplificar la lógica
        punto_attr_map = {
            'aeropuerto': 'aeropuerto',
            'carretero': 'carretero',
            'central de autobus': 'centralAutobus',
            'disuadidos': 'casaSeguridad',
            'ferrocarril': 'ferrocarril',
            'visitas de verificación': 'hotel',
            'puestos a disposición': 'puestosADispo',
            'voluntarios': 'voluntarios',
        }
        
        tiposPNombre = list(punto_attr_map.keys())
        puntoR = next((name for name, attr in punto_attr_map.items() if getattr(rescate, attr)), '')

        # Preparar datos iniciales para el formulario
        try:
            fecha_naci_dt = datetime.strptime(rescate.fechaNacimiento, "%d/%m/%Y")
            fecha_naci_str = fecha_naci_dt.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            fecha_naci_str = ""

        datosR = {
            'idRescate': pk,
            'fecha': rescate.fecha,
            'hora': datetime.strptime(rescate.hora, "%H:%M").strftime("%H:%M") if rescate.hora else "",
            'tipo_punto': puntoR,
            'puntoEstra': rescate.puntoEstra,
            'nacionalidad': rescate.nacionalidad,
            'nombre': rescate.nombre,
            'apellidos': rescate.apellidos,
            'parentesco': rescate.parentesco,
            'fechaNacimiento': fecha_naci_str,
            'sexo': rescate.sexo,
            'embarazo': rescate.embarazo,
            'numFamilia': rescate.numFamilia,
            'oficinaR': rescate.oficinaRepre
        }

        form = RegistroNewForm(initial=datosR)

        # Optimización: Consultas únicas y procesamiento en memoria
        # Estado Fuerza
        types_puntosAll = []
        types_PRescateC = []
        types_PRescateCA = []
        types_PRescateF = []
        datos_puntos_estrategicos = {}

        for ef in EstadoFuerza.objects.all():
            oficina = ef.oficinaR
            tipo = ef.tipoP
            nombre = ef.nomPuntoRevision.strip()
            nombre_upper = nombre

            types_puntosAll.append(oficina)
            
            # Agrupación para el diccionario de puntos estratégicos
            if oficina not in datos_puntos_estrategicos:
                datos_puntos_estrategicos[oficina] = {}
            if tipo not in datos_puntos_estrategicos[oficina]:
                datos_puntos_estrategicos[oficina][tipo] = []
            datos_puntos_estrategicos[oficina][tipo].append(nombre)

            # Filtros específicos para la oficina actual del rescate
            if oficina == ofiRep:
                if tipo == "Carretero":
                    types_PRescateC.append(nombre_upper)
                elif tipo == "Central de autobús":
                    types_PRescateCA.append(nombre_upper)
                elif tipo == "Ferroviario":
                    types_PRescateF.append(nombre_upper)

        # Puntos de Internación
        types_PRescateA = []
        datos_puntos_internacion = {}
        for pi in PuntosInternacion.objects.all():
            est = pi.estadoPunto
            tipo = pi.tipoPunto
            nom = pi.nombrePunto.strip()
            
            if est not in datos_puntos_internacion:
                datos_puntos_internacion[est] = {}
            if tipo not in datos_puntos_internacion[est]:
                datos_puntos_internacion[est][tipo] = []
            datos_puntos_internacion[est][tipo].append(nom)

            if est == ofiRep and tipo == "AEREOS":
                types_PRescateA.append(nom)

        # Municipios
        types_PRescateM = []
        datos_municipios = {}
        for mun in Municipios.objects.all():
            est = mun.estado
            nom = mun.nomMunicipio.strip()
            
            if est not in datos_municipios:
                datos_municipios[est] = []
            datos_municipios[est].append(nom)

            if est == ofiRep:
                types_PRescateM.append(nom)

        # Nacionalidades
        types_Naciona = [p.nombre_pais.strip() for p in Paises.objects.all()]

        context = {
            "form": form,
            "value": rescate,
            "datosR": datosR,
            "puntosEstrategicos": datos_puntos_estrategicos,
            "puntosInternacion": datos_puntos_internacion,
            "municipios": datos_municipios,
            "res_aero": types_PRescateA,
            "res_carre": types_PRescateC,
            "res_central": types_PRescateCA,
            "res_ferro": types_PRescateF,
            "municipio": types_PRescateM,
            "nacion": types_Naciona,
            'tiposPNombre': tiposPNombre,
        }
        
        return render(request, "dashboard/editarDato.html", context=context)
    
    elif request.method == 'POST':
        form = RegistroNewForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "El registro ha sido modificado")
            fecha_form = form.cleaned_data['fecha']
            try:
                fecha_sel = datetime.strptime(f"{fecha_form}", "%d-%m-%y")
                return redirect('tabla_registros_fecha', year=fecha_sel.year, month=fecha_sel.month, day=fecha_sel.day)
            except ValueError:
                return redirect('/dashboard')
        else:
            print(form.errors)
            messages.success(request, "Datos Erróneos")
            return render(request, "dashboard/editarDato.html", context={"form": form, "value": rescate})

    return redirect("/dashboard")

@login_required
def mostrarData(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            user_profile = getattr(request.user, 'usuarioL', None)
            userDataI = [user_profile] if user_profile else []
            
            form = ExcelForm(request.POST)
            form1 = RegistroNewForm(request.POST)
            
            if(form.is_valid()):
                dia = request.POST["fechaDescarga_day"]
                mes = request.POST["fechaDescarga_month"]
                year = request.POST["fechaDescarga_year"]

                fechaR = datetime.strptime(f"{dia}/{mes}/{year}", "%d/%m/%Y").strftime('%d-%m-%y')

                if request.user.is_superuser:
                    valores = RescatePunto.objects.filter(fecha=fechaR)
                    template = "dashboard/datos_diaSU.html"
                else:
                    oficina = userDataI[0].oficinaR if userDataI else None
                    valores = RescatePunto.objects.filter(fecha=fechaR, oficinaRepre=oficina)
                    template = "dashboard/datos_dia.html"

                data = {
                'usuario' : userDataI,
                'form': form,
                'values' : valores,
                'fecha_P' : fechaR,
                }

                return render(request, template, context=data)

            if form1.is_valid():
                fechaR = request.POST["fecha"]
                form1.save()

                if request.user.is_superuser:
                    valores = RescatePunto.objects.filter(fecha=fechaR)
                else:
                    oficina = user_profile.oficinaR if user_profile else None
                    valores = RescatePunto.objects.filter(fecha=fechaR, oficinaRepre=oficina)

                data = {
                'usuario' : userDataI,
                'form': form,
                'values' : valores,
                }
                messages.success(request, "El registro ha sido modificado")
                return render(request, "dashboard/datos_dia.html", context=data)
            else:
                print("datos erroneos")
                print(form1.errors)
                idR = request.POST["idRescate"]
                rescate = RescatePunto.objects.get(idRescate=idR)
                datos = {
                "form" : form1,
                "value": rescate,
                }
                messages.success(request, "Datos Erroneos")
                return render(request, "dashboard/editarDato.html", context=datos )


    else:
        messages.success(request, "Necesitas ingresar para poder modificar la informacion")
        return redirect('')

@login_required

def puntosI(request):
    data = PuntosInternacion.objects.all().order_by('estadoPunto',"nombrePunto")
    form = CargarArchivoForm()
    context = {"puntosI": data,
               "form": form,
               }
    return render(request, "dashboard/puntosInternacion.html", context)

@login_required

def agregar_puntoInternacion(request):
    idUltimo = PuntosInternacion.objects.latest('idPuntoInter')
    idUltimo = idUltimo.idPuntoInter
    # print(idUltimo)
    if request.method == 'POST':
        
        try:
            # oficinaR = request.POST.get('estadoPunto'),
            # print("El id de oficinaR = "),
            # print(oficinaR),
            PuntosInternacion.objects.create(
                idPuntoInter = idUltimo+1,
                estadoPunto = request.POST.get('estadoPunto'),
                nombrePunto = request.POST.get('nombrePunto'),
                tipoPunto = request.POST.get('tipoPunto'),

            )
            print('Agregado éxitosamente')
            return redirect('paginaPuntosI')
        except:
            print('No se ha podido agregar')
    return render(request, 'dashboard/anadirPuntoInternacion.html')


@login_required

def editar_puntoInternacion(request, id_puntoI):

    puntoI = PuntosInternacion.objects.get(idPuntoInter = id_puntoI)

    data = {
        'form': puntoI
    }
    if request.method == 'POST':
        print("Entró al POST")
        formulario = puntosIForm(data = request.POST, instance=puntoI)

        if formulario.is_valid():
            print("Entró a la validación")
            formulario.save()
            data['message'] = "Datos Modificados correctamente"
            data['form'] = formulario
            return redirect('paginaPuntosI')
        else:
            print("Entró al ELSE")
            print(formulario.errors)



    return render(request, 'editarPuntosI.html', context= data)


@login_required

def eliminarPuntoI(request, id_puntoI):
    idPuntoI  = PuntosInternacion.objects.get(idPuntoInter = id_puntoI)
    idPuntoI.delete()

    return redirect('paginaPuntosI')


@login_required

def edoFuerza(request):
    data = EstadoFuerza.objects.all().order_by('oficinaR',"nomPuntoRevision")
    form = CargarArchivoForm()
    context = {"edoFuerza": data,
               "form": form,
               }
    return render(request, "dashboard/edoFuerza.html", context)

@login_required

def agregar_punto(request):
    idUltimo = EstadoFuerza.objects.latest('idEdoFuerza')
    idUltimo = idUltimo.idEdoFuerza
    print(idUltimo)
    if request.method == 'POST':
        
        try:
            oficinaR = request.POST.get('oficinaR'),
            print("El id de oficinaR = "),
            print(oficinaR),
            EstadoFuerza.objects.create(
                idEdoFuerza = idUltimo+1,
                oficinaR = request.POST.get('oficinaR'),
                numPunto = request.POST.get('numPunto'),
                nomPuntoRevision = request.POST.get('nomPuntoRevision'),
                tipoP = request.POST.get('tipoP'),
                ubicacion = request.POST.get('ubicacion'),
                coordenadasTexto = request.POST.get('coordenadasTexto'),
                latitud = request.POST.get('latitud'),
                longitud = request.POST.get('longitud'),
                personalINM = request.POST.get('personalINM'),
                personalSEDENA = request.POST.get('personalSEDENA'),
                personalMarina = request.POST.get('personalMarina'),
                personalGuardiaN = request.POST.get('personalGuardiaN'),
                personalOTROS = request.POST.get('personalOTROS'),
                vehiculos = request.POST.get('vehiculos'),
                seccion = request.POST.get('seccion'),
            )
            print('Agregado éxitosamente')
            return redirect('pagina_pruebas_edoFuerza')
        except:
            print('No se ha podido agregar')
    return render(request, 'dashboard/anadirPunto.html')


@login_required
def editar_estado_fuerza(request, id_edo_fuerza):
    #estado_fuerza = get_object_or_404(EstadoFuerza, idEdoFuerza=id_edo_fuerza)

    estado_fuerza = EstadoFuerza.objects.get(idEdoFuerza = id_edo_fuerza)

    data = {
        'form': estado_fuerza
    }
    if request.method == 'POST':
        print("Entró al POST")
        formulario = EstadoFuerzaForm(data = request.POST, instance=estado_fuerza)

        if formulario.is_valid():
            print("Entró a la validación")
            formulario.save()
            data['message'] = "Datos Modificados correctamente"
            data['form'] = formulario
            return redirect('pagina_pruebas_edoFuerza')
        else:
            print("Entró al ELSE")
            print(formulario.errors)



    return render(request, 'editarEdoFuerza.html', context= data)

@login_required

def eliminarEdoFuerza(request, id_edo_fuerza):
    id_edo_fuerza  = EstadoFuerza.objects.get(idEdoFuerza = id_edo_fuerza)
    id_edo_fuerza.delete()

    return redirect('pagina_pruebas_edoFuerza')

@login_required

def Usuarios(request):
    data = Usuario.objects.all().order_by("estado")
    form = CargarArchivoForm()
    context = {"usuario": data,
               "form": form,
               }
    return render(request, "dashboard/usuarios.html", context)


@login_required
def agregar_usuario(request):
    idUltimo = Usuario.objects.latest('idUser')
    idUltimo = idUltimo.idUser
    print(idUltimo)
    if request.method == 'POST':
        
        try:
            Usuario.objects.create(
                idUser = idUltimo+1,
                nickname = request.POST.get('nickname'),
                nombre = request.POST.get('nombre'),
                apellido = request.POST.get('apellido'),
                password = request.POST.get('password'),
                estado = request.POST.get('estado'),
                tipo = request.POST.get('tipo'),
                str_pass = request.POST.get('str_pass'),
                tipo_disp = request.POST.get('tipo_disp'),
            )
            print('Agregado éxitosamente')
            return redirect('pagina_pruebas_usuarios')
        except:
            print('No se ha podido agregar')
    return render(request, 'dashboard/anadirUsuario.html')

@login_required

def editar_usuario(request, id_usuario):

    usuario = Usuario.objects.get(idUser = id_usuario)

    data = {
        'form': usuario
    }
    if request.method == 'POST':
        # print("Entró al POST")
        formulario = UsuarioForm(data = request.POST, instance=usuario)

        if formulario.is_valid():
            # print("Entró a la validación")

            Usuario.objects.filter(idUser = id_usuario).update(
                idUser = id_usuario,
                nickname = request.POST.get('nickname'),
                nombre = request.POST.get('nombre'),
                apellido = request.POST.get('apellido'),
                estado = request.POST.get('estado'),
                tipo = request.POST.get('tipo'),
                str_pass = request.POST.get('str_pass'),
                tipo_disp = request.POST.get('tipo_disp'),
            )

            data['message'] = "Datos Modificados correctamente"
            data['form'] = formulario
            return redirect('pagina_pruebas_usuarios')
        else:
            # print("Entró al ELSE")
            idUser = request.POST.get('idUser')
            password = request.POST.get('password')
            Usuario.objects.filter(idUser = idUser).update(
                 password = make_password(password)
             )
            print('Actualizó contraseña')
            print(formulario.errors)

    return render(request, 'editarUsuario.html', context= data)

@login_required

def eliminarUsuario(request, id_usuario):
    id_usuario  = Usuario.objects.get(idUser = id_usuario)
    id_usuario.delete()

    return redirect('pagina_pruebas_usuarios')



# def update_record(request, pk):
#     if request.user.is_authenticated:
#         registro = RescatePunto.objects.get(idRescate=pk)
#         form = addRegistro(request.POST or None, instance = registro)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "El registro ha sido modificado")
#             redirect('dashboard')
#         return render(request, 'dashboard/editarDato.html', {'form' : form})
#     else: 
#         messages.success(request, "Necesitas ingresar para poder modificar la informacion")
#         return redirect('')