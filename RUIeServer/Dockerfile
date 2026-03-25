#imagen a instalar
FROM python:3.9

#usamos el directorio de trabajo
WORKDIR /src/backendRUIe

#ESTABLECER VARIABLES DEL ENTORNO 
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

#ACTUALIZAR PIP
RUN pip install --upgrade pip

#actualizar e instalar conectores postgres
RUN apt-get update && apt-get install -y gcc libpq-dev python3-dev musl-dev postgresql-client python-gi-dev gtk+3

#Copiar los requisitos del sistema
COPY ./req.txt ./

#instalar dependencias 
RUN pip install -r req.txt

#se crea el directorio para los archivos Staticos de django
RUN mkdir /src/backendRUIe/static

#Copiar el proyecto entero
COPY . .
#se ejecuta el archivo
#ENTRYPOINT ["/usr/src/django_proj/entrypoint.sh"]