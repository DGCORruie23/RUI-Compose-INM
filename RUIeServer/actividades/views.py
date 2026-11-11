from django.shortcuts import render

# Create your views here.

def actividades_index(request):
    return render(request, 'actividades/index.html')