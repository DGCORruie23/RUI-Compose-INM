$archivo = "RUIeServer\mapa\templates\mapa\mapa_activo.html"
$lineas = [System.Collections.Generic.List[string]](Get-Content -Path $archivo -Encoding UTF8)

$idxModalJs = -1
for ($i = 0; $i -lt $lineas.Count; $i++) {
    if ($lineas[$i] -like '*vehiculos/js/modal.js*') { $idxModalJs = $i; break }
}
if ($idxModalJs -eq -1) { Write-Host "No se encontró la línea de modal.js" -ForegroundColor Red; return }

$nuevaLinea = "<script src=""{% static 'vehiculos/js/hold-menu.js' %}""></script>"
$lineas.Insert($idxModalJs + 1, $nuevaLinea)

$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines((Resolve-Path $archivo), $lineas, $encoding)
Write-Host "Listo. hold-menu.js agregado en la línea $($idxModalJs + 2)" -ForegroundColor Green
