"""
URL configuration for serverRUI project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls import handler404
from usuario import views
from usuarioL.views import index, pagina404
from dashboard import views as viewsDash
from django.contrib.auth import views as viewsL
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', index, name="index"),

    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    path('log-in/', viewsL.LoginView.as_view(template_name= 'base/log_in.html'), name='log-in'),
    path('log-out', viewsL.LogoutView.as_view(), name="logout" ),

    path('login/validar/', views.login_user),
    path('info/', include('usuario.urls')),

    path('registro/insertR', views.insert_rescates),
    path('registro/insertC', views.insert_conteo),
    path('registro/insertD', views.insert_disuadidos),
    path('descargas/', views.servirApps, name="descargas"),
    path('descargas/apk', views.downloadAPK, name="descarga_android"),

    path('estadistica/', include('estadistica.urls')),
    # path('info/pruebas/edoFuerza/editarEdoFuerza/<int:id_edo_fuerza>', viewsDash.editar_estado_fuerza, name='editar_estado_fuerza'),
    # path('info/pruebas/usuarios/eliminarUsuario/<int:id_usuario>', viewsDash.eliminarUsuario, name='eliminar_usuario'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = pagina404