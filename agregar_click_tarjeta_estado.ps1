$archivo = "RUIeServer\mapa\templates\mapa\mapa_activo.html"
$lineas = [System.Collections.Generic.List[string]](Get-Content -Path $archivo -Encoding UTF8)

# Buscar el comentario "Tarjeta de Vehículos" que esté seguido, en las
# siguientes 15 líneas, por el id "estVehTotal" (la del Estado, no la
# del Inmueble que ya quedó lista antes).
$idxComentario = -1
for ($i = 0; $i -lt $lineas.Count; $i++) {
    if ($lineas[$i] -like '*Tarjeta de Veh*') {
        $rango = $lineas.GetRange($i, [Math]::Min(15, $lineas.Count - $i))
        if ($rango -join "`n" -like '*estVehTotal*') {
            $idxComentario = $i
            break
        }
    }
}
if ($idxComentario -eq -1) { Write-Host "No se encontró la tarjeta de vehículos del estado" -ForegroundColor Red; return }

$idxDiv = $idxComentario + 1
$lineaOriginal = $lineas[$idxDiv]

if ($lineaOriginal -notlike '*bg-white/80 backdrop-blur-md p-6 rounded-*') {
    Write-Host "La línea siguiente al comentario no es el <div> esperado. Revisa a mano." -ForegroundColor Red
    Write-Host $lineaOriginal
    return
}

if ($lineaOriginal -like '*onclick*') {
    Write-Host "Esa tarjeta YA tiene un onclick — no se tocó, para no duplicar." -ForegroundColor Yellow
    return
}

$patron = 'class="bg-white/80 backdrop-blur-md p-6 rounded-\[2rem\] border border-gray-100 shadow-sm relative overflow-hidden flex items-center gap-5"'
$reemplazo = 'class="bg-white/80 backdrop-blur-md p-6 rounded-[2rem] border border-gray-100 shadow-sm relative overflow-hidden flex items-center gap-5 cursor-pointer hover:border-emerald-300 hover:shadow-md transition-all" onclick="window.VehiculosModal.abrir(''/vehiculos/fragmento/resumen-estado/?estado='' + encodeURIComponent(document.getElementById(''estNombreHeader'').innerText))" title="Ver detalle en el modulo de Parque Vehicular"'

$lineaNueva = $lineaOriginal -replace $patron, $reemplazo

if ($lineaNueva -eq $lineaOriginal) {
    Write-Host "El reemplazo no encontró la clase exacta a modificar. Revisa a mano." -ForegroundColor Red
    Write-Host $lineaOriginal
    return
}

$lineas[$idxDiv] = $lineaNueva

$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines((Resolve-Path $archivo), $lineas, $encoding)
Write-Host "Listo. Tarjeta de vehículos del ESTADO ahora es clickeable (línea $($idxDiv + 1))." -ForegroundColor Green
