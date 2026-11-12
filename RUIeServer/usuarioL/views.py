from django.shortcuts import render
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from datetime import datetime, timedelta
from usuario.models import RescatePunto
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import math
import secrets
import time


CAPTCHA_SESSION_KEY = '_math_captcha_answer'
CAPTCHA_TS_SESSION_KEY = '_math_captcha_ts'
CAPTCHA_EXPIRY_SECONDS = 300  # 5 minutos de vigencia


def _load_captcha_font(size=28):
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "arialbd.ttf",
        "arial.ttf",
    ]
    for font_path in font_candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


@never_cache
def captcha_image(request):
    """Genera una imagen PNG con una operación matemática distorsionada y guarda la respuesta en sesión."""
    rng = secrets.SystemRandom()
    op = rng.choice(['+', '-', '×'])

    if op == '+':
        a = rng.randint(2, 25)
        b = rng.randint(2, 20)
        result = a + b
    elif op == '-':
        a = rng.randint(10, 35)
        b = rng.randint(1, a - 1)
        result = a - b
    else:
        a = rng.randint(2, 9)
        b = rng.randint(2, 9)
        result = a * b

    request.session[CAPTCHA_SESSION_KEY] = str(result)
    request.session[CAPTCHA_TS_SESSION_KEY] = int(time.time())
    request.session.modified = True

    expression = f"{a} {op} {b} = ?"

    width, height = 200, 60
    bg_color = (242, 247, 246)
    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    # Cuadrícula sutil de fondo
    for x in range(0, width, 16):
        draw.line([(x, 0), (x, height)], fill=(224, 234, 232), width=1)
    for y in range(0, height, 16):
        draw.line([(0, y), (width, y)], fill=(224, 234, 232), width=1)

    # Líneas y arcos distractores
    palette = [
        (16, 49, 43),
        (0, 121, 107),
        (30, 90, 80),
        (95, 35, 55),
        (45, 70, 110),
    ]
    for _ in range(6):
        x1, y1 = rng.randint(0, width), rng.randint(0, height)
        x2, y2 = rng.randint(0, width), rng.randint(0, height)
        line_color = (rng.randint(140, 195), rng.randint(155, 205), rng.randint(155, 200))
        draw.line([(x1, y1), (x2, y2)], fill=line_color, width=rng.randint(1, 2))

    # Renderizar cada carácter con ligera rotación y desplazamiento vertical
    font = _load_captcha_font(size=28)
    x_cursor = 18
    for ch in expression:
        if ch == ' ':
            x_cursor += 8
            continue
        char_img = Image.new('RGBA', (36, 48), (0, 0, 0, 0))
        char_draw = ImageDraw.Draw(char_img)
        color = rng.choice(palette)
        char_draw.text((6, 6), ch, font=font, fill=color)
        angle = rng.randint(-18, 18)
        rotated = char_img.rotate(angle, resample=Image.BICUBIC, expand=False)
        y_offset = rng.randint(4, 12)
        image.paste(rotated, (x_cursor, y_offset), rotated)
        x_cursor += 20

    # Deformación senoidal ligera para dificultar OCR automatizado
    warped = Image.new('RGB', (width, height), bg_color)
    src_pixels = image.load()
    dst_pixels = warped.load()
    amp = rng.uniform(2.0, 3.2)
    freq = rng.uniform(0.06, 0.09)
    phase = rng.uniform(0, math.pi * 2)
    for x in range(width):
        shift_y = int(amp * math.sin(freq * x + phase))
        for y in range(height):
            src_y = y + shift_y
            if 0 <= src_y < height:
                dst_pixels[x, y] = src_pixels[x, src_y]

    # Puntos de ruido
    warp_draw = ImageDraw.Draw(warped)
    for _ in range(90):
        px, py = rng.randint(0, width - 1), rng.randint(0, height - 1)
        warp_draw.point((px, py), fill=(rng.randint(80, 180), rng.randint(90, 180), rng.randint(90, 180)))

    warped = warped.filter(ImageFilter.SMOOTH)

    buf = io.BytesIO()
    warped.save(buf, format='PNG')
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response


class CaptchaAuthenticationForm(AuthenticationForm):
    captcha = forms.CharField(
        required=True,
        max_length=10,
        label="Verificación de seguridad",
        error_messages={'required': 'Por favor resuelve la operación matemática.'},
    )

    def clean(self):
        # Primero validamos el CAPTCHA e invalidamos la respuesta en sesión (un solo uso)
        user_answer = (self.cleaned_data.get('captcha') or '').strip()
        expected_answer = self.request.session.pop(CAPTCHA_SESSION_KEY, None)
        created_ts = self.request.session.pop(CAPTCHA_TS_SESSION_KEY, 0)
        self.request.session.modified = True

        now = int(time.time())
        if not expected_answer or (now - int(created_ts)) > CAPTCHA_EXPIRY_SECONDS:
            raise forms.ValidationError(
                "El código de seguridad expiró. Por favor intenta con el nuevo cálculo.",
                code='captcha_expired',
            )

        if user_answer != str(expected_answer):
            raise forms.ValidationError(
                "El resultado de la operación matemática es incorrecto.",
                code='captcha_invalid',
            )

        return super().clean()


class CaptchaLoginView(auth_views.LoginView):
    template_name = 'base/log_in.html'
    authentication_form = CaptchaAuthenticationForm



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
