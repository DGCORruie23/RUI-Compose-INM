$archivo = "RUIeServer\mapa\templates\mapa\mapa_activo.html"
$contenido = Get-Content -Path $archivo -Raw -Encoding UTF8

$viejo = "onclick=`"window.VehiculosModal.abrir('/vehiculos/api/popover/?inmueble=' + encodeURIComponent(document.getElementById('inmNombreHeader').innerText))`""
$nuevo = "onclick=`"window.VehiculosModal.abrir('/vehiculos/fragmento/resumen-estado/?inmueble=' + encodeURIComponent(document.getElementById('inmNombreHeader').innerText))`""

if ($contenido -notmatch [regex]::Escape($viejo)) {
    Write-Host "No se encontró el onclick anterior. Revisa a mano." -ForegroundColor Red
    return
}

$contenidoNuevo = $contenido.Replace($viejo, $nuevo)

$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Resolve-Path $archivo), $contenidoNuevo, $encoding)
Write-Host "Listo. La tarjeta ahora abre la vista completa de Parque Vehicular." -ForegroundColor Green
