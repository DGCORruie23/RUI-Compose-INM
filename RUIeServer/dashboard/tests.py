from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from usuario.models import RescatePunto, Paises
from dashboard.forms import RegistroCreateForm
from usuarioL.models import usuarioL
from datetime import datetime

class DashboardTestCase(TestCase):
    def setUp(self):
        # Create test user and profile
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.profile = usuarioL.objects.create(user=self.user, oficinaR='CDMX')
        
        # Create dummy country
        self.pais = Paises.objects.create(nombre_pais='GUATEMALA', iso3='GTM')
        
        # Client
        self.client = Client()

    def test_form_validation_and_save(self):
        form_data = {
            'fecha': '20-07-26',
            'hora': '12:00',
            'tipo_punto': 'aeropuerto',
            'puntoEstra': 'Sin Información',
            'nacionalidad': 'GUATEMALA',
            'nombre': 'JUAN',
            'apellidos': 'PEREZ',
            'parentesco': 'PADRE',
            'fechaNacimiento': '1990-05-15',
            'sexo': 'True',
            'embarazo': 'False',
            'numFamilia': 1,
            'oficinaR': 'CDMX',
            'nombreAgente': 'AGENTE PRUEBA'
        }
        form = RegistroCreateForm(data=form_data)
        self.assertTrue(form.is_valid(), msg=form.errors.as_text())
        
        # Save and verify
        nuevo_rescate = form.save()
        self.assertIsNotNone(nuevo_rescate.idRescate)
        self.assertEqual(nuevo_rescate.nombre, 'JUAN')
        self.assertEqual(nuevo_rescate.apellidos, 'PEREZ')
        self.assertEqual(nuevo_rescate.nacionalidad, 'GUATEMALA')
        self.assertEqual(nuevo_rescate.iso3, 'GTM')
        self.assertEqual(nuevo_rescate.fechaNacimiento, '15/05/1990')
        self.assertEqual(nuevo_rescate.sexo, True)
        self.assertEqual(nuevo_rescate.embarazo, False)
        self.assertEqual(nuevo_rescate.numFamilia, 1)
        self.assertEqual(nuevo_rescate.oficinaRepre, 'CDMX')
        self.assertEqual(nuevo_rescate.nombreAgente, 'AGENTE PRUEBA')

    def test_view_agregar_data_get(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('agregar_registro_fecha', kwargs={'year': 2026, 'month': 7, 'day': 20}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Agregar Registro')
        self.assertContains(response, '20-07-26')

    def test_view_agregar_data_post(self):
        self.client.login(username='testuser', password='testpassword')
        form_data = {
            'fecha': '20-07-26',
            'hora': '14:30',
            'tipo_punto': 'aeropuerto',
            'puntoEstra': 'Sin Información',
            'nacionalidad': 'GUATEMALA',
            'nombre': 'MARIA',
            'apellidos': 'GOMEZ',
            'parentesco': 'MADRE',
            'fechaNacimiento': '1995-10-20',
            'sexo': 'False',
            'embarazo': 'True',
            'numFamilia': 2,
            'oficinaR': 'CDMX',
            'nombreAgente': 'AGENTE PRUEBA 2'
        }
        response = self.client.post(
            reverse('agregar_registro_fecha', kwargs={'year': 2026, 'month': 7, 'day': 20}),
            data=form_data
        )
        self.assertRedirects(
            response,
            reverse('tabla_registros_fecha', kwargs={'year': 2026, 'month': 7, 'day': 20})
        )
        
        rescate = RescatePunto.objects.get(nombre='MARIA', apellidos='GOMEZ')
        self.assertEqual(rescate.hora, '14:30')
        self.assertEqual(rescate.fecha, '20-07-26')
        self.assertEqual(rescate.sexo, False)
        self.assertEqual(rescate.embarazo, True)

    def test_bulk_correction(self):
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username='testuser', password='testpassword')
        
        # Create some rescue records
        r1 = RescatePunto.objects.create(
            fecha='20-07-26', hora='10:00', nombre='A', apellidos='B', nacionalidad='GUATEMALA', iso3='GTM',
            fechaNacimiento='01/01/2000', edad=26, sexo=True, embarazo=False, numFamilia=0, oficinaRepre='CDMX',
            aeropuerto=True, puntoEstra='AEROPUERTO CDMX', numPresuntosDelincuentes=0
        )
        r2 = RescatePunto.objects.create(
            fecha='20-07-26', hora='11:00', nombre='C', apellidos='D', nacionalidad='GUATEMALA', iso3='GTM',
            fechaNacimiento='01/01/2000', edad=26, sexo=True, embarazo=False, numFamilia=0, oficinaRepre='CDMX',
            aeropuerto=True, puntoEstra='AEROPUERTO CDMX', numPresuntosDelincuentes=0
        )

        form_data = {
            'registros_seleccionados': [r1.idRescate, r2.idRescate],
            'nueva_oficina': 'CHIAPAS',
            'nuevo_tipo_punto': 'carretero',
            'nuevo_punto': 'CASETA SAN CRISTOBAL',
            'fecha_redirect': '20-07-26'
        }

        response = self.client.post(reverse('corregir_registros_masivo'), data=form_data)
        self.assertRedirects(response, reverse('tabla_registros_fecha', kwargs={'year': 2026, 'month': 7, 'day': 20}))

        # Verify bulk updates in DB
        r1.refresh_from_db()
        r2.refresh_from_db()

        self.assertEqual(r1.oficinaRepre, 'CHIAPAS')
        self.assertEqual(r1.carretero, True)
        self.assertEqual(r1.aeropuerto, False)
        self.assertEqual(r1.puntoEstra, 'CASETA SAN CRISTOBAL')

        self.assertEqual(r2.oficinaRepre, 'CHIAPAS')
        self.assertEqual(r2.carretero, True)
        self.assertEqual(r2.aeropuerto, False)
        self.assertEqual(r2.puntoEstra, 'CASETA SAN CRISTOBAL')

    def test_bulk_correction_non_superuser(self):
        # Normal user login (not superuser, oficinaR='CDMX')
        self.client.login(username='testuser', password='testpassword')
        
        # Create some rescue records
        r1 = RescatePunto.objects.create(
            fecha='20-07-26', hora='10:00', nombre='A', apellidos='B', nacionalidad='GUATEMALA', iso3='GTM',
            fechaNacimiento='01/01/2000', edad=26, sexo=True, embarazo=False, numFamilia=0, oficinaRepre='CDMX',
            aeropuerto=True, puntoEstra='AEROPUERTO CDMX', numPresuntosDelincuentes=0
        )

        form_data = {
            'registros_seleccionados': [r1.idRescate],
            'nueva_oficina': 'CHIAPAS', # Attempting to bypass limits
            'nuevo_tipo_punto': 'carretero',
            'nuevo_punto': 'CASETA SAN CRISTOBAL',
            'fecha_redirect': '20-07-26'
        }

        response = self.client.post(reverse('corregir_registros_masivo'), data=form_data)
        r1.refresh_from_db()
        
        # Should stay at CDMX because they are not superuser
        self.assertEqual(r1.oficinaRepre, 'CDMX')
        self.assertEqual(r1.carretero, True)
        self.assertEqual(r1.puntoEstra, 'CASETA SAN CRISTOBAL')
