import json
import math
import os

def inverse_lcc(x, y):
    # LCC parameters for EPSG:6372 (LCC Mexico)
    # lat_1 = 17.5, lat_2 = 29.5, lat_0 = 12.0, lon_0 = -102.0
    # x_0 = 2500000.0, y_0 = 0.0
    # Ellipsoid: GRS80 (a = 6378137.0, f = 1/298.257222101)
    
    lat_1 = math.radians(17.5)
    lat_2 = math.radians(29.5)
    lat_0 = math.radians(12.0)
    lon_0 = math.radians(-102.0)
    x_0 = 2500000.0
    y_0 = 0.0
    
    a = 6378137.0
    f = 1 / 298.257222101
    
    e2 = 2 * f - f**2
    e = math.sqrt(e2)
    
    def compute_t(phi):
        sin_phi = math.sin(phi)
        # Avoid dividing by zero or taking log of negative numbers
        sin_phi = max(-0.9999, min(0.9999, sin_phi))
        return math.tan(math.pi/4 - phi/2) / (((1 - e * sin_phi) / (1 + e * sin_phi)) ** (e/2))
        
    def compute_m(phi):
        sin_phi = math.sin(phi)
        return math.cos(phi) / math.sqrt(1 - e2 * sin_phi**2)
        
    m1 = compute_m(lat_1)
    m2 = compute_m(lat_2)
    t1 = compute_t(lat_1)
    t2 = compute_t(lat_2)
    t0 = compute_t(lat_0)
    
    n = (math.log(m1) - math.log(m2)) / (math.log(t1) - math.log(t2))
    F = m1 / (n * (t1 ** n))
    rho_0 = a * F * (t0 ** n)
    
    dx = x - x_0
    dy = rho_0 - (y - y_0)
    
    rho = math.copysign(math.sqrt(dx**2 + dy**2), n)
    
    if rho == 0.0:
        t = 0.0
    else:
        t = (rho / (a * F)) ** (1/n)
        
    theta = math.atan2(dx, dy)
    
    lon = lon_0 + theta / n
    
    phi = math.pi/2 - 2 * math.atan(t)
    for _ in range(5):
        sin_phi = math.sin(phi)
        term = ((1 - e * sin_phi) / (1 + e * sin_phi)) ** (e/2)
        phi = math.pi/2 - 2 * math.atan(t * term)
        
    return math.degrees(lon), math.degrees(phi)

def project_coords(coords, geom_type):
    if geom_type == "Point":
        return list(inverse_lcc(coords[0], coords[1]))
    elif geom_type in ["LineString", "MultiPoint"]:
        return [list(inverse_lcc(pt[0], pt[1])) for pt in coords]
    elif geom_type in ["Polygon", "MultiLineString"]:
        return [[list(inverse_lcc(pt[0], pt[1])) for pt in ring] for ring in coords]
    elif geom_type == "MultiPolygon":
        return [[[list(inverse_lcc(pt[0], pt[1])) for pt in ring] for ring in poly] for poly in coords]
    return coords

ESTADO_NOMBRES = {
    "01": "Aguascalientes",
    "02": "Baja California",
    "03": "Baja California Sur",
    "04": "Campeche",
    "05": "Coahuila de Zaragoza",
    "06": "Colima",
    "07": "Chiapas",
    "08": "Chihuahua",
    "09": "Ciudad de México",
    "10": "Durango",
    "11": "Guanajuato",
    "12": "Guerrero",
    "13": "Hidalgo",
    "14": "Jalisco",
    "15": "México",
    "16": "Michoacán de Ocampo",
    "17": "Morelos",
    "18": "Nayarit",
    "19": "Nuevo León",
    "20": "Oaxaca",
    "21": "Puebla",
    "22": "Querétaro",
    "23": "Quintana Roo",
    "24": "San Luis Potosí",
    "25": "Sinaloa",
    "26": "Sonora",
    "27": "Tabasco",
    "28": "Tamaulipas",
    "29": "Tlaxcala",
    "30": "Veracruz de Ignacio de la Llave",
    "31": "Yucatán",
    "32": "Zacatecas"
}

def main():
    input_path = "/Users/dgcor/Documents/DOCKER PROJ/RUIE-Compose-GCP/RUIe-Compose-INM/RUIeServer/mapa/static/mapa/data/inegi_mexico.geojson"
    output_path = "/Users/dgcor/Documents/DOCKER PROJ/RUIE-Compose-GCP/RUIe-Compose-INM/RUIeServer/mapa/static/mapa/data/inegi_latlon_mexico.geojson"
    
    print(f"Loading {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print("Reprojecting features to WGS84 and mapping names...")
    for i, feature in enumerate(data.get("features", [])):
        geom = feature.get("geometry")
        if geom and "coordinates" in geom:
            geom["coordinates"] = project_coords(geom["coordinates"], geom["type"])
            
        # Map state names
        cve = feature.get("properties", {}).get("cve_ent")
        if cve:
            name = ESTADO_NOMBRES.get(cve, f"Estado {cve}")
            feature["properties"]["name"] = name
            
    print(f"Saving to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print("Done!")

if __name__ == "__main__":
    main()
