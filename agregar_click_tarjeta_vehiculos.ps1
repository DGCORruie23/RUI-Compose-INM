$archivo = "RUIeServer\mapa\templates\mapa\mapa_activo.html"
$lineas = [System.Collections.Generic.List[string]](Get-Content -Path $archivo -Encoding UTF8)

# Buscar el comentario "Tarjeta de Vehículos" que esté seguido, en las
# siguientes 15 líneas, por el id "inmVehTotal" (para no confundirlo con
# la tarjeta de "Vehículos del Estado", que usa "estVehTotal").
$idxComentario = -1
for ($i = 0; $i -lt $lineas.Count; $i++) {
    if ($lineas[$i] -like '*Tarjeta de Veh*') {
        $rango = $lineas.GetRange($i, [Math]::Min(15, $lineas.Count - $i))
        if ($rango -join "`n" -like '*inmVehTotal*') {
            $idxComentario = $i
            break
        }
    }
}
if ($idxComentario -eq -1) { Write-Host "No se encontró la tarjeta de vehículos del inmueble" -ForegroundColor Red; return }

# La línea del <div> contenedor es la siguiente al comentario.
$idxDiv = $idxComentario + 1
$lineaOriginal = $lineas[$idxDiv]

if ($lineaOriginal -notlike '*bg-white/80 backdrop-blur-md p-6 rounded-*') {
    Write-Host "La línea siguiente al comentario no es el <div> esperado. Revisa a mano." -ForegroundColor Red
    Write-Host $lineaOriginal
    return
}

$lineaNueva = $lineaOriginal -replace 'class="bg-white/80 backdrop-blur-md p-6 rounded-\[2rem\] border border-gray-100 shadow-sm relative overflow-hidden flex items-center gap-5"', 'class="bg-white/80 backdrop-blur-md p-6 rounded-[2rem] border border-gray-100 shadow-sm relative overflow-hidden flex items-center gap-5 cursor-pointer hover:border-emerald-300 hover:shadow-md transition-all" onclick="window.VehiculosModal.abrir(''/vehiculos/api/popover/?inmueble='' + encodeURIComponent(document.getElementById(''inmNombreHeader'').innerText))" title="Ver detalle en el módulo de Parque Vehicular"'

if ($lineaNueva -eq $lineaOriginal) {
    Write-Host "El reemplazo no encontró la clase exacta a modificar. Revisa a mano." -ForegroundColor Red
    return
}

$lineas[$idxDiv] = $lineaNueva

$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines((Resolve-Path $archivo), $lineas, $encoding)
Write-Host "Listo. Tarjeta de vehículos del inmueble ahora es clickeable (línea $($idxDiv + 1))." -ForegroundColor Green
