from django.shortcuts import render
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, HoverTool, TapTool, CustomJS
from bokeh.embed import components
import json
import random
import os
from django.conf import settings

def mapa_informacion(request):
    # Ruta al archivo geojson descargado
    geojson_path = os.path.join(settings.BASE_DIR, 'mapa', 'static', 'mapa', 'data', 'mexico.geojson')
    
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geo_data = json.load(f)
        
    # Añadir datos aleatorios a cada estado para ambos periodos
    for feature in geo_data['features']:
        # Datos Periodo CS
        feature['properties']['cs_repatriados'] = random.randint(1000, 5000)
        feature['properties']['cs_retornados'] = random.randint(50, 500)
        feature['properties']['cs_rescatados'] = random.randint(100, 1000)
        feature['properties']['cs_ingresos'] = random.randint(5000, 25000)
        feature['properties']['cs_tramites'] = random.randint(200, 2000)
        
        # Datos Periodo DT
        feature['properties']['dt_repatriados'] = random.randint(800, 4000)
        feature['properties']['dt_retornados'] = random.randint(40, 400)
        feature['properties']['dt_rescatados'] = random.randint(80, 800)
        feature['properties']['dt_ingresos'] = random.randint(4000, 20000)
        feature['properties']['dt_tramites'] = random.randint(150, 1500)
        
        # Desgloses (Ejemplo para Repatriados)
        feature['properties']['cs_repatriados_m'] = random.randint(0, feature['properties']['cs_repatriados'])
        feature['properties']['cs_repatriados_h'] = feature['properties']['cs_repatriados'] - feature['properties']['cs_repatriados_m']
        
        # Para el tooltip actual usamos CS por defecto
        feature['properties']['repatriados'] = f"{feature['properties']['cs_repatriados']:,}"
        feature['properties']['retornados'] = f"{feature['properties']['cs_retornados']:,}"
        feature['properties']['rescatados'] = f"{feature['properties']['cs_rescatados']:,}"
        feature['properties']['ingresos'] = f"{feature['properties']['cs_ingresos']:,}"
        feature['properties']['tramites'] = f"{feature['properties']['cs_tramites']:,}"
        
    geo_source = GeoJSONDataSource(geojson=json.dumps(geo_data))
    
    # Crear figura de Bokeh
    p = figure(
        title="Monitoreo Migratorio por Estado",
        sizing_mode="scale_both",
        toolbar_location=None,
        tools="tap",
        match_aspect=True,
    )
    p.xaxis.visible = False
    p.yaxis.visible = False
    p.grid.grid_line_color = None
    p.outline_line_color = None
    p.min_border = 0
    
    # Dibujar los estados
    states = p.patches(
        'xs', 'ys', 
        source=geo_source,
        fill_color="#cbd5e1",
        line_color="#ffffff",
        line_width=1,
        fill_alpha=1.0,
        hover_fill_color="#285C4D",
        selection_fill_color="#285C4D",
        nonselection_fill_alpha=0.2,
        nonselection_fill_color="#cbd5e1",
        nonselection_line_alpha=0.2
    )
    
    # Añadir HoverTool con HTML personalizado según imagen
    hover_html = """
        <div style="padding: 10px; min-width: 200px; font-family: Arial, sans-serif;">
            <div style="font-size: 20px; font-weight: 500; margin-bottom: 5px; color: #333;">@name</div>
            <div style="border-bottom: 1px solid #ddd; margin-bottom: 8px;"></div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 16px; color: #333;">Repatriados</span>
                <span style="font-size: 16px; font-weight: 500; color: #333;">@repatriados</span>
            </div>
            <div style="border-bottom: 1px solid #eee; margin-bottom: 8px;"></div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 16px; color: #333;">Retornados</span>
                <span style="font-size: 16px; font-weight: 500; color: #333;">@retornados</span>
            </div>
            <div style="border-bottom: 1px solid #eee; margin-bottom: 8px;"></div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 16px; color: #333;">Rescatados</span>
                <span style="font-size: 16px; font-weight: 500; color: #333;">@rescatados</span>
            </div>
            <div style="border-bottom: 1px solid #eee; margin-bottom: 8px;"></div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 16px; color: #333;">Ingresos</span>
                <span style="font-size: 16px; font-weight: 500; color: #333;">@ingresos</span>
            </div>
            <div style="border-bottom: 1px solid #eee; margin-bottom: 8px;"></div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                <span style="font-size: 16px; color: #333;">Trámites</span>
                <span style="font-size: 16px; font-weight: 500; color: #333;">@tramites</span>
            </div>
        </div>
    """
    
    hover = HoverTool(
        renderers=[states],
        tooltips=hover_html
    )
    p.add_tools(hover)
    
    # Añadir CustomJS para el evento de click (Tap)
    tap_js = CustomJS(args=dict(source=geo_source), code="""
        const indices = source.selected.indices;
        if (indices.length > 0) {
            const index = indices[0];
            const data = source.data;
            
            // Guardar datos en el objeto global para que el HTML los use
            window.selectedStateData = {
                name: data['name'][index],
                cs: {
                    repatriados: data['cs_repatriados'][index],
                    retornados: data['cs_retornados'][index],
                    rescatados: data['cs_rescatados'][index],
                    ingresos: data['cs_ingresos'][index],
                    tramites: data['cs_tramites'][index],
                    repatriados_m: data['cs_repatriados_m'][index],
                    repatriados_h: data['cs_repatriados_h'][index]
                },
                dt: {
                    repatriados: data['dt_repatriados'][index],
                    retornados: data['dt_retornados'][index],
                    rescatados: data['dt_rescatados'][index],
                    ingresos: data['dt_ingresos'][index],
                    tramites: data['dt_tramites'][index]
                }
            };
            
            // Disparar evento para actualizar el panel
            if (window.updateInformationPanel) {
                window.updateInformationPanel();
            }
        }
    """)
    p.select(TapTool).callback = tap_js
    
    script, div = components(p)
    
    context = {
        'map_script': script,
        'map_div': div,
    }
    
    return render(request, 'mapa/informacion.html', context)
