from django.shortcuts import render
from django.contrib.auth.forms import AuthenticationForm
from datetime import datetime, timedelta
from usuario.models import RescatePunto



# Create your views here.
def index(request):

    fechaIN = datetime.strptime(f"2024-01-01", "%Y-%m-%d")
    fechaFN = datetime.today()
    # fechaFN = datetime.strptime(f"{fechaF}", "%Y-%m-%d")

    # fecha_inicio = datetime(2024, 1, 1)
    # print(fecha_inicio)
    print(fechaIN)

    # fecha_inicio = datetime(yearI, mesI, diaI)
    # fecha_fin = datetime(diaF, mesF, yearF)

    array_fechas = [(fechaIN + timedelta(days=d)).strftime("%d-%m-%y") for d in range((fechaFN - fechaIN).days + 1)]
    rescatesT = RescatePunto.objects.filter(fecha__in=array_fechas).count()
    rescatesTH = RescatePunto.objects.filter(fecha__in=array_fechas, sexo = 1).count()
    rescatesTM = RescatePunto.objects.filter(fecha__in=array_fechas, sexo = 0).count()
    datos = {
                "fecha" : fechaFN,
                "total" : rescatesT,
                "totalH": rescatesTH,
                "totalM": rescatesTM,
                }
    return render(request, 'base/index.html',context=datos)

def pagina404(request, exception):
    return render(request, 'base/error404.html')

# class CustomAuthenticationForm(AuthenticationForm):
#     def __init__(self, request=None, *args, **kwargs):
#         super().__init__(request=None, *args, **kwargs)
#         self.fields['username'].label = 'a cool label'
#         self.fields['password'].label = 'another cool label'
