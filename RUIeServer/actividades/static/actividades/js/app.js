/* ==================================================================
   IA-NAMI · PÁGINA PRINCIPAL (PULSO)
   ÍNDICE JS: [1] CONFIG Y CATÁLOGOS   [2] DATOS (cubo y consultas)
              [3] UTILIDADES           [4] ESTADO Y FILTRO
              [5] ANÁLISIS AUTOMÁTICO  [6] INDICADORES
              [7] MAPA (estados, círculos, puntos)
              [8] FLUJOS ANIMADOS Y TRANSICIÓN DE COLOR
              [9] BARRA DE TIEMPO Y REPRODUCCIÓN
              [10] COLUMNA DE ANÁLISIS Y FRANJA DE CAJAS
              [11] BUSCADOR, SECCIONES Y AVISOS   [12] ARRANQUE
   Los datos llegan de datos/datos.js, que genera robot/convertir.py a
   partir de las bases de la carpeta DATA. El periodo se toma de ahí.
   ================================================================== */
(function(){
'use strict';

/* ==== [1] CONFIG Y CATÁLOGOS ====================================== */
const D = window.IANAMI_DATOS, GEO = window.IANAMI_GEO, CEN = window.IANAMI_CEN;
const NN = D.nats.length, NS = D.ests.length;
let NW = D.ends.length, ND = D.dias, P0 = 0, P1 = D.dias;   // semanas y días del periodo elegido; P0-P1: su lugar en los datos completos
const OT = NN - 2, MX = NN - 1;                       // índices de "Otras" y "México"
// Series diarias por estado y por nacionalidad: llegan dispersas ([día, columna, valor]) y aquí se expanden
['ds','dn'].forEach(p => Object.keys(D[p]).forEach(k => { const L = p==='ds' ? NS : NN, a = new Float64Array(ND*L), c = D[p][k];
  for (let i=0;i<c.length;i+=3) a[c[i]*L + c[i+1]] = c[i+2]; D[p][k] = a; }));
// Copia de los datos completos: cada periodo se arma a partir de aquí (aplicarPeriodo)
const D0 = { dias:D.dias, ends:D.ends.slice(), daily:Object.assign({}, D.daily), ds:Object.assign({}, D.ds), dn:Object.assign({}, D.dn), wks:[] };
[D.puntos, D.repPuntos, D.emPuntos, D.cbp ? D.cbp.sectores : []].forEach(l => l.forEach(o => D0.wks.push({ obj:o, wk:o.wk.slice() })));
const EST = D.ests;
const ESTC = EST.map(e => e==='Ciudad de México'?'CDMX':e==='Estado de México'?'Edo. de México':e==='Baja California Sur'?'Baja California S.':e);
const ECLAVE = EST.map(e => 'MX_' + (e==='Estado de México' ? 'México' : e));   // clave del estado en el mapa
const MES12 = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
const INICIO0 = new Date(D.inicio+'T00:00:00');       // primer día de las bases
let INICIO = INICIO0;                                  // primer día del periodo elegido; el calendario sale de aquí
const INDS = [
  {k:'ing',  n:'Ingresos',    g:'reg', nat:true,  donde:'Por dónde ingresan'},
  {k:'rech', n:'Rechazos',    g:'reg', nat:true,  donde:'Dónde son rechazados'},
  {k:'tram', n:'Trámites',    g:'reg', nat:true,  donde:'Dónde tramitan'},
  {k:'resc', n:'Rescatados',  g:'irr', nat:true,  donde:'Dónde son rescatados'},
  {k:'pres', n:'Presentados', g:'irr', nat:true,  donde:'Dónde son presentados'},
  {k:'can',  n:'Canalizados', g:'irr', nat:true,  donde:'Dónde son canalizados'},
  {k:'ret',  n:'Retornados',  g:'irr', nat:true,  donde:'Desde dónde retornan'},
  {k:'recib',n:'Recibidos',   g:'usa', nat:true,  donde:'Dónde son recibidos'},
  {k:'rep',  n:'Repatriados', g:'usa', nat:false, donde:'Dónde son repatriados'},
  // Encuentros: los registra la CBP en EE. UU. (no el INM); no tienen estado de México, se reparten por sector de la frontera
  {k:'cbp',  n:'Encuentros',  g:'usa', nat:true, sinEdo:true, donde:'Dónde los encuentra la CBP'}
].filter(m => D.cube[m.k] && (m.k!=='cbp' || (D.cbpT && D.cbp)));
const IND = {}; INDS.forEach(m => IND[m.k] = m);
// Indicadores que solo existen en la pantalla completa de Regulación (no están en el cubo; ver [13])
IND.co = {k:'co', n:'No expiden tarjetas', g:'reg', nat:true}; IND.va = {k:'va', n:'Validación de actas', g:'reg', nat:true};
const GRUPOS = [['reg','Articulo 159',3],['irr','Articulo 129',4],['usa','Gestión Administrativa',IND.cbp ? 3 : 2]];
const ICONO = {
  ing:'M3 12h12M11 7l5 5-5 5M20 4v16', rech:'M5.6 5.6l12.8 12.8M12 3a9 9 0 1 0 0 18a9 9 0 0 0 0-18z', tram:'M7 3h7l4 4v14H7zM14 3v4h4M10 12h5M10 16h5',
  resc:'M12 3a9 9 0 1 0 0 18a9 9 0 0 0 0-18zM12 9a3 3 0 1 0 0 6a3 3 0 0 0 0-6zM5.7 5.7l4.2 4.2M14.1 14.1l4.2 4.2M18.3 5.7l-4.2 4.2M9.900 14.100l-4.200 4.200',
  pres:'M4 21V9l8-5 8 5v12M9 21v-6h6v6', can:'M12 20s-7-4.300-7-9.400A4 4 0 0 1 12 8a4 4 0 0 1 7 2.600C19 15.700 12 20 12 20z',
  co:'M7 3h7l4 4v14H7zM14 3v4h4M10 11h5M12.5 15.5m-2 0a2 2 0 1 0 4 0a2 2 0 1 0-4 0', va:'M5 3h11l3 3v15H5zM9 9h6M9 13h3M13 16l2 2 4-4',
  ret:'M21 12H9M13 7l-5 5 5 5M4 4v16', recib:'M12 4v10M8 10l4 4 4-4M5 19h14', rep:'M4 11l8-7 8 7M6 10v10h12V10M10 20v-5h4v5',
  cbp:'M3 21V9l9-6 9 6v12M3 13h18M8 21v-4h8v4M12 3v4'
};
// Secciones del menú (las que aún no existen muestran qué llevarán)
// Prospectiva y Contexto todavía no existen: no se muestran en el menú (su vista se conserva para cuando se construyan)
const SECCIONES = [['pulso','Pulso']];
// Procesos del INM y las direcciones que los alimentan
const DIRS = [
  {k:'control',    s:'Control migratorio',     n:'DGCVM y DGCOR', ind:['ing','rech','pres','can','ret','resc','recib']},
  {k:'regulacion', s:'Regulación migratoria',  n:'DGRAM',         ind:['tram'], docs:true},
  {k:'proteccion', s:'Protección al migrante', n:'DGPMV',         ind:['rep']}
];
// Agrupaciones territoriales (vienen de Cinturones_Contencion.csv y Centro_Coordinador_Operaciones.csv)
const AGR = {
  c:{ n:'Cinturón', sin:'Sin cinturón', nombres:['Cinturón 1','Cinturón 2','Cinturón 3','Cinturón 4'],
      m:{'Chiapas':0,'Tabasco':0,'Oaxaca':1,'Veracruz':1,'Hidalgo':2,'Nuevo León':2,'Puebla':2,'San Luis Potosí':2,'Tamaulipas':2,'Tlaxcala':2,'Baja California':3,'Chihuahua':3,'Coahuila':3,'Sonora':3} },
  o:{ n:'CECO', sin:'Sin CECO', nombres:['CECO Suchiate','CECO Río Bravo'],
      m:{'Chiapas':0,'Tabasco':0,'Oaxaca':0,'Veracruz':0,'Quintana Roo':0,'Yucatán':0,'Puebla':0,'Estado de México':0,'Hidalgo':0,'Campeche':0,'Tlaxcala':0,'Chihuahua':1,'Baja California':1,'Nuevo León':1,'San Luis Potosí':1,'Coahuila':1,'Tamaulipas':1,'Sonora':1,'Sinaloa':1,'Durango':1} }
};
Object.keys(AGR).forEach(a => { AGR[a].de = EST.map(e => AGR[a].m[e]==null ? -1 : AGR[a].m[e]); });
const TODOS_GRUPO = {}; Object.keys(AGR).forEach(a => { TODOS_GRUPO[a] = []; AGR[a].de.forEach((q,s) => { if (q>=0) TODOS_GRUPO[a].push(s); }); });
const miembros = (a,q) => { const o = []; AGR[a].de.forEach((x,s) => { if (x===q) o.push(s); }); return o; };
// Contexto por país: catálogo verificado en js/contexto.js (qué pasó, efecto migratorio y fuente)
const CATS = {pol:['Política','#6B5B95'], eco:['Economía','#8F7F2E'], vio:['Violencia','#B4472F'], des:['Desastre','#3D7A8C'], mig:['Política migratoria','#2B2926']};
const CTX = window.IANAMI_CONTEXTO || {reg:[]};
const ORIGEN = {840:[-97,36.2], 124:[-100,54], 643:[38,56]};     // puntos de partida ajustados
const ANCLA_EU = [-99.3, 32.4];
// Íconos del mapa: punto de internación (marcador), repatriación (casa) y estación migratoria (edificio)
const GLIFO_PUNTO = {
  ing:'M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3',
  rep:'M3 10.5L12 3l9 7.5M5.5 9v11h13V9M10 20v-5h4v5',
  em: 'M6 21V4.5A1.5 1.5 0 0 1 7.5 3h9A1.5 1.5 0 0 1 18 4.5V21M3 21h18M10 7h1M13 7h1M10 11h1M13 11h1M10 15h1M13 15h1'
};
function svgPunto(tipo, color, fondo){ return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><circle cx="16" cy="16" r="14.5" fill="'+fondo+'" stroke="'+color+'" stroke-width="1.8"/>'+
  '<g transform="translate(8.8 8.8) scale(.6)" fill="none" stroke="'+color+'" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="'+GLIFO_PUNTO[tipo]+'"/></g></svg>'; }
const ICONO_PUNTO = (tipo, color, fondo) => 'image://data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svgPunto(tipo, color, fondo));
const NOMBRE_PUNTO = {ing:'Puntos de internación', rep:'Puntos de repatriación', em:'Estaciones migratorias'};
const CAJA = [[-125,35.5],[-62,2.5]];                   // encuadre inicial: México, Centroamérica, Caribe y norte de Sudamérica
const ESCALA_LAT = 0.92;                                // corrección de proporción a la latitud de México
// Mapa del mundo con América al centro: Asia y Oceanía a la izquierda, Europa y África a la derecha.
// Todo lo que está al este del meridiano CORTE se dibuja también 360° a la izquierda.
const CORTE = 62;
const CAJA_MUNDO = [[CORTE-358,80],[CORTE-2,-56]];      // el mundo completo, sin la Antártida
const VISTA_MX = {c:[-93.5,19], z:1};                    // z = 1 es el encuadre de México; los demás zooms se miden contra él
const REGIONES = { NA:['Norteamérica',[-100,45]], CA:['Centroamérica y Caribe',[-80,15]], SA:['Sudamérica',[-60,-18]],
                   EU:['Europa',[15,50]], AF:['África',[18,2]], AS:['Asia',[95-360,30]], OC:['Oceanía',[140-360,-25]] };
const VEL = 5;                                         // días por segundo al reproducir (mínimo)
const velocidad = () => Math.max(VEL, ND/30);         // un periodo largo se recorre en unos 30 segundos
// Colores del mapa por tema (independientes del tema de la página)
const TACTIL = matchMedia('(hover: none)').matches;   // pantallas táctiles: el primer toque muestra la tarjeta
const TM = {
  oscuro:{ mar:'#22201D', tierra:'#34312D', linea:'#4B4741', eu:'#3A3733', euL:'#5A554E', mx:'#47433D', mxL:'#9A958A', tinta:'#F1EEE4', halo:'#22201D',
           reg:'#62B8A0', irr:'#E8827A', usa:'#DCC66C', arena:'#D8CDA0', relleno:'#8C7F4B', region:'#45402F', neu:['#4A463F','#5E5950','#746E62','#8B8475'],
           r_reg:['#2F4741','#3F6B60','#4F8F7F','#62B8A0','#A4E6D3'], r_irr:['#4A3A38','#7A4C48','#A85F59','#D6756D','#FFB0A8'], r_usa:['#4A4530','#7A6F3A','#A89845','#DCC66C','#F7E7A4'] },
  claro:{  mar:'#E4E1D5', tierra:'#F7F5EE', linea:'#CFCBBB', eu:'#F1EEE4', euL:'#B9B4A6', mx:'#FBFAF6', mxL:'#8A8579', tinta:'#2B2926', halo:'#F7F5EE',
           reg:'#2F6657', irr:'#C4605A', usa:'#8F7F2E', arena:'#A1925A', relleno:'#D9CB93', region:'#EFE8CC', neu:['#EEE9D6','#DDD5B8','#CABF98','#B3A77A'],
           r_reg:['#E3ECE8','#AFC9C1','#7AA598','#2F6657','#17382F'], r_irr:['#F6E6E3','#E5B9B3','#D38E86','#C4605A','#7E302B'], r_usa:['#F1EBD0','#DDD09A','#C2B15E','#8F7F2E','#55490F'] }
};

// Cuadrícula («cuadritos») de todas las gráficas: líneas alineadas a los ejes, nunca un fondo aparte que se encime.
// Eje de valores: línea principal y una secundaria más tenue entre cada par; eje de categorías: una línea por categoría.
window.IANAMI_CUAD = op => { if (!op || op.geo || [].concat(op.series || []).some(s => s && /^(pie|heatmap|sankey|graph|map|lines)$/.test(s.type))) return op;
  const fija = (a, cat) => [].concat(a || []).forEach(x => { if (!x || x.show===false) return; const sl = x.splitLine || {};
    if (sl.show===false) return;
    if (x.type==='category'){ const n = (x.data || []).length; x.splitLine = Object.assign({ show:true }, sl, { interval:n && n<=60 ? 0 : 'auto', lineStyle:Object.assign({}, sl.lineStyle, { color:'#ECE9DF' }) }); return; }
    x.splitLine = Object.assign({}, sl, { show:true, lineStyle:Object.assign({}, sl.lineStyle, { color:'#E3DFD3' }) });
    if (x.type!=='log'){ x.minorTick = Object.assign({ show:false, splitNumber:2 }, x.minorTick); x.minorSplitLine = Object.assign({ show:true, lineStyle:{ color:'#F2F0E9' } }, x.minorSplitLine); } });
  const esCat = a => [].concat(a || []).some(x => x && x.type==='category');
  if (esCat(op.xAxis) && esCat(op.yAxis)) return op;          // matrices (cruces): sin cuadrícula
  if (op.tooltip && op.tooltip.confine===undefined) op.tooltip.confine = true;   // el recuadro flotante se queda dentro de la gráfica: no se corta ni deja espacio extra en la página
  fija(op.xAxis); fija(op.yAxis); return op; };

// Barras al 100% «¿Qué documento obtiene cada nacionalidad?»: el mismo componente para todas las gráficas de ese tipo.
// Pasar el cursor (o tocar) un color lo resalta en todas las barras y muestra su % y lugar en cada renglón; la leyenda ordena.
window.IANAMI_MEZCLA = function(el, c){ if (!el) return;
  const e = s => String(s).replace(/[&<>"]/g, x => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[x]));
  const claro = h => { const m = /^#?([\da-f]{2})([\da-f]{2})([\da-f]{2})$/i.exec(h || ''); if (!m) return false; const [r,g,b] = m.slice(1).map(x => parseInt(x,16)); return .299*r+.587*g+.114*b > 175; };
  const C = c.cats, num = n => Math.round(n).toLocaleString('en-US'), corto = n => n>=1e6 ? (n/1e6).toFixed(2)+' M' : n>=1e4 ? (n/1e3).toFixed(1)+' mil' : num(n);
  let F = c.filas.filter(f => f.tot>0);
  if (c.orden!=null) F = F.slice().sort((a,b) => b.v[c.orden]/b.tot - a.v[c.orden]/a.tot);
  const mayor = f => f.v.reduce((m,x,i) => x>f.v[m] ? i : m, 0);
  const tc = k => claro(C[k].col) ? '#7A766C' : C[k].col;
  const dTxt = (f, k) => '<b class="num" style="color:'+tc(k)+'">'+(f.v[k]/f.tot*100).toFixed(1)+'%</b> '+e(C[k].nom);
  el.className = 'rg-mz mz-g';
  el.innerHTML = F.map(f => { const k0 = c.orden!=null ? c.orden : c.base!=null ? c.base : mayor(f);
      return '<div class="rg-mz-r'+(c.sel!=null && c.sel===f.k ? ' sel' : '')+'" data-mzk="'+f.k+'"><span title="'+e(f.nom)+'">'+e(f.nom)+'</span><span class="rg-mz-b">'+C.map((cat,i) => { const v = f.v[i], p = v/f.tot*100;
        return v ? '<i data-c="'+i+'" data-p="'+p.toFixed(1)+'" style="flex:'+v+' 1 0;background:'+cat.col+';color:'+(claro(cat.col) ? '#2B2926' : '#fff')+(c.orden!=null && c.orden!==i ? ';opacity:.3' : '')+'" title="'+e(cat.nom)+': '+num(v)+' · '+p.toFixed(1)+'%">'+(p>=12 ? Math.round(p)+'%' : '')+'</i>' : ''; }).join('')+
        '</span><span class="rg-mz-d" data-base="'+e(dTxt(f, k0))+'">'+dTxt(f, k0)+'</span><span class="x num">'+corto(f.tot)+'</span></div>'; }).join('')+
    '<div class="rg-ley rg-mz-l"><span>Ordenar por:</span>'+C.map((cat,i) => '<button data-mzo="'+i+'" class="'+(c.orden===i ? 'on' : '')+'"><i style="background:'+cat.col+'"></i>'+e(cat.nom)+'</button>').join('')+'</div>';
  let foco = null;
  const enfoca = k => { if (k===foco) return; foco = k; el.classList.toggle('foco', k!=null);
    const ps = k==null ? [] : [...el.querySelectorAll('.rg-mz-b i[data-c="'+k+'"]')].map(i => +i.dataset.p);
    el.querySelectorAll('.rg-mz-r').forEach(r => { r.querySelectorAll('.rg-mz-b i').forEach(i => i.classList.toggle('f', k!=null && +i.dataset.c===k));
      const d = r.querySelector('.rg-mz-d'), s = k!=null ? r.querySelector('.rg-mz-b i[data-c="'+k+'"]') : null, lug = s ? 1+ps.filter(p => p > +s.dataset.p).length : 0;
      d.innerHTML = k==null ? d.dataset.base : '<b class="num" style="color:'+tc(k)+'">'+(s ? s.dataset.p : '0.0')+'%</b> '+e(C[k].nom)+(lug ? ' <small>· '+lug+'.º de '+ps.length+'</small>' : ''); }); };
  el.onmouseover = ev => { const t = ev.target.closest('.rg-mz-b i[data-c], [data-mzo]'); enfoca(t ? +(t.dataset.c!=null ? t.dataset.c : t.dataset.mzo) : null); };
  el.onmouseleave = () => enfoca(null);
  el.onclick = ev => { const o = ev.target.closest('[data-mzo]'); if (o){ c.onOrden && c.onOrden(c.orden===+o.dataset.mzo ? null : +o.dataset.mzo); return; }
    const r = ev.target.closest('[data-mzk]'); if (r && c.onFila) c.onFila(isNaN(+r.dataset.mzk) ? r.dataset.mzk : +r.dataset.mzk); };
};

/* ==== [2] DATOS (cubo y consultas) ================================= */
// Cubo denso por indicador [semana][estado][nacionalidad] y sus dos resúmenes
// Cubo semanal de todas las fechas (…0); CUBO, WS y WN son la vista del periodo elegido
const CUBO0 = {}, WS0 = {}, WN0 = {}, CUBO = {}, WS = {}, WN = {};
INDS.forEach(m => { const a = new Float32Array(NW*NS*NN), ws = new Float64Array(NW*NS), wn = new Float64Array(NW*NN), c = D.cube[m.k];
  for (let i=0;i<c.length;i+=4){ a[(c[i]*NS + c[i+1])*NN + c[i+2]] += c[i+3]; ws[c[i]*NS+c[i+1]] += c[i+3]; wn[c[i]*NN+c[i+2]] += c[i+3]; }
  CUBO0[m.k] = a; WS0[m.k] = ws; WN0[m.k] = wn; });
const NCAT = {ing_via:3, rech_det:2, tram_se:16, tram_res:3, tram_exp:2, tram_plz:2, tram_tipo:(D.tramTipos||[]).length, resc_rei:2, resc_des:3, pres_est:D.estaciones.length, can_nna:12, can_ad:2, ret_tipo:2, recib_edad:2, rep_comp:8};
const COMP = {};                                  // desgloses del periodo (llegan por mes: [mes, estado, nacionalidad, categoría, valor])
// Parte de un mes de las bases que cae dentro del periodo elegido (0 a 1)
// Con el play en pantalla completa, los desgloses siguen al día del cursor: cada mes se prorratea dentro de [a, b)
function fraccionRango(m, a, b){
  const x = new Date(INICIO0.getFullYear(), INICIO0.getMonth()+m, 1), y = new Date(INICIO0.getFullYear(), INICIO0.getMonth()+m+1, 1);
  const s = Math.max(0, Math.round((x-INICIO0)/864e5)), e = Math.min(D0.dias, Math.round((y-INICIO0)/864e5)), o = Math.min(e,b) - Math.max(s,a);
  return e>s && o>0 ? o/(e-s) : 0;
}
function compHasta(k, ss, n, hasta){
  const nc = NCAT[k], c = D.comp[k], o = new Array(nc).fill(0), sset = ss ? new Set(ss) : null, fr = {};
  for (let i=0; i<c.length; i+=5){ if (sset && !sset.has(c[i+1])) continue; if (n!=null && c[i+2]!==n) continue;
    let f = fr[c[i]]; if (f==null) f = fr[c[i]] = fraccionRango(c[i], P0, hasta); if (f) o[c[i+3]] += c[i+4]*f; }
  return o;
}
function fraccionMes(m){
  const a = new Date(INICIO0.getFullYear(), INICIO0.getMonth()+m, 1), b = new Date(INICIO0.getFullYear(), INICIO0.getMonth()+m+1, 1);
  const s = Math.max(0, Math.round((a-INICIO0)/864e5)), e = Math.min(D0.dias, Math.round((b-INICIO0)/864e5)), o = Math.min(e,P1) - Math.max(s,P0);
  return e>s && o>0 ? o/(e-s) : 0;
}
// Arma todas las series para el periodo [p0, p1) de los datos completos. Las semanas que el periodo corta se prorratean.
function aplicarPeriodo(p0, p1){
  P0 = p0; P1 = p1; ND = p1-p0; INICIO = new Date(INICIO0.getFullYear(), INICIO0.getMonth(), INICIO0.getDate()+p0);
  const sem = [], E0 = D0.ends;
  for (let w=0; w<E0.length; w++){ const a = w ? E0[w-1] : 0, b = E0[w], x = Math.max(a,p0), y = Math.min(b,p1); if (y>x) sem.push([w, (y-x)/(b-a), y-p0]); }
  NW = sem.length; D.ends = sem.map(x => x[2]);
  INDS.forEach(m => { const A = CUBO0[m.k], B = WS0[m.k], C = WN0[m.k], a = new Float32Array(NW*NS*NN), ws = new Float64Array(NW*NS), wn = new Float64Array(NW*NN), L = NS*NN;
    sem.forEach((x,j) => { const w = x[0], f = x[1];
      for (let i=0;i<L;i++) a[j*L+i] = A[w*L+i]*f;
      for (let i=0;i<NS;i++) ws[j*NS+i] = B[w*NS+i]*f;
      for (let i=0;i<NN;i++) wn[j*NN+i] = C[w*NN+i]*f; });
    CUBO[m.k] = a; WS[m.k] = ws; WN[m.k] = wn;
    D.daily[m.k] = D0.daily[m.k].slice(p0,p1); D.ds[m.k] = D0.ds[m.k].subarray(p0*NS, p1*NS); D.dn[m.k] = D0.dn[m.k].subarray(p0*NN, p1*NN); });
  D0.wks.forEach(o => { o.obj.wk = sem.map(x => o.wk[x[0]]*x[1]); });
  Object.keys(NCAT).forEach(k => { const nc = NCAT[k], a = new Float64Array(NS*NN*nc), c = D.comp[k];
    for (let i=0;i<c.length;i+=5){ const f = fraccionMes(c[i]); if (f) a[(c[i+1]*NN + c[i+2])*nc + c[i+3]] += c[i+4]*f; } COMP[k] = a; });
  calendario();
}
const TODOS = EST.map((e,i)=>i);

// ss = lista de estados (o null = todos); n = nacionalidad (o null = todas)
function sumaSem(k, w0, w1, ss, n){
  if (conEdo(ss) && sinEdo(k)) return 0;                  // encuentros: no hay estado de México
  if (Array.isArray(n)){ let t = 0; for (let i=0;i<n.length;i++) t += sumaSem(k,w0,w1,ss,n[i]); return t; }
  let t = 0;
  if (n==null){ const a = WS[k], l = ss || TODOS; for (let w=w0;w<=w1;w++) for (let j=0;j<l.length;j++) t += a[w*NS+l[j]]; return t; }
  if (!ss){ const a = WN[k]; for (let w=w0;w<=w1;w++) t += a[w*NN+n]; return t; }
  const a = CUBO[k]; for (let w=w0;w<=w1;w++) for (let j=0;j<ss.length;j++) t += a[(w*NS+ss[j])*NN+n];
  return t;
}
function semanal(k, ss, n){ const o = []; for (let w=0;w<NW;w++) o.push(sumaSem(k,w,w,ss,n)); return o; }
function diario(k, F){                         // serie diaria con el filtro activo (lleva k y F para comparar con el año anterior)
  const o = new Array(ND).fill(0), n = 'nd' in F ? F.nd : F.n; o.k = k; o.F = F;
  if (conEdo(F.ss) && sinEdo(k)) return o;
  if (F.ss && n!=null){                          // estado × nacionalidad solo existe por semana: se reparte en sus días
    for (let w=0;w<NW;w++){ const i0 = w ? D.ends[w-1] : 0, i1 = D.ends[w], v = sumaSem(k,w,w,F.ss,n)/(i1-i0); for (let d=i0;d<i1;d++) o[d] = v; }
    return o; }
  if (Array.isArray(n)){ const a = D.dn[k]; for (let d=0;d<ND;d++) for (let j=0;j<n.length;j++) o[d] += a[d*NN+n[j]]; return o; }
  if (F.ss){ const a = D.ds[k]; for (let d=0;d<ND;d++) for (let j=0;j<F.ss.length;j++) o[d] += a[d*NS+F.ss[j]]; return o; }
  if (n!=null){ const a = D.dn[k]; for (let d=0;d<ND;d++) o[d] = a[d*NN+n]; return o; }
  const t = D.daily[k].slice(); t.k = k; t.F = F; return t;
}
function comp(k, ss, n){
  if (Array.isArray(n)){ const o = new Array(NCAT[k]).fill(0); n.forEach(x => comp(k,ss,x).forEach((v,i) => o[i] += v)); return o; }
  if (SALA.on && S.dia<ND && D.comp[k]) return compHasta(k, ss, n, P0+Math.max(0, S.dia));   // pantalla completa con play: hasta el día del cursor
  const nc = NCAT[k], a = COMP[k], o = new Array(nc).fill(0), l = ss || TODOS, n0 = n==null?0:n, n1 = n==null?NN-1:n;
  for (let j=0;j<l.length;j++) for (let ni=n0; ni<=n1; ni++){ const b = (l[j]*NN+ni)*nc; for (let c=0;c<nc;c++) o[c] += a[b+c]; }
  return o; }
// Rechazo con la misma definición que Control migratorio: rechazos ÷ (extranjeros que llegan por aire y tierra + rechazos).
// Sin mexicanos ni marítima (tripulación de cruceros). Devuelve [rechazos, llegadas].
function rechazoExt(ss, n){
  let l = n==null ? null : (Array.isArray(n) ? n : [n]);
  if (l) { l = l.filter(x => x!==MX); if (!l.length) return [0,0]; }
  const v = comp('ing_via',ss,l), re = sumaSem('rech',0,NW-1,ss,l);
  let ing = v[0]+v[1], r = re;
  if (!l){ const m = comp('ing_via',ss,MX); ing -= m[0]+m[1]; r -= sumaSem('rech',0,NW-1,ss,MX); }
  return [r, ing + r];
}
// Posición del cursor en semanas y valores "al momento" (ritmo semanal interpolado) y acumulados
function ritmo(k, ss, n){
  if (alFinal()) return sumaSem(k,0,NW-1,ss,n);
  const u = Math.max(0, Math.min(NW-1, (S.dia-3.5)/7)), i = Math.floor(u), f = u-i, a = sumaSem(k,i,i,ss,n), b = i<NW-1 ? sumaSem(k,i+1,i+1,ss,n) : a;
  return a + (b-a)*f;
}
function acum(k, ss, n){
  if (conEdo(ss) && sinEdo(k)) return 0;
  if (Array.isArray(n)){ let t = 0; for (let i=0;i<n.length;i++) t += acum(k,ss,n[i]); return t; }
  let t = 0;
  if (n==null){ if (!ss) return suma(D.daily[k],0,S.dia); const a = D.ds[k]; for (let d=0;d<S.dia;d++) for (let j=0;j<ss.length;j++) t += a[d*NS+ss[j]]; return t; }
  if (!ss){ const a = D.dn[k]; for (let d=0;d<S.dia;d++) t += a[d*NN+n]; return t; }
  // estado × nacionalidad solo existe por semana: se reparte dentro de la semana
  for (let w=0;w<NW;w++){ const ini = w?D.ends[w-1]:0, fin = D.ends[w];
    if (S.dia>=fin) t += sumaSem(k,w,w,ss,n); else { if (S.dia>ini) t += sumaSem(k,w,w,ss,n)*(S.dia-ini)/(fin-ini); break; } }
  return t;
}
// ---- Encuentros de la CBP por sector de la frontera (EE. UU.). a, b: días de las bases (como rangoBase); n: nacionalidad, lista o null.
// Cada sector: total, mexicanos, por agencia [USBP, OFO, CBP ONE], por nacionalidad extranjera y por semana del periodo.
const CBPT = D.cbpT && D.cbp ? D.cbpT : null, SECI = CBPT ? CBPT.sec.map(x => D.cbp.sectores.findIndex(P => P.n===x)) : [], AGI = CBPT ? CBPT.ag.map(x => ['USBP','OFO','CBP ONE'].indexOf(x)) : [];
function sinEdo(k){ return !!(IND[k] && IND[k].sinEdo); }
function conEdo(ss){ return !!ss && ss.length<NS; }
function cbpSec(a, b, n){ const o = (D.cbp ? D.cbp.sectores : []).map(() => ({ v:0, mx:0, ag:[0,0,0], nat:{}, wk:new Array(NW).fill(0) })); if (!CBPT) return o;
  const ns = n==null ? null : new Set(Array.isArray(n) ? n : [n]), T = CBPT;
  for (let i=0; i<T.d.length; i++){ const d = T.d[i]; if (d<a || d>=b) continue; const nn = T.n[i]; if (ns && !ns.has(nn)) continue; const j = SECI[T.s[i]]; if (j<0) continue;
    const x = o[j], v = T.v[i]; x.v += v; if (nn===MX) x.mx += v; else x.nat[nn] = (x.nat[nn] || 0) + v; if (AGI[T.a[i]]>=0) x.ag[AGI[T.a[i]]] += v; x.wk[semDe(d-P0+1)] += v; }
  return o; }
const cbpAhora = F => cbpSec(P0, P0+S.dia, F.nd);
function topNats(fn, cuantas){ const o = []; for (let n=0;n<OT;n++){ const v = fn(n); if (v>0) o.push([n,v]); } return o.sort((a,b)=>b[1]-a[1]).slice(0,cuantas); }
function topEsts(fn, cuantos){ const o = []; for (let s=0;s<NS;s++){ const v = fn(s); if (v>0) o.push([s,v]); } return o.sort((a,b)=>b[1]-a[1]).slice(0,cuantos); }
function xyNat(n){ const iso = D.nats[n][1], c = ORIGEN[iso] || CEN['P_'+String(iso).padStart(3,'0')];
  return !c ? null : c[0] > CORTE ? [c[0]-360, c[1]] : c; }
const enRegion = n => !S.region || D.nats[n][2]===S.region;
const LISTA_REG = {}; Object.keys(REGIONES).forEach(r => { LISTA_REG[r] = []; for (let n=0;n<OT;n++) if (D.nats[n][2]===r) LISTA_REG[r].push(n); });
function xyEst(s){ return CEN[ECLAVE[s]]; }
function xyGrupo(ss){ let x = 0, y = 0; ss.forEach(s => { const c = xyEst(s); x += c[0]; y += c[1]; }); return [x/ss.length, y/ss.length]; }

/* ==== [3] UTILIDADES ============================================== */
const $ = id => document.getElementById(id);
const suma = (a,i,j) => { let t=0; for (let x=Math.max(0,i);x<j;x++) t+=a[x]; return t; };
const miles = n => Math.round(n).toLocaleString('en-US');
const corto = n => n>=1e6 ? (n/1e6).toFixed(2)+' M' : miles(n);
const pct = (a,b) => b ? Math.round(a/b*100) : 0;
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const sinAcento = s => s.normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase();
const diaDe = i => new Date(INICIO.getFullYear(), INICIO.getMonth(), INICIO.getDate()+i);
const indiceDe = iso => Math.round((new Date(iso+'T00:00:00') - INICIO)/864e5);
let VARIOS_ANIOS = false, MESES_INI = [];
function fechaDia(i){ const f = diaDe(i); return f.getDate()+' '+MES12[f.getMonth()]+(VARIOS_ANIOS ? ' '+String(f.getFullYear()).slice(2) : ''); }
function fechaLarga(i){ const f = diaDe(i); return f.getDate()+' '+MES12[f.getMonth()]+' '+f.getFullYear(); }
function fechaISO(iso){ const f = new Date(iso+'T00:00:00'); return f.getDate()+' '+MES12[f.getMonth()]+' '+f.getFullYear(); }
function calendario(){                          // etiquetas de meses de la barra de tiempo
  VARIOS_ANIOS = diaDe(0).getFullYear() !== diaDe(ND-1).getFullYear(); MESES_INI = [];
  for (let i=0;i<ND;i++){ const f = diaDe(i); if (!i || f.getDate()===1) MESES_INI.push([i, MES12[f.getMonth()]+((!i || !f.getMonth()) ? ' '+f.getFullYear() : '')]); }
}
const idxBase = iso => Math.round((new Date(iso+'T00:00:00') - INICIO0)/864e5);   // día dentro de las bases completas
const fechaBase = i => new Date(INICIO0.getFullYear(), INICIO0.getMonth(), INICIO0.getDate()+i);
const isoDe = f => f.getFullYear()+'-'+String(f.getMonth()+1).padStart(2,'0')+'-'+String(f.getDate()).padStart(2,'0');
// Rango del periodo elegido dentro de las bases: [inicio, fin) o null si no hay datos
function rangoPeriodo(per){
  per = per || S.per; let a = 0, b = D0.dias;
  if (per==='shein') a = idxBase('2024-10-01');
  else if (per==='trump') a = idxBase('2025-01-20');
  else if (per==='anio'){ const y = S.anio, m = S.mes; a = idxBase(isoDe(new Date(y, m ? m-1 : 0, 1))); b = idxBase(isoDe(new Date(m ? y : y+1, m ? m : 0, 1))); }
  else if (per==='pers'){ a = idxBase(S.desde); b = idxBase(S.hasta)+1; }
  a = Math.max(0, a); b = Math.min(D0.dias, b); return b>a ? [a,b] : null;
}
function cambiarPeriodo(){
  const r = rangoPeriodo(); if (!r) return;
  if (S.play) S.play = false;
  aplicarPeriodo(r[0], r[1]); S.dia = ND; S.t = ND; validarCmp();
  $('tgraf').setAttribute('aria-valuemax', ND); pintarTodo();
}
const mesAnio = f => MES12[+f.slice(5,7)-1]+' '+f.slice(0,4);
// Ayuda (i): el texto va en el propio botón; se asoma con el cursor y queda fija con un toque
const infoP = txt => '<button class="rg-i" data-itxt="'+esc(txt)+'" aria-label="Qué muestra esta sección">i</button>';
let ayudaFija = false;
function ayuda(b, fija){ let p = $('rg-pop'); if (!p){ p = document.createElement('div'); p.id = 'rg-pop'; p.className = 'rg-pop'; document.body.appendChild(p); }
  if (!b){ if (!ayudaFija || fija===null){ p.hidden = true; ayudaFija = false; } return; }
  ayudaFija = !!fija; p.innerHTML = (fija ? '<button class="rg-pop-x" data-tipayx aria-label="Cerrar">×</button>' : '')+b.dataset.itxt; p.hidden = false; p.classList.toggle('fija', ayudaFija);
  const r = b.getBoundingClientRect(), w = p.offsetWidth; p.style.left = Math.max(8, Math.min(r.left-12, window.innerWidth-w-8))+'px'; p.style.top = (r.bottom+8)+'px'; }
/* ==== COMPARTIR: PDF de lo que está en pantalla, para descargar o mandar por WhatsApp ==== */
const LIBS_PDF = ['lib/html2canvas.min.js', 'lib/jspdf.umd.min.js'];   // incluidas en el sitio (versiones 1.4.1 y 2.5.1)
window.IANAMI_LIBS_PDF = () => Promise.all(LIBS_PDF.map(u => cargarJS(u)));   // Analizar las usa para el PDF de las láminas
// Carga una librería del sitio; si no está, la toma de la red como respaldo
const RESPALDO = { 'lib/html2canvas.min.js':'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js', 'lib/jspdf.umd.min.js':'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js' };
const cargarJS = u => new Promise((ok, mal) => { if (document.querySelector('script[src="'+u+'"]')) return ok(); const s = document.createElement('script'); s.src = u; s.onload = ok;
  s.onerror = () => { s.remove(); if (!RESPALDO[u]) return mal(); const r = document.createElement('script'); r.src = RESPALDO[u]; r.onload = ok; r.onerror = mal; document.head.appendChild(r); }; document.head.appendChild(s); });
function tituloVista(){ if (SALA.on) return 'Infografía'+(nombreFiltro() ? ' · '+nombreFiltro() : ''); if (S.vista==='pulso') return 'Pulso'+(nombreFiltro() ? ' · '+nombreFiltro() : '');
  const h = document.querySelector('#vista-otra h1'), t = document.querySelector('.rg-vistas .on'); return (h ? h.textContent.replace('Pantalla completa','').replace('Infografía','').trim() : 'IA-NAMI')+(t ? ' · '+t.textContent : ''); }
// html2canvas no entiende colores modernos (color-mix, color(srgb …)): en la copia que se dibuja se cambian por rgb
const COLOR_PROPS = ['color','backgroundColor','borderTopColor','borderRightColor','borderBottomColor','borderLeftColor','outlineColor','textDecorationColor','fill','stroke','boxShadow','backgroundImage'];
let cvColor = null;
function aRGB(v){ if (!cvColor){ cvColor = document.createElement('canvas').getContext('2d', { willReadFrequently:true }); cvColor.canvas.width = cvColor.canvas.height = 1; }
  cvColor.clearRect(0,0,1,1); cvColor.fillStyle = '#000'; cvColor.fillStyle = v; cvColor.fillRect(0,0,1,1); const d = cvColor.getImageData(0,0,1,1).data; return 'rgba('+d[0]+','+d[1]+','+d[2]+','+(d[3]/255).toFixed(3)+')'; }
function colorFijo(doc){ const win = doc.defaultView || window;
  doc.querySelectorAll('*').forEach(el => { const cs = win.getComputedStyle(el);
    COLOR_PROPS.forEach(k => { const v = cs[k]; if (!v || (v.indexOf('color(')<0 && v.indexOf('color-mix(')<0 && v.indexOf('oklch(')<0 && v.indexOf('lab(')<0)) return;
      if (k==='backgroundImage' || k==='boxShadow') el.style[k] = 'none'; else el.style[k] = aRGB(v); }); }); }
window.IANAMI_COLORFIJO = colorFijo;
async function hacerPDF(){
  await Promise.all(LIBS_PDF.map(cargarJS));
  const zona = SALA.on ? $('mapa') : S.vista==='pulso' ? $('vista-pulso') : $('vista-otra'), tit = 'IA-NAMI · '+tituloVista()+' · '+(S.vista==='pulso' ? ($('rango') ? $('rango').textContent : '') : ((document.querySelector('#vista-otra .rango b') || {}).textContent || ''));
  const lienzo = await html2canvas(zona, { scale:1.6, backgroundColor:'#F4F2EA', useCORS:true, ignoreElements:el => el.id==='rg-pop' || el.id==='kpi-tip' || (el.classList && el.classList.contains('res')),
    onclone:doc => { const st = doc.createElement('style'); st.textContent = '*,*::before,*::after{animation:none!important;transition:none!important} .sl-e{opacity:1!important;transform:none!important} #sl-cm,#aviso-breve{display:none!important}'; doc.head.appendChild(st); colorFijo(doc); } });
  const { jsPDF } = window.jspdf, pdf = new jsPDF({ orientation:'landscape', unit:'pt', format:'a4' }), W = pdf.internal.pageSize.getWidth(), H = pdf.internal.pageSize.getHeight(), m = 22;
  const esc2 = (W-2*m)/lienzo.width, alto = Math.floor((H-2*m-14)/esc2);
  for (let y=0, p=0; y<lienzo.height; y+=alto, p++){
    if (p) pdf.addPage(); const h = Math.min(alto, lienzo.height-y), c = document.createElement('canvas'); c.width = lienzo.width; c.height = h;
    c.getContext('2d').drawImage(lienzo, 0, y, lienzo.width, h, 0, 0, lienzo.width, h);
    pdf.setFontSize(9); pdf.setTextColor(92, 89, 82); pdf.text(tit, m, m); pdf.text('Hoja '+(p+1), W-m, m, { align:'right' });
    pdf.addImage(c.toDataURL('image/jpeg', .9), 'JPEG', m, m+8, W-2*m, h*esc2);
  }
  return { pdf:pdf, nombre:('IA-NAMI_'+tituloVista()).normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^\w]+/g,'_').replace(/_+$/,'')+'_'+(() => { const d = new Date(); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); })()+'.pdf', tit:tit };
}
// WhatsApp: el celular y la tableta solo abren su menú de compartir en el instante del toque, y la computadora bloquea ventanas
// que no salen del clic. Por eso: en computadora WhatsApp Web se abre en el clic y el PDF se descarga al estar listo;
// en celular y tableta el PDF se prepara y un segundo toque («Compartir PDF») abre el menú del teléfono con el archivo.
const TACTIL_COMP = () => matchMedia('(pointer:coarse)').matches && !!(navigator.canShare && navigator.share);
let PDF_LISTO = null;
async function compartir(modo){
  const b = $('b-comp'), txt = b.innerHTML, menu = modo==='wa' && TACTIL_COMP(); $('menu-comp').hidden = true;
  if (modo==='wa' && !menu) window.open('https://wa.me/?text='+encodeURIComponent('IA-NAMI · '+tituloVista()+' — te comparto el PDF (adjúntalo desde tus descargas).'), '_blank', 'noopener');
  b.disabled = true; b.textContent = 'Generando PDF…';
  try {
    const r = await hacerPDF();
    if (menu){ PDF_LISTO = { f:new File([r.pdf.output('blob')], r.nombre, { type:'application/pdf' }), tit:r.tit };
      const m = $('menu-comp'); m.innerHTML = '<button data-comp="enviar"><b>Compartir PDF</b><span>toca para elegir WhatsApp u otra app</span></button>'; m.hidden = false; }
    else { r.pdf.save(r.nombre); if (modo==='wa') alertaComp('PDF descargado: adjúntalo en el chat de WhatsApp que se abrió.'); }
  } catch (e){ alertaComp('No se pudo generar el PDF. Intenta de nuevo.'); }
  b.disabled = false; b.innerHTML = txt;
}
function enviarPDF(){ const x = PDF_LISTO; $('menu-comp').hidden = true; if (!x) return;
  if (!navigator.canShare({ files:[x.f] })){ const u = URL.createObjectURL(x.f), a = document.createElement('a'); a.href = u; a.download = x.f.name; a.click(); setTimeout(() => URL.revokeObjectURL(u), 2000); return; }
  navigator.share({ files:[x.f], title:x.tit }).catch(e => { if (!e || e.name!=='AbortError') alertaComp('No se pudo abrir el menú de compartir.'); }); }
function alertaComp(m){ const a = $('menu-comp'); a.innerHTML = '<p class="mini" style="padding:8px 10px;margin:0">'+esc(m)+'</p>'; a.hidden = false; setTimeout(() => { a.hidden = true; menuComp(false); }, 3500); }
// Liga de la vista actual: sección, periodo, comparación, indicador, lugar, región e infografía. Corta y legible.
function ligaVista(){ const p = new URLSearchParams(), v = S.vista;
  if (v==='dir'){ p.set('ver', 'proceso'); p.set('n', S.dir || 0); }
  else if (v!=='pulso') p.set('ver', v);
  else { if (SALA.on) p.set('ver', 'infografia');
    p.set('per', S.per); if (S.per==='anio'){ p.set('a', S.anio); if (S.mes) p.set('m', S.mes); } if (S.per==='pers'){ p.set('de', S.desde); p.set('a', S.hasta); }
    if (!cmpFijo()) p.set('cmp', S.cmp); if (S.ind) p.set('i', S.ind); if (S.sel && (S.sel.t==='n' || S.sel.t==='e')) p.set('l', S.sel.t+S.sel.i); if (S.region) p.set('r', S.region); }
  return location.origin+location.pathname+'?'+p.toString(); }
function copiarLiga(){ menuComp(false); const u = ligaVista(), ok = () => avisoBreve(SALA.on ? 'Liga copiada: abre esta misma infografía' : 'Liga copiada: abre esta misma vista'), mal = () => window.prompt('Copia la liga de esta vista:', u);
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(u).then(ok, mal); else mal(); }
function avisoBreve(t){ let e = $('aviso-breve'); if (!e){ e = document.createElement('div'); e.id = 'aviso-breve'; e.className = 'aviso-breve'; }
  const cont = SALA.on ? $('mapa') : document.body; if (e.parentNode!==cont) cont.appendChild(e);   // en la infografía (pantalla completa) el aviso va dentro de ella para que se vea
  e.textContent = t; e.classList.add('on'); clearTimeout(avisoBreve.t); avisoBreve.t = setTimeout(() => e.classList.remove('on'), 2400); }
// Al abrir una liga de vista: se restaura lo mismo que veía quien la compartió
function abrirLigaVista(){ const p = new URLSearchParams(location.search), v = p.get('ver'); if (!v && !p.get('per')) return false; if (v && !/^(proceso|infografia|pulso|bases|arma|analizar)$/.test(v)) return false;
  if (v==='proceso'){ S.dir = Math.max(0, Math.min(DIRS.length-1, +p.get('n') || 0)); irA('dir'); return true; }
  if (v && v!=='infografia' && v!=='pulso'){ irA(v); return true; }
  const per = p.get('per'); if (per && /^(shein|trump|anio|pers)$/.test(per)){ S.per = per; if (per==='anio'){ S.anio = +p.get('a') || S.anio; S.mes = +p.get('m') || 0; } if (per==='pers' && p.get('de') && p.get('a')){ S.desde = p.get('de'); S.hasta = p.get('a'); } }
  const c = p.get('cmp'); if (c) S.cmp = c==='sem' ? 'sem' : +c; const i = p.get('i'); S.ind = i && IND[i] ? i : null; if (p.get('r')) S.region = p.get('r');
  irA('pulso'); cambiarPeriodo(); const l = p.get('l'); if (l && /^[ne]\d+$/.test(l)) fijarSel({ t:l[0], i:+l.slice(1) }, true);
  if (v==='infografia') setTimeout(() => { SALA.compartida = true; document.body.classList.add('sala-compartida'); abrirSala(); const b = i && document.querySelector('#sl-im [data-ind="'+i+'"]'); if (b) b.click();
    setTimeout(() => document.documentElement.classList.remove('vz-arranque'), 250);
    const fs = () => { if (SALA.on && !document.fullscreenElement && $('mapa').requestFullscreen) $('mapa').requestFullscreen().catch(() => {}); }; addEventListener('click', fs, true); }, 300);   // la infografía entra limpia: se elige su indicador
  return true; }
function menuComp(abrir){ const m = $('menu-comp'); if (!m) return; if (!abrir){ m.hidden = true; return; }
  m.innerHTML = '<button data-comp="liga"><b>Copiar liga</b><span>abre esta misma vista: periodo, indicador y lugar</span></button><button data-comp="pdf"><b>Descargar PDF</b><span>de lo que estás viendo</span></button><button data-comp="wa"><b>Enviar por WhatsApp</b><span>'+(TACTIL_COMP() ? 'se prepara el PDF y eliges el chat' : 'se abre WhatsApp Web y se descarga el PDF')+'</span></button>';
  m.hidden = false; }
const cssv = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const colG = g => cssv(g==='reg'?'--reg':g==='irr'?'--irr':'--usa');
const reducido = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
const hex = c => [parseInt(c.substr(1,2),16), parseInt(c.substr(3,2),16), parseInt(c.substr(5,2),16)];
function chispa(a, w, h, color, punto){        // mini-línea de tendencia
  const lo = Math.min.apply(null,a), hi = Math.max.apply(null,a), n = a.length;
  const X = i => 3 + i*(w-6)/(n-1), Y = v => hi>lo ? h-3-(v-lo)/(hi-lo)*(h-6) : h/2;
  const p = a.map((v,i)=>X(i).toFixed(1)+','+Y(v).toFixed(1)).join(' ');
  const i = punto==null ? n-1 : punto;
  return '<svg width="'+w+'" height="'+h+'" viewBox="0 0 '+w+' '+h+'" aria-hidden="true"><polyline points="'+p+'" fill="none" stroke="'+color+'" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/><circle cx="'+X(i).toFixed(1)+'" cy="'+Y(a[i]).toFixed(1)+'" r="2.8" fill="'+color+'"/></svg>';
}
function mezclaRGB(rampa, t){                  // color intermedio de una rampa, como [r,g,b]
  t = Math.max(0, Math.min(1, t)); const x = t*(rampa.length-1), i = Math.min(rampa.length-2, Math.floor(x)), f = x-i, a = hex(rampa[i]), b = hex(rampa[i+1]);
  return [a[0]+(b[0]-a[0])*f, a[1]+(b[1]-a[1])*f, a[2]+(b[2]-a[2])*f];
}
function tri(arriba, color){ return '<svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><path d="'+(arriba?'M6 2l5 8H1z':'M6 10L1 2h10z')+'" fill="'+color+'"/></svg>'; }

/* ==== [4] ESTADO Y FILTRO ========================================= */
const S = { vista:'pulso', ind:null, funcSel:{reg:null, irr:null}, funcSel:{reg:null, irr:null}, sel:null, dia:ND, t:ND, play:false, tema:'claro', flujos:true, circulos:true, puntos:false, cbp:false, car:false, carSel:null, modoVista:'mx', centro:VISTA_MX.c, region:null, agr:'e', cmp:30, per:'shein', anio:fechaBase(D.dias-1).getFullYear(), mes:0, desde:D.inicio, hasta:D.corte, cruce:{ing:0, resc:0, pres:0}, topModo:'resc', kpiModo:'tarjetas', zoom:VISTA_MX.z, estreno:true };
let E = 1;                                      // escala para pantallas muy grandes
// Filtro que produce la selección: una lista de estados (estado, cinturón o CECO) o una nacionalidad
// ss: estados; n: una nacionalidad; r: nacionalidades de la región elegida; nd: lo que usan los cálculos (n o r)
function filtro(){
  const s = S.sel, r = S.region && !(s && s.t==='n') ? LISTA_REG[S.region] : null;
  const F = {ss:null, n:null, r:r};
  if (s && s.t==='e') F.ss = [s.i];
  else if (s && s.t==='g') F.ss = miembros(s.a, s.q);
  else if (s && s.t==='n') F.n = s.i;
  else if (!s && S.agr!=='e'){ F.ss = TODOS_GRUPO[S.agr]; F.todo = true; }   // Cinturón o CECO: todos sus estados
  F.nd = F.n!=null ? F.n : r;
  return F;
}
const nombreRegion = () => S.region ? REGIONES[S.region][0] : '';
function nombreFiltro(){ return [S.sel ? nombreSel() : S.agr==='c' ? 'Cinturones de contención' : S.agr==='o' ? 'Todos los CECO' : '', S.sel && S.sel.t==='n' ? '' : nombreRegion()].filter(Boolean).join(' · '); }
const alFinal = () => S.dia>=ND && !S.play;
const semDe = d => { for (let w=0;w<NW;w++) if (d<=D.ends[w]) return w; return NW-1; };
const listaPuntos = tp => tp==='ing'?D.puntos:tp==='rep'?D.repPuntos:D.emPuntos;
function nombreSel(){ const s = S.sel; if (!s) return ''; return s.t==='n'?D.nats[s.i][0]:s.t==='e'?EST[s.i]:s.t==='g'?AGR[s.a].nombres[s.q]:listaPuntos(s.tipo)[s.i].n; }
let chart = null, AVISOS = [];

// En el Pulso un punto no se elige (las tarjetas de abajo son siempre del país, estado o nacionalidad): el clic lleva a su proceso,
// donde está su análisis completo. Punto de internación → Control › Ingresos con ese punto; estación → Control › Rescates (presentados);
// punto de repatriación → Protección al migrante con ese punto.
function irPunto(tp, i){ const P = listaPuntos(tp)[i]; if (!P || !window.IANAMI_NAV) return;
  if (tp==='ing') window.IANAMI_NAV.ir('control', { vista:'int', ptos:[P.n] });
  else if (tp==='em') window.IANAMI_NAV.ir('control', { vista:'est', em:'pre' });
  else window.IANAMI_NAV.ir('proteccion', { ptos:[P.n.replace(/\(vuelos\)$/, '(vuelos PRIM)')] }); }
function fijarInd(k){ S.ind = (S.ind===k ? null : k); pintarTodo(); if (S.ind) acercarSiMundo(); }   // segundo clic lo apaga
// desdeCard: el clic vino de una barra de las tarjetas de abajo: solo filtra, sin tarjetas nuevas ni vuelo del mapa
function fijarSel(sel, volar, desdeCard){ S.sel = sel; S.selCard = !!(sel && desdeCard); if (S.ind==='rep' && sel && sel.t==='n') S.ind = null; if (S.ind && sinEdo(S.ind) && sel && sel.t!=='n') S.ind = null;
  if (volar && sel) prepararVuelo();                 // se apagan líneas y círculos; reaparecen al llegar
  pintarTodo(); if (volar && sel) volarA(sel); }

/* ==== [5] ANÁLISIS AUTOMÁTICO ===================================== */
// Compara los últimos N días con datos contra los N anteriores (N = 7 o 30) con el filtro activo.
// Variación: últimos N días contra los N anteriores, o el periodo contra el mismo periodo del año anterior ('aa')
// Regla única: año, mes y personalizado se comparan solos contra su periodo equivalente (mismas fechas del año anterior;
// en personalizado sin año anterior, contra el tramo de igual duración justo antes). Sheinbaum y Trump muestran el total
// y una tendencia reciente que se elige: semana anterior, últimos 30 días o últimos 3 meses; el % siempre dice de qué es.
const cmpFijo = () => S.per==='anio' || S.per==='pers';
function refFija(){ const q0 = idxBase(isoDe(new Date(INICIO.getFullYear()-1, INICIO.getMonth(), INICIO.getDate())));
  if (q0>=0) return { t:'aa', q0:q0, txt:S.per==='anio' ? (S.mes ? MES12[S.mes-1]+' '+(S.anio-1) : String(S.anio-1)) : 'mismas fechas de '+(INICIO.getFullYear()-1) };
  if (S.per==='pers' && P0-ND>=0) return { t:'prev', q0:P0-ND, txt:'los '+ND+' días previos' }; return null; }
const NOM_CMP = { sem:'Última semana', 30:'Últimos 30 días', 90:'Últimos 3 meses' };
const sufCmp = () => cmpFijo() ? (refFija() ? 'vs. '+refFija().txt : 'sin comparación') : S.cmp==='sem' ? 'en la última semana' : S.cmp===90 ? 'en los últimos 3 meses' : 'en los últimos 30 días';
const cmpN = () => cmpFijo() ? 30 : S.cmp==='sem' ? 7 : S.cmp;               // ventana para los avisos
const etiquetaN = n => n==='sem' ? '7 días' : n===90 ? '3 meses' : n+' días';
// Semana anterior: la última semana completa (lunes a domingo) con datos contra la previa
function semanasCmp(U){ let b = U; while (b>0 && (diaDe(b-1).getDay()!==0)) b--; return b-14>=0 ? [b-7, b, b-14, b-7] : null; }
function textoCmp(){ if (cmpFijo()){ const r = refFija(); return r ? 'el periodo vs. '+r.txt : 'el periodo (sin periodo anterior con datos para comparar)'; }
  if (S.cmp==='sem'){ const w = semanasCmp(ND); return w ? 'semana del '+fechaDia(w[0])+' al '+fechaDia(w[1]-1)+' vs. la anterior' : 'semana anterior'; }
  return S.cmp==='aa' ? 'el periodo vs. el mismo periodo del año anterior' : 'últimos '+etiquetaN(S.cmp)+' vs. '+(S.cmp===90 ? 'los 3 meses' : 'los '+S.cmp+' días')+' anteriores'; }
function variacion(d){
  const U = d.k ? finDatos(d.k) : ND;            // los días pendientes no entran a la comparación
  if (cmpFijo()){ const r = refFija(); if (!r || !d.k) return {a:0, b:0, dl:0, ok:false}; const q0 = r.t==='prev' ? P0-U : r.q0, b = q0>=0 ? sumaCompleta(d.k, d.F, q0, q0+U) : null, a = suma(d,0,U);
    return {a:a, b:b||0, dl: b ? (a/b-1)*100 : 0, ok: b!=null && b>=30}; }
  if (S.cmp==='aa'){ const q0 = idxBase(isoDe(new Date(INICIO.getFullYear()-1, INICIO.getMonth(), INICIO.getDate()))), b = q0>=0 && d.k ? sumaCompleta(d.k, d.F, q0, q0+U) : null, a = suma(d,0,U);
    return {a:a, b:b||0, dl: b ? (a/b-1)*100 : 0, ok: b!=null && b>=30}; }
  if (S.cmp==='sem'){ const w = semanasCmp(U); if (!w) return {a:0, b:0, dl:0, ok:false}; const a = suma(d,w[0],w[1]), b = suma(d,w[2],w[3]); return {a:a, b:b, dl: b ? (a/b-1)*100 : 0, ok: b>=10}; }
  const N = S.cmp, a = suma(d,U-N,U), b = suma(d,U-2*N,U-N);
  return {a:a, b:b, dl: b ? (a/b-1)*100 : 0, ok: 2*N<=U && b >= (N>=30?30:10)};
}
// Suma en cualquier tramo de las bases completas (para comparar con el año anterior)
function sumaCompleta(k, F, q0, q1){
  const n = F && 'nd' in F ? F.nd : F ? F.n : null; let t = 0;
  if (F && F.ss && n!=null) return null;
  for (let d=Math.max(0,q0); d<Math.min(D0.dias,q1); d++){
    if (F && F.ss) for (let j=0;j<F.ss.length;j++) t += D0.ds[k][d*NS+F.ss[j]];
    else if (Array.isArray(n)) for (let j=0;j<n.length;j++) t += D0.dn[k][d*NN+n[j]];
    else if (n!=null) t += D0.dn[k][d*NN+n]; else t += D0.daily[k][d];
  }
  return t;
}
const fechaIdx = i => { const f = fechaBase(i); return f.getDate()+' '+MES12[f.getMonth()]+' '+String(f.getFullYear()).slice(2); };
function cmpDisponible(o){ if (o==='sem') return !!semanasCmp(ND); return o==='aa' ? idxBase(isoDe(new Date(INICIO.getFullYear()-1, INICIO.getMonth(), INICIO.getDate()))) >= 0 : 2*o<=ND; }
function validarCmp(){ if (['sem',30,90].indexOf(S.cmp)<0 || !cmpDisponible(S.cmp)) S.cmp = [30,'sem',90].find(cmpDisponible) || 30; }
// Temporada: el mismo cambio medido en las mismas fechas de hace un año (52 semanas antes, en las bases completas).
// Tramos en días del periodo: a = el reciente, b = el de comparación. Da el % de hace un año o null si no se puede medir.
function haceUnAnio(k, F, a0, a1, b0, b1){
  if (cmpFijo() || S.cmp==='aa') return null;            // comparar contra el año anterior ya descuenta la temporada
  const q = P0-364; if (q+Math.min(a0,b0) < 0) return null;
  const A = sumaCompleta(k, F, q+a0, q+a1), B = sumaCompleta(k, F, q+b0, q+b1);
  if (A==null || B==null || B < 30) return null;
  return ((A/(a1-a0))/(B/(b1-b0))-1)*100;
}
// Un hallazgo es de temporada si hace un año pasó lo mismo: mismo sentido y al menos la mitad del cambio
const deTemporada = (dl, ya) => ya!=null && Math.sign(dl)===Math.sign(ya) && Math.abs(ya) >= Math.abs(dl)/2;
function analizar(F){
  const out = [], N = cmpN(), umbral = N>=30 ? 15 : 25;
  INDS.forEach(m => {
    if (F.nd!=null && !m.nat) return;
    const d = diario(m.k, F), v = variacion(d);
    if (v.ok && Math.abs(v.dl)>=umbral){ const U = finDatos(m.k), w = S.cmp==='sem' ? semanasCmp(U) : [U-N, U, U-2*N, U-N], ya = w ? haceUnAnio(m.k, F, w[0], w[1], w[2], w[3]) : null;
      if (!deTemporada(v.dl, ya)) out.push({t:'cambio', k:m.k, dl:v.dl, a:v.a, b:v.b, ya:ya, imp:Math.abs(v.a-v.b)}); }
    const base = d.slice(Math.max(0,ND-70), ND-14).sort((x,y)=>x-y), mitad = base.length>>1, med = base[mitad] || 0;   // lo habitual: 8 semanas previas
    const des = base.map(x=>Math.abs(x-med)).sort((x,y)=>x-y)[mitad]*1.4826 || 1;
    let mejor = null;
    // los picos solo se buscan con 4 semanas o más de referencia
    if (ND-14 >= 28) for (let i=ND-Math.min(N,14);i<ND;i++){ const z = (d[i]-med)/des; if (d[i]>=25 && z>=4 && (!mejor || z>mejor.z)) mejor = {i:i, z:z, v:d[i], med:med}; }
    if (mejor) out.push({t:'pico', k:m.k, i:mejor.i, v:mejor.v, med:mejor.med, imp:mejor.v-mejor.med});
  });
  const u = NW-1, diasSem = (a,b) => D.ends[b] - (a>0 ? D.ends[a-1] : 0);
  const ws = Math.max(1, Math.round(N/7)), w = [u-ws+1, u, u-2*ws+1, u-ws];   // semanas que cubren cada ventana
  w.push(diasSem(w[0],w[1]), diasSem(w[2],w[3]));
  if (F.n==null && w[2]>=0){
    [['resc',300],['ing',4000],['rech',150]].forEach(par => { const k = par[0]; let mejor = null;
      for (let n=0;n<OT;n++){ if (F.r && D.nats[n][2]!==S.region) continue; const a = sumaSem(k,w[0],w[1],F.ss,n)/w[4], b = sumaSem(k,w[2],w[3],F.ss,n)/w[5];
        if (b*28>=par[1]){ const dl = (a/b-1)*100; if (Math.abs(dl)>=25 && (!mejor || Math.abs(dl)>Math.abs(mejor.dl))) mejor = {n:n, dl:dl, a:a, b:b}; } }
      if (mejor){ const dd = x => x>0 ? D.ends[x-1] : 0, ya = haceUnAnio(k, {ss:F.ss, n:mejor.n}, dd(w[0]), D.ends[w[1]], dd(w[2]), D.ends[w[3]]);
        if (!deTemporada(mejor.dl, ya)) out.push({t:'nac', k:k, n:mejor.n, dl:mejor.dl, a:mejor.a, b:mejor.b, ya:ya, imp:Math.abs(mejor.a-mejor.b)*N}); }
    });
  }
  if (!F.ss && F.nd==null){                     // estados que más se movieron (antes eran los puntos que parpadeaban)
    const o = [];
    INDS.forEach(m => { const a = D.ds[m.k], U = finDatos(m.k);
      for (let s=0;s<NS;s++){ let x = 0, y = 0;
        for (let d=U-N;d<U;d++) x += a[d*NS+s]; for (let d=U-2*N;d<U-N;d++) y += a[d*NS+s];
        if (2*N<=U && y>=(N>=30?80:25)){ const dl = (x/y-1)*100; if (Math.abs(dl)>=40){ const ya = haceUnAnio(m.k, {ss:[s]}, U-N, U, U-2*N, U-N); if (!deTemporada(dl, ya)) o.push({t:'est', k:m.k, s:s, dl:dl, a:x, b:y, ya:ya, imp:Math.abs(x-y)}); } } } });
    o.sort((x,y)=>y.imp-x.imp); const vistos = {}; let c = 0;
    o.forEach(r => { if (!vistos[r.s] && c<3){ vistos[r.s] = 1; c++; out.push(r); } });
  }
  // caravanas que salieron en la ventana de comparación: van primero
  if (F.n==null && !F.ss) carPeriodo().filter(c => c.i>=ND-N && c.i<ND).forEach(c => out.push({t:'car', c:c.j, imp:Infinity}));
  return out.sort((x,y)=>y.imp-x.imp);
}
// Cada aviso se redacta como hallazgo: qué cambió, cuánto y contra qué
// Regla de redacción: siempre «pasó de X a Y» con su %, en palabras cuando el cambio es muy grande, y contra qué periodo se compara
function cuanto(a, b, fmt){ fmt = fmt || corto; const r = a/Math.max(b,1e-9), p = Math.round((r-1)*100);
  const pal = r>=2 ? (r<3 ? 'más del doble' : r<4 ? 'más del triple' : 'más de '+Math.floor(r)+' veces') : r<=0.25 ? 'menos de la cuarta parte' : r<=0.5 ? 'menos de la mitad' : '';
  return (r>=1 ? 'subieron' : 'bajaron')+' de '+fmt(b)+' a '+fmt(a)+' ('+(p>=0 ? '+' : '−')+Math.abs(p)+'%'+(pal ? ', '+pal : '')+')'; }
const ventanaTxt = () => cmpFijo() ? 'el periodo vs. '+(refFija() ? refFija().txt : 'el periodo anterior') : S.cmp==='sem' ? 'última semana vs. la anterior' : 'últimos '+etiquetaN(cmpN())+' vs. los '+etiquetaN(cmpN())+' previos';
function textoAviso(a){
  const N = a.k ? IND[a.k].n : '', vt = '';   // contra qué periodo ya lo dice el encabezado del recuadro
  if (a.t==='cambio') return '<b>'+N+'</b> '+cuanto(a.a, a.b)+'.'+vt;
  if (a.t==='pico')   return '<b>'+N+'</b>: '+miles(a.v)+' el '+fechaDia(a.i)+', cuando lo habitual es '+miles(a.med)+' al día ('+(a.v/Math.max(a.med,1)>=2 ? 'más de '+Math.floor(a.v/Math.max(a.med,1))+' veces lo habitual' : '+'+Math.round((a.v/Math.max(a.med,1)-1)*100)+'%')+').';
  if (a.t==='nac')    return '<b>'+esc(D.nats[a.n][0])+'</b>: '+N.toLowerCase()+' al día '+cuanto(a.a, a.b, miles)+'.'+vt;
  if (a.t==='est')    return '<b>'+esc(EST[a.s])+'</b>: '+N.toLowerCase()+' '+cuanto(a.a, a.b, miles)+'.'+vt;
  if (a.t==='car'){ const c = D.caravanas[a.c];
    return '<b>'+esc(nombreCar(c))+'</b>: salió el '+fechaISO(c.f).replace(/ \d{4}$/,'')+' de '+esc(lugarCorto(c.s))+' con unas '+miles(c.p)+' personas'+(c.d ? '; se disolvió en '+esc(lugarCorto(c.d)) : '')+'.'; }
  return '<b>'+esc(D.nats[a.n][0])+'</b> concentra '+pct(a.a,a.b)+'% de los <b>rechazos</b>.';
}
function filaAviso(a, i){
  const c = colG(a.t==='car' ? 'irr' : IND[a.k].g); let ic, ci;
  const eti = a.t==='car' ? 'Caravana' : IND[a.k].n+(a.t==='pico' ? ' · pico' : a.t==='nac' ? ' · por país' : a.t==='est' ? ' · por estado' : a.t==='conc' ? ' · concentración' : '');
  if (a.t==='car'){ ic = '<svg width="12" height="12" viewBox="0 0 16 16">'+GLIFO_CAR+'</svg>'; ci = '≈'+corto(D.caravanas[a.c].p); }
  else if (a.t==='conc'){ const p = pct(a.a,a.b); ic = '<svg width="12" height="12" viewBox="0 0 12 12"><circle cx="6" cy="6" r="4.5" fill="none" stroke="'+c+'" stroke-width="3" stroke-dasharray="'+(p*0.283).toFixed(1)+' 28.3" transform="rotate(-90 6 6)"/></svg>'; ci = p+'%'; }
  else if (a.t==='pico'){ ic = '<svg width="12" height="12" viewBox="0 0 12 12"><path d="M1 10l3-3 2 2 5-7" fill="none" stroke="'+c+'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'; ci = '▲ '+Math.round((a.v/Math.max(a.med,1)-1)*100)+'%'; }
  else { ic = tri(a.dl>=0, c); ci = Math.abs(a.dl).toFixed(0)+'%'; }
  return '<button class="av" data-av="'+i+'" style="--c:'+c+'"><span class="av-t"><span class="av-k">'+eti+'</span><span class="av-v">'+ic+ci+'</span></span><span class="tx">'+textoAviso(a)+'</span>'+(a.ya!=null ? '<span class="av-ya">Hace un año en estas fechas: '+(a.ya>=0?'+':'−')+Math.abs(a.ya).toFixed(0)+'%</span>' : '')+'</button>';
}
function abrirAviso(i){ const a = AVISOS[i]; if (!a) return;
  if (a.t==='car'){ verCaravana(a.c); return; }
  S.ind = a.k;
  if (a.n!=null) fijarSel({t:'n', i:a.n}, true); else if (a.s!=null) fijarSel({t:'e', i:a.s}, true); else { pintarTodo(); acercarSiMundo(); } }

/* ==== [6] INDICADORES ============================================= */
// Definición de funciones para Art. 159 y Art. 129
const FUNCIONES_OPC = [
  { id: 1, n: 'Función I' },
  { id: 2, n: 'Función II' },
  { id: 3, n: 'Función III' },
  { id: 4, n: 'Función IV' },
  { id: 5, n: 'Función V' },
  { id: 6, n: 'Función VI' }
];

const ITEMS_POR_FUNCION = {
  reg: {
    1: [
      { k: 'ing', n: 'Ingresos' },
      { k: 'rech', n: 'Rechazos' },
      { k: 'tram', n: 'Trámites' }
    ],
    2: [
      { k: 'reg_f2_1', n: 'Opción 1' },
      { k: 'reg_f2_2', n: 'Opción 2' },
      { k: 'reg_f2_3', n: 'Opción 3' }
    ],
    3: [
      { k: 'reg_f3_1', n: 'Opción 1' },
      { k: 'reg_f3_2', n: 'Opción 2' },
      { k: 'reg_f3_3', n: 'Opción 3' }
    ],
    4: [
      { k: 'reg_f4_1', n: 'Opción 1' },
      { k: 'reg_f4_2', n: 'Opción 2' },
      { k: 'reg_f4_3', n: 'Opción 3' }
    ],
    5: [
      { k: 'reg_f5_1', n: 'Opción 1' },
      { k: 'reg_f5_2', n: 'Opción 2' },
      { k: 'reg_f5_3', n: 'Opción 3' }
    ],
    6: [
      { k: 'reg_f6_1', n: 'Opción 1' },
      { k: 'reg_f6_2', n: 'Opción 2' },
      { k: 'reg_f6_3', n: 'Opción 3' }
    ]
  },
  irr: {
    1: [
      { k: 'resc', n: 'Rescatados' },
      { k: 'pres', n: 'Presentados' },
      { k: 'can', n: 'Canalizados' }
    ],
    2: [
      { k: 'ret', n: 'Retornados' },
      { k: 'irr_f2_2', n: 'Opción 2' },
      { k: 'irr_f2_3', n: 'Opción 3' }
    ],
    3: [
      { k: 'irr_f3_1', n: 'Opción 1' },
      { k: 'irr_f3_2', n: 'Opción 2' },
      { k: 'irr_f3_3', n: 'Opción 3' }
    ],
    4: [
      { k: 'irr_f4_1', n: 'Opción 1' },
      { k: 'irr_f4_2', n: 'Opción 2' },
      { k: 'irr_f4_3', n: 'Opción 3' }
    ],
    5: [
      { k: 'irr_f5_1', n: 'Opción 1' },
      { k: 'irr_f5_2', n: 'Opción 2' },
      { k: 'irr_f5_3', n: 'Opción 3' }
    ],
    6: [
      { k: 'irr_f6_1', n: 'Opción 1' },
      { k: 'irr_f6_2', n: 'Opción 2' },
      { k: 'irr_f6_3', n: 'Opción 3' }
    ]
  }
};

function renderCardKpi(m, F, conAviso, semAct) {
  const iconPath = ICONO[m.k] || 'M12 3a9 9 0 1 0 0 18a9 9 0 0 0 0-18z';
  const ic = '<span class="kc-ic"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="'+iconPath+'"/></svg></span>';
  if (m.sinEdo && conEdo(F.ss) && !F.todo) return '<button class="kc" disabled title="Los encuentros los registra la CBP en EE. UU.: no se reparten por O.R."><span class="kc-top">'+ic+'<span class="kc-n">'+m.n+'</span></span><span class="kc-v num">—</span><span class="kc-pie"><span class="kc-d">no aplica por O.R.</span></span></button>';
  if (F.nd!=null && !m.nat) return '<button class="kc" disabled><span class="kc-top">'+ic+'<span class="kc-n">'+m.n+'</span></span><span class="kc-v num">—</span><span class="kc-pie"><span class="kc-d">solo mexicanos</span></span></button>';
  if (!D.cube[m.k]) {
    const on = S.ind===m.k;
    return '<button class="kc'+(on?' on':'')+'" data-k="'+m.k+'" aria-pressed="'+on+'">'+
      '<span class="kc-top">'+ic+'<span class="kc-n">'+m.n+'</span></span>'+
      '<span class="kc-v num" data-v="0">0</span>'+
      '<span class="kc-pie"><span class="kc-d">al ' + fechaDia(S.dia-1) + '</span><span class="kc-b" aria-hidden="true"></span></span></button>';
  }
  const d = diario(m.k,F), v = suma(d,0,S.dia), va = variacion(d), fuerte = va.ok && Math.abs(va.dl)>=20;
  const sem = D.ends.map((e,i)=>suma(d, i?D.ends[i-1]:0, e)), mx = Math.max.apply(null,sem) || 1;
  const delta = S.dia<ND ? '<span class="kc-d">al '+fechaDia(S.dia-1)+'</span>' : (va.ok ? '<span class="kc-d'+(fuerte?' f':'')+'">'+(cmpFijo() ? '' : '<span class="kc-l">'+({ sem:'Semana', 30:'30 días', 90:'3 meses' })[S.cmp]+': '+(va.a>=1e6 ? (va.a/1e6).toFixed(2)+' M' : va.a>=1e4 ? (va.a/1e3).toFixed(1)+' mil' : va.a>0 && va.a<5 ? 'menos de 5' : miles(va.a))+'</span> ')+(va.dl>=0?'▲ ':'▼ ')+Math.abs(va.dl).toFixed(1)+'%'+(cmpFijo() ? '<span class="kc-l"> vs. '+refFija().txt+'</span>' : '')+'</span>' : '<span class="kc-d">sin comparación</span>');
  const on = S.ind===m.k;
  return '<button class="kc'+(on?' on':'')+'" data-k="'+m.k+'" aria-pressed="'+on+'">'+
    '<span class="kc-top">'+ic+(FUENTE[m.k] ? '<span class="kc-nf">' : '')+'<span class="kc-n">'+m.n+(conAviso[m.k]?'<u title="Tiene un aviso de cambio"></u>':'')+'</span>'+(FUENTE[m.k] ? '<span class="kc-f">'+FUENTE[m.k][0]+'</span></span>' : '')+'</span>'+
    '<span class="kc-v num" data-v="'+v+'">'+corto(v)+'</span>'+
    '<span class="kc-pie">'+delta+'<span class="kc-b" aria-hidden="true">'+sem.map((x,i)=>'<i class="'+(i===semAct?'h':i<semAct?'p':'')+'" style="height:'+Math.max(8,x/mx*100).toFixed(0)+'%"></i>').join('')+'</span></span></button>';
}

function pintarKpis(){
  const F = filtro(), conAviso = {}; AVISOS.slice(0,5).forEach(a => conAviso[a.k] = 1);
  const semAct = semDe(S.dia);
  $('kpis').dataset.modo = S.kpiModo;
  $('kpis').innerHTML = GRUPOS.map(g => {
    const gKey = g[0];
    const tieneFunciones = (gKey === 'reg' || gKey === 'irr');
    let contenido = '';
    
    if (tieneFunciones) {
      const funcActiva = S.funcSel[gKey];
      if (!funcActiva) {
        // Mostrar los 6 botones de funciones
        const btns = FUNCIONES_OPC.map(fn => {
          const fnIc = '<span class="btn-func-ic"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg></span>';
          return '<button class="btn-func" data-sel-grupo="'+gKey+'" data-sel-func="'+fn.id+'">'+fnIc+fn.n+'</button>';
        }).join('');
        contenido = '<div class="eti">'+g[1]+'</div><div class="funcs-grid">'+btns+'</div>';
      } else {
        // Función seleccionada: cabecera con botón volver + las 3 tarjetas grandes abajo
        const fInfo = FUNCIONES_OPC.find(fn => fn.id === funcActiva) || { n: 'Función ' + funcActiva };
        const items = (ITEMS_POR_FUNCION[gKey] && ITEMS_POR_FUNCION[gKey][funcActiva]) || [
          { k: gKey+'_1', n: 'Opción 1' },
          { k: gKey+'_2', n: 'Opción 2' },
          { k: gKey+'_3', n: 'Opción 3' }
        ];
        const cardsHtml = items.map(m => renderCardKpi(m, F, conAviso, semAct)).join('');
        contenido = '<div class="barra-func-header">' +
            '<span class="badge-func-activa"><svg width="9" height="12" viewBox="0 0 8 12" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1.5 1.5 6 6 1.5 10.5"/></svg>'+fInfo.n+'</span>' +
            '<button class="btn-volver-func" data-volver-grupo="'+gKey+'">← Volver a funciones</button>' +
          '</div>' +
          '<div class="cards-fila">'+cardsHtml+'</div>';
      }
    } else {
      // Grupo directo (ej. Gestión Administrativa)
      const cardsHtml = INDS.filter(m => m.g === gKey).map(m => renderCardKpi(m, F, conAviso, semAct)).join('');
      contenido = '<div class="eti">'+g[1]+'</div><div>'+cardsHtml+'</div>';
    }

    return '<div class="kg g-'+gKey+'" style="flex:'+g[2]+' 1 0">'+contenido+'</div>';
  }).join('')+'<button class="plegar" id="plegar" aria-label="'+(S.kpiModo==='tarjetas'?'Compactar indicadores':'Mostrar tarjetas')+'" title="'+(S.kpiModo==='tarjetas'?'Compactar indicadores':'Mostrar tarjetas')+'"><svg width="12" height="12" viewBox="0 0 12 12"><path d="'+(S.kpiModo==='tarjetas'?'M2 8l4-4 4 4':'M2 4l4 4 4-4')+'" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>';
  if (S.estreno){ S.estreno = false; if (!reducido()) contar(); }
}


const DEF_IND = {
  ing:'Entradas al país por puntos de internación aéreos, terrestres y marítimos: extranjeros y mexicanos que regresan.',
  rech:'Personas a las que, en segunda revisión, se les negó la internación al país.',
  tram:'Trámites migratorios concluidos en oficinas del INM: los que expiden tarjeta (residencias y visitantes) y los que no (constancias, oficios, permisos o sin documento).',
  resc:'Rescates de personas extranjeras en situación irregular, según el reporte de las oficinas de representación. Se cuentan eventos: si a una persona se le rescata dos veces, cuenta dos.',
  pres:'Personas presentadas ante una estación o estancia migratoria.',
  can:'Niñas, niños y adolescentes, y sus acompañantes, canalizados a la protección del DIF.',
  ret:'Personas extranjeras retornadas a su país, por deportación o retorno asistido.',
  recib:'Personas extranjeras recibidas en México desde EE. UU.',
  rep:'Personas mexicanas repatriadas desde EE. UU.',
  cbp:'Encuentros que registra la CBP en la frontera de EE. UU. con México. Esta actividad la hace EE. UU., no el INM. Incluye mexicanos y no se reparte por O.R.: se ve por sector de la frontera.'
};
const BASE_IND = {ing:'ing', rech:'seg', tram:'tram', resc:'resc', pres:'pres', can:'can_nna', ret:'ret', recib:'recib', rep:'rep', cbp:'cbp'};
const FUENTE = {ing:['extranjeros y mexicanos',null], resc:['eventos · O.R.','O.R.'], pres:['Sistema','Sistema'], cbp:['en EE. UU.','CBP (EE. UU.)']};     // [nota en la tarjeta, fuente en el detalle]
const nomInd = k => IND[k].n+(k==='resc' ? ' (eventos)' : '');                 // nombre para títulos de listas
// Último día con datos de cada indicador dentro del periodo: los días posteriores están pendientes, no son cero
function finDatos(k){
  const bs = (k==='can' ? ['can_nna','can_ad'] : [BASE_IND[k==='co' ? 'tram' : k]]).map(c => D.bases.find(x => x.k===c)).filter(b => b && b.hasta);
  if (!bs.length) return ND;
  return Math.max(0, Math.min(ND, Math.min.apply(null, bs.map(b => idxBase(b.hasta)+1)) - P0));
}
// Mexicanos que ingresaron (ya están dentro de «Ingresos»): para decir cuántos son extranjeros y cuántos mexicanos
function ingMx(ss, hasta){ const A = D0.ds.ing_mx, B2 = D0.daily.ing_mx; if (!A || !B2) return 0; const b = P0 + Math.min(hasta==null ? S.dia : hasta, ND); let t = 0;
  if (!ss){ for (let d=P0; d<b; d++) t += B2[d] || 0; return t; }
  for (let d=P0; d<b; d++) for (let j=0; j<ss.length; j++) t += A[d*NS+ss[j]]; return t; }
function totalPais(ext, mx){ const T = ext+mx || 1;
  return '<span class="tip-tot">Ingresaron al país <b>'+miles(ext+mx)+'</b> personas: extranjeros <b>'+miles(ext)+'</b> ('+(ext/T*100).toFixed(1)+'%) + mexicanos <b>'+miles(mx)+'</b> ('+(mx/T*100).toFixed(1)+'%)'+
    '<i class="tip-b"><i style="width:'+(ext/T*100).toFixed(1)+'%"></i></i></span>'; }
function cbpMx(t, mx){ const T = t || 1;
  return '<span class="tip-tot">Encuentros <b>'+miles(t)+'</b>: otros países <b>'+miles(t-mx)+'</b> ('+((t-mx)/T*100).toFixed(1)+'%) + mexicanos <b>'+miles(mx)+'</b> ('+(mx/T*100).toFixed(1)+'%)'+
    '<i class="tip-b"><i style="width:'+((t-mx)/T*100).toFixed(1)+'%;background:'+colG('usa')+'"></i></i></span>'; }
function tipKpi(el){
  const k = el.dataset.k, m = IND[k], F = filtro(), va = variacion(diario(k,F)), b = D.bases.find(x => x.k===BASE_IND[k]) || {};
  const tot = acum(k,F.ss,m.nat ? F.nd : null) || 1, tn = m.nat && F.n==null ? topNats(n => enRegion(n) ? acum(k,F.ss,n) : 0, 3) : [];
  return '<b>'+m.n+(nombreFiltro() ? ' · '+esc(nombreFiltro()) : '')+'</b><span>'+DEF_IND[k]+'</span>'+(k==='ing' && F.n==null ? (m => totalPais(acum('ing',F.ss,null) - m, m))(ingMx(F.ss)) : '')+(k==='cbp' && F.n==null ? cbpMx(acum('cbp',null,F.r ? F.nd : null), F.r ? 0 : acum('cbp',null,MX)) : '')+
    (va.ok ? '<span>'+(cmpFijo() ? 'Este periodo' : S.cmp==='sem' ? 'Última semana completa' : 'Últimos '+etiquetaN(S.cmp))+': <b>'+corto(va.a)+'</b> · '+(cmpFijo() ? refFija().txt : S.cmp==='sem' ? 'semana previa' : 'anteriores')+': '+corto(va.b)+' ('+(va.dl>=0?'▲ ':'▼ ')+Math.abs(va.dl).toFixed(1)+'%)</span>' : '')+
    (U => U>0 ? '<span>Promedio: <b>'+miles(suma(diario(k,F),0,U)/U)+'</b> al día · <b>'+miles(suma(diario(k,F),0,U)/U*7)+'</b> a la semana'+(U>=60 ? ' · <b>'+miles(suma(diario(k,F),0,U)/U*30.4)+'</b> al mes' : '')+'</span>' : '')(finDatos(k))+
    (k==='tram' && D.comp.tram_exp ? (e => { const p = comp('tram_plz',F.ss,F.nd), te = e[0]+e[1], tp = p[0]+p[1]; return te ? '<span>Expiden tarjetas: <b>'+miles(e[0])+'</b> · no expiden: <b>'+miles(e[1])+'</b>'+(tp && p[1] ? ' · <b>'+pct(p[0], tp)+'%</b> dentro del plazo normativo' : '')+'</span>' : ''; })(comp('tram_exp',F.ss,F.nd)) : '')+
    (k==='resc' ? (r => '<span>Eventos: <b>'+miles(r[0]+r[1])+'</b> · personas (1ra vez): <b>'+miles(r[0])+'</b> · reincidentes: '+miles(r[1])+'</span>')(comp('resc_rei',F.ss,F.nd)) : '')+
    (tn.length ? '<span>Principales: '+tn.map(r => esc(D.nats[r[0]][0])+' '+pct(r[1],tot)+'%').join(' · ')+'</span>' : '')+
    (finDatos(k)<ND ? '<span>Días pendientes: la base llega al '+fechaLarga(finDatos(k)-1)+'; la comparación se hace hasta ese día.</span>' : '')+
    '<small>'+(FUENTE[k] && FUENTE[k][1] ? 'Fuente: '+FUENTE[k][1]+' · ' : '')+'Base: '+esc(b.archivo || '')+(b.hasta ? ' · datos al '+fechaISO(b.hasta) : '')+(TACTIL ? '' : ' · clic para verlo en el mapa')+'</small>';
}
let tipEspera = 0;
let PUNTERO = 'mouse';                           // último tipo de puntero: con el dedo, la ventanita se fija y se cierra con ×
document.addEventListener('pointerdown', e => { PUNTERO = e.pointerType; }, true);
function mostrarTip(el, tocar){
  const t = $('kpi-tip'); clearTimeout(tipEspera); if (!el){ t.hidden = true; t.classList.remove('fija'); return; }
  if (PUNTERO==='touch' && !tocar) return;
  t.innerHTML = (tocar ? '<button class="kpi-tip-x" data-tipx aria-label="Cerrar">×</button>' : '')+tipKpi(el); t.hidden = false; t.classList.toggle('fija', !!tocar);
  const r = el.getBoundingClientRect(), w = t.offsetWidth;
  t.style.left = Math.max(8, Math.min(r.left, window.innerWidth-w-8))+'px'; t.style.top = (r.bottom+8)+'px';
}
function contar(){                              // las cifras suben una vez al abrir
  const els = Array.prototype.slice.call(document.querySelectorAll('.kc-v[data-v]')), t0 = performance.now(), dur = 900;
  const paso = t => { const e = Math.min(1,(t-t0)/dur), f = 1-Math.pow(1-e,3);
    els.forEach(el => { if (el.isConnected) el.textContent = corto(+el.dataset.v*f); }); if (e<1) requestAnimationFrame(paso); };
  requestAnimationFrame(paso);
}

/* ==== [7] MAPA (estados, círculos, puntos) ========================= */
const COL = { act:{}, meta:{}, sucio:true };     // color actual y color meta de cada estado, para la transición suave
function regiones(){
  const t = TM[S.tema], F = filtro(), rgb = c => 'rgb('+Math.round(c[0])+','+Math.round(c[1])+','+Math.round(c[2])+')';
  const eu = {}; let euMax = 1;
  if (S.ind==='cbp' && CBPT){ const tod = cbpSec(P0, P1, F.nd), sec = cbpAhora(F), m = {}; D.cbp.sectores.forEach((P,i) => { eu[P.eu] = (eu[P.eu] || 0) + sec[i].v; m[P.eu] = (m[P.eu] || 0) + tod[i].v; }); euMax = Math.max(1, ...Object.values(m)); }
  return GEO.features.filter(f => f.properties.t==='m' || f.properties.t==='u').map(f => { const k = f.properties.key, mx = f.properties.t==='m';
    const s = mx ? ECLAVE.indexOf(k) : -1, sel = mx && F.ss && !F.todo && F.ss.indexOf(s)>=0, c = COL.act[k], enc = mx ? 0 : eu[k.slice(3)];
    const area = c ? rgb(c) : enc ? rgb(mezclaRGB(t.r_usa, 0.1+0.45*enc/euMax)) : (mx?t.mx:t.eu);
    return { name:k, itemStyle:{ areaColor:area, borderColor: sel?t.tinta:(mx?t.mxL:t.euL), borderWidth: (sel?2:(mx?0.8:0.5))*E },
             emphasis:{ itemStyle:{ areaColor:area, borderColor:t.tinta, borderWidth:(mx?2:0.8)*E } } }; })
    .concat(paisesResaltados(t, F));
}
// País elegido (relleno y contorno) y países de la región elegida (relleno tenue); también su copia a la izquierda
function paisesResaltados(t, F){
  const o = [], pais = (n, st) => { const k = 'P_'+String(D.nats[n][1]).padStart(3,'0'); [k, 'W_'+k].forEach(x => o.push({ name:x, itemStyle:st, emphasis:{ itemStyle:st } })); };
  if (F.r) F.r.forEach(n => pais(n, { areaColor:t.region }));
  if (F.n!=null) pais(F.n, { areaColor:t.relleno, borderColor:t.tinta, borderWidth:1.6*E });
  return o;
}
function opcionBase(){
  const t = TM[S.tema], et = { color:t.tinta, fontFamily:'Barlow, sans-serif', textBorderColor:t.halo, textBorderWidth:2.5*E };
  return {
    backgroundColor:'transparent', animationDurationUpdate:420, animationEasingUpdate:'cubicOut',
    tooltip:{ trigger:'item', confine:true, position:junto, backgroundColor: S.tema==='oscuro'?'#F7F5EE':'#2B2926', borderWidth:0, padding:[9*E,11*E],
              textStyle:{ color: S.tema==='oscuro'?'#2B2926':'#F4F2EA', fontSize:12 }, extraCssText:'box-shadow:0 8px 24px rgba(0,0,0,.35);border-radius:'+(9*E)+'px;', formatter: tarjeta },
    geo:{ map:'ianami', nameProperty:'key', roam:true, boundingCoords:CAJA_MUNDO, center:S.centro || VISTA_MX.c, zoom:S.zoom*KMX(), scaleLimit:{min:0.6, max:40*KMX()}, layoutCenter:['50%','50%'], layoutSize:encuadre(), aspectScale:ESCALA_LAT,
          itemStyle:{ areaColor:t.tierra, borderColor:t.linea, borderWidth:0.5*E },
          emphasis:{ label:{show:false}, itemStyle:{ areaColor:t.region, borderColor:t.tinta, borderWidth:0.9*E } },    // al pasar sobre un país se ilumina
          select:{ disabled:true }, label:{show:false}, tooltip:{ show:true, formatter:tarjeta }, regions:regiones() },
    series:[
      { id:'bub', type:'scatter', coordinateSystem:'geo', data:[],
        label:Object.assign({ show:true, position:'right', distance:6*E, formatter:p=>p.data.et||'', fontSize:11.5*E, fontWeight:600 }, et),
        labelLayout:{hideOverlap:true}, emphasis:{scale:1.12} },
      { id:'pts', type:'scatter', coordinateSystem:'geo', data:[],
        label:Object.assign({ show:false, position:'right', distance:5*E, formatter:p=>p.data.et, fontSize:11*E }, et), labelLayout:{hideOverlap:true} },
      { id:'cbp', type:'effectScatter', coordinateSystem:'geo', data:[], symbol:'circle', showEffectOn:'render', rippleEffect:{ brushType:'stroke', scale:2.2, period:4, number:2 },
        label:Object.assign({ show:false, position:'top', distance:4*E, formatter:p=>p.data.et, fontSize:11*E, fontWeight:600 }, et), labelLayout:{hideOverlap:true} },
      { id:'grp', type:'scatter', coordinateSystem:'geo', data:[], symbolSize:1, silent:true, itemStyle:{opacity:0},
        label:Object.assign({ show:true, position:'inside', formatter:p=>p.data.et, fontSize:13*E, fontWeight:600 }, et, {fontFamily:'Barlow Condensed, Barlow, sans-serif'}) },
      { id:'lat', type:'effectScatter', coordinateSystem:'geo', data:[], showEffectOn:'render',          // latido: dónde están, sin flujo
        rippleEffect:{ brushType:'stroke', scale:2.6, period:3.6, number:2 },
        label:Object.assign({ show:true, position:'right', distance:6*E, formatter:p=>p.data.et||'', fontSize:11.5*E, fontWeight:600 }, et), labelLayout:{hideOverlap:true} },
      { id:'car', type:'effectScatter', coordinateSystem:'geo', data:[], showEffectOn:'render', zlevel:1,     // caravanas: salida que late
        rippleEffect:{ brushType:'fill', scale:3.2, period:2.6, number:3 },
        label:Object.assign({ show:true, position:'left', distance:7*E, formatter:p=>p.data.et||'', fontSize:11.5*E, fontWeight:600 }, et), labelLayout:{hideOverlap:true} }
    ]
  };
}
// El mapa nunca se deforma: conserva su proporción y el encuadre inicial cabe completo;
// si el contenedor es más ancho o más alto, simplemente se ve más mapa alrededor.
function encuadre(){
  const lz = $('lz'), proporcion = ancho(CAJA_MUNDO) / alto(CAJA_MUNDO) * ESCALA_LAT;
  return Math.round(Math.min(lz.clientWidth, lz.clientHeight*proporcion));
}
const ancho = c => c[1][0]-c[0][0], alto = c => c[0][1]-c[1][1];
const pxGrado = (gLon, gLat) => { const lz = $('lz'); return Math.min(lz.clientWidth/(gLon*ESCALA_LAT), lz.clientHeight/gLat); };
// Zoom del mapa que equivale al encuadre de México (el mapa base es el mundo)
function KMX(){ return pxGrado(ancho(CAJA), alto(CAJA)) / pxGrado(ancho(CAJA_MUNDO), alto(CAJA_MUNDO)); }
// Zoom (medido contra México) para que quepa una región de tantos grados
function zoomPara(gLon, gLat){ return pxGrado(gLon, gLat) / pxGrado(ancho(CAJA), alto(CAJA)); }
function vistaMundo(){ const m = CAJA_MUNDO; return { c:[(m[0][0]+m[1][0])/2, (m[0][1]+m[1][1])/2], z:zoomPara(ancho(m), alto(m)) }; }
function reencuadrar(){ chart.resize(); chart.setOption({geo:{layoutSize:encuadre(), scaleLimit:{min:0.6, max:40*KMX()}}});
  if (S.modoVista==='mundo'){ const v = vistaMundo(); chart.setOption({geo:{center:v.c, zoom:v.z*KMX()}}); S.zoom = v.z; } else if (S.modoVista==='mx'){ chart.setOption({geo:{center:VISTA_MX.c, zoom:VISTA_MX.z*KMX()}}); S.zoom = VISTA_MX.z; } }
// Vuelo que deja a la vista un punto lejano y a México
function volarConMexico(xy){ S.modoVista = 'libre';
  const z = zoomPara(Math.abs(xy[0]+102)+60, Math.abs(xy[1]-23)+40);
  volar([(xy[0]-102)/2, (xy[1]+23)/2], Math.max(vistaMundo().z, Math.min(1, z))); }
// Al elegir un indicador desde la vista del mundo, el mapa se acerca a México: ahí está el detalle por estado
function acercarSiMundo(){ if (S.modoVista==='mundo'){ S.modoVista = 'mx'; volar(VISTA_MX.c, VISTA_MX.z); } }
// La tarjeta aparece junto al cursor y nunca se sale del mapa
function junto(pt, params, dom, rect, size){
  const w = size.contentSize[0], h = size.contentSize[1], W = size.viewSize[0], H = size.viewSize[1], m = 8*E, sep = 16*E;
  let x = pt[0]+sep, y = pt[1]+sep;
  if (x+w > W-m) x = pt[0]-w-sep;
  if (y+h > H-m) y = pt[1]-h-sep;
  return [Math.max(m, Math.min(x, W-w-m)), Math.max(m, Math.min(y, H-h-m))];
}
function capaPuntos(kc){                        // qué puntos corresponden al indicador
  if (kc==='rep') return {lista:D.repPuntos, tipo:'rep', siempre:true};
  if (kc==='pres') return {lista:D.emPuntos, tipo:'em', siempre:true};
  if (kc==null || kc==='ing' || kc==='rech') return {lista:D.puntos, tipo:'ing', siempre:false};
  return null;
}
// Promedio de los últimos 7 días de un estado (al día del cursor) y el mayor promedio de 7 días del periodo
const MAX7 = {};
function prom7(k, s){ const A = D.ds[k], b = Math.min(S.dia, finDatos(k)), a = Math.max(0, b-7); let t = 0; for (let d=a; d<b; d++) t += A[d*NS+s]; return b>a ? t/(b-a) : 0; }
function max7(k){ const key = k+'|'+P0+'|'+P1; if (MAX7[key]!=null) return MAX7[key]; const A = D.ds[k], U = finDatos(k); let m = 0;
  for (let s=0;s<NS;s++){ let t = 0; for (let d=0; d<U; d++){ t += A[d*NS+s]; if (d>=7) t -= A[(d-7)*NS+s]; m = Math.max(m, t/Math.min(7, d+1)); } }
  return MAX7[key] = m; }
function pintarMapa(){
  const t = TM[S.tema], F = filtro(), fin = alFinal(), kc = S.ind;
  const kcE = kc || (SALA.on ? (perfilSala().mapa || 'resc') : null), nFE = kcE && IND[kcE].nat ? F.nd : null;   // en Panorama de pantalla completa, los estados se pintan por rescates
  const g = kc ? IND[kc].g : (kcE ? IND[kcE].g : 'irr'), col = t[g], rampa = t['r_'+g], nF = kc && IND[kc].nat ? F.nd : null, ag = S.agr!=='e' ? AGR[S.agr] : null;
  const meta = {}, grp = []; let maxE = 0;
  // -- Estados (o cinturones / CECO) coloreados; la escala es fija para que la reproducción sea comparable
  if (kcE){
    if (ag){ const tot = ag.nombres.map((x,q) => ritmo(kcE, miembros(S.agr,q), nFE));
      ag.nombres.forEach((x,q) => { const ss = miembros(S.agr,q); maxE = Math.max(maxE, fin ? sumaSem(kcE,0,NW-1,ss,nFE) : Math.max.apply(null, semanal(kcE,ss,nFE))); });
      for (let s=0;s<NS;s++){ const q = ag.de[s]; if (q>=0 && tot[q]>0) meta[ECLAVE[s]] = mezclaRGB(rampa, 0.12+0.88*Math.sqrt(tot[q]/Math.max(maxE,1))); }
      ag.nombres.forEach((nom,q) => grp.push({ value:xyGrupo(miembros(S.agr,q)), et:nom+' · '+corto(fin?tot[q]:acum(kcE,miembros(S.agr,q),nFE)) }));
    } else if (!fin && nFE==null){                // al reproducir: promedio de los últimos 7 días, con la escala fija del periodo
      maxE = max7(kcE);
      for (let s=0;s<NS;s++){ const v = prom7(kcE, s); if (v>0) meta[ECLAVE[s]] = mezclaRGB(rampa, 0.08+0.92*Math.sqrt(v/Math.max(maxE,1e-9))); }
    } else {
      for (let s=0;s<NS;s++) maxE = Math.max(maxE, fin ? sumaSem(kcE,0,NW-1,[s],nFE) : Math.max.apply(null, semanal(kcE,[s],nFE)));
      for (let s=0;s<NS;s++){ const v = ritmo(kcE,[s],nFE); if (v>0) meta[ECLAVE[s]] = mezclaRGB(rampa, 0.08+0.92*Math.sqrt(v/Math.max(maxE,1))); }
    }
  } else if (ag){                                // sin indicador: se pinta a qué cinturón o CECO pertenece cada estado
    const cs = S.agr==='c' ? t.neu : [t.r_reg[1], t.r_usa[1]];
    for (let s=0;s<NS;s++){ const q = ag.de[s]; if (q>=0) meta[ECLAVE[s]] = hex(cs[q]); }
    ag.nombres.forEach((nom,q) => grp.push({ value:xyGrupo(miembros(S.agr,q)), et:nom }));
  }
  if (!kc && F.ss && !F.todo) F.ss.forEach(s => { meta[ECLAVE[s]] = hex(t.relleno); });   // estado o grupo elegido: se rellena
  COL.meta = meta; COL.sucio = true;
  // -- Círculos por nacionalidad y flujos de origen a destino
  const bub = [], lat = [], fl = [], fz = Math.max(0.62, Math.min(1, 0.55+0.45*S.zoom));     // círculos algo menores al alejarse
  const burbuja = (n, v, mx, c, et, fijo, late) => { const xy = xyNat(n); if (!xy) return;
    // sin flujos, los círculos laten
    // id fijo por país: al cambiar el orden no se desliza de un país a otro
    (late || !S.flujos ? lat : bub).push({ id:'n'+n, value:[xy[0],xy[1],v], nat:n, et:et, symbolSize: (fijo || (7 + 30*Math.sqrt(Math.min(1, v/Math.max(mx,1)))))*E*fz,
               itemStyle: SALA.on ? { color:alfa(c,.24), opacity:1, borderColor:c, borderWidth:(F.n===n?2.6:1.6)*E }      // en pantalla completa: contorno y relleno translúcido
                         : { color:c, opacity:.72, borderColor:(F.n===n?t.tinta:t.halo), borderWidth:(F.n===n?2.5:1)*E } }); };
  const flujo = (id, a, b, v, mx, c) => { if (a && b) fl.push({ id:id, a:a, b:b, c:c, w: 1 + 3.4*Math.sqrt(Math.min(1, v/Math.max(mx,1))) }); };
  const destinoDe = (k, n) => { if (F.ss && !F.todo) return [xyGrupo(F.ss), 'F']; const r = topEsts(s => !F.ss || F.ss.indexOf(s)>=0 ? sumaSem(k,0,NW-1,[s],n) : 0, 1)[0]; return r ? [xyEst(r[0]), r[0]] : [null,null]; };
  // Puntos de internación principales de una nacionalidad (ingresos y rechazos), dentro del filtro de estados
  const puntoDe = (k, n) => { const l = k==='ing' ? D.ingPunto : k==='rech' ? D.rechPunto : null; if (!l || !l[n]) return null;
    const r = l[n].map(x => [D.puntos[x[0]], x[1]]).filter(x => !F.ss || F.ss.indexOf(x[0].s)>=0); return r.length ? r : null; };
  const salida = k => k==='ret' || k==='rech';             // rechazos y retornados salen de México hacia el país
  const nR = S.region ? 10 : 0;                              // con una región elegida se muestran más nacionalidades
  const pmap = SALA.on && perfilSala().mapa;
  const pares = kc ? [[kc, (kc==='ing' || kc==='resc') ? 10 : (nR||8), true]] : pmap ? [[pmap, 10, true]] : [['ing', 10, false], ['resc', 10, true]];     // sin indicador: panorama regular + irregular
  pares.forEach(par => { const k = par[0], c = k==='rech' ? t.arena : t[IND[k].g], latido = k==='tram';   // trámites: sin flujo, solo latido
    if (k==='rep'){ const l = D.repPuntos.map(p=>[p, suma(p.wk,0,NW)]).sort((x,y)=>y[1]-x[1]).slice(0,7), mx = l[0][1];
      l.forEach((r,i) => flujo('rep'+i, ANCLA_EU, [r[0].x,r[0].y], r[1], mx, c)); return; }
    if (k==='recib'){ const l = topEsts(s => ritmo(k,[s],F.nd), 5), mx = l.length?l[0][1]:1; l.forEach(r => flujo('recib'+r[0], ANCLA_EU, xyEst(r[0]), r[1], mx, c));
      if (kc){ const ln = F.n!=null ? [[F.n, ritmo(k,F.ss,F.n)]] : topNats(n => enRegion(n) ? ritmo(k,F.ss,n) : 0, 10), mb = ln.length ? (fin?ln[0][1]:Math.max.apply(null,semanal(k,F.ss,ln[0][0]))) : 1; ln.forEach((r,i) => burbuja(r[0], r[1], mb, c, i<5?D.nats[r[0]][0]+' · '+corto(fin?r[1]:acum(k,F.ss,r[0])):'', 0, r[0]===F.n)); }
      return; }
    if (F.n!=null){                               // una nacionalidad: hacia sus principales estados
      const l = topEsts(s => ritmo(k,[s],F.n), 3), mx = l.length?l[0][1]:1;
      const pp = puntoDe(k, F.n);
      if (!latido && pp) pp.forEach((x,j) => { const a = xyNat(F.n), b = [x[0].x, x[0].y]; if (salida(k)) flujo(k+'p'+j, b, a, x[1], pp[0][1], c); else flujo(k+'p'+j, a, b, x[1], pp[0][1], c); });
      else if (!latido) l.forEach(r => { const a = xyNat(F.n), b = xyEst(r[0]); if (salida(k)) flujo(k+'n'+r[0], b, a, r[1], mx, c); else flujo(k+'n'+r[0], a, b, r[1], mx, c); });
      if (par[2]) burbuja(F.n, ritmo(k,null,F.n), 1, c, D.nats[F.n][0]+' · '+corto(fin?sumaSem(k,0,NW-1,null,F.n):acum(k,null,F.n)), 22, true);
      return; }
    const l = topNats(n => enRegion(n) ? ritmo(k,F.ss,n) : 0, par[1]), mx = l.length?l[0][1]:1;
    const mb = l.length ? (fin ? l[0][1] : Math.max.apply(null, semanal(k,F.ss,l[0][0]))) : 1;
    l.forEach((r,i) => { const a = xyNat(r[0]);
      if (!latido){ const pp = puntoDe(k, r[0]);
        if (pp){ const tp = pp.reduce((x,y) => x+y[1], 0);         // se reparte entre sus principales puntos de internación
          pp.forEach((x,j) => { const b = [x[0].x, x[0].y], v = r[1]*x[1]/tp; if (salida(k)) flujo(k+r[0]+'p'+j, b, a, v, mx, c); else flujo(k+r[0]+'p'+j, a, b, v, mx, c); }); }
        else { const d = destinoDe(k, r[0]); if (!d[0]) return; if (salida(k)) flujo(k+r[0], d[0], a, r[1], mx, c); else flujo(k+r[0], a, d[0], r[1], mx, c); } }
      if (par[2]) burbuja(r[0], r[1], mb, c, (i<5 || !S.flujos) ? D.nats[r[0]][0]+' · '+corto(fin?r[1]:acum(k,F.ss,r[0])) : '', 0, latido);
      else if (!bub.concat(lat).some(x=>x.nat===r[0])) burbuja(r[0], r[1], mb, c, D.nats[r[0]][0]+' · '+corto(fin?r[1]:acum(k,F.ss,r[0])), 0); });
  });
  if (F.n!=null && !bub.concat(lat).some(x => x.nat===F.n)) burbuja(F.n, 1, 1, t.tinta, D.nats[F.n][0], 18, true);   // el país elegido siempre se ve
  if (!S.circulos) [bub, lat].forEach(a => { for (let i=a.length-1;i>=0;i--) if (a[i].nat!==F.n) a.splice(i,1); });   // círculos ocultos (menos el país elegido)
  if (!S.flujos && !S.car) ponerFlujos([]);
  // -- Puntos de ingreso, repatriación y estaciones
  const cp = capaPuntos(kc), pts = []; let maxP = 1;
  if (cp){ cp.lista.forEach(p => maxP = Math.max(maxP, suma(p.wk,0,NW)));
    const selP = S.sel && S.sel.t==='p' && S.sel.tipo===cp.tipo;
    const ver = S.puntos || (kc && cp.siempre) || (kc && S.zoom>=1.9) || selP;
    cp.lista.forEach((p,i) => { const v = suma(p.wk,0,semDe(S.dia)+1); if (v<=0) return;
      if (ver) pts.push({ value:[p.x,p.y,v], pt:i, pTipo:cp.tipo, et:p.n,
        symbol: ICONO_PUNTO(cp.tipo, t[cp.tipo==='ing'?'reg':cp.tipo==='rep'?'usa':'irr'], S.tema==='oscuro' ? '#2B2926' : '#FFFFFF'),
        symbolSize: (15 + 11*Math.sqrt(v/maxP))*E,
        label:{ show: S.zoom>=3.4 || (cp.siempre && S.zoom>=1.5) || (selP && S.sel.i===i) },
        itemStyle:{ color:t[cp.tipo==='ing'?'reg':cp.tipo==='rep'?'usa':'irr'], opacity:.95, borderWidth:0 } }); });
  }
  // -- Encuentros de la CBP por sector, del lado de EE. UU.
  const enc = [];
  if (S.ind==='cbp' && CBPT){ const tod = cbpSec(P0, P1, F.nd), sec = cbpAhora(F), mxc = Math.max(1, ...tod.map(x => x.v));     // escala fija del periodo: la reproducción es comparable
    D.cbp.sectores.forEach((P,i) => { const v = sec[i].v; if (v<=0) return;
      enc.push({ value:[P.x,P.y,v], cb:i, et:P.n+' · '+corto(v), symbolSize:(8 + 20*Math.sqrt(v/mxc))*E, label:{ show:S.zoom>=0.75 },
                 itemStyle:{ color:t.usa, opacity:.9, borderColor:t.tinta, borderWidth:1.4*E } }); }); }
  // -- Caravanas: dónde salieron y, si se sabe, dónde se disolvieron
  const car = [], rutas = [];
  if (S.car){ const l = carPeriodo().filter(c => c.i<S.dia), mxp = Math.max.apply(null, l.map(c => c.p).concat(1)), orig = {};
    l.forEach(c => { const C = D.caravanas[c.j]; if (!C.sx) return; const q = C.sx.join(','); (orig[q] = orig[q] || {xy:C.sx, l:[]}).l.push(c.j);
      if (C.dx) rutas.push({ id:'car'+c.j, a:C.sx, b:C.dx, ruta:rutaCaravana(c.j).p, c:t.irr, w:1 + 2.6*Math.sqrt(C.p/mxp), car:C.p, sel:S.carSel===c.j }); });
    Object.keys(orig).forEach(q => { const o = orig[q], p = o.l.reduce((x,j) => x+D.caravanas[j].p, 0);
      car.push({ value:o.xy.concat(p), cars:o.l, et:lugarCorto(D.caravanas[o.l[0]].s)+' · '+o.l.length+(o.l.length===1?' caravana':' caravanas'),
                 symbolSize:(11 + 9*Math.sqrt(o.l.length/Math.max(1,l.length)))*E, itemStyle:{ color:t.irr, opacity:.95, borderColor:t.halo, borderWidth:1.6*E } }); });
    rutas.forEach(r => { const j = +r.id.slice(3);
      car.push({ value:r.b.concat(D.caravanas[j].p), fin:j, et:'', symbol:'circle', symbolSize:(r.sel?10:7)*E, label:{show:false}, showEffectOn:'emphasis',
                 itemStyle:{ color:t.halo, borderColor:t.irr, borderWidth:2*E } }); }); }
  if (S.flujos || S.car) ponerFlujos((S.flujos ? fl : []).concat(rutas));
  if (SALA.on && SALA.tapas) [bub, lat].forEach(l => l.forEach(x => { if (x.et && tapaEtiqueta(x)) x.et = ''; }));   // en pantalla completa, sin etiquetas bajo las cifras
  CAM.bub = bub; CAM.lat = lat;
  const ver = l => CAM.vuela ? [] : CAM.f<1 ? l.map(x => Object.assign({}, x, { symbolSize:x.symbolSize*CAM.f })) : l;
  chart.setOption({ series:[ {id:'bub', data:ver(bub)}, {id:'pts', data:pts}, {id:'cbp', data:enc}, {id:'grp', data:grp}, {id:'lat', data:ver(lat)}, {id:'car', data:car} ] });
  // -- Rótulo acoplado: título, cifra, leyenda y selector "Ver por"
  const quien = (S.sel && S.sel.t!=='p' ? (S.sel.t==='n'?' de ':' en ')+nombreSel() : '')+(F.todo ? ' en '+(S.agr==='c' ? 'cinturones' : 'los CECO') : '')+(F.r ? ' · '+nombreRegion() : '');
  let h;
  if (kc){ const tot = acum(kc,F.ss,nF);
    h = '<b>'+esc(nomInd(kc)+quien)+'</b><span>'+(fin ? 'Periodo completo' : 'Ritmo semanal al '+fechaDia(S.dia-1))+'</span>'+
        '<div class="gr"><span class="num">'+corto(tot)+'</span>'+chispa(semanal(kc,F.ss,nF),88,26,col,semDe(S.dia))+'</div>'+
        (sinEdo(kc) ? '<span class="mini">Círculos y estados de EE. UU.: sectores de la frontera donde la CBP registra los encuentros. No se reparte por O.R.</span>'
          : '<div class="rampa"><span>menos</span><i style="background:linear-gradient(90deg,'+rampa.join(',')+')"></i><span>'+corto(maxE)+'</span></div>'); }
  else h = '<b>Panorama'+esc(quien)+'</b><span>De dónde llegan'+(fin?'':' · al '+fechaDia(S.dia-1))+'. Elige un indicador para colorear los estados.</span>'+
           '<span class="lin"><i style="background:'+t.reg+'"></i>Ingresos (regular)</span><span class="lin"><i style="background:'+t.irr+'"></i>Rescatados (irregular, eventos)</span>'+
           '<span class="nota">Línea: del país al lugar de registro · círculo: tamaño según el total</span>';
  if (pts.length){ const cP = t[cp.tipo==='ing'?'reg':cp.tipo==='rep'?'usa':'irr'];
    h += '<span class="lin"><span style="display:inline-flex;width:14px;height:14px">'+svgPunto(cp.tipo, cP, '#FFFFFF')+'</span>'+NOMBRE_PUNTO[cp.tipo]+'</span>'; }
  if (S.car){ const l = carPeriodo();
    h += '<span class="lin"><span style="display:inline-flex;width:14px;height:14px;color:'+t.irr+'"><svg width="14" height="14" viewBox="0 0 16 16">'+GLIFO_CAR+'</svg></span>'+
         (l.length ? 'Caravanas · '+l.length+' · ≈'+corto(l.reduce((x,c) => x+c.p, 0))+' personas' : 'Sin caravanas en el periodo')+'</span>'; }
  if (S.ind==='cbp' && CBPT) h += '<span class="lin"><i style="background:'+t.usa+';width:9px;height:9px;border-radius:50%"></i>Encuentros CBP · '+corto(enc.reduce((x,y)=>x+y.value[2],0))+'</span>';
  const vp = S.agr!=='e' ? S.agr : S.modoVista==='mundo' ? 'm' : S.modoVista==='mx' ? 'e' : '';   // si el usuario movió el mapa, ninguno de los dos
  h += '<div class="verpor" role="group" aria-label="Vista del mapa">'+[['m','Mundo'],['e','Estado'],['c','Cinturón'],['o','CECO']].map(x=>'<button data-agr="'+x[0]+'" class="'+(vp===x[0]?'on':'')+'" aria-pressed="'+(vp===x[0])+'">'+x[1]+'</button>').join('')+'</div>';
  if (F.n==null) h += '<label class="origen">Origen <select id="region" aria-label="Región de origen"><option value="">todas las regiones</option>'+
    Object.keys(REGIONES).map(r => '<option value="'+r+'"'+(S.region===r?' selected':'')+'>'+REGIONES[r][0]+'</option>').join('')+'</select></label>';
  $('m-tit').innerHTML = h;
}
// Tarjetas al pasar el cursor. Muestran el perfil completo (todos los indicadores con su variación)
// para leer un país, un estado o un punto sin tener que hacer clic.
function variaTxt(d){ const va = variacion(d); return va.ok && Math.abs(va.dl)>=1 ? (va.dl>=0?'▲ ':'▼ ')+Math.abs(va.dl).toFixed(0)+'%' : ''; }
function notaPerfil(k, ss, n){                   // el dato que da contexto a cada indicador
  if (k==='rech'){ const t = rechazoExt(ss,n); return t[1] && t[0]/t[1] >= 0.0005 ? (t[0]/t[1]*100).toFixed(2)+'% de llegadas' : ''; }
  if (k==='resc'){ const r = comp('resc_rei',ss,n); return r[1] ? pct(r[1],r[0]+r[1])+'% reincidentes' : ''; }
  if (k==='can'){ const v = suma(comp('can_nna',ss,n),0,12); return v ? miles(v)+' NNA' : ''; }
  if (k==='ret'){ const v = comp('ret_tipo',ss,n); return v[1] ? pct(v[1],v[0]+v[1])+'% asistido' : ''; }
  if (k==='recib'){ const v = comp('recib_edad',ss,n); return v[1] ? pct(v[1],v[0]+v[1])+'% menores' : ''; }
  return '';
}
function perfil(ss, n, activo, tc, breve){
  const conDelta = !(ss && n!=null), out = [];    // estado × nacionalidad no existe por día: ahí no hay variación
  GRUPOS.forEach(g => {
    let filas = INDS.filter(m => m.g===g[0] && (n==null || m.nat)).map(m => { const v = acum(m.k, ss, n); if (!v) return '';
      const nota = breve ? '' : notaPerfil(m.k, ss, n);
      return '<div class="q'+(m.k===activo?' a':'')+'"><span>'+m.n+(nota?'<small>'+nota+'</small>':'')+'</span><b>'+corto(v)+'</b><em>'+(conDelta ? variaTxt(diario(m.k,{ss:ss,n:n})) : '')+'</em></div>'; }).join('');
    if (g[0]==='reg'){ const dv = Array.isArray(n) ? (ss ? 0 : n.reduce((t,x) => t+((D.docs.nat[x]||[])[0]||0), 0)) : n!=null ? (ss ? 0 : (D.docs.nat[n] || [])[0]) : (ss && ss.length===1 ? D.docs.est[ss[0]] : 0);
      if (dv) filas += '<div class="q"><span>Con documento vigente</span><b>'+corto(dv)+'</b><em></em></div>'; }
    if (filas) out.push((breve ? '' : '<div class="g"><i style="background:'+tc[g[0]]+'"></i>'+g[1]+'</div>')+filas); });
  return out.join('');
}
function soloKpi(k, ss, n, tc, sem, breve){      // tarjeta con un indicador elegido: solo ese dato
  const nota = notaPerfil(k, ss, n), d = (ss && n!=null) ? '' : variaTxt(diario(k,{ss:ss,n:n}));
  return '<span class="v">'+miles(acum(k, ss, n))+'</span>'+((nota || d) ? '<span class="s">'+[nota, d ? d+' '+sufCmp() : ''].filter(Boolean).join(' · ')+'</span>' : '')+
         (breve ? '' : chispa(semanal(k,ss,n),232,30,k==='rech'?tc.arena:tc[IND[k].g],sem));
}
const accion = (txt, may) => { const a = (TACTIL ? 'toca otra vez para ' : 'clic para ')+txt; return may ? a[0].toUpperCase()+a.slice(1) : a; };
// País del mapa → nacionalidad de las bases (los países sin registros no tienen nacionalidad)
const NAT_ISO = {}; D.nats.slice(0, OT).forEach((x,i) => { NAT_ISO[x[1]] = i; });
const NOM_GEO = {}; GEO.features.forEach(f => { if (f.properties.t==='p') NOM_GEO[f.properties.key] = f.properties.nom; });
function natDePais(clave){ const iso = +clave.replace('W_','').slice(2); return NAT_ISO[iso]!=null ? NAT_ISO[iso] : -1; }
function tarjetaPais(clave, cuando){
  const n = natDePais(clave), nom = n>=0 ? D.nats[n][0] : (NOM_GEO[clave.replace('W_','')] || 'País');
  const l = n<0 ? [] : [['ing','Ingresos'],['resc','Rescatados'],['rech','Rechazos']].map(x => [x[1], acum(x[0], null, n)]).filter(x => x[1]>0);
  return '<div class="tt"><b class="h">'+esc(nom)+'</b><span class="s">'+cuando+'</span>'+
    (l.length ? l.map(x => '<div class="r"><span>'+x[0]+'</span><span></span><span class="x">'+miles(x[1])+'</span></div>').join('')+'<span class="f">'+(TACTIL ? 'Toca otra vez' : 'Clic')+' para filtrar por '+esc(nom)+'</span>'
              : '<span class="f">Sin registros en el periodo</span>')+'</div>';
}
function tarjeta(p){
  const F = filtro(), kc = S.ind, fin = alFinal(), sem = semDe(S.dia), breve = $('lz').clientHeight < 430*E;
  const tc = TM[S.tema==='claro' ? 'oscuro' : 'claro'];              // la tarjeta va en el tono contrario al mapa
  const cuando = fin ? 'Periodo completo' : 'Acumulado al '+fechaDia(S.dia-1);
  const pie = txt => breve ? '' : '<span class="f">▲▼ '+textoCmp()+(txt ? ' · '+txt : '')+'</span>';
  const fila = (n,frac,tx,color) => '<div class="r"><span>'+n+'</span><span class="b"><i style="width:'+Math.max(2,Math.min(100,frac*100)).toFixed(0)+'%;background:'+color+'"></i></span><span class="x">'+tx+'</span></div>';
  const dato = (n,tx) => '<div class="r"><span>'+n+'</span><span></span><span class="x">'+tx+'</span></div>';
  if (p.seriesId==='bub' || p.seriesId==='lat'){ const n = p.data.nat, kn = kc && IND[kc].nat ? kc : null;
    return '<div class="tt"><b class="h">'+esc(D.nats[n][0])+'</b><span class="s">'+(kn ? IND[kn].n+' · ' : '')+cuando+(F.ss ? ' · en '+esc(nombreFiltro()) : '')+'</span>'+
      (kn ? soloKpi(kn, F.ss, n, tc, sem, breve) : perfil(F.ss, n, null, tc, breve))+pie(accion('abrir su ficha'))+'</div>'; }
  if (p.componentType==='geo'){
    if (p.name.indexOf('US_')===0 && S.ind==='cbp' && CBPT){ const sec = cbpAhora(F), eu = p.name.slice(3); let v = 0, T = 0; D.cbp.sectores.forEach((P,i) => { T += sec[i].v; if (P.eu===eu) v += sec[i].v; });
      if (v) return '<div class="tt"><b class="h">'+esc(eu)+'</b><span class="s">Encuentros de la CBP · '+cuando+(F.n!=null ? ' · '+esc(D.nats[F.n][0]) : '')+'</span><span class="v">'+miles(v)+'</span><span class="f">'+pct(v, T)+'% de los encuentros en la frontera</span></div>'; }
    if (/^(W_)?P_\d+$/.test(p.name)) return tarjetaPais(p.name, cuando);
    if (p.name.indexOf('MX_')!==0) return '';
    const s = ECLAVE.indexOf(p.name); if (s<0) return '';
    const gru = ['c','o'].map(a => AGR[a].de[s]>=0 ? AGR[a].nombres[AGR[a].de[s]] : null).filter(Boolean).join(' · ');
    const nF = F.nd, top = kc && IND[kc].nat && F.n==null && !breve ? topNats(n => enRegion(n) ? acum(kc,[s],n) : 0, 3) : [], mx = top.length ? top[0][1] : 1;
    return '<div class="tt"><b class="h">'+esc(EST[s])+'</b><span class="s">'+(kc ? IND[kc].n+' · ' : '')+(gru || 'Sin cinturón ni CECO')+' · '+cuando+(F.n!=null ? ' · '+esc(D.nats[F.n][0]) : F.r ? ' · '+nombreRegion() : '')+'</span>'+
      (kc ? soloKpi(kc, [s], IND[kc].nat ? nF : null, tc, sem, breve) : perfil([s], nF, null, tc, breve))+
      (top.length ? '<div class="g">Principales nacionalidades · '+IND[kc].n.toLowerCase()+'</div>'+top.map(r => fila(esc(D.nats[r[0]][0]), r[1]/mx, corto(r[1]), tc[IND[kc].g])).join('') : '')+
      pie(accion('ver todos sus datos'))+'</div>'; }
  if (p.seriesId==='pts'){ const tp = p.data.pTipo, P = listaPuntos(tp)[p.data.pt], col = tc[tp==='ing'?'reg':tp==='rep'?'usa':'irr'];
    const nom = tp==='ing' ? ['Aéreo','Terrestre','Marítimo'][P.t]+' · ingresos' : tp==='rep' ? 'Punto de repatriación' : 'Presentados';
    const extra = tp==='ing' ? '<div class="g">Quién entra por aquí</div>'+P.top.slice(0,3).map(r => fila(esc(typeof r[0]==='number'?D.nats[r[0]][0]:r[0]), r[1]/P.top[0][1], corto(r[1]), col)).join('')+(P.seg?dato('Rechazos en segunda revisión', miles(P.rech)):'')
                : tp==='rep' ? dato('Menores', miles(P.men))+dato('No acompañados', miles(P.na)) : '';
    return '<div class="tt"><b class="h">'+esc(P.n)+'</b><span class="s">'+nom+' · ubicación aproximada</span><span class="v">'+miles(p.data.value[2])+'</span>'+chispa(P.wk,232,30,col,sem)+extra+(SALA.on ? '' : '<span class="f">'+accion('ver su análisis en '+(tp==='rep' ? 'Protección al migrante' : 'Control migratorio'), true)+'</span>')+'</div>'; }
  if (p.seriesId==='car'){
    if (p.data.fin!=null) return tarjetaCaravana(D.caravanas[p.data.fin]);
    const l = p.data.cars.map(j => D.caravanas[j]);
    if (l.length===1) return tarjetaCaravana(l[0]);
    return '<div class="tt"><span class="s">'+esc($('rango') ? $('rango').textContent : '')+'</span><b class="h">Caravanas desde '+esc(lugarCorto(l[0].s))+'</b>'+
      '<span class="v">'+l.length+' <small>caravanas · ≈'+miles(l.reduce((x,c)=>x+c.p,0))+' personas (estimadas)</small></span>'+
      '<div class="cv cab"><span>Día</span><span>Caravana</span><span>Personas</span></div>'+
      l.map(c => '<div class="cv"><span>'+fechaEv(c.f).replace(/ \d{4}$/,'')+'</span><span>'+esc(c.n)+'</span><b>≈'+miles(c.p)+'</b></div>').join('')+
      '<span class="f">Ubicación aproximada</span></div>'; }
  if (p.seriesId==='cbp'){ const P = D.cbp.sectores[p.data.cb], X = cbpAhora(F)[p.data.cb], W = cbpSec(P0, P1, F.nd)[p.data.cb], tot = X.v || 1, top = Object.entries(X.nat).sort((a,b) => b[1]-a[1]).slice(0,3);
    return '<div class="tt"><b class="h">'+esc(P.n)+'</b><span class="s">Encuentros de la CBP · '+esc(P.eu)+(P.mx>=0 ? ', frente a '+esc(EST[P.mx]) : '')+(F.n!=null ? ' · '+esc(D.nats[F.n][0]) : '')+'</span><span class="v">'+miles(X.v)+'</span>'+chispa(W.wk,232,30,tc.usa,sem)+
      (F.n==null ? '<div class="g">Quiénes</div>'+fila('Mexicanos', X.mx/tot, pct(X.mx,tot)+'%', tc.usa)+fila('Otros países', (X.v-X.mx)/tot, pct(X.v-X.mx,tot)+'%', tc.usa) : '')+
      '<div class="g">Agencia</div>'+[['Patrulla Fronteriza (USBP)',0],['Puertos de entrada (OFO)',1],['Citas CBP ONE',2]].filter(x => X.ag[x[1]]).map(x => fila(x[0], X.ag[x[1]]/tot, pct(X.ag[x[1]],tot)+'%', tc.usa)).join('')+
      (breve || F.n!=null || !top.length ? '' : '<div class="g">Principales nacionalidades extranjeras</div>'+top.map(r => fila(esc(D.nats[+r[0]][0]), r[1]/top[0][1], corto(r[1]), tc.usa)).join(''))+
      '<span class="f">'+cuando+' · fuente: CBP</span></div>'; }
  return '';
}
let vuelo = 0;
function volar(c, zr){                          // zr: zoom medido contra el encuadre de México
  if (SALA.on && !SALA.fijo){ const r = encuadreSala(c, zr); c = r[0]; zr = r[1]; } SALA.fijo = false;
  const g = chart.getOption().geo[0], c0 = g.center, z0 = g.zoom, z = zr*KMX();
  cancelAnimationFrame(vuelo);
  if (reducido()){ chart.setOption({geo:{center:c, zoom:z}}); S.zoom = zr; CAM.vuela = false; pintarMapa(); return; }
  let i = 0; const N = 26;
  const paso = () => { i++; const x = i/N, e = x<.5 ? 4*x*x*x : 1-Math.pow(-2*x+2,3)/2;
    chart.setOption({geo:{ center:[c0[0]+(c[0]-c0[0])*e, c0[1]+(c[1]-c0[1])*e], zoom: z0*Math.pow(z/z0,e) }});
    if (i<N) vuelo = requestAnimationFrame(paso); else { S.zoom = zr; if (CAM.vuela) llegar(); else pintarMapa(); } };
  paso();
}
function volarA(sel){
  S.modoVista = 'libre';
  if (sel.t==='e'){ volar(xyEst(sel.i), 2.2); return; }
  if (sel.t==='g'){ volar(xyGrupo(miembros(sel.a,sel.q)), 1.25); return; }
  if (sel.t==='p'){ const P = listaPuntos(sel.tipo)[sel.i]; volar([P.x,P.y], 5); return; }
  const xy = xyNat(sel.i); if (xy) volarConMexico(xy);
}
function herramienta(a){
  const g = chart.getOption().geo[0];
  if (a==='mas'){ S.modoVista = 'libre'; volar(g.center, Math.min(40, g.zoom/KMX()*1.7)); }
  else if (a==='menos'){ S.modoVista = 'libre'; volar(g.center, Math.max(vistaMundo().z*0.6, g.zoom/KMX()/1.7)); }
  else if (a==='mx'){ S.modoVista = 'mx'; volar(VISTA_MX.c, VISTA_MX.z); }
  else if (a==='mundo'){ const v = vistaMundo(); S.modoVista = 'mundo'; volar(v.c, v.z); }
  else if (a==='sala'){ if (SALA.on) cerrarSala(); else abrirSala(); }
  else if (a==='tema'){ S.tema = S.tema==='oscuro'?'claro':'oscuro'; $('mapa').dataset.m = S.tema; rehacerMapa(); }
  else { S[a] = !S[a]; const b = document.querySelector('#m-her [data-a="'+a+'"]'); b.classList.toggle('on', S[a]); b.setAttribute('aria-pressed', S[a]);
    if (a==='car'){ S.carSel = null; pintarTiempo(); }
    pintarMapa(); if (a==='cbp' && S.cbp) acercarSiMundo(); if (a==='car' && S.car) volarCaravanas(); }
}
function rehacerMapa(){ const g = chart.getOption().geo[0], z = g.zoom, c = g.center; COL.act = {}; chart.setOption(opcionBase(), true); chart.setOption({geo:{center:c, zoom:z}}); pintarTodo(); }

// Corredor carretero del sur (ubicación aproximada): las caravanas avanzan por tierra, no en línea recta.
// Tronco: frontera con Guatemala → Tapachula → costa de Chiapas → Istmo; luego, ramal a Oaxaca (190) o a la costa (200).
const TRONCO = [[-92.15,14.68],[-92.26,14.90],[-92.47,15.14],[-92.66,15.32],[-92.90,15.43],[-93.21,15.69],[-93.47,15.90],[-93.75,16.09],[-93.90,16.24],[-94.20,16.29],[-94.35,16.48],[-94.61,16.56],[-94.95,16.55],[-95.03,16.43],[-95.22,16.33]];
const CAMINOS = [ TRONCO.concat([[-95.44,16.44],[-95.70,16.50],[-95.95,16.55],[-96.30,16.78],[-96.72,17.06]]),
                  TRONCO.concat([[-95.20,16.20],[-95.38,16.13],[-95.75,15.97],[-96.13,15.78]]) ];
const RUTAS = {};
function rutaCaravana(j){
  if (RUTAS[j]) return RUTAS[j];
  const c = D.caravanas[j], a = c.sx, b = c.dx, d2 = (p,q) => (p[0]-q[0])*(p[0]-q[0]) + (p[1]-q[1])*(p[1]-q[1]);
  const cerca = (cam, p) => { let m = 0; cam.forEach((x,i) => { if (d2(x,p) < d2(cam[m],p)) m = i; }); return m; };
  let mejor = null;
  CAMINOS.forEach(cam => { const ia = cerca(cam,a), ib = cerca(cam,b), e = d2(cam[ia],a) + d2(cam[ib],b); if (!mejor || e<mejor.e) mejor = {cam:cam, ia:ia, ib:ib, e:e}; });
  let r = [a, b];
  if (mejor && mejor.e < 1.5){ const t = mejor.ia<=mejor.ib ? mejor.cam.slice(mejor.ia, mejor.ib+1) : mejor.cam.slice(mejor.ib, mejor.ia+1).reverse();
    r = [a].concat(t, [b]).filter((p,i,l) => i===0 || d2(p,l[i-1]) > 0.0004); }
  let largo = 0; for (let i=1;i<r.length;i++) largo += km(r[i-1], r[i]);
  return (RUTAS[j] = {p:r, km:largo});
}
// Caravanas: las del periodo elegido, con su día dentro del periodo
const GLIFO_CAR = '<g fill="currentColor"><circle cx="3.6" cy="4.6" r="1.6"/><circle cx="8" cy="4.6" r="1.6"/><circle cx="12.4" cy="4.6" r="1.6"/></g><g stroke="currentColor" stroke-width="1.7" stroke-linecap="round" fill="none"><path d="M3.6 7.4v4.4M8 7.4v4.4M12.4 7.4v4.4M1.5 14h13"/></g>';
const carPeriodo = () => (D.caravanas || []).map((c,j) => ({ j:j, i:indiceDe(c.f), p:c.p })).filter(c => c.i>=0 && c.i<ND);
const nombreCar = c => /^caravana/i.test(c.n) ? c.n : /^sin nombre$/i.test(c.n) ? 'Caravana sin nombre' : 'Caravana «'+c.n+'»';
const lugarCorto = s => String(s).replace(/^Parque Bicentenario,\s*/i,'').split(',')[0];
function km(a, b){ const r = Math.PI/180, x = Math.sin((b[1]-a[1])*r/2), y = Math.sin((b[0]-a[0])*r/2);
  return 12742*Math.asin(Math.sqrt(x*x + Math.cos(a[1]*r)*Math.cos(b[1]*r)*y*y)); }
function tarjetaCaravana(c){
  const kv = (n,tx) => '<div class="kv"><span>'+n+'</span><b>'+tx+'</b></div>', j = D.caravanas.indexOf(c);
  return '<div class="tt"><span class="s">'+fechaISO(c.f)+'</span><b class="h">'+esc(nombreCar(c))+'</b><span class="v">≈'+miles(c.p)+' <small>personas (estimadas)</small></span>'+
    kv('Salida', esc(c.s))+kv('Disolución', c.d ? esc(c.d) : 'sin registro')+
    (c.sx && c.dx ? kv('Recorrido', '≈'+miles(rutaCaravana(j).km)+' km por carretera') : '')+'<span class="f">Ubicación aproximada</span></div>';
}
function cajaCaravanas(l){                      // zona que cubre las caravanas indicadas
  const xs = [], ys = []; l.forEach(c => [c.sx, c.dx].forEach(p => { if (p){ xs.push(p[0]); ys.push(p[1]); } }));
  if (!xs.length) return null;
  const x0 = Math.min.apply(null,xs), x1 = Math.max.apply(null,xs), y0 = Math.min.apply(null,ys), y1 = Math.max.apply(null,ys);
  return { c:[(x0+x1)/2, (y0+y1)/2], z:Math.min(9, zoomPara(Math.max(4, (x1-x0)*1.9), Math.max(3, (y1-y0)*2.4))) };
}
function volarCaravanas(){
  const l = carPeriodo().map(c => D.caravanas[c.j]), v = cajaCaravanas(l); if (!v) return;
  S.modoVista = 'libre'; volar(v.c, v.z); mostrarSalida(1000);
}
function mostrarSalida(ms){                      // al llegar, se abre la tarjeta de la salida principal
  setTimeout(() => { const o = chart.getOption(), si = o.series.findIndex(x => x.id==='car'); if (si<0 || !o.series[si].data.length) return;
    let mejor = 0; o.series[si].data.forEach((d,i) => { if (d.cars && d.cars.length > (o.series[si].data[mejor].cars||[]).length) mejor = i; });
    chart.dispatchAction({ type:'showTip', seriesIndex:si, dataIndex:mejor }); }, ms);
}
function verCaravana(j){                         // desde "Lo que cambió": activa la capa y va a esa caravana
  const c = D.caravanas[j];
  if (!S.car){ S.car = true; const b = document.querySelector('#m-her [data-a="car"]'); b.classList.add('on'); b.setAttribute('aria-pressed', true); }
  S.carSel = j; S.dia = ND; pintarTodo();
  const v = cajaCaravanas([c]); if (v){ S.modoVista = 'libre'; volar(v.c, v.z); }
  setTimeout(() => { const o = chart.getOption(), si = o.series.findIndex(x => x.id==='car'); if (si<0) return;
    const di = o.series[si].data.findIndex(d => d.fin===j || (d.cars && d.cars.indexOf(j)>=0 && !c.dx));
    if (di>=0) chart.dispatchAction({ type:'showTip', seriesIndex:si, dataIndex:di }); }, 1000);
}

/* ==== [8] FLUJOS ANIMADOS Y TRANSICIÓN DE COLOR ==================== */
// Los flujos se dibujan en un lienzo propio, cuadro por cuadro, con la posición real del mapa:
// por eso siguen al mapa al moverlo y aparecen y desaparecen de forma gradual.
const FL = {};                                  // flujos vivos: id → {a,b,c, w, wm, al, alm}
// Vuelo hacia lo que se buscó: primero se apaga lo que hay, la cámara llega y de ahí salen las líneas y crecen los círculos
const CAM = { vuela:false, llega:0, vis:1, f:1, bub:[], lat:[] };
function prepararVuelo(){ if (reducido()) return; CAM.vuela = true; CAM.llega = 0; }
function llegar(){ if (!CAM.vuela) return; CAM.vuela = false; CAM.llega = performance.now() + 120; CAM.vis = 1; CAM.f = 0; pintarMapa(); crecerCirculos(); }
function crecerCirculos(){ const t0 = performance.now() + 120, dur = 650;
  const paso = ahora => { const e = Math.max(0, Math.min(1, (ahora - t0)/dur)), f = 1 - Math.pow(1-e, 3); CAM.f = f;
    const esc = l => l.map(x => Object.assign({}, x, { symbolSize: x.symbolSize*f }));
    chart.setOption({ series:[ {id:'bub', data:esc(CAM.bub)}, {id:'lat', data:esc(CAM.lat)} ] }, {lazyUpdate:true, silent:true});
    if (e<1) requestAnimationFrame(paso); else CAM.f = 1; };
  requestAnimationFrame(paso); }
// Parte de la curva entre el origen y la fracción p (para que la línea se trace desde el origen)
function subCurva(pa, cx, cy, pb, p){ const q = 1-p, mx = pa[0]*q + cx*p, my = pa[1]*q + cy*p, ex = q*q*pa[0] + 2*q*p*cx + p*p*pb[0], ey = q*q*pa[1] + 2*q*p*cy + p*p*pb[1]; return [mx, my, ex, ey]; }
function ponerFlujos(lista){
  Object.keys(FL).forEach(k => { FL[k].alm = 0; });
  lista.forEach(f => { const x = FL[f.id];
    if (x){ x.a = f.a; x.b = f.b; x.c = f.c; x.wm = f.w; x.alm = 1; x.car = f.car; x.sel = f.sel; x.ruta = f.ruta; } else FL[f.id] = { a:f.a, b:f.b, c:f.c, w:f.w, wm:f.w, al:0, alm:1, car:f.car, sel:f.sel, ruta:f.ruta, t0:performance.now() - Math.random()*4000 }; });
}
let ctxF = null, cuadro = 0;
function ajustarLienzo(){ const cv = $('flujo'), r = $('lz'), dpr = Math.min(window.devicePixelRatio||1, 2);
  cv.width = Math.round(r.clientWidth*dpr); cv.height = Math.round(r.clientHeight*dpr); ctxF = cv.getContext('2d'); ctxF.setTransform(dpr,0,0,dpr,0,0); }
function animar(ahora){
  requestAnimationFrame(animar);
  if (document.hidden || S.vista!=='pulso' || !chart || !ctxF) return;
  cuadro++;
  // -- transición de color de los estados
  if (COL.sucio && cuadro%2===0){
    const t = TM[S.tema], base = hex(t.mx); let mov = false;
    ECLAVE.forEach(k => { const m = COL.meta[k] || base; let a = COL.act[k]; if (!a){ a = COL.act[k] = base.slice(); }
      for (let j=0;j<3;j++){ const d = m[j]-a[j]; if (Math.abs(d)>0.6){ a[j] += d*0.22; mov = true; } else a[j] = m[j]; } });
    chart.setOption({ geo:{ regions:regiones() } }, {lazyUpdate:true, silent:true});
    if (!mov) COL.sucio = false;
  }
  // -- flujos
  const w = $('lz').clientWidth, h = $('lz').clientHeight, quieto = reducido();
  ctxF.clearRect(0,0,w,h);
  CAM.vis = CAM.vuela ? Math.max(0, CAM.vis - 0.16) : Math.min(1, CAM.vis + 0.1);
  if (CAM.vis<=0.01){ moverFicha(); return; }
  let orden = 0; const llega = CAM.llega, recien = llega && ahora < llega + 1800;
  if (llega && !recien) CAM.llega = 0;
  Object.keys(FL).forEach(id => { const f = FL[id]; if (recien && f.alm===0){ f.al = 0; delete FL[id]; return; }   // lo de antes del vuelo ya no se dibuja
    const pr = recien ? Math.max(0, Math.min(1, (ahora - llega - (orden++)*55)/900)) : 1, ep = 1 - Math.pow(1-pr, 3);
    f.al += (f.alm-f.al)*0.07; f.w += (f.wm-f.w)*0.1;
    if (f.alm===0 && f.al<0.01){ delete FL[id]; return; }
    const pa = chart.convertToPixel('geo', f.a), pb = chart.convertToPixel('geo', f.b); if (!pa || !pb) return;
    const dx = pb[0]-pa[0], dy = pb[1]-pa[1], len = Math.hypot(dx,dy); if (len<6) return;
    let nx = -dy/len, ny = dx/len; if (ny>0){ nx = -nx; ny = -ny; }            // la curva siempre se arquea hacia arriba
    if (f.car){ caminata(f, pa, pb, dx, dy, len, nx, ny, ahora, quieto); return; }
    const cx = (pa[0]+pb[0])/2 + nx*len*0.2, cy = (pa[1]+pb[1])/2 + ny*len*0.2, gw = f.w*E;
    ctxF.lineCap = 'round'; ctxF.strokeStyle = f.c; ctxF.fillStyle = f.c;
    if (ep<=0) return;
    if (ep<1){ const sc = subCurva(pa, cx, cy, pb, ep); ctxF.globalAlpha = 0.45*f.al*CAM.vis; ctxF.lineWidth = gw; ctxF.beginPath(); ctxF.moveTo(pa[0],pa[1]); ctxF.quadraticCurveTo(sc[0],sc[1],sc[2],sc[3]); ctxF.stroke();
      ctxF.globalAlpha = f.al*CAM.vis; ctxF.beginPath(); ctxF.arc(sc[2], sc[3], Math.max(2*E, gw*0.9), 0, 6.283); ctxF.fill(); return; }   // la punta avanza hacia el destino
    ctxF.globalAlpha = 0.20*f.al*CAM.vis; ctxF.lineWidth = gw; ctxF.beginPath(); ctxF.moveTo(pa[0],pa[1]); ctxF.quadraticCurveTo(cx,cy,pb[0],pb[1]); ctxF.stroke();
    // partículas que viajan del origen al destino, a velocidad constante
    const n = Math.max(2, Math.min(14, Math.round(len/(70*E)))), fase = quieto ? 0.5 : (ahora*0.045*E/len) % (1/n);
    for (let i=0;i<n;i++){ const p = fase + i/n; if (p>1) continue; const q = 1-p;
      const x = q*q*pa[0] + 2*q*p*cx + p*p*pb[0], y = q*q*pa[1] + 2*q*p*cy + p*p*pb[1];
      ctxF.globalAlpha = f.al*CAM.vis*Math.pow(Math.sin(Math.PI*p), 0.55)*0.95*(recien ? Math.min(1, (ahora - llega - 900)/600) : 1);
      if (ctxF.globalAlpha<=0) continue;
      ctxF.beginPath(); ctxF.arc(x, y, Math.max(1.5*E, gw*0.62), 0, 6.283); ctxF.fill(); }
    // punta discreta en el destino
    ctxF.globalAlpha = 0.5*f.al*CAM.vis; ctxF.beginPath(); ctxF.arc(pb[0], pb[1], Math.max(2*E, gw*0.8), 0, 6.283); ctxF.fill();
  });
  ctxF.globalAlpha = 1;
  moverFicha();
}
// Caravana: el contingente avanza por la carretera como un grupo compacto que camina;
// lo ya recorrido queda marcado y lo que falta se ve punteado. Al llegar, se detiene un momento y vuelve a salir.
function caminata(f, pa, pb, dx, dy, len, nx, ny, ahora, quieto){
  const px = f.ruta.map(q => chart.convertToPixel('geo', q)); if (px.some(q => !q)) return;
  const ac = [0]; for (let i=1;i<px.length;i++) ac.push(ac[i-1] + Math.hypot(px[i][0]-px[i-1][0], px[i][1]-px[i-1][1]));
  const L = ac[ac.length-1]; if (L<8) return;
  const en = d => { d = Math.max(0, Math.min(L, d)); let i = 1; while (i<ac.length-1 && ac[i]<d) i++;
    const u = (d-ac[i-1])/Math.max(1e-6, ac[i]-ac[i-1]), x = px[i-1][0]+(px[i][0]-px[i-1][0])*u, y = px[i-1][1]+(px[i][1]-px[i-1][1])*u, l = Math.max(1e-6, ac[i]-ac[i-1]);
    return [x, y, -(px[i][1]-px[i-1][1])/l, (px[i][0]-px[i-1][0])/l]; };
  const vida = 11000, ciclo = quieto ? 1 : Math.min(1, ((ahora - f.t0) % vida) / (vida*0.82)), cab = L*ciclo;
  const trazo = (d0, d1) => { ctxF.beginPath(); let p = en(d0); ctxF.moveTo(p[0],p[1]); for (let i=1;i<ac.length;i++) if (ac[i]>d0 && ac[i]<d1) ctxF.lineTo(px[i][0],px[i][1]); p = en(d1); ctxF.lineTo(p[0],p[1]); ctxF.stroke(); };
  ctxF.strokeStyle = f.c; ctxF.fillStyle = f.c; ctxF.lineCap = 'round'; ctxF.lineJoin = 'round';
  ctxF.globalAlpha = 0.35*f.al; ctxF.lineWidth = 1.5*E; ctxF.setLineDash([2.5*E, 4*E]); trazo(cab, L); ctxF.setLineDash([]);
  ctxF.globalAlpha = (f.sel ? 0.8 : 0.55)*f.al; ctxF.lineWidth = (f.sel ? 3 : 2.2)*E; if (cab>1) trazo(0, cab);
  // el contingente: personas repartidas a lo largo y a lo ancho del camino, con un leve vaivén al caminar
  const gente = Math.max(8, Math.min(34, Math.round(f.car/45))), largo = Math.min(L*0.22, (14 + gente*0.9)*E);
  for (let i=0;i<gente;i++){ const r1 = Math.abs(Math.sin(i*12.9898)*43758.5) % 1, r2 = Math.abs(Math.sin(i*78.233)*12543.1) % 1;
    const d = cab - r1*largo; if (d<0) continue;
    const q = en(d), bam = quieto ? 0 : Math.sin(ahora*0.009 + i*1.7)*0.7*E, lado = (r2-0.5)*7*E*(0.6 + 0.4*Math.sin(r1*6)) + bam;
    ctxF.globalAlpha = f.al*(0.55 + 0.45*(1-r1));
    ctxF.beginPath(); ctxF.arc(q[0] + q[2]*lado, q[1] + q[3]*lado, (1.45 + 0.5*r2)*E, 0, 6.283); ctxF.fill(); }
}

/* ==== [9] BARRA DE TIEMPO Y REPRODUCCIÓN ========================== */
// Barras, promedio, cursor y meses comparten una sola escala X: siempre quedan alineados.
// El cursor avanza día por día (barra por barra) y entre días se desliza de forma continua.
let Wt = 300;
let TT = null;
function tipTiempo(e){
  const tip = $('t-tip'); if (!tip || !TT) return; if (!e){ tip.hidden = true; return; }
  const sv = $('tgraf'), r = sv.getBoundingClientRect(), W = sv.viewBox.baseVal.width || r.width, i = Math.floor((e.clientX-r.left)/r.width*W/TT.pw);
  if (i<0 || i>=ND){ tip.hidden = true; return; }
  tip.innerHTML = '<b>'+fechaLarga(i)+'</b>'+TT.capas.map(c => '<span><i style="background:'+c.c+'"></i>'+IND[c.k].n+': <b>'+(i<c.U ? miles(c.d[i]) : 'pendiente')+'</b></span>').join('');
  tip.hidden = false; const p = sv.parentNode.getBoundingClientRect(), w = tip.offsetWidth;
  tip.style.left = Math.max(0, Math.min(e.clientX-p.left+12, p.width-w))+'px'; tip.style.top = '-6px';
}
function pintarTiempo(){
  // Sin indicador: ingresos hacia arriba y rescatados hacia abajo (espejo), cada uno con su propia escala.
  // Con indicador: solo esa serie. Debajo, la tira de vacaciones; arriba, los eventos.
  const sv = $('tgraf'), W = Wt = Math.max(200, sv.clientWidth), H = 100, F = filtro(), t = TM[S.tema], pw = W/ND, dos = !S.ind;
  const serie = k => diario(k, IND[k].nat || F.nd==null ? F : {ss:F.ss, n:null, nd:null});
  const capas = dos ? [['ing',46,36,1],['resc',48,28,-1]] : [[S.ind,76,60,1]], TIRA = 84;
  let h = '<defs><pattern id="pend" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="5" stroke="'+t.tinta+'" stroke-opacity=".2" stroke-width="2"/></pattern></defs>';
  const cadaCuanto = Math.ceil(MESES_INI.length*46/W);                 // si hay muchos meses, se rotula uno de cada tantos
  MESES_INI.forEach((m,i) => { const x = (m[0]*pw).toFixed(1); h += '<line x1="'+x+'" y1="8" x2="'+x+'" y2="'+(TIRA+4)+'" stroke="'+t.tinta+'" stroke-opacity=".12"/>'+(i%cadaCuanto ? '' : '<text x="'+(m[0]*pw+4).toFixed(1)+'" y="'+(H-2)+'" font-size="11" fill="'+t.tinta+'" fill-opacity=".7" font-family="Barlow, sans-serif">'+m[1]+'</text>'); });
  const tot = {}; TT = { pw:pw, capas:[] };
  capas.forEach(cp => { const k = cp[0], b = cp[1], al = cp[2], dir = cp[3], d = serie(k), mx = Math.max.apply(null,d) || 1, c = t[IND[k].g], U = finDatos(k);
    TT.capas.push({ k:k, d:d, c:c, U:U });
    tot[k] = suma(d,0,S.dia);
    d.forEach((v,i) => { const bh = Math.max(0.6, v/mx*al); h += '<rect x="'+(i*pw+0.5).toFixed(1)+'" y="'+(dir>0 ? b-bh : b).toFixed(1)+'" width="'+Math.max(1,pw-1.5).toFixed(1)+'" height="'+bh.toFixed(1)+'" rx="1" fill="'+c+'" fill-opacity="'+(i<S.dia?0.7:0.2)+'"/>'; });
    const ma = []; for (let i=0;i<Math.min(S.dia,U);i++){ const a = Math.max(0,i-6); ma.push(((i+0.5)*pw).toFixed(1)+','+(b - dir*suma(d,a,i+1)/(i+1-a)/mx*al).toFixed(1)); }
    if (ma.length>1) h += '<polyline points="'+ma.join(' ')+'" fill="none" stroke="'+t.tinta+'" stroke-width="1.6" stroke-linejoin="round" stroke-opacity=".85"/>';
    if (U<ND) h += '<rect x="'+(U*pw).toFixed(1)+'" y="'+(dir>0 ? b-al : b)+'" width="'+((ND-U)*pw).toFixed(1)+'" height="'+al+'" fill="url(#pend)"><title>'+IND[k].n+' pendiente: la base llega al '+fechaLarga(U-1)+'</title></rect>';
  });
  if (dos) h += '<line x1="0" y1="47" x2="'+W+'" y2="47" stroke="'+t.tinta+'" stroke-opacity=".35"/>';
  temporadas().forEach(x => { const a = Math.max(0, indiceDe(x[0])), b = Math.min(ND, indiceDe(x[1])+1); if (b<=a) return;       // vacaciones SEP y fiestas
    h += '<rect x="'+(a*pw).toFixed(1)+'" y="'+TIRA+'" width="'+Math.max(2,(b-a)*pw).toFixed(1)+'" height="4" rx="2" fill="'+COLOR_TEMP[x[3]]+'"><title>'+esc(x[2])+'</title></rect>'; });
  if (S.car){ const yb = dos ? 76.5 : 76.5; carPeriodo().forEach(c => { const C = D.caravanas[c.j], x = (c.i+0.5)*pw, a = 3.5 + 3*Math.sqrt(Math.min(1, C.p/2000));
    h += '<path d="M'+x.toFixed(1)+' '+yb+'l'+a.toFixed(1)+' 6.5h'+(-2*a).toFixed(1)+'z" fill="'+t.irr+'" stroke="'+t.halo+'" stroke-width="1"><title>'+fechaISO(C.f)+' · '+esc(nombreCar(C))+' · ≈'+miles(C.p)+' personas</title></path>'; }); }
  CTX.reg.concat(F.n!=null ? (CTX[D.nats[F.n][1]] || []) : []).filter(e => e.f.length===10 && indiceDe(e.f)>=0 && indiceDe(e.f)<ND).forEach(e => { const x = (indiceDe(e.f)+0.5)*pw;
    h += '<g><title>'+esc(e.que)+'</title><line x1="'+x.toFixed(1)+'" y1="5" x2="'+x.toFixed(1)+'" y2="'+TIRA+'" stroke="'+t.tinta+'" stroke-opacity=".6" stroke-dasharray="2 3"/><circle cx="'+x.toFixed(1)+'" cy="5" r="3.5" fill="'+CATS[e.c][1]+'" stroke="'+t.halo+'" stroke-width="1.5"/>'+
         (dos ? '' : '<text x="'+(x+7).toFixed(1)+'" y="9" font-size="10.5" fill="'+t.tinta+'" fill-opacity=".8" font-family="Barlow, sans-serif">'+esc(e.que.replace('presidencial ','').slice(0,40))+'</text>')+'</g>'; });
  h += '<g id="cursor"><line x1="0" y1="0" x2="0" y2="'+(TIRA+4)+'" stroke="'+t.tinta+'" stroke-width="2"/><circle cx="0" cy="'+(TIRA+2)+'" r="5.5" fill="'+t.tinta+'" stroke="'+t.mar+'" stroke-width="2"/></g>';
  sv.setAttribute('viewBox','0 0 '+W+' '+H); sv.innerHTML = h; moverCursor(S.play ? S.t : S.dia);
  sv.setAttribute('aria-valuenow', S.dia); sv.setAttribute('aria-valuetext','al '+fechaDia(S.dia-1));
  const cua = c => '<i class="t-c" style="background:'+c+'"></i>';
  $('t-tit').innerHTML = infoP('Registros por día en el periodo. Sin un indicador activo se muestran ingresos (hacia arriba) y rescatados (hacia abajo), cada uno con su escala. La línea es el promedio de 7 días y la franja dorada, las vacaciones SEP.')+(dos ? cua(t.reg)+'<b>Ingresos</b> '+corto(tot.ing)+' &nbsp; '+cua(t.irr)+'<b>Rescatados</b> '+corto(tot.resc)+' <span class="t-n">por día · cada serie con su escala</span>'
                             : cua(t[IND[S.ind].g])+'<b>'+IND[S.ind].n+'</b> '+corto(tot[S.ind])+' <span class="t-n">por día</span>'+(S.dia<ND || S.play ? ' <span class="t-n">· estados: promedio de 7 días</span>' : ''));
  $('t-ley').innerHTML = leyendaTemporadas()+'<svg width="20" height="6" viewBox="0 0 20 6" style="vertical-align:middle"><line x1="0" y1="3" x2="20" y2="3" stroke="'+t.tinta+'" stroke-width="2"/></svg> promedio de 7 días';
  $('play').innerHTML = S.play ? '<svg width="14" height="14" viewBox="0 0 16 16"><path d="M3.5 2.5h3v11h-3zM9.5 2.5h3v11h-3z" fill="currentColor"/></svg>' : '<svg width="14" height="14" viewBox="0 0 16 16"><path d="M4.5 2.5v11l9-5.5z" fill="currentColor"/></svg>';
  $('play').setAttribute('aria-label', S.play ? 'Pausar' : 'Reproducir el periodo');
  $('vertodo').hidden = S.dia>=ND && !S.play;                // regresa al periodo completo sin esperar a que termine
}
// Colores de las temporadas: vacaciones de la SEP en dorado; fechas de EE. UU. en salvia
const COLOR_TEMP = { sep:'#BDB58D', eu:'#778E88' };
// Leyenda con el nombre de cada temporada que cae en el periodo visible (no una etiqueta genérica)
function temporadasEnPeriodo(){ const vistos = {}, l = [];
  temporadas().forEach(x => { const a = Math.max(0, indiceDe(x[0])), b = Math.min(ND, indiceDe(x[1])+1); if (b<=a || vistos[x[4]]) return; vistos[x[4]] = 1; l.push([x[4], x[3]]); });
  return l; }
function leyendaTemporadas(){ return temporadasEnPeriodo().map(x => '<span style="display:inline-block;width:14px;height:4px;border-radius:2px;background:'+COLOR_TEMP[x[1]]+';margin-right:4px;vertical-align:middle"></span>'+esc(x[0])+' · ').join(''); }
// Temporadas que tocan el periodo: vacaciones SEP (invierno, Semana Santa, verano), Navidad y Acción de Gracias (EE. UU.)
// Del catálogo único (js/temporadas.js): las fechas de EE. UU. solo con un indicador «Desde EE. UU.»
function temporadas(){ const eu = !!(S.ind && IND[S.ind] && IND[S.ind].g==='usa');
  return (window.IANAMI_FECHAS ? window.IANAMI_FECHAS(eu) : []).map(x => [x[0], x[1], x[2]+(x[4] ? ' · ciclo '+x[4] : ''), x[3]==='eu' ? 'eu' : 'sep', x[2]]); }
function moverCursor(d){ const c = document.getElementById('cursor'); if (c) c.setAttribute('transform','translate('+Math.min(Wt-1, d*Wt/ND).toFixed(2)+',0)');
  const sc = document.getElementById('sl-cur'); if (sc){ const w = $('sl-tg').viewBox.baseVal.width || 1; sc.setAttribute('transform','translate('+Math.min(w-1, d*w/ND).toFixed(2)+',0)'); } }
function fijarDia(d){ d = Math.max(1, Math.min(ND, Math.round(d))); if (d===S.dia) return; S.dia = d; S.t = d; pintarTodo(true); }
function diaDesdeX(ev){ const r = $('tgraf').getBoundingClientRect(); return (ev.clientX-r.left)/r.width*ND + 0.5; }
let ultimo = 0;
function reproducir(){
  if (S.play){ detener(); return; }
  S.play = true; if (S.dia>=ND){ S.dia = 1; } S.t = S.dia; ultimo = performance.now(); pintarTodo(true); requestAnimationFrame(cuadroPlay);
}
function cuadroPlay(ahora){
  if (!S.play) return;
  S.t = Math.min(ND, S.t + (ahora-ultimo)/1000*velocidad()); ultimo = ahora; moverCursor(S.t);
  const d = Math.floor(S.t); if (d!==S.dia){ S.dia = d; pintarTodo(true); }
  if (S.t>=ND){ detener(); return; }
  requestAnimationFrame(cuadroPlay);
}
function detener(){ S.play = false; S.t = S.dia; pintarTodo(true); }

/* ==== [10] COLUMNA DE ANÁLISIS Y FRANJA DE CAJAS =================== */
function pintarDocs(){
  const dv = D.docs, F = filtro(); let tot = dv.total, sub = 'en todo el país', hm = [dv.h, dv.m], barra = '';
  if (F.ss){ tot = F.ss.reduce((x,s)=>x+dv.est[s],0); sub = 'en '+nombreFiltro(); hm = null; }
  else if (F.n!=null){ const r = dv.nat[F.n]; tot = r ? r[0] : null; sub = 'de '+D.nats[F.n][0]; hm = r ? [r[1], r[2]] : null; }
  else if (F.r){ tot = 0; hm = [0,0]; F.r.forEach(x => { const r = dv.nat[x]; if (r){ tot += r[0]; hm[0] += r[1]; hm[1] += r[2]; } }); sub = 'de '+nombreRegion(); }
  if (!F.ss && F.nd==null){
    const cs = [cssv('--ink'), cssv('--usa'), cssv('--reg'), cssv('--ink3')], t = dv.tipos, otras = t.slice(3).reduce((x,y)=>x+y[1],0);
    const seg = t.length>=3 && dv.total>0 ? [t[0], t[1], t[2], ['Otras',otras]] : [];
    if (seg.length) barra = '<div class="apil">'+seg.map((x,i)=>'<span style="width:'+(x[1]/dv.total*100).toFixed(1)+'%;background:'+cs[i]+'" title="'+x[0]+': '+miles(x[1])+'"></span>').join('')+'</div>'+
            '<div class="ley">'+seg.map((x,i)=>'<span><i style="background:'+cs[i]+'"></i>'+x[0]+' '+pct(x[1],dv.total)+'%</span>').join('')+'</div>';
  }
  $('docs').innerHTML = '<h2><span>Extranjeros con documento vigente</span>'+infoP('Personas extranjeras con un documento migratorio vigente (residencia o visitante) al último corte semanal de la DGRAM. Es una foto al día del corte: por eso solo aparece cuando consultas un periodo que llega a hoy.')+'</h2>'+
    '<div class="docs-f"><span class="num">'+(tot==null?'s/d':miles(tot))+'</span><span class="mini">'+esc(sub)+(hm?' · '+pct(hm[1],hm[0]+hm[1])+'% mujeres':'')+'</span></div>'+barra+
    '<span class="mini">Corte: '+fechaISO(dv.corte)+'</span>';
}
function pintarAnalisis(){
  const F = filtro(); AVISOS = analizar(F).filter(a => !S.ind || a.k===S.ind || (a.t==='car' && S.ind==='resc'));   // con un indicador elegido, solo sus cambios
  const quien = (S.ind ? IND[S.ind].n+' · ' : '')+(nombreFiltro() || 'todo el país');
  $('analisis').innerHTML = '<h2><span>Lo que cambió</span>'+infoP('Cambios recientes que conviene atender: indicadores que subieron o bajaron más de lo normal, nacionalidades o estados que se movieron y caravanas. La comparación es contra el periodo de «Comparar con». No aparece lo que es de temporada: si hace un año en estas mismas fechas pasó lo mismo, no es noticia. Solo aparece cuando el periodo llega a hoy.')+(AVISOS.length ? '<small class="av-n">'+AVISOS.length+' hallazgos</small>' : '')+'</h2><span class="mini">'+esc(quien)+' · '+textoCmp()+'</span>'+
    (AVISOS.length ? '<div class="avisos-lista">'+AVISOS.map(filaAviso).join('')+'</div>' : '<span class="mini">Sin cambios relevantes con este filtro.</span>');
}
const barrasNat = (l, color) => { const mx = l.length?l[0][1]:1; return l.map(r => '<button class="barra" data-n="'+r[0]+'"><span>'+(r[2] ? r[2]+'.º ' : '')+esc(D.nats[r[0]][0])+'</span><span class="b"><i style="width:'+(r[1]/mx*100).toFixed(1)+'%;background:'+color+'"></i></span><span class="x">'+corto(r[1])+'</span></button>').join(''); };
function htmlBreve(n){                          // datos clave de una nacionalidad
  const rr = comp('resc_rei',null,n), ts = comp('tram_se',null,n), H = suma(ts,0,8), M = suma(ts,8,16), nn = comp('can_nna',null,n), nna = suma(nn,0,12), na = nn.reduce((t,x,i)=>t+(i%3===1?x:0),0);
  const tr = rechazoExt(null,n);
  return (rr[0]+rr[1] ? '<span class="mini"><b>'+pct(rr[1],rr[0]+rr[1])+' de cada 100</b> rescates son de reincidentes.</span>' : '')+
    (tr[1] ? '<span class="mini"><b>'+(tr[0]/tr[1]*100).toFixed(2)+'%</b> de los extranjeros que llegan por aire o tierra son rechazados.</span>' : '')+
    (H+M ? '<span class="mini"><b>'+pct(M,H+M)+'%</b> de sus trámites son de mujeres.</span>' : '')+
    (nna ? '<span class="mini"><b>'+miles(nna)+'</b> niñas, niños y adolescentes canalizados; '+miles(na)+' no acompañados.</span>' : '');
}
function htmlTops(F, k){
  const f = n => enRegion(n) ? acum(k,F.ss,n) : 0, uno = S.sel && S.sel.t==='n' ? S.sel.i : -1; let l = topNats(f, TOP);
  if (uno>=0 && f(uno)>0 && !l.some(r => r[0]===uno)){ const todos = topNats(f, D.nats.length), lugar = todos.findIndex(r => r[0]===uno); l = l.slice(0, TOP-1).concat([[uno, f(uno), lugar+1]]); }
  else if (uno>=0) l = l.map((r, i) => r[0]===uno ? [r[0], r[1], i+1] : r);   // la elegida lleva su lugar, como en estados
  return '<div class="caja"><h2><span>Principales nacionalidades · '+nomInd(k)+'</span>'+infoP('Las nacionalidades con más registros de este indicador en el periodo, y su parte del total.')+(S.region ? '<small>'+REGIONES[S.region][0]+'</small>' : '')+'</h2>'+
    '<span class="mini">'+(S.dia<ND ? 'Acumulado al '+fechaDia(S.dia-1) : 'Periodo completo')+'</span>'+
    (barrasNat(l, colG(IND[k].g)) || '<span class="mini">Sin registros.</span>')+'</div>';
}
// Reparto en una barra continua, con cifra y porcentaje de cada parte
function reparto(tit, arr, grande){
  const tot = arr.reduce((x,y)=>x+y[1],0); if (!tot) return '';
  return '<div class="rep'+(grande?' g':'')+'"><span class="mini"><b>'+tit+'</b></span>'+(grande ? '<div class="rep-n">'+arr.map(r => '<span><b class="num">'+pct(r[1],tot)+'%</b>'+r[0]+' · '+miles(r[1])+'</span>').join('')+'</div>' : '')+
    '<div class="rep-b">'+arr.map(r => r[1] ? '<i style="flex:'+r[1]+';background:'+r[2]+'" title="'+r[0]+': '+miles(r[1])+'"></i>' : '').join('')+'</div>'+
    (grande ? '' : '<div class="ley">'+arr.map(r => '<span><i style="background:'+r[2]+'"></i>'+r[0]+' '+pct(r[1],tot)+'%</span>').join('')+'</div>')+'</div>';
}
// Dos categorías: cuadrícula de 100 (de cada 100, cuántos), cifras y el reparto mes a mes
function anillo(kc, s, n, cats){
  const v = comp(kc,s,n), a0 = v[cats[0][1]], a1 = v[cats[1][1]], tot = a0 + a1; if (!tot) return '';
  const q = Math.round(a0/tot*100), celdas = []; for (let i=0;i<100;i++) celdas.push('<i style="background:'+(i<q ? cats[0][2] : cats[1][2])+'"></i>');
  const frase = '<p class="cien-f">De cada <b>100</b>, <b style="color:'+cats[0][2]+'">'+q+'</b> '+cats[0][3]+' y <b>'+(100-q)+'</b> '+cats[1][3]+'.</p>';
  const cifras = cats.map(x => '<div class="cien-l"><i style="background:'+x[2]+'"></i><span>'+x[0]+'</span><b class="num">'+miles(v[x[1]])+'</b></div>').join('')+'<div class="cien-l t"><span>Total</span><b class="num">'+miles(tot)+'</b></div>';
  // mes a mes, dentro del periodo
  const meses = {}, ss = s ? new Set(s) : null, nn = n==null ? null : new Set(Array.isArray(n) ? n : [n]), a = D.comp[kc];
  for (let i=0;i<a.length;i+=5){ const f = fraccionMes(a[i]); if (!f || (ss && !ss.has(a[i+1])) || (nn && !nn.has(a[i+2]))) continue;
    const m = meses[a[i]] = meses[a[i]] || [0,0]; m[a[i+3]] += a[i+4]*f; }
  const ms = Object.keys(meses).map(Number).sort((x,y)=>x-y).filter(m => meses[m][0]+meses[m][1] > 0), rot = ms.length<=12;
  const mes = ms.length>1 ? '<div class="cien-m"><span class="mini"><b>Mes a mes</b> · % '+cats[0][3]+'</span><div class="cien-c">'+ms.map(m => { const x = meses[m], t = x[0]+x[1], p0 = x[cats[0][1]]/t, f = new Date(INICIO0.getFullYear(), INICIO0.getMonth()+m, 1);
      return '<div title="'+MES12[f.getMonth()]+' '+f.getFullYear()+' · '+cats[0][0]+': '+miles(x[cats[0][1]])+' de '+miles(t)+'">'+(rot ? '<span>'+Math.round(p0*100)+'%</span>' : '')+
        '<i><b style="height:'+(p0*100).toFixed(1)+'%;background:'+cats[0][2]+'"></b><b style="height:'+((1-p0)*100).toFixed(1)+'%;background:'+cats[1][2]+'"></b></i><small>'+MES12[f.getMonth()]+'</small></div>'; }).join('')+'</div></div>' : '';
  return '<div class="cien"><div class="cien-g" role="img" aria-label="'+q+' de cada 100: '+cats[0][0]+'">'+celdas.join('')+'</div><div class="cien-d">'+frase+cifras+'</div></div>'+mes;
}
const TOP = 8;                                  // renglones de las listas de abajo
const nomEst = i => String(D.estaciones[i]).replace(/^E[MP] /,'');
// Cuarta tarjeta: nacionalidades de una categoría (vía de ingreso, primera vez o reincidente, estación)
function cajaCruce(k, F){
  const c = colG(IND[k].g), q = S.cruce[k] || 0, cfg = {
    ing:{ kc:'ing_via', cats:['vía aérea','vía terrestre','vía marítima'], tit:'Nacionalidades por ', de:'de sus ingresos' },
    resc:{ kc:'resc_rei', cats:['primera vez','reincidentes'], tit:'Nacionalidades · ', de:'de sus rescates (eventos)' },
    pres:{ kc:'pres_est', cats:D.estaciones.map((x,i)=>nomEst(i)), tit:'Nacionalidades en ', de:'de sus presentados' } }[k];
  const tot = n => comp(cfg.kc,F.ss,n), l = topNats(n => enRegion(n) ? tot(n)[q] : 0, TOP), mx = l.length ? l[0][1] : 1;
  return '<div class="caja"><h2><span>'+cfg.tit+esc(cfg.cats[q])+'</span>'+infoP('Principales nacionalidades de la categoría activa en «Composición» y su parte dentro de esa categoría.')+'</h2><span class="mini">Se cambia desde Composición · periodo completo · el % es la parte '+cfg.de+'</span>'+
    (l.map(r => { const t = tot(r[0]).reduce((a,b)=>a+b,0);
      return '<button class="barra pc" data-n="'+r[0]+'"><span>'+esc(D.nats[r[0]][0])+' <small>'+pct(r[1],t)+'%</small></span><span class="b"><i style="width:'+(r[1]/mx*100).toFixed(1)+'%;background:'+c+'"></i></span><span class="x">'+corto(r[1])+'</span></button>'; }).join('') || '<span class="mini">Sin registros.</span>')+'</div>';
}
// Rechazos: nacionalidades que sí se internaron tras la segunda revisión, con su tasa de rechazo
function cajaInternacion(F){
  const c = colG('reg'), l = topNats(n => enRegion(n) ? comp('rech_det',F.ss,n)[0] : 0, TOP), mx = l.length ? l[0][1] : 1;
  return '<div class="caja"><h2><span>Se internaron tras la 2da revisión</span>'+infoP('Nacionalidades que pasaron a segunda revisión y se internaron. El % es su tasa de rechazo en esa revisión.')+'</h2><span class="mini">Se internaron tras la 2da revisión · periodo completo · el % es su tasa de rechazo</span>'+
    (l.map(r => { const v = comp('rech_det',F.ss,r[0]);
      return '<button class="barra pc" data-n="'+r[0]+'"><span>'+esc(D.nats[r[0]][0])+' <small>'+pct(v[1],v[0]+v[1])+'%</small></span><span class="b"><i style="width:'+(r[1]/mx*100).toFixed(1)+'%;background:'+c+'"></i></span><span class="x">'+corto(r[1])+'</span></button>'; }).join('') || '<span class="mini">Sin registros.</span>')+'</div>';
}
// Trámites: los 10 tipos más frecuentes
function cajaTramites(F){
  const v = comp('tram_tipo',F.ss,F.nd).map((x,i)=>[i,x]).filter(r => r[1]>0 && D.tramTipos[r[0]]!=='Otros').sort((x,y)=>y[1]-x[1]).slice(0,5), mx = v.length ? v[0][1] : 1, tot = comp('tram_tipo',F.ss,F.nd).reduce((a,b)=>a+b,0);
  return '<div class="caja"><h2><span>Principales trámites</span>'+infoP('Los tipos de trámite migratorio con más registros en el periodo y su parte del total.')+'</h2><span class="mini">Periodo completo · el % es la parte del total</span>'+
    (v.map(r => '<div class="barra larga" title="'+esc(D.tramTipos[r[0]])+'"><span>'+esc(D.tramTipos[r[0]])+' <small>'+pct(r[1],tot)+'%</small></span><span class="b"><i style="width:'+(r[1]/mx*100).toFixed(1)+'%;background:'+colG('reg')+'"></i></span><span class="x">'+corto(r[1])+'</span></div>').join('') || '<span class="mini">Sin registros.</span>')+'</div>';
}
// Sexo y edad donde la base los trae; en las demás, su propio desglose.
function htmlComp(k, F){
  const c = colG(IND[k].g), c2 = cssv('--ink3'), s = F.ss, n = IND[k].nat ? F.nd : null;
  const fila = (nom,v,tot,color) => '<div class="fila"><span>'+nom+'</span><span class="b"><i style="width:'+(tot?v/tot*100:0).toFixed(1)+'%;background:'+(color||c)+'"></i></span><span class="x">'+(tot?pct(v,tot)+'%':'—')+'</span></div>';
  const grupo = (tit,arr) => { const tot = arr.reduce((x,y)=>x+y[1],0); return tot ? '<div><span class="mini"><b>'+tit+'</b></span>'+arr.map(r=>fila(r[0],r[1],tot,r[2])).join('')+'</div>' : ''; };
  // filas que se pueden elegir: llenan la tarjeta de nacionalidades de esa categoría
  const elegible = (tit, kk, arr) => { const tot = arr.reduce((x,y)=>x+y[1],0); if (!tot) return '';
    return '<div><span class="mini"><b>'+tit+'</b> · clic para ver sus nacionalidades</span>'+arr.map((r,i) => '<button class="fila elige'+(S.cruce[kk]===i?' on':'')+'" data-cruce="'+kk+':'+i+'"><span>'+r[0]+'</span><span class="b"><i style="width:'+(r[1]/tot*100).toFixed(1)+'%;background:'+(r[2]||c)+'"></i></span><span class="x">'+pct(r[1],tot)+'%</span></button>').join('')+'</div>'; };
  let h = '', sub = 'Esta base no trae sexo ni edad';
  if (k==='ing'){ const v = comp('ing_via',s,n);
    h = elegible('Vía de ingreso','ing',[['Aérea',v[0]],['Terrestre',v[1]],['Marítima',v[2]]]);
    if (n==null){ const tot = sumaSem('ing',0,NW-1,s,null), mxv = ingMx(s, ND); h += grupo('Quién ingresa al país',[['Extranjeros',Math.max(0, tot-mxv)],['Mexicanos que regresan',mxv,c2]]); } }
  else if (k==='rech'){ const v = comp('rech_det',s,n), tr = rechazoExt(s,n);
    h = grupo('Resultado de la segunda revisión',[['Rechazo',v[1]],['Internación',v[0],c2]]) + (tr[1] ? '<div><span class="mini"><b>'+(tr[0]/tr[1]*100).toFixed(2)+'%</b> de los extranjeros que llegan por aire o tierra termina en rechazo ('+miles(tr[0])+' de '+corto(tr[1])+'). Sin mexicanos ni cruceros, igual que en Control migratorio.</span></div>' : ''); }
  else if (k==='tram'){ const v = comp('tram_se',s,n), r = comp('tram_res',s,n), ed = ['0–11','12–17','18–24','25–34','35–44','45–54','55–64','65+'];
    let mx = 1; v.forEach(x => mx = Math.max(mx,x)); const H = suma(v,0,8), M = suma(v,8,16); sub = 'Sexo y edad de quien tramita';
    h = '<div class="pira"><div class="pira-c"><span><b class="num">'+pct(H,H+M)+'%</b>Hombres · '+corto(H)+'</span><span class="d"><b class="num">'+pct(M,H+M)+'%</b>Mujeres · '+corto(M)+'</span></div>'+
        ed.map((e,i)=>'<div class="pira-f" title="'+e+' años · hombres '+miles(v[i])+' · mujeres '+miles(v[8+i])+'"><em>'+corto(v[i])+'</em><span class="l"><i style="width:'+(v[i]/mx*100).toFixed(1)+'%;background:'+c2+'"></i></span><span class="e">'+e+'</span><span><i style="width:'+(v[8+i]/mx*100).toFixed(1)+'%;background:'+c+'"></i></span><em class="d">'+corto(v[8+i])+'</em></div>').reverse().join('')+'</div>'+
        reparto('Resolución',[['Positiva',r[0],c],['Negativa',r[1],c2],['Otra',r[2],cssv('--line')]]); }
  else if (k==='resc'){ const a = comp('resc_rei',s,n), d = comp('resc_des',s,n);
    h = elegible('Primera vez o reincidente','resc',[['Primera vez',a[0],c2],['Reincidente',a[1]]]) + grupo('Destino',[['Estación migr.',d[0]],['DIF',d[1]],['Sin destino',d[2],c2]]); }
  else if (k==='pres'){ const v = comp('pres_est',s,n).map((x,i)=>[i,x]).filter(r=>r[1]>0).sort((x,y)=>y[1]-x[1]).slice(0,TOP), mx = v.length ? v[0][1] : 1; sub = 'Estaciones con más presentados · clic para ver sus nacionalidades';
    return '<div class="caja"><h2><span>Estaciones con más presentados</span>'+infoP('Cómo se reparten las personas presentadas ante el INM, por estación o categoría.')+'</h2><span class="mini">'+sub+' · periodo completo</span>'+
      (v.map(r => '<button class="barra'+(S.cruce.pres===r[0]?' on':'')+'" data-cruce="pres:'+r[0]+'"><span>'+esc(nomEst(r[0]))+'</span><span class="b"><i style="width:'+(r[1]/mx*100).toFixed(1)+'%;background:'+c+'"></i></span><span class="x">'+corto(r[1])+'</span></button>').join('') || '<span class="mini">Sin registros con este filtro.</span>')+'</div>'; }
  else if (k==='can'){ const v = comp('can_nna',s,n), a = comp('can_ad',s,n), g2 = f => v.reduce((t,x,i)=>t+(f(i)?x:0),0); sub = 'Niñas, niños y adolescentes, y sus acompañantes';
    h = grupo('NNA por sexo',[['Niñas',g2(i=>i>=6)],['Niños',g2(i=>i<6),c2]]) + grupo('NNA por edad',[['0 a 11 años',g2(i=>Math.floor(i/3)%2===0)],['12 a 17 años',g2(i=>Math.floor(i/3)%2===1),c2]]) +
        grupo('Condición',[['Acompañado',g2(i=>i%3===0),c2],['No acompañado',g2(i=>i%3===1)],['Separado',g2(i=>i%3===2)]]) + grupo('Adultos acompañantes',[['Mujeres',a[1]],['Hombres',a[0],c2]]); }
  else if (k==='ret'){ const v = comp('ret_tipo',s,n);
    h = anillo('ret_tipo', s, n, [['Retorno asistido',1,c,'por retorno asistido'],['Deportación',0,c2,'por deportación']]); }
  else if (k==='recib'){ const v = comp('recib_edad',s,n); sub = 'Esta base trae adultos y menores, sin sexo';
    h = anillo('recib_edad', s, n, [['Menores',1,c,'son menores'],['Adultos',0,c2,'adultos']]); }
  else if (k==='cbp'){ const x = cbpAhora(F).reduce((a,y) => { a.v += y.v; a.mx += y.mx; y.ag.forEach((z,i) => a.ag[i] += z); return a; }, { v:0, mx:0, ag:[0,0,0] }); sub = 'Esta base no trae sexo ni edad';
    h = (F.n==null ? grupo('Quiénes',[['Otros países',x.v-x.mx],['Mexicanos',x.mx,c2]]) : '') + grupo('Agencia de la CBP',[['Patrulla Fronteriza (USBP)',x.ag[0]],['Puertos de entrada (OFO)',x.ag[1],c2],['Citas CBP ONE',x.ag[2],cssv('--line')]]); }
  else if (k==='rep'){ const v = comp('rep_comp',s,null); sub = 'Sexo y edad de los mexicanos repatriados';
    h = grupo('Adultos',[['Hombres',v[0],c2],['Mujeres',v[1]]]) + grupo('Menores',[['Niños',v[2],c2],['Niñas',v[3]]]) + grupo('Menores, con o sin compañía',[['Acompañados',v[4],c2],['Solos',v[5]]]) + grupo('Modalidad',[['Terrestre',v[6],c2],['Aérea',v[7]]]); }
  return '<div class="caja"><h2><span>Composición · '+(k==='rech' ? '2da revisión' : IND[k].n)+'</span>'+infoP('Cómo se reparte el indicador por tipo: vía, edad, sexo u otro.')+'</h2><span class="mini">'+sub+' · periodo completo</span><div class="cgrid">'+(h || '<span class="mini">Sin registros con este filtro.</span>')+'</div></div>';
}
// Encuentros por sector de la frontera (no hay estado de México)
function cajaSectores(F){ const sec = cbpAhora(F), l = D.cbp.sectores.map((P,i) => [P, sec[i].v]).filter(x => x[1]>0).sort((a,b) => b[1]-a[1]), mx = l.length ? l[0][1] : 1, c = colG('usa');
  return '<div class="caja"><h2><span>'+esc(IND.cbp.donde)+' · por sector</span>'+infoP('Sectores de la frontera de EE. UU. con México donde la CBP registra los encuentros. No se reparten por O.R.: la actividad es de EE. UU.')+'</h2><span class="mini">'+(S.dia<ND?'Acumulado al '+fechaDia(S.dia-1):'Periodo completo')+'</span>'+
    (l.map(x => '<div class="barra"><span>'+esc(x[0].n)+' <small>'+esc(x[0].eu)+'</small></span><span class="b"><i style="width:'+(x[1]/mx*100).toFixed(1)+'%;background:'+c+'"></i></span><span class="x">'+corto(x[1])+'</span></div>').join('') || '<span class="mini">Sin registros.</span>')+'</div>'; }
function cajaLugares(k, F){                      // un indicador repartido por estado, cinturón o CECO
  if (sinEdo(k)) return cajaSectores(F);
  const nF = IND[k].nat ? F.nd : null, c = colG(IND[k].g); let filas, tit;
  if (S.agr==='e' || (F.ss && !F.todo && !(S.selCard && S.sel && S.sel.t==='g'))){ const todos = topEsts(s => acum(k,[s],nF), NS), uno = F.ss && F.ss.length===1 ? F.ss[0] : -1;
    let lista = F.ss && F.ss.length>1 ? todos.filter(r => F.ss.indexOf(r[0])>=0).slice(0,TOP) : todos.slice(0,TOP);
    const lugar = todos.findIndex(r => r[0]===uno), mx = lista.length?lista[0][1]:1;
    if (lugar>=TOP) lista = lista.slice(0,TOP-1).concat([todos[lugar]]);
    tit = nomInd(k)+' por estado';   // el nombre de la tarjeta no cambia con el filtro: el filtro va en su etiqueta
    filas = lista.map(r => '<button class="barra'+(r[0]===uno?' on':'')+'" data-e="'+r[0]+'"><span>'+(r[0]===uno?(lugar+1)+'.º ':'')+esc(ESTC[r[0]])+'</span><span class="b"><i style="width:'+(r[1]/mx*100).toFixed(1)+'%;background:'+c+'"></i></span><span class="x">'+corto(r[1])+'</span></button>').join(''); }
  else { const ag = AGR[S.agr], tot = ag.nombres.map((x,q)=>acum(k,miembros(S.agr,q),nF)), sin = acum(k,null,nF)-tot.reduce((x,y)=>x+y,0);
    const mx = Math.max(sin, Math.max.apply(null,tot), 1); tit = nomInd(k)+' por '+ag.n.toLowerCase();
    filas = ag.nombres.map((nom,q) => '<button class="barra" data-g="'+S.agr+q+'"><span>'+nom+'</span><span class="b"><i style="width:'+(tot[q]/mx*100).toFixed(1)+'%;background:'+c+'"></i></span><span class="x">'+corto(tot[q])+'</span></button>').join('')+
            '<div class="barra"><span>'+ag.sin+'</span><span class="b"><i style="width:'+(Math.max(sin,0)/mx*100).toFixed(1)+'%;background:'+cssv('--ink3')+'"></i></span><span class="x">'+corto(Math.max(sin,0))+'</span></div>'; }
  return '<div class="caja"><h2><span>'+esc(tit)+'</span>'+infoP('Total por estado en el periodo, o por la agrupación activa en el mapa (cinturón o CECO).')+'</h2><span class="mini">'+(S.dia<ND?'Acumulado al '+fechaDia(S.dia-1):'Periodo completo')+(S.agr!=='e'&&(!F.ss||F.todo)?' · clic en un grupo para filtrar solo ese':'')+'</span>'+(filas || '<span class="mini">Sin registros.</span>')+'</div>';
}
function fechaEv(f){ const p = f.split('-'); return (p[2] ? (+p[2])+' ' : '')+MES12[+p[1]-1]+' '+p[0]; }
// Lo que se ve en nuestras cifras: 4 semanas después del evento contra las 4 anteriores (si cae dentro del periodo de las bases)
function cifraEvento(e, n){
  const i = indiceDe(e.f.length===7 ? e.f+'-01' : e.f); if (n==null || i<28 || i+28>ND) return '';
  const r = [['resc','rescatados'],['ing','ingresos']].map(x => { const d = diario(x[0],{ss:null,n:n}), a = suma(d,i-28,i), b = suma(d,i,i+28);
    return a>=20 ? x[1]+' '+(b>=a?'▲ ':'▼ ')+Math.abs((b/a-1)*100).toFixed(0)+'%' : ''; }).filter(Boolean);
  return r.length ? '<span class="cf">En nuestras cifras, 4 semanas después: '+r.join(' · ')+'</span>' : '';
}
// Contexto honesto: qué pasó en el país (con fuente) y qué muestran nuestros registros alrededor de esa fecha.
// No hay tarjeta si el país no tiene eventos propios. Los regionales solo entran si mencionan al país.
function contextoDe(n){ const nom = sinAcento(D.nats[n][0]), raiz = nom.slice(0, Math.max(5, nom.length-2));
  const own = CTX[D.nats[n][1]] || [], reg = (CTX.reg || []).filter(e => sinAcento(e.que+' '+(e.efecto || '')).indexOf(raiz)>=0);
  return own.length ? own.concat(reg).sort((a,b) => a.f<b.f ? 1 : -1) : null; }
// ---- Índices internacionales del país (IDH, IPG, IEF, INFORM): datos/indices.js, que genera robot/indices.py una vez al año
// con los archivos oficiales. Describen al país; no explican por sí solos la migración. Sin datos, no aparece nada.
const IDX = window.IANAMI_IDX && window.IANAMI_IDX.p ? window.IANAMI_IDX : null;
function idxPais(n){ const p = IDX && n!=null && D.nats[n] && IDX.p[D.nats[n][1]]; if (!p) return null;
  const l = Object.keys(IDX.ind).filter(k => p[k] && p[k].length).map(k => ({ k:k, d:IDX.ind[k], s:p[k], u:p[k][p[k].length-1] })); return l.length ? l : null; }
const fmtIdx = (k, v) => v.toFixed(k==='idh' ? 3 : k==='ipg' ? 2 : 1);
function lineaIdx(n){ const l = idxPais(n); if (!l) return '';
  return '<span class="fi-ix">'+l.map(x => '<span title="'+esc(x.d.n+' ('+x.d.esc+'), '+x.u[0]+'. '+x.d.nota+' Fuente: '+x.d.f)+'">'+x.d.c+' <b>'+fmtIdx(x.k, x.u[1])+'</b><small>’'+String(x.u[0]).slice(2)+'</small></span>').join('')+'</span>'; }
function bloqueIdx(n){ const l = idxPais(n); if (!l) return ''; const t = TM[S.tema];
  const fila = x => { const s = x.s, v = s.map(y => y[1]), mn = Math.min.apply(null, v), mx = Math.max.apply(null, v), a0 = s[0][0], a1 = s[s.length-1][0], W = 110, H = 26;
    const px = y => a1>a0 ? (y-a0)/(a1-a0)*(W-6)+3 : W/2, py = y => mx>mn ? H-3-(y-mn)/(mx-mn)*(H-6) : H/2;
    const svg = '<svg width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'" aria-hidden="true"><polyline fill="none" stroke="'+t.tinta+'" stroke-width="1.6" stroke-linejoin="round" points="'+s.map(y => px(y[0]).toFixed(1)+','+py(y[1]).toFixed(1)).join(' ')+'"/><circle cx="'+px(a1).toFixed(1)+'" cy="'+py(x.u[1]).toFixed(1)+'" r="2.6" fill="'+t.tinta+'"/></svg>';
    const dif = x.u[1]-s[0][1], igual = Math.abs(dif) < (x.k==='idh' ? 0.0005 : 0.05), mejora = dif*x.d.mejor > 0;
    return '<div class="ix-f"><span class="ix-n"><b>'+esc(x.d.n)+'</b><small>'+esc(x.d.c+' · '+x.d.esc+' · '+x.d.nota)+'</small></span>'+svg+
      '<span class="ix-v"><b>'+fmtIdx(x.k, x.u[1])+'</b><small>'+x.u[0]+'</small></span>'+
      '<span class="ix-c'+(igual ? '' : mejora ? ' mej' : ' emp')+'">'+(s.length>1 ? (igual ? 'sin cambio' : (mejora ? 'mejoró ' : 'empeoró ')+(dif>0 ? '+' : '−')+fmtIdx(x.k, Math.abs(dif)))+' desde '+s[0][0] : 'un solo año')+'</span>'+
      '<a href="'+esc(x.d.u)+'" target="_blank" rel="noopener">'+esc(x.d.f)+' ↗</a></div>'; };
  return '<div class="ctx-ix"><h3>Índices del país</h3>'+l.map(fila).join('')+'<span class="nota">Describen al país; no explican por sí solos la migración. Que un índice y nuestros registros cambien al mismo tiempo no prueba que uno cause el otro.</span></div>'; }
function cajaContexto(n){
  const l = contextoDe(n), ini = 0, fin = D0.dias, dia = e => idxBase(e.f.length===7 ? e.f+'-01' : e.f);
  const k = ['resc','ing','rech'].map(x => [x, rangoBase(x, 0, D0.dias, null, n)]).sort((a,b) => b[1]-a[1])[0][0];
  const cerca = l.filter(e => dia(e)>=ini-90 && dia(e)<=fin+90).sort((a,b) => { const da = dia(a), db = dia(b), ia = da>=0 && da<fin, ib = db>=0 && db<fin; return ia!==ib ? (ia ? -1 : 1) : da-db; }), antes = l.filter(e => dia(e)<ini-90), despues = l.filter(e => dia(e)>fin+90);
  const nuestro = e => { const i = dia(e); if (i-30<0 || i+30>D0.dias) return '<span class="cf">'+(i<0 || i>=D0.dias ? 'Fuera del periodo de nuestras bases.' : 'En el borde de nuestras bases: no alcanzan 30 días antes y después.')+'</span>';
    const a = rangoBase(k, i-30, i, null, n), b = rangoBase(k, i, i+30, null, n);
    return a>=20 ? '<span class="cf">Nuestros registros de '+IND[k].n.toLowerCase()+', 30 días antes y después: <b>'+miles(a)+' → '+miles(b)+'</b> ('+(b>=a ? '+' : '−')+Math.abs((b/a-1)*100).toFixed(0)+'%)</span>' : ''; };
  const ev = e => '<div class="ev"><time>'+fechaEv(e.f)+'</time><i style="background:'+CATS[e.c][1]+'" title="'+CATS[e.c][0]+'"></i><div><b>'+esc(e.que)+'</b>'+
    (e.doc && e.efecto ? '<span class="ef">Según la fuente: '+esc(e.efecto)+'</span>' : '')+nuestro(e)+(e.url ? '<a href="'+esc(e.url)+'" target="_blank" rel="noopener">'+esc(e.fuente)+' ↗</a>' : '')+'</div></div>';
  const ev2 = e => '<div class="ev"><time>'+fechaEv(e.f)+'</time><i style="background:'+CATS[e.c][1]+'"></i><div><b>'+esc(e.que)+'</b>'+(e.url ? '<a href="'+esc(e.url)+'" target="_blank" rel="noopener">'+esc(e.fuente)+' ↗</a>' : '')+'</div></div>';
  const pl = (tit, a) => a.length ? '<details class="ctx-mas"><summary>'+tit+' · '+a.length+'</summary>'+a.map(ev2).join('')+'</details>' : '';
  return '<div class="caja ancha" data-propia="1"><h2><span>Contexto · '+esc(D.nats[n][0])+'</span>'+infoP('Eventos del país verificados con fuente pública y, junto a cada uno, lo que registran nuestras bases 30 días antes y después. Que coincidan en el tiempo no prueba que uno cause el otro.')+'</h2>'+
    '<span class="mini">Qué pasó en el país y qué muestran nuestros registros</span><div class="ctx-lista">'+
    (cerca.length ? cerca.map(ev).join('') : '<span class="mini">Ningún evento cae dentro o cerca del periodo de nuestras bases ('+fechaISO(D.inicio)+' – '+fechaISO(D.corte)+').</span>')+
    pl('Después del periodo de nuestras bases', despues)+pl('Antes del periodo de nuestras bases', antes)+'</div>'+bloqueIdx(n)+
    '<div class="cats">'+Object.keys(CATS).map(c => '<span><i style="background:'+CATS[c][1]+'"></i>'+CATS[c][0]+'</span>').join('')+'</div>'+
    '<span class="nota">Coincidir en el tiempo no prueba la causa. El efecto migratorio solo se escribe cuando la fuente lo documenta.</span></div>';
}
function htmlEventos(lista, n){ return lista.map(e => '<div class="ev"><time>'+fechaEv(e.f)+'</time><i style="background:'+CATS[e.c][1]+'" title="'+CATS[e.c][0]+'"></i><div>'+
  '<b>'+esc(e.que)+'</b><span class="ef">→ '+esc(e.efecto)+(e.doc ? '' : ' <em>efecto inferido</em>')+'</span>'+cifraEvento(e, n)+
  (e.url ? '<a href="'+esc(e.url)+'" target="_blank" rel="noopener">'+esc(e.fuente)+' ↗</a>' : '')+'</div></div>').join(''); }
function pintarBajo(){
  const F = filtro(), s = S.sel, cajas = [];
  // 1) Todos los indicadores de la selección (país, estado, cinturón o CECO)
  const fijo = !!S.selCard;                     // filtro desde una card: mismas tarjetas, mismo orden; solo cambian las cifras
  if (s && s.t!=='p' && !fijo){ const lista = INDS.filter(m => F.nd==null || m.nat);
    cajas.push('<div class="caja" data-propia="1"><h2><span>'+esc(nombreSel())+'</span><small>todos sus indicadores</small></h2><span class="mini">'+(s.t==='g' ? miembros(s.a,s.q).map(x=>ESTC[x]).join(', ') : s.t==='e' ? ['c','o'].map(a => AGR[a].de[s.i]>=0 ? AGR[a].nombres[AGR[a].de[s.i]] : AGR[a].sin).join(' · ') : 'Clic en un renglón para verlo en el mapa')+'</span>'+
      lista.map(m => { const sem = semanal(m.k,F.ss,F.nd); return '<button class="fk'+(S.ind===m.k?' on':'')+'" data-k="'+m.k+'"><span>'+m.n+'</span>'+chispa(sem,64,20,colG(m.g),semDe(S.dia))+'<span class="x">'+corto(acum(m.k,F.ss,F.nd))+'</span></button>'; }).join('')+
      (s.t==='n' ? '<hr class="sep">'+htmlBreve(s.i) : '')+'</div>'); }
  // 1b) Principales nacionalidades (cuando no hay una elegida)
  if (F.n==null || fijo){ if (!S.ind){ cajas.push(htmlTops(F,'ing')); cajas.push(htmlTops(F,'resc')); } else if (IND[S.ind].nat) cajas.push(htmlTops(F,S.ind)); }
  // 3) Lugares: con indicador, el suyo; sin indicador, el par regular e irregular
  if (S.ind) cajas.push(cajaLugares(S.ind, F)); else { cajas.push(cajaLugares('ing', F)); cajas.push(cajaLugares('resc', F)); }
  // 4) Composición del indicador, con su tarjeta complementaria
  if (S.ind==='tram') cajas.push(cajaTramites(F));
  if (S.ind) cajas.push(htmlComp(S.ind, F));
  if ((F.n==null || fijo) && (S.ind==='ing' || S.ind==='resc' || S.ind==='pres')) cajas.push(cajaCruce(S.ind, F));
  if (S.ind==='rech' && (F.n==null || fijo)) cajas.push(cajaInternacion(F));   // rechazos: mismo orden que los demás (nacionalidades, estado, composición y su complemento)
  // 5) Contexto: aparece al elegir una nacionalidad en el mapa o el buscador
  if (F.n!=null && !fijo && contextoDe(F.n)) cajas.push(cajaContexto(F.n));
  else if (F.n!=null && !fijo && idxPais(F.n)) cajas.push('<div class="caja ancha" data-propia="1"><h2><span>Contexto · '+esc(D.nats[F.n][0])+'</span></h2>'+bloqueIdx(F.n)+'</div>');   // sin eventos propios: solo los índices
  $('bajo').innerHTML = cajas.join('');
  if (s && (s.t==='n' || s.t==='g')) document.querySelectorAll('#bajo .barra[data-'+s.t+'="'+(s.t==='n' ? s.i : s.a+s.q)+'"]').forEach(b => b.classList.add('on'));   // la barra elegida queda marcada
  const cl = document.querySelector('.ctx-lista');       // el contexto muestra de inicio los primeros 4 eventos
  if (cl){ const ev = cl.querySelectorAll(':scope > .ev'); if (ev.length>4) cl.style.maxHeight = ev[4].offsetTop+'px'; }
}
function pintarCtl(){ if (!$('rango') || !$('cmp') || !$('per')) return;
  const x = '<svg width="10" height="10" viewBox="0 0 12 12"><path d="M2 2l8 8M10 2l-8 8" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>';
  const f0 = diaDe(0), f1 = diaDe(S.dia-1);
  $('rango').textContent = f0.getDate()+' '+MES12[f0.getMonth()]+(f0.getFullYear()!==f1.getFullYear() ? ' '+f0.getFullYear() : '')+' – '+fechaLarga(S.dia-1);
  $('rango-nota').textContent = S.dia>=ND ? ND+' días' : S.dia+' de '+ND+' días';
  const fx = cmpFijo(), rf = fx ? refFija() : null, rgo = (a, b) => fechaDia(a)+' – '+fechaDia(b-1); $('cmp').closest('.varia').classList.toggle('fijo', fx);
  $('cmp').innerHTML = fx ? '<span class="cmp-fx">'+(rf ? 'Comparado con <b>'+rf.txt+'</b>' : 'Sin periodo anterior con datos para comparar')+'</span>'+(rf ? '<span class="cmp-n">'+(i0 => fechaIdx(P0)+' – '+fechaIdx(P0+ND-1)+' vs. '+fechaIdx(i0)+' – '+fechaIdx(i0+ND-1))(rf.t==='prev' ? P0-ND : rf.q0)+'</span>' : '') :
    '<select id="cmp-sel" aria-label="Comparar con">'+[['sem','Semana anterior'],[30,'Últimos 30 días'],[90,'Últimos 3 meses']].map(o => { const ok = cmpDisponible(o[0]);
    return '<option value="'+o[0]+'"'+(String(S.cmp)===String(o[0])?' selected':'')+(ok?'':' disabled')+'>'+o[1]+'</option>'; }).join('')+'</select>'+
    (S.cmp==='sem' ? (semanasCmp(ND) ? (w => '<span class="cmp-n">'+fechaDia(w[0])+' – '+fechaDia(w[1]-1)+' vs. '+fechaDia(w[2])+' – '+fechaDia(w[3]-1)+'</span>')(semanasCmp(ND)) : '')
      : 2*S.cmp<=ND ? '<span class="cmp-n">'+fechaDia(ND-S.cmp)+' – '+fechaDia(ND-1)+' vs. '+fechaDia(ND-2*S.cmp)+' – '+fechaDia(ND-S.cmp-1)+'</span>' : '');   // las fechas exactas que se comparan, en todas las opciones
  // Periodos: Sheinbaum, Trump, Año (con mes) y Personalizado
  $('per').innerHTML = [['shein','Sheinbaum'],['trump','Trump'],['anio','Año'],['pers','Personalizado']].map(o => { const ok = !!rangoPeriodo(o[0]==='anio' || o[0]==='pers' ? 'shein' : o[0]) && (o[0]!=='trump' || idxBase('2025-01-20') < D0.dias), on = S.per===o[0];
    return '<button data-per="'+o[0]+'" class="'+(on?'on':'')+'" aria-pressed="'+on+'"'+(ok ? '' : ' disabled title="Sin datos para este periodo"')+'>'+o[1]+'</button>'; }).join('');
  let ex = '';
  if (S.per==='anio'){ const y0 = INICIO0.getFullYear(), y1 = fechaBase(D0.dias-1).getFullYear(), anios = []; for (let y=y0;y<=y1;y++) anios.push(y);
    ex = '<select id="per-anio" aria-label="Año">'+anios.map(y => '<option'+(y===S.anio?' selected':'')+'>'+y+'</option>').join('')+'</select>'+
         '<select id="per-mes" aria-label="Mes"><option value="0">Todo el año</option>'+MES12.map((m,i) => { const r = idxBase(isoDe(new Date(S.anio,i,1))) < D0.dias && idxBase(isoDe(new Date(S.anio,i+1,1))) > 0;
           return '<option value="'+(i+1)+'"'+(S.mes===i+1?' selected':'')+(r?'':' disabled')+'>'+m+'</option>'; }).join('')+'</select>'; }
  if (S.per==='pers') ex = '<input type="date" id="per-desde" min="'+D.inicio+'" max="'+D.corte+'" value="'+S.desde+'" aria-label="Desde"> – <input type="date" id="per-hasta" min="'+D.inicio+'" max="'+D.corte+'" value="'+S.hasta+'" aria-label="Hasta">';
  $('per-extra').innerHTML = ex;
  $('chips').innerHTML = (S.sel ? '<span class="chip">'+esc(nombreSel())+'<button data-cerrar aria-label="Quitar filtro">'+x+'</button></span>' : '')+
    (S.region ? '<span class="chip">'+esc(nombreRegion())+'<button data-cerrar-region aria-label="Quitar región">'+x+'</button></span>' : '');
}
function pintarTodo(soloTiempo){
  if (S.vista!=='pulso') return;
  const actual = P1>=D0.dias, m = document.querySelector('.main');
  if (m && m.classList.contains('pasado')===actual){ m.classList.toggle('pasado', !actual); setTimeout(() => window.dispatchEvent(new Event('resize')), 520); }
  const av = $('aviso-pasado'); if (av) av.hidden = actual;
  pintarCtl(); if (!soloTiempo) pintarAnalisis(); if (!soloTiempo) pintarDocs(); pintarKpis(); pintarTiempo(); pintarMapa(); pintarBajo(); marcarFiltro();
  if (SALA.on) pintarSala(soloTiempo);
  pintarFicha();
}
// Con una nacionalidad, estado, grupo o punto elegido, cada tarjeta que cambió lleva una franja y el nombre
function marcarFiltro(){
  const nom = nombreFiltro();
  document.querySelectorAll('.rail .caja, #bajo .caja').forEach(c => {
    c.classList.toggle('filtro', !!nom);
    const h = c.querySelector('h2 > span'); if (!h) return;
    let t = h.querySelector('.tag');
    if (nom && !c.dataset.propia && !c.querySelector('.barra.on')){ if (!t){ t = document.createElement('span'); t.className = 'tag'; h.appendChild(t); } t.textContent = nom; }
    else if (t) t.remove();
  });
}

/* ==== [12] CONSULTAR Y COMPARTIR ================================== */
// ECharts y el zoom de pantallas grandes: la página se agranda con CSS zoom (clase esc) y ECharts toma la posición del
// mouse sin esa escala, así que señalaba otro punto (otra línea, otra barra). Aquí se le entrega ya corregida (zrX, zrY),
// que ECharts usa tal cual. Sin zoom no hace nada. En pantallas táctiles ECharts ya la calcula bien por su cuenta.
(function(){
  const raiz = el => { for (let x = el; x && x.getAttribute; x = x.parentNode){ if (x.getAttribute('_echarts_instance_')) return x.firstElementChild || x; } return null; };
  const fijar = e => { if (e.zrX!=null || e.clientX==null) return; const r = raiz(e.target); if (!r || !r.offsetWidth) return;
    const b = r.getBoundingClientRect(), k = b.width / r.offsetWidth; if (Math.abs(k-1) < 0.01) return;
    e.zrX = (e.clientX - b.left) / k; e.zrY = (e.clientY - b.top) / k; };
  ['mousemove','mousedown','mouseup','click','dblclick','contextmenu','wheel','mousewheel','pointermove','pointerdown','pointerup','mouseover','mouseout'].forEach(t => document.addEventListener(t, fijar, { capture:true, passive:true }));
})();
// Carga diferida: con dos años de datos, Control, Regulación y Protección pesan decenas de MB. El Pulso abre solo
// con datos/datos.js; lo demás se baja la primera vez que se abre esa parte y queda en memoria.
const VERSION = ((document.querySelector('script[src*="js/app.js"]') || {}).src || '').split('?')[1] || '';
const MODULOS = { control:['datos/control.js','js/control.js'], regulacion:['datos/regulacion.js','datos/plazos.js','js/regulacion.js'], proteccion:['datos/proteccion.js','js/proteccion.js'],
  consulta:['datos/control.js','datos/proteccion.js','datos/regulacion.js','datos/vocabulario.js','js/consulta.js'],
  analizar:['datos/control.js','datos/proteccion.js','datos/regulacion.js','datos/vocabulario.js','js/consulta.js','js/analizar.js'],
  arma:['datos/control.js','datos/proteccion.js','datos/regulacion.js','datos/vocabulario.js','js/consulta.js','js/informes.js'],
  vistazo:['datos/control.js','datos/proteccion.js','datos/regulacion.js','datos/vocabulario.js','js/consulta.js','js/vistazo.js'] };
const NOM_MOD = { control:'Control migratorio', regulacion:'Regulación migratoria', proteccion:'Protección al migrante', consulta:'Pregunta a INAMI', analizar:'Informe migratorio', arma:'Arma tu informe', vistazo:'Vistazo' };
const LISTO_MOD = { control:'IANAMI_CONTROL', regulacion:'IANAMI_REGULACION', proteccion:'IANAMI_PROTECCION', consulta:'IANAMI_CONSULTA', analizar:'IANAMI_ANALIZAR', arma:'IANAMI_ARMA', vistazo:'IANAMI_VISTAZO' };
const BAJADOS = {};
const modListo = k => !!window[LISTO_MOD[k]];
function bajarJS(src){ return BAJADOS[src] || (BAJADOS[src] = new Promise((ok, mal) => { const s = document.createElement('script'); s.src = src+(VERSION ? '?'+VERSION : '');
  s.onload = ok; s.onerror = () => { delete BAJADOS[src]; s.remove(); mal(new Error(src)); }; document.body.appendChild(s); })); }
function cargarModulo(k, enPagina){
  if (modListo(k)) return Promise.resolve();
  const av = $('cargando'); av.classList.remove('error'); av.textContent = 'Cargando '+NOM_MOD[k]+'…'; av.hidden = !!enPagina;
  return (MODULOS[k] || []).reduce((p, src) => p.then(() => bajarJS(src)), Promise.resolve())
    .then(() => { av.hidden = true; }, e => { av.classList.add('error'); av.textContent = 'No se pudo cargar '+NOM_MOD[k]+'. Revisa tu conexión e inténtalo de nuevo.'; setTimeout(() => { av.hidden = true; }, 4500); throw e; });
}
window.IANAMI_CARGAR = cargarModulo;
// Pregunta a INAMI vive en js/consulta.js; aquí solo se abre y se le da la navegación hacia los procesos.
function iniciarConsulta(){ if (!$('b-consulta')) return;
  $('b-consulta').addEventListener('click', () => { cargarModulo('consulta').then(() => { if (window.IANAMI_CONSULTA) window.IANAMI_CONSULTA.abrir(); }, () => {}); });
  $('b-comp').addEventListener('click', e => { e.stopPropagation(); menuComp($('menu-comp').hidden); });
  // Vista tablet («De un vistazo», js/vistazo.js): se abre en pantalla completa; la petición va en el mismo toque para que el navegador la acepte
  const vistazo = op => cargarModulo('vistazo').then(() => window.IANAMI_VISTAZO.abrir(op), () => {});
  $('b-vz').addEventListener('click', () => { const d = document.documentElement, fs = d.requestFullscreen || d.webkitRequestFullscreen;
    if (fs && !(document.fullscreenElement || document.webkitFullscreenElement)){ try { const p = fs.call(d); if (p && p.catch) p.catch(() => {}); } catch(e){} } vistazo(); });
  if (/[?&]vista=tablet\b/.test(location.search)) vistazo();
  if (/[?&]resumen-inami\b/.test(location.search)){ document.title = 'Resumen INAMI'; vistazo({ compartido:true }); }   // liga compartida: solo el Vistazo
  $('menu-comp').addEventListener('click', e => { e.stopPropagation(); const b = e.target.closest('[data-comp]'); if (!b) return; if (b.dataset.comp==='enviar') enviarPDF(); else if (b.dataset.comp==='liga') copiarLiga(); else compartir(b.dataset.comp); });
  document.addEventListener('click', e => { if (!e.target.closest('#menu-comp, #b-comp')) menuComp(false); });
}
// Abre un proceso con filtros (los usa «Profundizar en el tablero» de Pregunta a INAMI)
window.IANAMI_NAV = { ir(k, p){ const i = DIRS.findIndex(d => d.k===k); if (i<0) return;
  if (!modListo(k)){ S.dir = i; NAV_P = { k:k, p:p }; irA('dir'); return; }   // primero la sección con «Preparando los datos…»; al llegar el módulo se aplica lo pedido
  S.dir = i;
  const M = { control:window.IANAMI_CONTROL, regulacion:window.IANAMI_REGULACION, proteccion:window.IANAMI_PROTECCION }[k];
  if (M && M.fijar) M.fijar(p || {}); irA('dir'); window.scrollTo(0,0); } };

/* ==== [11] BUSCADOR, SECCIONES Y AVISOS =========================== */
const INDICE = [];
D.nats.slice(0,OT).forEach((n,i) => INDICE.push({t:'Nacionalidad', n:n[0], sel:{t:'n',i:i}}));
EST.forEach((e,i) => INDICE.push({t:'Estado', n:e, sel:{t:'e',i:i}}));
['c','o'].forEach(a => AGR[a].nombres.forEach((nom,q) => INDICE.push({t:AGR[a].n, n:nom, sel:{t:'g',a:a,q:q}})));
D.puntos.forEach((p,i) => INDICE.push({t:'Punto de ingreso → Control', n:p.n, sel:{t:'p',tipo:'ing',i:i}}));
D.repPuntos.forEach((p,i) => INDICE.push({t:'Repatriación → Protección', n:p.n, sel:{t:'p',tipo:'rep',i:i}}));
D.emPuntos.forEach((p,i) => INDICE.push({t:'Estación → Control', n:p.n, sel:{t:'p',tipo:'em',i:i}}));
INDICE.forEach(x => x.q = sinAcento(x.n));
let hallados = [];
function buscar(){
  const q = sinAcento($('buscar').value.trim()), el = $('res');
  if (!q){ el.hidden = true; return; }
  hallados = INDICE.filter(x => x.q.indexOf(q)===0).concat(INDICE.filter(x => x.q.indexOf(q)>0)).slice(0,9);
  el.hidden = false;
  el.innerHTML = hallados.length ? hallados.map((x,i) => '<button data-r="'+i+'" class="'+(i?'':'act')+'"><span>'+esc(x.n)+'</span><small>'+x.t+'</small></button>').join('') : '<span class="mini" style="padding:6px 9px;display:block">Sin coincidencias</span>';
}
function elegir(i){ const x = hallados[i]; if (!x) return; $('buscar').value = ''; $('res').hidden = true;
  if (x.sel.t==='p'){ irPunto(x.sel.tipo, x.sel.i); return; }
  if (x.sel.t==='g') S.agr = x.sel.a; fijarSel(x.sel, true); }
function pintarNav(){ $('nav').innerHTML = SECCIONES.map(s => s[0]==='dir'
  ? '<button data-menu-dir aria-haspopup="true" aria-expanded="false" class="'+(S.vista==='dir'?'on':'')+'">Procesos ▾</button>'
  : s[0]==='inf' ? '<button data-menu-inf aria-haspopup="true" aria-expanded="false" class="'+(S.vista==='arma' || S.vista==='analizar' ?'on':'')+'">Informes ▾</button>'
  : '<button data-vista="'+s[0]+'" class="'+(S.vista===s[0]?'on':'')+'"'+(S.vista===s[0]?' aria-current="page"':'')+'>'+s[1]+'</button>').join(''); }
// Con mouse, el menú de Procesos se abre al pasar el cursor; en pantallas táctiles, con un toque
const CON_HOVER = matchMedia('(hover:hover) and (pointer:fine)').matches; let tMenu = null;
if (CON_HOVER) document.addEventListener('mouseover', e => {
  const m = $('menu-dir'); if (!m) return; const boton = e.target.closest('[data-menu-dir]');
  if (boton || e.target.closest('#menu-dir')){ clearTimeout(tMenu); if (boton && m.hidden){ clearTimeout(tMenuI); menuInf(false); menuDir(true); } }
  else if (!m.hidden){ clearTimeout(tMenu); tMenu = setTimeout(() => menuDir(false), 220); }
  const mi = $('menu-inf'); if (!mi) return; const bi = e.target.closest('[data-menu-inf]');
  if (bi || e.target.closest('#menu-inf')){ clearTimeout(tMenuI); if (bi && mi.hidden){ clearTimeout(tMenu); menuDir(false); menuInf(true); } }
  else if (!mi.hidden){ clearTimeout(tMenuI); tMenuI = setTimeout(() => menuInf(false), 220); }
});
if (CON_HOVER) document.addEventListener('mouseout', e => { if (e.relatedTarget) return;   // el cursor salió de la ventana
  clearTimeout(tMenu); tMenu = setTimeout(() => menuDir(false), 220); clearTimeout(tMenuI); tMenuI = setTimeout(() => menuInf(false), 220); });
window.addEventListener('blur', () => { menuDir(false); menuInf(false); });
// Ayuda al pasar el cursor por los botones de la barra, con el mismo globo del tablero (no el genérico del navegador)
if (CON_HOVER){ let glb = null, tg = null; document.addEventListener('mouseover', e => { const b = e.target.closest && e.target.closest('[data-ayuda]'); clearTimeout(tg);
  if (!b){ if (glb) glb.hidden = true; return; }
  tg = setTimeout(() => { if (!glb){ glb = document.createElement('div'); glb.className = 'rg-pop ayuda-b'; document.body.appendChild(glb); }
    glb.innerHTML = b.dataset.ayuda; glb.hidden = false; const r = b.getBoundingClientRect(), w = glb.offsetWidth; glb.style.left = Math.max(8, Math.min(r.left+r.width/2-w/2, innerWidth-w-8))+'px'; glb.style.top = (r.bottom+8)+'px'; }, 250); });
  document.addEventListener('pointerdown', () => { clearTimeout(tg); if (glb) glb.hidden = true; }, true); }
document.addEventListener('pointerdown', e => { const t = e.target; if (!t.closest) return;   // el mapa se queda con el clic; el toque se ve antes
  if (!t.closest('#menu-dir,[data-menu-dir]')) menuDir(false); if (!t.closest('#menu-inf,[data-menu-inf]')) menuInf(false); }, true);
addEventListener('scroll', () => { menuDir(false); menuInf(false); }, { passive:true });
// Menú de Informes: Arma tu informe y el Informe migratorio de la semana
let tMenuI = null;
function menuInf(abrir){
  const m = $('menu-inf'), b = document.querySelector('[data-menu-inf]'); if (!m || !b) return;
  m.hidden = !abrir; b.setAttribute('aria-expanded', abrir);
  if (abrir){ const r = b.getBoundingClientRect(), top = document.querySelector('.top').getBoundingClientRect(), z = E || 1;
    m.innerHTML = '<button data-inf="arma" class="'+(S.vista==='arma'?'on':'')+'"><b>Arma tu informe</b><span>Busca, compara y junta láminas en tu informe</span></button>'+
      '<button data-inf="analizar" class="'+(S.vista==='analizar'?'on':'')+'"><b>Informe migratorio</b><span>El informe de la semana, listo para presentar</span></button>';
    m.style.left = Math.max(8, Math.min((r.left-top.left)/z, top.width/z-m.offsetWidth-8))+'px'; m.style.top = ((r.bottom-top.top)/z+2)+'px'; }
}
function menuDir(abrir){
  const m = $('menu-dir'), b = document.querySelector('[data-menu-dir]'); if (!m || !b) return;
  m.hidden = !abrir; b.setAttribute('aria-expanded', abrir);
  if (abrir){ const r = b.getBoundingClientRect(), top = document.querySelector('.top').getBoundingClientRect();
    const z = E || 1;                               // la barra se agranda con zoom (clase esc): el rectángulo viene escalado; left/top van sin escalar
    m.style.left = Math.max(8, Math.min((r.left-top.left)/z, top.width/z-m.offsetWidth-8))+'px'; m.style.top = ((r.bottom-top.top)/z+2)+'px';
    m.innerHTML = DIRS.map((d,i) => '<button data-dir="'+i+'" class="'+(S.vista==='dir' && (S.dir||0)===i ? 'on' : '')+'"><b>'+d.s+'</b><span>'+d.n+'</span></button>').join(''); }
}
// Tablero de una dirección: sus bases con total, variación, tendencia, nacionalidades y estados
function htmlDireccion(d){
  const F0 = {ss:null, n:null, nd:null}, fila = (nom, v, mx, c) => '<div class="barra"><span>'+esc(nom)+'</span><span class="b"><i style="width:'+(v/mx*100).toFixed(1)+'%;background:'+c+'"></i></span><span class="x">'+corto(v)+'</span></div>';
  const cajas = d.ind.map(k => { const m = IND[k], c = colG(m.g), dd = diario(k,F0), va = variacion(dd), tot = suma(dd,0,ND);
    const tn = m.nat ? topNats(n => sumaSem(k,0,NW-1,null,n), 5) : [], te = topEsts(s => sumaSem(k,0,NW-1,[s],null), 5);
    return '<div class="caja"><h2><span>'+m.n+'</span><small>'+(va.ok ? (va.dl>=0?'▲ ':'▼ ')+Math.abs(va.dl).toFixed(1)+'% '+sufCmp() : '')+'</small></h2>'+
      '<div style="display:flex;align-items:flex-end;justify-content:space-between;gap:10px"><span class="num" style="font-size:30px">'+miles(tot)+'</span>'+chispa(semanal(k,null,null),140,40,c)+'</div>'+
      (tn.length ? '<span class="mini"><b>Principales nacionalidades</b></span>'+tn.map(r => fila(D.nats[r[0]][0], r[1], tn[0][1], c)).join('') : '')+
      '<span class="mini"><b>Principales estados</b></span>'+te.map(r => fila(ESTC[r[0]], r[1], te[0][1], c)).join('')+'</div>'; });
  if (d.docs) cajas.push('<div class="caja"><h2><span>Documentos vigentes</span><small>al último corte</small></h2><span class="num" style="font-size:30px">'+miles(D.docs.total)+'</span>'+
    '<span class="mini"><b>Por tipo</b></span>'+D.docs.tipos.slice(0,5).map(x => fila(x[0], x[1], D.docs.tipos[0][1], colG('reg'))).join('')+'</div>');
  return '<span class="mini">Procesos › '+d.n+'</span><h1>'+d.s+'</h1><p>Bases de este proceso, del '+fechaLarga(0)+' al '+fechaLarga(ND-1)+'. Variación: '+textoCmp()+'.</p><div class="rej">'+cajas.join('')+'</div>';
}
// Para que las vistas de los procesos abran Pulso filtrado por una nacionalidad (se busca por nombre)
const normNom = t => String(t).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase().trim();
function natPorNombre(nom){ const k = normNom(nom); for (let i=0;i<NN-2;i++) if (normNom(D.nats[i][0])===k) return i; return -1; }
window.IANAMI_PULSO = {
  sala(pf){ abrirSala(pf); },                    // pantalla completa con el perfil de un proceso
  tiene: nom => natPorNombre(nom)>=0,
  rechazo: nom => rechazoExt(null, nom==null ? null : natPorNombre(nom)),   // [rechazos, llegadas] con la definición común
  verLugar(dim, nom){ if (dim==='n'){ const i = natPorNombre(nom); if (i<0) return false; S.ind = null; irA('pulso'); fijarSel({t:'n', i:i}, true); }   // perfil de Pregunta a INAMI: el Pulso en su Panorama, con el lugar elegido
    else { const i = EST.findIndex(e => sinAcento(e)===sinAcento(nom)); if (i<0) return false; S.ind = null; irA('pulso'); fijarSel({t:'e', i:i}, true); } window.scrollTo(0,0); return true; },
  verInd(k, natNom){ if (!IND[k]) return false; S.ind = k; S.sel = null; irA('pulso'); const i = natNom ? natPorNombre(natNom) : -1;   // desde Pregunta a INAMI
    if (i>=0) fijarSel({t:'n', i:i}, true); else { pintarTodo(); acercarSiMundo(); } window.scrollTo(0,0); return true; },
  verCapa(a){ if (a!=='car') return false; S.ind = null; irA('pulso'); if (!S.car){ S.car = true; const b = document.querySelector('#m-her [data-a="car"]'); if (b){ b.classList.add('on'); b.setAttribute('aria-pressed', true); } }
    S.carSel = null; pintarTodo(); volarCaravanas(); window.scrollTo(0,0); return true; },
  verNat(nom, ind){ const i = natPorNombre(nom); if (i<0) return false; S.ind = ind || 'ing'; irA('pulso'); fijarSel({t:'n', i:i}, true); window.scrollTo(0,0); return true; },
  ir(){ irA('pulso'); window.scrollTo(0,0); },   // «Salir» de la vista tablet
  // desde la vista tablet: el mismo periodo y el indicador (o el país o estado) que se estaba viendo
  desdeVistazo(o){ S.per = o.per; if (o.per==='anio'){ S.anio = o.anio; S.mes = o.mes || 0; } if (o.per==='pers'){ S.desde = o.desde; S.hasta = o.hasta; }
    S.ind = o.ind && IND[o.ind] ? o.ind : null; S.sel = null; irA('pulso'); cambiarPeriodo();
    if (o.nom){ const i = o.dim==='n' ? natPorNombre(o.nom) : EST.findIndex(e => sinAcento(e)===sinAcento(o.nom)); if (i>=0) fijarSel({t:o.dim==='n' ? 'n' : 'e', i:i}, true); }
    else if (S.ind) acercarSiMundo();
    window.scrollTo(0,0); return true; }
};
// Gráficas por mes o semana: el periodo incompleto (al inicio o al final, a medio mes) va con tramo punteado y sus días,
// para que su cifra más baja no se lea como una caída. Cada línea con algún periodo incompleto se parte en dos series del mismo
// nombre (la leyenda las prende y apaga juntas). inc(k) = días con datos del periodo k si está incompleto, o 0.
window.IANAMI_INC = function(series, inc){ const extra = [];
  series.forEach(s => { if (s.type!=='line' || !Array.isArray(s.data) || /^banda/.test(s.name || '')) return;
    const n = s.data.length, v = s.data.map(d => d!=null && typeof d==='object' ? d.value : d), es = k => inc(k)>0;
    if (!v.some((_,k) => es(k))) return;
    const dash = v.map(() => '-');
    for (let k=0; k<n; k++) if (es(k)){ const d = inc(k);
      dash[k] = { value:v[k], symbol:'emptyCircle', symbolSize:9, label:{ show:true, position:k===n-1 ? 'left' : k===0 ? 'right' : 'top', distance:8, fontSize:10.5, fontWeight:600, color:'#716D65', formatter:d+(d===1 ? ' día' : ' días') } };
      if (k>0 && !es(k-1)) dash[k-1] = { value:v[k-1], symbol:'none' }; if (k<n-1 && !es(k+1)) dash[k+1] = { value:v[k+1], symbol:'none' }; }
    s.data = s.data.map((d,k) => es(k) ? '-' : d);
    extra.push({ name:s.name, type:'line', smooth:s.smooth, data:dash, z:s.z, color:s.color, lineStyle:Object.assign({}, s.lineStyle || {}, { type:[5,5] }), emphasis:{ disabled:true } }); });
  return series.concat(extra); };
// En la ayuda de esas gráficas, cada línea una sola vez y sin los huecos del tramo punteado
window.IANAMI_INC_TT = ps => ps.filter(p => p.value!=='-' && p.value!=null && !(typeof p.value==='number' && isNaN(p.value))).filter((p,i,a) => a.findIndex(q => q.seriesName===p.seriesName)===i);
// «Atrás» del navegador: cada cambio de sección queda en el historial y «atrás» regresa a la anterior, con sus filtros
// (los filtros de cada sección se conservan en memoria). La liga compartida del Resumen y la Infografía no cambian el historial.
let NAV_HIST = false;
function marcaHist(v){ if (NAV_HIST || SALA.on || /[?&]resumen-inami\b/.test(location.search)) return; const h = history.state, st = { ianami:true, v:v, dir:S.dir || 0 };
  if (h && h.ianami && h.v===v && (v!=='dir' || h.dir===st.dir)) return;
  try { if (h && h.ianami) history.pushState(st, ''); else history.replaceState(st, ''); } catch(e){} }
window.addEventListener('popstate', e => { const st = e.state; if (!st || !st.ianami) return;
  if (SALA.on){ if (SALA.compartida) return; cerrarSala(); }
  NAV_HIST = true; try { if (st.v==='dir') S.dir = st.dir; irA(st.v); } finally { NAV_HIST = false; } });
try { if (!(history.state && history.state.ianami)) history.replaceState({ ianami:true, v:S.vista || 'pulso', dir:S.dir || 0 }, ''); } catch(e){}   // la vista con la que abre
// Mientras se preparan los datos de una sección: el esqueleto con un aviso claro, y la sección se dibuja en el siguiente cuadro
// (así el aviso alcanza a verse). Si se cambia de sección antes, el dibujo pendiente ya no se hace.
let PREP = 0, NAV_P = null;
const esqPrep = nom => '<div class="esq" role="status" aria-live="polite"><div class="prep"><i></i>Preparando los datos de '+esc(nom)+'…</div><i class="e1"></i><div class="e2"><i></i><i></i><i></i><i></i></div><div class="e3"><i></i><i></i></div></div>';
function preparar(nom, fn){ const t = ++PREP; $('vista-otra').innerHTML = esqPrep(nom); requestAnimationFrame(() => setTimeout(() => { if (t===PREP) fn(); }, 0)); }
function irA(v){ PREP++;
  marcaHist(v);
  if (window.IANAMI_VISTAZO && window.IANAMI_VISTAZO.activa()) window.IANAMI_VISTAZO.cerrar();   // ir a otra sección cierra la vista tablet
  S.vista = v; pintarNav(); const pulso = v==='pulso'; $('vista-pulso').hidden = !pulso; $('vista-otra').hidden = pulso;
  if (pulso){ ajustarAlto(); reencuadrar(); ajustarLienzo(); pintarTodo(); return; }
  if (S.play) detener();
  if (v==='dir'){ const k = DIRS[S.dir || 0].k; if (MODULOS[k] && !modListo(k)){ $('vista-otra').innerHTML = esqPrep(NOM_MOD[k]);
    cargarModulo(k, true).then(() => { if (S.vista!=='dir' || DIRS[S.dir || 0].k!==k) return; if (NAV_P && NAV_P.k===k){ const x = NAV_P; NAV_P = null; window.IANAMI_NAV.ir(x.k, x.p); } else irA('dir'); }, () => {}); return; } }
  if (v==='arma'){ if (!modListo('arma')){ $('vista-otra').innerHTML = esqPrep('Arma tu informe');
      cargarModulo('arma', true).then(() => { if (S.vista==='arma') irA('arma'); }, () => {}); return; }
    preparar('Arma tu informe', () => window.IANAMI_ARMA.pintar($('vista-otra'))); return; }
  if (v==='analizar'){ if (!modListo('analizar')){ $('vista-otra').innerHTML = esqPrep('Informe migratorio');
      cargarModulo('analizar', true).then(() => { if (S.vista==='analizar') irA('analizar'); }, () => {}); return; }
    window.IANAMI_ANALIZAR.pintar($('vista-otra')); return; }
  const F0 = {ss:null, n:null}; let h = '';
  if (v==='dir' && DIRS[S.dir || 0].k==='regulacion' && window.IANAMI_REGULACION){ preparar(NOM_MOD.regulacion, () => window.IANAMI_REGULACION.pintar($('vista-otra'))); return; }   // Regulación tiene su propia vista
  if (v==='dir' && DIRS[S.dir || 0].k==='control' && window.IANAMI_CONTROL){ preparar(NOM_MOD.control, () => window.IANAMI_CONTROL.pintar($('vista-otra'))); return; }      // Control migratorio también
  if (v==='dir' && DIRS[S.dir || 0].k==='proteccion' && window.IANAMI_PROTECCION){ preparar(NOM_MOD.proteccion, () => window.IANAMI_PROTECCION.pintar($('vista-otra'))); return; }   // Protección al migrante
  if (v==='dir') h = htmlDireccion(DIRS[S.dir || 0]);
  else if (v==='bases') h = vistaBases();
  else { const T = {
      analizar:['Analizar','Cruces y comparaciones en un solo lugar.',['Cruzar dos bases por nacionalidad, estado o punto (por ejemplo, ingresos contra rechazos).','Comparar de 2 a 4 nacionalidades, estados, cinturones o CECO lado a lado, con base 100.','Calendario de calor por día y matriz nacionalidad × estado.']],
      prosp:['Prospectiva','Hacia dónde va cada flujo.',['Proyección a 4–8 semanas con su rango.','Fechas en que cambió el comportamiento.','Nacionalidades que se mueven igual y probabilidad de pasar a nivel alto.']],
      contexto:['Contexto','Lo que pasa fuera y explica lo de adentro.',['Línea de tiempo de eventos por país desde 2018, con fuente.','Caravanas: ubicación, tamaño y avance.','Encuentros de la CBP en EE. UU. y cruces por el Darién.','Índices por país: desarrollo humano, paz, fragilidad y riesgo.']] }[v];
    h = '<h1>'+T[0]+'</h1><p>'+T[1]+' Esta sección se construye después; esto es lo que llevará:</p><div class="rej"><div class="caja"><ul>'+T[2].map(x=>'<li>'+x+'</li>').join('')+'</ul></div></div>'; }
  $('vista-otra').innerHTML = h;
}
// ---- Sección Bases: qué trae cada base, hasta cuándo y qué se observó. Todo lo escriben los robots
// (datos/datos.js → bases; datos/observaciones.js → lo que anotó cada robot). Nada se captura a mano.
function obsDe(b){ const l = (b.obs || []).slice(), O = window.IANAMI_OBS || {};
  Object.keys(O).filter(r => r[0]!=='_').forEach(r => (O[r][b.n] || []).forEach(x => { if (l.indexOf(x)<0) l.push(x); })); return l; }
// Estado de cada base contra el corte de la carga: las bases se cargan una vez por semana y el corte es el último día que trae
// la base más reciente; se marcan las que se quedaron antes de ese día. Aparte, si la última carga ya tiene más de 7 días, se avisa.
// Las periódicas (validación de actas, vuelos comerciales, Guatemala-Honduras, documentos vigentes, caravanas) no se cuentan como atrasadas.
const DGS = [['DGCVM','Dirección General de Control y Verificación Migratoria'], ['DGCOR','Dirección General de Coordinación de Oficinas de Representación'], ['DGRAM','Dirección General de Regulación y Archivo Migratorio'],
  ['DGPMV','Dirección General de Protección al Migrante y Vinculación'], ['CBP','Oficina de Aduanas y Protección Fronteriza de EE. UU. (fuente externa)'], ['—','Registro propio']];
const PERIODICAS = /Validación del Registro Civil|vuelos comerciales|Guatemala y Honduras|Documentos vigentes|Caravanas/i;
// Bitácora: qué cambió en los datos en cada carga (la escribe el robot al comparar con la carga anterior; datos/bitacora.js)
function bitacoraBases(){ const L = (window.IANAMI_BITACORA || []).filter(e => e.tipo!=='días nuevos'), N = (window.IANAMI_BITACORA || []).filter(e => e.tipo==='días nuevos');
  const vistos = {}, U = L.filter(e => { const k = e.fecha.slice(0,10)+'|'+e.base+'|'+e.desde+'|'+e.hasta+'|'+e.antes+'|'+e.despues; if (vistos[k]) return false; vistos[k] = 1; return true; });   // dos robots leen la misma base: se anota una vez
  const mes = m => MES12[+m.slice(5,7)-1]+' '+m.slice(0,4), dif = (a, b) => { const d = Math.round(b-a); return (d>=0 ? '+' : '−')+miles(Math.abs(d)); };
  const fila = e => '<tr><td class="x">'+esc(fechaISO(e.fecha.slice(0,10)))+'</td><td><b>'+esc(e.base)+'</b><br><span class="mini">'+esc((e.archivos || []).join(' · '))+'</span></td>'+
    '<td><span class="bs-est '+(e.tipo==='corrección' ? 'n' : 'at')+'">'+esc(e.tipo==='corrección' ? 'Corrección' : 'Cambió lo ya cargado')+'</span></td>'+
    '<td>'+(e.meses || []).map(m => '<b>'+mes(m[0])+'</b>: '+m[1]+' '+(m[1]===1 ? 'día' : 'días')+', '+miles(Math.round(m[2]))+' → '+miles(Math.round(m[3]))+' ('+dif(m[2], m[3])+')').join('<br>')+
    (e.quitados ? '<br><span class="mini">'+e.quitados+' '+(e.quitados===1 ? 'día quedó' : 'días quedaron')+' en cero (no venían en la entrega más reciente)</span>' : '')+'</td></tr>';
  return '<details class="caja bs-bit bs-dg"><summary><span class="bs-dg-n"><b>Cambios en los datos</b> <span>qué cambió en cada carga</span></span><span class="bs-dg-r">'+(U.length ? U.length+' '+(U.length===1 ? 'registro' : 'registros') : 'sin cambios')+'</span></summary><p class="mini">Cada carga se compara con la anterior: aquí queda qué días cambiaron, cuánto había y cuánto hay ahora, y qué archivo lo cambió. Sirve para explicar por qué una cifra ya presentada es distinta hoy.</p>'+
    (U.length ? '<div class="tb-w"><table class="tb bs"><thead><tr><th>Carga</th><th>Base y archivo</th><th>Tipo</th><th>Qué cambió</th></tr></thead><tbody>'+U.slice(0, 60).map(fila).join('')+'</tbody></table></div>'
      : '<p>Sin cambios en días ya cargados'+(N.length ? ': las últimas cargas solo agregaron días nuevos.' : '. La bitácora empieza a llenarse con la próxima carga.')+'</p>')+'</details>'; }
function vistaBases(){
  const P = (window.IANAMI_OBS || {})._periodos || {}, hoy = new Date(), ayer = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate()-1), iso = d => d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'), AY = iso(ayer);
  const dif = (a, b) => Math.round((new Date(a+'T00:00:00') - new Date(b+'T00:00:00'))/864e5);
  const B = (D.bases || []).map(b => Object.assign({}, b, P[b.n] && !b.hasta ? { desde:P[b.n].desde, hasta:P[b.n].hasta, filas:b.filas!=null ? b.filas : P[b.n].filas, pendiente:false } : {}));
  Object.keys(P).forEach(n => { if (!B.some(b => b.n===n)) B.push({ n:n, archivo:P[n].archivo, desde:P[n].desde, hasta:P[n].hasta, filas:P[n].filas, cargado:null }); });
  B.forEach(b => { b.area = (DGS.find(a => a[0]!=='—' && new RegExp('(^|, )'+a[0]+' ').test(b.archivo || '')) || DGS[5])[0]; b.per = PERIODICAS.test(b.n); });
  const diarias = B.filter(b => b.hasta && !b.per), CORTE = diarias.reduce((m, b) => b.hasta>m ? b.hasta : m, ''), CARGA = String(D.generado || '').slice(0, 10), viejo = CARGA ? dif(iso(hoy), CARGA) : 0;
  diarias.forEach(b => { b.atraso = Math.max(0, dif(CORTE, b.hasta)); }); const atras = diarias.filter(b => b.atraso>0).sort((a,b) => b.atraso-a.atraso);
  const estado = b => !b.hasta ? (b.pendiente ? '<span class="bs-est n">Pendiente</span>' : '<span class="bs-est n">Conteo a una fecha</span>')
    : b.per ? '<span class="bs-est n" title="No se envía cada día">Periódica</span><br><span class="mini">último dato: '+fechaISO(b.hasta)+'</span>'
    : b.atraso===0 ? '<span class="bs-est ok">Llega al corte</span>' : '<span class="bs-est '+(b.atraso>7 ? 'mal' : 'at')+'">'+b.atraso+' '+(b.atraso===1 ? 'día' : 'días')+' antes del corte</span>';
  const periodo = b => b.hasta ? '<b>'+fechaISO(b.desde)+'</b><span class="bs-a">→</span><b>'+fechaISO(b.hasta)+'</b>'
    : b.pendiente ? '—' : b.k==='car' ? '<span class="mini">Registro de eventos, sin días</span>' : '<span class="mini">No trae días: es un conteo a una fecha'+(b.cargado ? '. Archivo del '+fechaISO(b.cargado) : '')+'</span>';
  const fila = b => { const ob = obsDe(b), arch = String(b.archivo || '').split(', ');
    return '<tr'+(b.pendiente ? ' class="bs-pend"' : '')+'><td><b>'+esc(b.n)+'</b><br><span class="mini">'+arch.map(esc).join('<br>')+'</span></td>'+
      '<td class="x bs-per">'+periodo(b)+'</td><td>'+estado(b)+'</td>'+
      '<td class="x">'+(b.filas!=null ? miles(b.filas) : '—')+'</td><td class="x">'+(b.faltan!=null ? miles(b.faltan) : '—')+'</td>'+
      '<td class="bs-obs">'+(ob.length ? '<details><summary>'+ob.length+' '+(ob.length===1 ? 'observación' : 'observaciones')+'</summary><ul>'+ob.map(x => '<li>'+esc(x)+'</li>').join('')+'</ul></details>' : '<span class="mini">Sin observaciones</span>')+'</td></tr>'; };
  const fc = d => fechaISO(d), vj = viejo>7 ? ' <span class="bs-est mal">La última carga fue hace '+viejo+' días: toca actualizar.</span>' : '';
  const resumen = !diarias.length ? '' : atras.length===0
    ? '<div class="bs-sem ok"><b>Datos al '+fc(CORTE)+'</b>'+(CARGA ? ' (carga del '+fc(CARGA)+')' : '')+': las '+diarias.length+' bases que se envían por día llegan a esa fecha.'+vj+'</div>'
    : '<div class="bs-sem at"><b>Datos al '+fc(CORTE)+'</b>'+(CARGA ? ' (carga del '+fc(CARGA)+')' : '')+': '+(diarias.length-atras.length)+' de '+diarias.length+' bases que se envían por día llegan a esa fecha.'+vj+
      ' Se quedaron antes:<div class="bs-sem-g">'+[...new Set(atras.map(b => b.atraso))].map(n => { const l = atras.filter(b => b.atraso===n);
        return '<p><b>'+n+' '+(n===1 ? 'día' : 'días')+' antes</b> <small>(llegan al '+fc(l[0].hasta)+')</small>: '+l.map(b => esc(b.n)+' <small>'+b.area+'</small>').join(' · ')+'</p>'; }).join('')+'</div>'+
      '<p class="bs-sem-n">En el tablero, los días que le faltan a una base se marcan como pendientes y no entran en las comparaciones. Las periódicas (validación de actas, vuelos comerciales, Guatemala y Honduras, documentos vigentes y caravanas) no se cuentan aquí.</p></div>';
  const grupo = a => { const l = B.filter(b => b.area===a[0]).sort((x,y) => (x.per?1:0)-(y.per?1:0) || (y.atraso||0)-(x.atraso||0) || x.n.localeCompare(y.n)); if (!l.length) return '';
    const d = l.filter(b => b.hasta && !b.per), al = d.filter(b => b.atraso===0).length, at = d.length-al, pe = l.length-d.length;
    return '<details class="bs-dg"><summary><span class="bs-dg-n"><b>'+a[0]+'</b> <span>'+esc(a[1])+'</span></span><span class="bs-dg-r">'+l.length+' '+(l.length===1 ? 'base' : 'bases')+
      (d.length ? ' · <span class="bs-est '+(at ? 'at' : 'ok')+'">'+(at ? at+' antes del corte' : 'todas al corte')+'</span>' : '')+(pe ? ' · '+pe+' periódica'+(pe>1 ? 's' : '') : '')+'</span></summary>'+
      '<div class="tb-w"><table class="tb bs"><thead><tr><th>Base y archivos</th><th>Periodo<br><small>primer día → último día con datos</small></th><th>¿Llega al corte?<br><small>'+(CORTE ? fc(CORTE) : '')+'</small></th><th>Renglones</th><th>Días sin datos<br><small>dentro del periodo</small></th><th>Observaciones</th></tr></thead><tbody>'+l.map(fila).join('')+'</tbody></table></div></details>'; };
  return '<h1>Bases</h1><p>Qué trae cada base, del primer al último día con datos, y si llega al corte de la carga, agrupadas por dirección general. Toca una dirección para ver sus bases, y «observaciones» para leerlas. Última conversión: '+esc(D.generado)+'.</p>'+resumen+
    '<div class="caja bs-c">'+DGS.map(grupo).join('')+'<span class="nota">«Días sin datos»: días entre el primero y el último en que el archivo no trae ningún renglón (por ejemplo, fines de semana sin atención). «Periódica»: base que no se envía cada día. Cada base puede venir en varios archivos (histórico, envíos diarios y correcciones): gana la entrega más reciente y cada archivo manda en todo su periodo, así que nada se suma dos veces. Una corrección se nombra «… CORRECCION 2026-09.xlsx» y reemplaza el mes completo. Las observaciones las escribe el proceso al leer cada archivo; lo que haya que corregir se corrige en el archivo que entrega la dirección.</span></div>'+bitacoraBases();
}
// El mapa ocupa el alto que queda de la pantalla, dejando asomar la franja de cajas.
function ajustarAlto(){
  const lz = $('lz');
  if (window.innerWidth<=980 || window.innerHeight<=520){ lz.style.removeProperty('--alto'); return; }
  const arriba = lz.getBoundingClientRect().top + window.scrollY, pie = document.querySelector('.tiempo').getBoundingClientRect().height;
  const libre = window.innerHeight - arriba - pie - 44*E, ancho = lz.clientWidth;
  lz.style.setProperty('--alto', Math.round(Math.max(300*E, Math.min(libre, ancho*0.66)))+'px');
}
function escala(){ const n = window.innerWidth>=2200 ? Math.min(4, window.innerWidth/1920) : 1; if (Math.abs(n-E)<0.02) return false; E = n; document.documentElement.style.setProperty('--e', E.toFixed(3)); return true; }

/* ==== [13] PANTALLA COMPLETA (MODO SALA) =========================== */
// El mapa a toda la pantalla con lo principal encima: una cifra grande, cuatro datos, una frase de un vistazo,
// una gráfica de barras y la barra de tiempo. Usa el mismo motor del Pulso (periodo, filtro, día del cursor),
// así que el mapa, las cifras y la reproducción siempre dicen lo mismo. Al salir, el Pulso queda como estaba.
const SALA = { on:false, cmp:false, A:null, B:null, guarda:null, gr:null, anim:{}, por:{}, fijo:false };
const PALABRA = { ing:'ingresos al país', rech:'rechazos', tram:'trámites concluidos', resc:'rescates', pres:'presentados en estación', can:'NNA y acompañantes canalizados al DIF', ret:'retornados', recib:'recibidos de EE. UU.', rep:'mexicanos repatriados', cbp:'encuentros de la CBP (EE. UU.)', co:'trámites que no expiden tarjeta', va:'solicitudes de validación de actas' };
const ORDEN_SALA = ['ing','resc','rep','rech','can','pres'];
const IND_SALA = [['', 'Resumen', 'Panorama', 'Lo principal de todo en un vistazo'], ['ing', 'Regular', 'Ingresos', 'Extranjeros y mexicanos que entraron'], ['tram', 'Regular', 'Trámites', 'Trámites migratorios concluidos'],
  ['resc', 'Irregular', 'Rescatados', 'Rescates (eventos) según las O.R.'], ['can', 'Irregular', 'Canalizados', 'NNA y acompañantes al DIF'], ['rep', 'Desde EE. UU.', 'Repatriados', 'Mexicanos devueltos por EE. UU.']].concat(IND.cbp ? [['cbp', 'Desde EE. UU.', 'Encuentros', 'Los registra la CBP en EE. UU.']] : []);
const ICONO_PAN = 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z';
const MES_L = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
// Suma de un indicador entre los días a y b (de las bases completas), con estados ss y nacionalidad n (número, lista o null)
function rangoBase(k, a, b, ss, n){
  if (Array.isArray(n)){ let t = 0; n.forEach(x => t += rangoBase(k, a, b, ss, x)); return t; }
  let t = 0; a = Math.max(0, a); b = Math.min(D0.dias, b); if (conEdo(ss) && sinEdo(k)) return 0;
  if (ss && n!=null){ const C = CUBO0[k], E0 = D0.ends;            // estado × nacionalidad: por semana, prorrateado
    for (let w=0; w<E0.length; w++){ const wa = w ? E0[w-1] : 0, wb = E0[w], x = Math.max(wa,a), y = Math.min(wb,b); if (y<=x) continue;
      let s = 0; ss.forEach(e => s += C[(w*NS+e)*NN+n]); t += s*(y-x)/(wb-wa); } return t; }
  if (ss){ const A = D0.ds[k]; for (let d=a; d<b; d++) for (let j=0;j<ss.length;j++) t += A[d*NS+ss[j]]; return t; }
  if (n!=null){ const A = D0.dn[k]; for (let d=a; d<b; d++) t += A[d*NN+n]; return t; }
  const A = D0.daily[k]; for (let d=a; d<b; d++) t += A[d]; return t;
}
// «Ingresos» es el total (extranjeros + mexicanos), igual que en el Pulso. En Control, los rechazos no cuentan mexicanos (igual que su vista)
const sinMx = (k, n) => k==='rech' && SALA.perfil==='control' && n==null;
// «… (X extranjeros y Y mexicanos)»: lo que se dice siempre que aparece el total de ingresos (sin filtro de país)
const partIng = (ss, n, f) => { if (n!=null) return ''; const t = acum('ing', ss, null), m = acum('ing', ss, MX); return t ? ' ('+(f || cortoK)(t-m)+' extranjeros y '+(f || cortoK)(m)+' mexicanos)' : ''; };   // en Control, los rechazos tampoco cuentan mexicanos (igual que su vista)
const valAcum = (k, ss, n) => k==='co' ? coRango(P0, P0+Math.min(S.dia, ND), ss, n) : acum(k, ss, n) - (sinMx(k, n) ? acum(k, ss, MX) : 0);
const valRango = (k, a, b, ss, n) => k==='co' ? coRango(a, b, ss, n) : rangoBase(k, a, b, ss, n) - (sinMx(k, n) ? rangoBase(k, a, b, ss, MX) : 0);
// La misma unidad que --u en el CSS: centésima del rectángulo 16:9 que cabe; en columna (teléfono o vertical), fija
const uSala = () => { const w = innerWidth, h = innerHeight; return (w<=760 || w/h<=1.25 || h<=560) ? 13.6*Math.max(1, Math.min(2.6, w/390, h/700)) : Math.min(w/100, h*1.7778/100); };
const nFde = (k, F) => IND[k].nat ? F.nd : null;
const salaInd = () => (SALA.on && SALA.extra) || S.ind || null;   // null = Panorama; «co» y «va» son propios de Regulación (debajo, el mapa sigue en trámites)
const nomRango = (a, b) => { const f0 = fechaBase(a), f1 = fechaBase(b-1);
  if (f0.getDate()===1 && isoDe(new Date(f1.getFullYear(), f1.getMonth(), f1.getDate()+1)).slice(8)==='01' && f0.getMonth()===f1.getMonth() && f0.getFullYear()===f1.getFullYear()) return MES_L[f0.getMonth()]+' '+f0.getFullYear();
  return f0.getDate()+' '+MES12[f0.getMonth()]+(f0.getFullYear()!==f1.getFullYear() ? ' '+f0.getFullYear() : '')+' – '+f1.getDate()+' '+MES12[f1.getMonth()]+' '+f1.getFullYear(); };
const nomCortoR = r => { const t = nomRango(r[0], r[1]); return /^[a-z]+ \d{4}$/.test(t) ? t.slice(0,3)+' '+t.slice(-4) : t; };
const cortoK = v => v>=1e6 ? (v/1e6).toFixed(2)+' M' : v>=1e4 ? (v/1e3).toFixed(1)+' mil' : miles(v);
const cifraG = v => { const s = cortoK(v), m = s.match(/^(.*) ([Mk])$/); return m ? m[1]+'<small>'+m[2]+'</small>' : s; };
// Cifras que se mueven: de lo que muestran a su nuevo valor (como los indicadores del Pulso)
function mover(el, v, fmt, dur){
  if (!el) return; if (el._anim && el._v===v) return;                   // ya va hacia ese valor
  const de = el._cur==null ? 0 : el._cur; el._v = v; cancelAnimationFrame(el._raf || 0);
  if (reducido() || de===v){ el._cur = v; el._anim = false; el.innerHTML = fmt(v); return; }
  el._anim = true; const t0 = performance.now(), paso = t => { const e = Math.min(1, Math.max(0, (t-t0)/dur)), f = 1-Math.pow(1-e,3); el._cur = de + (v-de)*f; el.innerHTML = fmt(el._cur);
    if (e<1) el._raf = requestAnimationFrame(paso); else el._anim = false; };
  el._raf = requestAnimationFrame(paso);
}
// Periodos disponibles para comparar: meses completos y, cuando haya datos, antes y con Trump
function mesesBase(){ const l = []; let f = new Date(INICIO0.getFullYear(), INICIO0.getMonth(), 1);
  while (true){ const a = idxBase(isoDe(f)), sig = new Date(f.getFullYear(), f.getMonth()+1, 1), b = idxBase(isoDe(sig)); if (a>=D0.dias) break;
    if (a>=0 && b<=D0.dias) l.push([a, b]); f = sig; } return l; }
const hayTrump = () => idxBase('2025-01-20') < D0.dias - 27;
function cmpInicial(){
  if (hayTrump()) return [[idxBase('2024-10-01'), idxBase('2025-01-20')], [idxBase('2025-01-20'), D0.dias]];
  const m = mesesBase(); return m.length>=2 ? [m[m.length-2], m[m.length-1]] : null;
}
function menuSlc(){ const m = $('sl-cm'); if (m) m.innerHTML = '<button type="button" data-slc="liga"><b>Copiar liga</b><span>abre esta misma infografía</span></button><button type="button" data-slc="pdf"><b>Descargar PDF</b><span>de lo que estás viendo</span></button><button type="button" data-slc="wa"><b>Enviar por WhatsApp</b><span>manda la liga de esta infografía</span></button>'; }
function abrirSala(pf){
  if (SALA.on) return; if (S.play) detener();
  SALA.perfil = PERFILES[pf] ? pf : 'pulso';
  SALA.guarda = { vista:S.vista, tema:S.tema, per:S.per, desde:S.desde, hasta:S.hasta, anio:S.anio, mes:S.mes, ind:S.ind, sel:S.sel, region:S.region, agr:S.agr, p:[P0, P1], dia:S.dia };
  SALA.on = true; SALA.cmp = false; SALA.anim = {}; SALA.extra = null;
  S.sel = null; S.region = null; S.ind = null; S.agr = 'e';      // entra limpia: la consulta del Pulso no se arrastra (al salir regresa)
  if (S.vista!=='pulso'){ SALA.guarda.proceso = true; S.vista = 'pulso'; $('vista-pulso').hidden = false; $('vista-otra').hidden = true; }   // abierta desde un proceso: el mapa del Pulso cubre la pantalla
  const m = $('mapa'); m.classList.add('sala'); document.body.classList.add('en-sala');
  if (m.requestFullscreen && !reducido()) m.requestFullscreen().catch(() => {});
  const L = document.createElement('div'); L.className = 'sl'; L.id = 'sala'; L.setAttribute('role','region'); L.setAttribute('aria-label','Pulso en pantalla completa');
  L.innerHTML =
    '<header class="sl-h">'+
      '<div class="sl-lo">IA-NAMI<small>'+esc(perfilSala().nom)+'</small></div>'+
      '<div class="sl-bus"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>'+
        '<input id="sl-q" type="search" autocomplete="off" placeholder="Busca un país o un estado (O.R.)" aria-label="Buscar país o estado"><button type="button" id="sl-qx" aria-label="Quitar" hidden>×</button><div class="sl-res" id="sl-res" hidden></div></div>'+
      '<label class="sl-dd"><small>Región</small><select id="sl-reg"></select></label>'+
      '<div class="sl-dd sl-ib"><small>Indicador</small><button type="button" id="sl-indb" aria-haspopup="listbox" aria-expanded="false"></button><div class="sl-im" id="sl-im" role="listbox" aria-label="Indicador" hidden></div></div>'+
      '<div class="sl-per"><small>Periodo</small><div class="sl-seg" id="sl-seg"></div></div>'+
      '<div class="sl-cmpb" id="sl-cmpb"></div>'+
      '<div class="sl-corte" id="sl-corte"></div>'+
      '<div class="sl-cm" id="sl-cm" hidden></div>'+
      '<button type="button" class="sl-x sl-liga" id="sl-liga" aria-label="Copiar liga de esta infografía" data-ayuda="<b>Compartir</b><br>Copia la liga de esta infografía, con el mismo periodo e indicador."><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15V3M7 8l5-5 5 5M5 14v6h14v-6"/></svg></button>'+
      '<button type="button" class="sl-x" id="sl-x" aria-label="Salir de pantalla completa" title="Salir (Esc)"><svg width="14" height="14" viewBox="0 0 12 12"><path d="M2 2l8 8M10 2l-8 8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>'+
    '</header>'+
    '<div class="sl-pop" id="sl-pop" hidden></div>'+
    '<div class="sl-ctx sl-e" style="--d:.05s" id="sl-ctx"></div>'+
    '<section class="sl-a"><div class="sl-tri" id="sl-tri"></div><div class="sl-big sl-e" style="--d:.12s" id="sl-big">0</div><div class="sl-cap sl-e" style="--d:.2s" id="sl-cap"></div><div class="sl-dl sl-e" style="--d:.24s" id="sl-dl"></div>'+
      '<div class="sl-g" id="sl-g"></div></section>'+
    '<p class="sl-fr sl-e" style="--d:.3s" id="sl-fr"></p>'+
    '<section class="sl-q sl-e" style="--d:.38s"><div class="sl-qt" id="sl-qt"></div><div class="sl-qs" id="sl-qs"></div><div class="sl-qc" id="sl-qc"></div></section>'+
    '<section class="sl-t sl-e" style="--d:.44s"><div class="sl-tl" id="sl-tl"></div>'+
      '<div class="sl-tb"><button type="button" class="sl-pl" id="sl-pl" aria-label="Reproducir el periodo"></button><button type="button" class="sl-todo" id="sl-todo" title="Regresa al periodo completo">Ver todo</button></div>'+
      '<svg id="sl-tg" role="slider" tabindex="0" aria-label="Día del periodo"></svg><div class="sl-fte" id="sl-fte"></div></section>';
  $('lz').appendChild(L);
  $('sl-reg').innerHTML = '<option value="">Todo el mundo</option>'+Object.keys(REGIONES).map(r => '<option value="'+r+'">'+REGIONES[r][0]+'</option>').join('');
  const IS = perfilSala().inds;
  $('sl-im').innerHTML = IS.map((x,i) => (i===0 || IS[i-1][1]!==x[1] ? '<span class="sl-ig">'+x[1]+'</span>' : '')+
    '<button type="button" role="option" data-ind="'+x[0]+'"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="'+(x[0] ? ICONO[x[0]] : ICONO_PAN)+'"/></svg><span><b>'+x[2]+'</b><small>'+x[3]+'</small></span></button>').join('');
  document.addEventListener('pointerdown', cerrarIndSala, true);
  menuSlc(); L.addEventListener('click', clicSala); L.addEventListener('change', cambioSala);
  $('sl-q').addEventListener('input', buscarSala); $('sl-q').addEventListener('keydown', e => { if (e.key==='Enter'){ elegirSala(0); e.preventDefault(); } if (e.key==='Escape'){ if (!$('sl-res').hidden){ $('sl-res').hidden = true; e.stopPropagation(); } else e.target.blur(); } });
  const tg = $('sl-tg'); tg.addEventListener('pointerdown', e => { if (SALA.extra==='va') return; if (S.play) detener(); fijarDia(diaSala(e)); tg.setPointerCapture(e.pointerId); });
  tg.addEventListener('pointermove', e => { if (e.buttons && SALA.extra!=='va') fijarDia(diaSala(e)); });
  tg.addEventListener('keydown', e => { if (SALA.extra==='va') return; if (e.key==='ArrowLeft'){ fijarDia(S.dia-1); e.preventDefault(); } if (e.key==='ArrowRight'){ fijarDia(S.dia+1); e.preventDefault(); } });
  setTimeout(() => { reencuadrar(); ajustarLienzo(); rehacerMapa(); S.modoVista = 'mundo'; prepararVuelo(); volarSala(); }, 60);   // entra al mundo completo; rehacerMapa pinta todo, sala incluida
}
function cerrarIndSala(e){ const m = $('sl-im'); if (m && !m.hidden && !e.target.closest('.sl-ib')){ m.hidden = true; $('sl-indb').setAttribute('aria-expanded', false); } }
function cerrarSala(){
  if (!SALA.on) return; if (S.play) detener(); document.removeEventListener('pointerdown', cerrarIndSala, true);
  SALA.on = false; SALA.extra = null; $('mapa').classList.remove('sl-va'); const g = SALA.guarda; if (SALA.gr){ SALA.gr.dispose(); SALA.gr = null; }
  const L = $('sala'); if (L) L.remove();
  $('mapa').classList.remove('sala'); document.body.classList.remove('en-sala');
  if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
  S.tema = g.tema; $('mapa').dataset.m = S.tema; COL.act = {};
  Object.assign(S, { per:g.per, desde:g.desde, hasta:g.hasta, anio:g.anio, mes:g.mes, ind:g.ind, sel:g.sel, region:g.region, agr:g.agr });
  aplicarPeriodo(g.p[0], g.p[1]); S.dia = Math.min(g.dia, ND); S.t = S.dia; $('tgraf').setAttribute('aria-valuemax', ND);
  if (g.proceso){ S.vista = g.vista; $('vista-pulso').hidden = true; $('vista-otra').hidden = false; return; }   // de regreso al proceso, tal como estaba
  setTimeout(() => { ajustarAlto(); reencuadrar(); ajustarLienzo(); rehacerMapa(); }, 60);
}
// ---- controles
function clicSala(e){
  const cm = $('sl-cm'); if (cm && !cm.hidden && !e.target.closest('#sl-cm, #sl-liga')) cm.hidden = true;   // el menú de compartir se cierra al tocar fuera
  const b = e.target.closest('button'); if (!b) return;
  if (b.id==='sl-x'){ if (!SALA.compartida) cerrarSala(); return; }
  if (b.id==='sl-liga'){ const m = $('sl-cm'); m.hidden = !m.hidden; return; }
  if (b.dataset.slc==='liga'){ $('sl-cm').hidden = true; copiarLiga(); return; }
  if (b.dataset.slc==='wa'){ $('sl-cm').hidden = true; window.open('https://wa.me/?text='+encodeURIComponent('Infografía IA-NAMI: '+ligaVista()), '_blank', 'noopener'); return; }
  if (b.dataset.slc==='pdf'){ const m = $('sl-cm'); m.innerHTML = '<p class="sl-nota" style="margin:6px 8px">Generando PDF…</p>';
    hacerPDF().then(r => { r.pdf.save(r.nombre); m.hidden = true; menuSlc(); avisoBreve('PDF descargado'); }, () => { m.hidden = true; menuSlc(); avisoBreve('No se pudo generar el PDF. Intenta de nuevo.'); }); return; }
  if (b.id==='sl-indb'){ const m = $('sl-im'), ab = m.hidden; m.hidden = !ab; b.setAttribute('aria-expanded', ab); if (ab){ const on = m.querySelector('.on') || m.querySelector('button'); on.focus(); } return; }
  if (b.dataset.ind!=null){ $('sl-im').hidden = true; $('sl-indb').setAttribute('aria-expanded', false); const v = b.dataset.ind || null; SALA.extra = v==='co' || v==='va' ? v : null; S.ind = SALA.extra ? 'tram' : v; if (SALA.extra==='va' && S.play) detener(); if (S.ind==='rep' && S.sel && S.sel.t==='n') S.sel = null; if (S.ind && sinEdo(S.ind) && S.sel && S.sel.t!=='n') S.sel = null; pintarTodo(); return; }
  if (b.dataset.por){ SALA.por[salaInd() || 'resc'] = b.dataset.por; pintarSala(false); return; }
  if (b.id==='sl-pl'){ reproducir(); return; }
  if (b.id==='sl-todo'){ verTodo(); return; }
  if (b.id==='sl-qx'){ S.sel = null; $('sl-q').value = ''; b.hidden = true; prepararVuelo(); pintarTodo(); S.modoVista = 'mundo'; volarSala(); return; }
  if (b.dataset.sr!=null){ elegirSala(+b.dataset.sr); return; }
  if (b.dataset.sp){ const p = b.dataset.sp;
    if (p==='cmp'){ abrirComparar(); return; }
    SALA.cmp = false; $('sl-pop').hidden = true; S.per = p; cambiarPeriodo(); return; }
  if (b.id==='sl-cmpe'){ abrirComparar(); return; }
  if (b.id==='sl-cmpok'){ const A = $('sl-ca').value.split(',').map(Number), B = $('sl-cb').value.split(',').map(Number);
    if (A[0]>=B[0] && A[0]<B[1]){ $('sl-cmsg').textContent = 'El periodo de referencia tiene que ser anterior al que comparas.'; return; }
    aplicarComparar(A, B); return; }
  if (b.dataset.cpre){ const c = cmpInicial(); if (c){ aplicarComparar(c[0], c[1]); } return; }
  if (b.id==='sl-cmpno'){ $('sl-pop').hidden = true; return; }
}
function cambioSala(e){
  const id = e.target.id;
  if (id==='sl-ca-y' || id==='sl-cb-y'){ const s = $(id.slice(0, -2)), mes = s.selectedOptions[0] ? s.selectedOptions[0].textContent : ''; s.innerHTML = mesesDe(+e.target.value); const o = [...s.options].find(x => x.textContent===mes); if (o) o.selected = true; return; }
  if (id==='sl-reg'){ S.region = e.target.value || null; if (S.sel && S.sel.t==='n') S.sel = null; prepararVuelo(); pintarTodo(); if (S.region) volarConMexico(REGIONES[S.region][1]); else { S.modoVista = 'mundo'; volarSala(); } }

}
// Comparar dos periodos: primero el año y luego el mes, para que la lista no crezca sin fin con los años
const anioDe = m => fechaBase(m[0]).getFullYear();
function mesesDe(y, sel){ return mesesBase().filter(m => anioDe(m)===y).map(m => '<option value="'+m[0]+','+m[1]+'"'+(sel && sel[0]===m[0] && sel[1]===m[1] ? ' selected' : '')+'>'+['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'][fechaBase(m[0]).getMonth()]+'</option>').join(''); }
function opcionesCmp(sel, id){ const M = mesesBase(), y0 = sel ? fechaBase(sel[0]).getFullYear() : anioDe(M[M.length-1]), ys = [...new Set(M.map(anioDe))];
  return '<span class="sl-ym"><select id="'+id+'-y" aria-label="Año">'+ys.map(y => '<option'+(y===y0 ? ' selected' : '')+'>'+y+'</option>').join('')+'</select><select id="'+id+'" aria-label="Mes">'+mesesDe(y0, sel)+'</select></span>'; }
function abrirComparar(){
  const c = SALA.cmp ? [SALA.A, SALA.B] : cmpInicial(), p = $('sl-pop'); if (!c){ return; }
  const trumpTxt = hayTrump() ? '<button type="button" data-cpre="1" class="sl-pre">Antes de Trump vs. con Trump</button>' : '<p class="sl-nota">«Antes de Trump vs. con Trump» se activa cuando las bases lleguen a 2025 (hoy terminan el '+fechaISO(D.corte)+').</p>';
  p.innerHTML = '<b>Comparar dos periodos</b><p class="sl-nota">Las cifras se comparan por día, así los periodos pueden durar distinto.</p>'+trumpTxt+
    '<label>Referencia'+opcionesCmp(c[0], 'sl-ca')+'</label><label>Contra'+opcionesCmp(c[1], 'sl-cb')+'</label>'+
    '<span class="sl-cmsg" id="sl-cmsg"></span><div class="sl-pb"><button type="button" id="sl-cmpno">Cancelar</button><button type="button" id="sl-cmpok" class="pri">Comparar</button></div>';
  p.hidden = false;
}
function aplicarComparar(A, B){
  SALA.cmp = true; SALA.A = A; SALA.B = B; $('sl-pop').hidden = true;
  if (S.play) S.play = false; S.per = 'pers'; S.desde = isoDe(fechaBase(B[0])); S.hasta = isoDe(fechaBase(B[1]-1));
  aplicarPeriodo(B[0], B[1]); S.dia = ND; S.t = ND; $('tgraf').setAttribute('aria-valuemax', ND); pintarTodo();
}
function verTodo(){ S.play = false; S.dia = ND; S.t = ND; pintarTodo(); }
// ---- buscador: países y estados (las O.R. son por estado)
let hallSala = [];
function buscarSala(){
  const q = sinAcento($('sl-q').value.trim()), el = $('sl-res'); $('sl-qx').hidden = !$('sl-q').value && !S.sel;
  if (!q){ el.hidden = true; return; }
  const L = INDICE.filter(x => x.t==='Nacionalidad' || x.t==='Estado');
  hallSala = L.filter(x => x.q.indexOf(q)===0).concat(L.filter(x => x.q.indexOf(q)>0)).slice(0,7);
  el.innerHTML = hallSala.length ? hallSala.map((x,i) => '<button type="button" data-sr="'+i+'" class="'+(i?'':'act')+'"><span>'+esc(x.n)+'</span><small>'+(x.t==='Estado' ? 'estado · O.R.' : 'país')+'</small></button>').join('') : '<span class="sl-nada">Sin coincidencias</span>';
  el.hidden = false;
}
function elegirSala(i){
  const x = hallSala[i]; if (!x) return; $('sl-res').hidden = true; $('sl-q').value = x.n; $('sl-qx').hidden = false;
  if (x.sel.t==='n') S.region = null;                          // un país se ve en el mismo modo en que estaba: en Panorama, lo general de ese país; con un indicador, ese indicador
  fijarSel(x.sel, true);
}
const diaSala = e => { const r = $('sl-tg').getBoundingClientRect(); return (e.clientX-r.left)/r.width*ND + 0.5; };
// ---- pintar
function pintarSala(soloTiempo){
  const L = $('sala'); if (!L) return;
  const F = filtro(), k = salaInd(), t = TM[S.tema], nF = k ? nFde(k, F) : null, fin = S.dia>=ND && !S.play;
  L.classList.toggle('pan', !k); L.classList.toggle('va', k==='va'); $('mapa').classList.toggle('sl-va', k==='va');
  const ent = S.sel ? nombreSel() : S.region ? nombreRegion() : 'todo el mundo';
  const per = nomRango(P0, P1);
  // controles
  if (!soloTiempo){
    $('sl-reg').value = S.region || '';
    const xi = perfilSala().inds.find(x => x[0]===(k || '')) || [k, '', IND[k] ? IND[k].n : k, ''];
    $('sl-indb').innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="'+(k ? ICONO[k] : ICONO_PAN)+'"/></svg><span>'+esc(xi[2])+'</span><em>▾</em>';
    $('sl-im').querySelectorAll('[data-ind]').forEach(o => { const on = o.dataset.ind===(k || ''); o.classList.toggle('on', on); o.setAttribute('aria-selected', on); });
    if (document.activeElement!==$('sl-q')){ $('sl-q').value = S.sel && S.sel.t!=='p' ? nombreSel() : ''; $('sl-qx').hidden = !S.sel; }
    $('sl-seg').innerHTML = [['shein','Sheinbaum'],['trump','Trump'],['cmp','Comparar']].map(o => { const ok = o[0]==='trump' ? hayTrump() : true, on = o[0]==='cmp' ? SALA.cmp : !SALA.cmp && S.per===o[0];
      return '<button type="button" data-sp="'+o[0]+'" class="'+(on?'on':'')+'"'+(ok ? '' : ' disabled title="Sin datos del periodo Trump: las bases llegan al '+fechaISO(D.corte)+'"')+'>'+o[1]+'</button>'; }).join('');
    $('sl-cmpb').innerHTML = SALA.cmp ? '<button type="button" id="sl-cmpe" class="sl-dd sl-cb"><small>Comparación</small><span>'+nomCortoR(SALA.A)+' <em>→</em> '+nomCortoR(SALA.B)+' <i>▾</i></span></button>' : '';
    const ah = new Date();
    $('sl-corte').innerHTML = '<span>Datos al <b>'+fechaISO(D.corte)+'</b></span><span>consultado '+ah.getDate()+' '+MES12[ah.getMonth()]+' '+ah.getFullYear()+', '+String(ah.getHours()).padStart(2,'0')+':'+String(ah.getMinutes()).padStart(2,'0')+'</span>';
    $('sl-ctx').innerHTML = '<span class="k">Estás viendo</span><b>'+(k ? cap1(PALABRA[k]) : perfilSala().ctx)+'</b><i>·</i>'+esc(ent)+'<i>·</i>'+(SALA.cmp ? esc(nomRango(SALA.B[0], SALA.B[1]))+' vs. '+esc(nomRango(SALA.A[0], SALA.A[1]))+', por día' : esc(per));
    $('sl-fte').textContent = 'Fuente'+(perfilSala().orden.length>1 ? 's' : '')+': '+fuentesSala(k || perfilSala().mapa || 'ing')+' · el mapa muestra '+(SALA.cmp ? nomRango(SALA.B[0], SALA.B[1]) : 'el periodo')+(fin ? '' : ' hasta el '+fechaLarga(S.dia-1));
  }
  if (k==='va'){ pintarVa(F, t); tapasSala(); return; }            // periodo propio: nada de lo de abajo aplica
  // cifra principal
  const dur = S.play ? 200 : SALA.anim.big ? 650 : 1100; SALA.anim.big = true;
  let pa = null, pb = null;
  if (!k) panoramaSala(F, t, dur);
  else if (SALA.cmp){ pa = valRango(k, SALA.A[0], SALA.A[1], F.ss, nF)/(SALA.A[1]-SALA.A[0]); pb = valRango(k, SALA.B[0], SALA.B[1], F.ss, nF)/(SALA.B[1]-SALA.B[0]);
    mover($('sl-big'), pb, cifraG, dur);
    $('sl-cap').innerHTML = cap1(PALABRA[k])+' <u>por día</u> en '+esc(nomRango(SALA.B[0], SALA.B[1]));
    $('sl-dl').innerHTML = pa>0 ? flecha(pa, pb)+' vs. '+esc(nomRango(SALA.A[0], SALA.A[1]))+', que tuvo '+cortoK(pa)+' por día' : 'sin registros en '+esc(nomRango(SALA.A[0], SALA.A[1]));
  } else {
    const v = valAcum(k, F.ss, nF), dias = Math.max(1, Math.min(S.dia, finDatos(k)));
    mover($('sl-big'), v, cifraG, dur);
    $('sl-cap').innerHTML = cap1(PALABRA[k])+(fin ? ' en el periodo' : ' hasta el '+fechaLarga(S.dia-1));
    $('sl-dl').innerHTML = '<b>'+cortoK(v/dias)+'</b> por día · '+dias+' días'+(k==='ing' && nF==null ? (x => x ? ' · '+x.slice(2, -1) : '')(partIng(F.ss, null)) : '');
  }
  // debajo de la cifra: el desglose del indicador
  const otros = k && k!=='co' ? ORDEN_SALA.filter(x => x!==k && (F.nd==null || IND[x].nat) && x!=='tram').slice(0,4) : [], G = $('sl-g');
  if (k) desgloseSala(k, F, t, dur); else G.innerHTML = '', G.dataset.k = '';
  // frase de un vistazo
  $('sl-fr').innerHTML = k ? fraseSala(k, F, nF, pa, pb, otros) : frasePanorama(F);
  tapasSala();
  if (k) pintarBarrasSala(k, F, nF); else cambiosSala(F, t);
  pintarTiempoSala(k || perfilSala().mapa || 'ing', F);
}
const cap1 = s => s.charAt(0).toUpperCase()+s.slice(1);
// Solo cambios con peso: un país que pasa de 20 a 1 al día no le dice nada a quien decide
const relevante = a => a.k && a.t!=='car' && (a.t==='cambio' || a.t==='pico' || Math.max(a.a||0, a.b||0)*cmpN() >= 300);
const ventanaCmp = () => textoCmp().replace(' vs. la anterior','');
function flecha(a, b){ const x = (b/a-1)*100; if (Math.abs(x)<0.5) return '<span class="ig">= sin cambio</span>'; return '<span class="'+(x<0?'baja':'sube')+'">'+(x<0?'▼ ':'▲ ')+Math.abs(x).toFixed(Math.abs(x)<10 ? 1 : 0)+'%</span>'; }
function fuentesSala(k){ const f = { co:'DGRAM', va:'DGRAM', ing:'DGCVM', rech:'DGCVM', tram:'DGRAM', resc:'DGCOR', pres:'DGCVM', can:'SIRENNA', ret:'DGCOR', recib:'DGCOR', rep:'DGPMV', cbp:'CBP' };
  const l = [...new Set([k].concat(perfilSala().orden).map(x => f[x]))]; return l.length>1 ? l.slice(0,-1).join(', ')+' y '+l[l.length-1] : l[0]; }
// Reparto de un indicador en el periodo (en Control, los rechazos sin mexicanos, igual que su vista)
function compSala(key, F){ const ss = F.ss, n = F.nd, v = comp(key, ss, n);
  if (key==='rech_det' && SALA.perfil==='control' && n==null){ const m = comp(key, ss, MX); return v.map((x,i) => Math.max(0, x - m[i])); } return v; }
function cbpTotal(F){ return cbpAhora(F).reduce((a,y) => { a.v += y.v; a.mx += y.mx; y.ag.forEach((z,i) => a.ag[i] += z); return a; }, { v:0, mx:0, ag:[0,0,0] }); }
function repartos(k, F){ const z = (key) => compSala(key, F);
  if (k==='ing'){ const v = z('ing_via'); return [[['Aérea',v[0]],['Terrestre',v[1]],['Marítima',v[2]]]]; }
  if (k==='tram'){ const v = z('tram_se'), sx = [['Hombres',suma(v,0,8)],['Mujeres',suma(v,8,16)]];
    if (SALA.perfil!=='regulacion') return [sx];
    const ti = z('tram_tipo').map((x,i) => [CORTO_TRAM(D.tramTipos[i]), x, D.tramTipos[i]]).filter(r => r[2]!=='Otros').sort((a,b) => b[1]-a[1]), T = z('tram_tipo').reduce((a,x) => a+x, 0);
    const tp = ti.slice(0,2).map(r => [r[0], r[1]]).concat([['Otros', T - ti[0][1] - ti[1][1]]]); tp.t = 'Tipo'; tp.propios = true;
    const dt = docTram(F), dc = dt ? [['Tarjeta',dt.tar],['Constancia u oficio',dt.co],['Sin expedición',dt.sin]] : null; if (dc) dc.t = 'Documento que salió';
    const r = z('tram_res'), rs = [['Positiva',r[0]],['Negativa',r[1]],['Otra',r[2]]]; rs.t = 'Resolución'; sx.t = 'Sexo'; return dc ? [dc, tp, sx] : [tp, rs, sx]; }
  if (k==='resc'){ const a = z('resc_rei'), d = z('resc_des'); return [[['Primera vez',a[0]],['Reincidentes',a[1]]], [['A estación migratoria',d[0]],['Al DIF',d[1]],['Sin destino',d[2]]]]; }
  if (k==='rep'){ const v = comp('rep_comp', F.ss, null); return [[['Adultos',v[0]+v[1]],['NNA',v[2]+v[3]]]]; }
  if (k==='cbp'){ const x = cbpTotal(F), a = [['Patrulla Fronteriza',x.ag[0]],['Puertos de entrada',x.ag[1]],['CBP ONE',x.ag[2]]]; a.t = 'Agencia'; a.propios = true; return F.nd==null ? [[['Otros países',x.v-x.mx],['Mexicanos',x.mx]], a] : [a]; }
  if (k==='rech'){ const v = z('rech_det'), r = [['Internación',v[0]],['Rechazo',v[1]]]; r.t = 'Segunda revisión'; return [r]; }
  if (k==='pres'){ const v = z('pres_est').map((x,i) => [nomEst(i), x]).sort((a,b) => b[1]-a[1]), r = v.slice(0,2).concat([['Otras', v.slice(2).reduce((a,x) => a+x[1], 0)]]); r.t = 'Por estación'; r.propios = true; return [r]; }
  if (k==='can'){ const v = z('can_nna'), a = z('can_ad'); return [[['NNA',v.reduce((s,x) => s+x, 0)],['Adultos acompañantes',a[0]+a[1]]]]; }
  if (k==='ret'){ const v = z('ret_tipo'); return [[['Retorno asistido',v[1]],['Deportación',v[0]]]]; }
  return []; }
// Barra al 100 % con su leyenda (color del indicador en tres intensidades)
function barra100(l, c){ const T = l.reduce((a,x) => a+x[1], 0); if (!T) return '';
  const tit = l.t ? '<span class="t">'+esc(l.t)+':</span>' : '';
  const al = [1, .62, .34], seg = l.map((x,i) => '<i style="width:'+(x[1]/T*100).toFixed(2)+'%;background:'+alfa(c, al[i]||.2)+'" title="'+esc(x[0])+': '+miles(x[1])+'"></i>').join('');
  return '<div class="sl-bc"><div class="sl-b100">'+seg+'</div><div class="sl-bl">'+tit+l.map((x,i) => '<span><i style="background:'+alfa(c, al[i]||.2)+'"></i><b>'+Math.round(x[1]/T*100)+'%</b> '+esc(l.propios || /^[A-ZÁÉÍÓÚ]{2}/.test(x[0]) ? x[0] : x[0].charAt(0).toLowerCase()+x[0].slice(1)).replace('al Dif','al DIF')+'</span>').join('')+'</div></div>'; }
const CUATRO = [['ing','Ingresos','reg','personas que entraron'],['tram','Trámites','reg','trámites concluidos'],['resc','Rescatados','irr','rescates (eventos)'],['rep','Repatriados','usa','mexicanos desde EE. UU.']];
function panoramaSala(F, t, dur){
  const P = perfilSala(), el = $('sl-tri'), l = P.pan.filter(x => x[5] ? x[5].ok(F) : (F.nd==null || IND[x[0]].nat));
  el.classList.toggle('dos', !!P.dos);
  if (el.dataset.k!==l.map(x => x[0]).join()+S.tema+SALA.perfil){ el.dataset.k = l.map(x => x[0]).join()+S.tema+SALA.perfil;
    el.innerHTML = l.map((x,i) => (x[4] && (i===0 || l[i-1][4]!==x[4]) ? '<div class="sl-tg sl-e" style="--d:'+(.1+i*.07)+'s">'+x[4]+'</div>' : '')+'<div class="sl-tr sl-e" style="--d:'+(.12+i*.07)+'s"><div class="sl-tc"><span class="k" style="color:'+t[x[2]]+'">'+x[1]+'</span><span class="v" data-t="'+x[0]+'">0</span><span class="n">'+x[3]+' <span class="d"></span></span></div><div class="sl-rp"></div></div>').join(''); }
  l.forEach(x => { const v = el.querySelector('[data-t="'+x[0]+'"]'), box = v.closest('.sl-tr'), d = box.querySelector('.d'), n = x[5] ? null : nFde(x[0], F);
    if (SALA.cmp && !x[5]){ const a = valRango(x[0], SALA.A[0], SALA.A[1], F.ss, n)/(SALA.A[1]-SALA.A[0]), b = valRango(x[0], SALA.B[0], SALA.B[1], F.ss, n)/(SALA.B[1]-SALA.B[0]);
      mover(v, b, cifraG, dur); d.innerHTML = '· por día · '+(a>0 ? flecha(a, b) : 'sin registros antes'); }
    else if (x[5]){ mover(v, x[5].val(F), cifraG, dur); d.innerHTML = '· '+x[5].nota; }
    else { const tv = valAcum(x[0], F.ss, n); mover(v, tv, cifraG, dur); d.innerHTML = '· '+cortoK(tv/Math.max(1, Math.min(S.dia, finDatos(x[0]))))+' por día'; }
    const rp = (x[5] ? x[5].rep(F) : repartos(x[0], F)).map(r => barra100(r, t[x[2]])).join('');
    const extra = x[0]==='rep' ? (vv => '<div class="sl-ex"><span>Vía aérea (vuelos PRIM) <b>'+miles(vv[7])+'</b></span><span>Vía terrestre <b>'+miles(vv[6])+'</b></span></div>')(comp('rep_comp', F.ss, null))
      : x[0]==='rech' ? (r => r[1] ? '<div class="sl-ex"><span>Tasa de rechazo <b>'+(r[0]/r[1]*100).toFixed(2)+'%</b> de los que llegan por aire o tierra</span></div>' : '')(rechazoExt(F.ss, F.nd)) : '';
    const html = rp + extra; const c = box.querySelector('.sl-rp'); if (c._h!==html){ c._h = html; c.innerHTML = html; } });
}
// Documento que salió de cada trámite (base de DGRAM): tarjetas, constancias y oficios, o sin expedición. Respeta periodo, día del cursor y filtro.
const RGD = { mapE:null, mapN:null };
function docTram(F){ const R = window.IANAMI_REG; if (!R || !R.cols) return null; const C = R.cols, off = idxBase(R.inicio), a = P0, b = P0 + Math.min(S.dia, ND);
  if (!RGD.mapE){ const ie = {}, in_ = {}; EST.forEach((e,i) => ie[sinAcento(e)] = i); D.nats.forEach((x,i) => in_[sinAcento(x[0])] = i);
    RGD.mapE = R.dic.e.map(e => ie[sinAcento(e)]!=null ? ie[sinAcento(e)] : -1); RGD.mapN = R.dic.n.map(x => in_[sinAcento(x)]!=null ? in_[sinAcento(x)] : -1); }
  const nl = F.nd==null ? null : (Array.isArray(F.nd) ? F.nd : [F.nd]), v = new Array(R.condiciones.length).fill(0); let fu = 0;
  for (let i=0; i<C.c.length; i++){ const d = off + C.d[i]; if (d<a || d>=b) continue;
    if (F.ss && F.ss.indexOf(RGD.mapE[C.e[i]])<0) continue; if (nl && nl.indexOf(RGD.mapN[C.n[i]])<0) continue; v[C.c[i]] += C.v ? C.v[i] : 1; if (C.f && C.f[i]) fu += C.v ? C.v[i] : 1; }
  const T = R.tarjetas, tar = v.slice(0,T).reduce((x,y) => x+y, 0), sin = v[v.length-1], otros = v.slice(T, v.length-1).map((x,j) => [R.condiciones[T+j], x]);
  return { tar:tar, co:otros.reduce((x,y) => x+y[1], 0), sin:sin, otros:otros, fuera:fu, plazo:!!C.f }; }
// ---- Constancias y oficios: trámites cuyo documento no es tarjeta (condiciones entre las tarjetas y «Sin expedición»).
// Se separan una vez; cada consulta recorre solo esos renglones. Días en el mismo índice que las bases del Pulso (P0…).
const NOM_CO = { 'Oficio S.R.E.':'Oficio de la S.R.E.', 'Permiso salida y regreso':'Permiso de salida y regreso', 'Sin expedición':'Sin expedición de documento' };
const CO = {};
function coFilas(){ if (CO.d) return CO; const R = window.IANAMI_REG; if (!R || !R.cols) return { d:[], nom:[] };
  docTram({ ss:null, nd:null });                       // arma la equivalencia de estados y nacionalidades
  const C = R.cols, off = idxBase(R.inicio), T = R.tarjetas, U = R.condiciones.length-1; CO.e = []; CO.n = []; CO.c = []; CO.v = []; const d = [];
  for (let i=0; i<C.c.length; i++){ const c = C.c[i]; if (c<T) continue; d.push(off + C.d[i]); CO.e.push(RGD.mapE[C.e[i]]); CO.n.push(RGD.mapN[C.n[i]]); CO.c.push(c-T); CO.v.push(C.v ? C.v[i] : 1); }
  CO.nom = R.condiciones.slice(T); CO.d = d; return CO; }
function coRango(a, b, ss, n, reparto){ const X = coFilas(), nl = n==null ? null : (Array.isArray(n) ? n : [n]), v = new Array(X.nom.length).fill(0);
  for (let i=0; i<X.d.length; i++){ const d = X.d[i]; if (d<a || d>=b) continue; if (ss && ss.indexOf(X.e[i])<0) continue; if (nl && nl.indexOf(X.n[i])<0) continue; v[X.c[i]] += X.v[i]; }
  return reparto ? v : v.reduce((s,x) => s+x, 0); }
function coDiario(F){ const X = coFilas(), nl = F.nd==null ? null : (Array.isArray(F.nd) ? F.nd : [F.nd]), v = new Array(ND).fill(0);
  for (let i=0; i<X.d.length; i++){ const d = X.d[i]-P0; if (d<0 || d>=ND) continue; if (F.ss && F.ss.indexOf(X.e[i])<0) continue; if (nl && nl.indexOf(X.n[i])<0) continue; v[d] += X.v[i]; }
  return v; }
// ---- Validación de actas del Registro Civil: base nueva con su propio periodo (desde RG.va_ini). No sigue al periodo,
// al play ni a la comparación del tablero, y no se cruza con nada más; solo respeta el país, el estado o la región elegidos.
// Renglón: [día, días entre registro y solicitud, O.R., entidad de registro, nacionalidad, trámite, acto, resultado, oficina]
function vaFilas(F){ const R = window.IANAMI_REG; if (!R || !R.va) return []; const VD = R.va_dic;
  if (!RGD.vaN){ const ie = {}, in_ = {}; EST.forEach((e,i) => ie[sinAcento(e)] = i); D.nats.forEach((x,i) => in_[sinAcento(x[0])] = i);
    const m = (l, q) => l.map(x => q[sinAcento(x)]!=null ? q[sinAcento(x)] : -1); RGD.vaN = m(VD.n, in_); RGD.vaE = m(VD.ent, ie); RGD.vaO = m(VD.ofr, ie); }
  const nl = F.nd==null ? null : (Array.isArray(F.nd) ? F.nd : [F.nd]);
  return R.va.filter(r => (!nl || nl.indexOf(RGD.vaN[r[4]])>=0) && (!F.ss || F.ss.indexOf(RGD.vaE[r[3]])>=0 || F.ss.indexOf(RGD.vaO[r[2]])>=0)); }
function vaPeriodo(){ const R = window.IANAMI_REG, ini = new Date(R.va_ini+'T00:00:00'), nd = Math.max.apply(null, R.va.map(r => r[0]))+1;
  const f = d => { const x = new Date(ini.getFullYear(), ini.getMonth(), ini.getDate()+d); return x.getDate()+' '+MES12[x.getMonth()]; };
  return { nd:nd, f:f, txt:f(0)+' – '+f(nd-1)+' '+ini.getFullYear() }; }
function vaDesglose(F){ const VD = window.IANAMI_REG.va_dic, V = vaFilas(F), iM = VD.acto.indexOf('Matrimonio'), iN = VD.acto.indexOf('Nacimiento'), iP = VD.res.indexOf('Pendiente');
  const n = f => V.reduce((s,r) => s + (f(r) ? 1 : 0), 0);
  return [['Matrimonio', n(r => r[6]===iM)], ['Nacimiento', n(r => r[6]===iN)],
    ['Matrimonio de ≤30 días', n(r => r[6]===iM && r[1]>=0 && r[1]<=30), 'Acta de matrimonio registrada 30 días o menos antes de la solicitud: señal para revisar, no una conclusión'],
    ['Acta de otro estado', n(r => VD.ofr[r[2]]!=='DGRAM' && VD.ofr[r[2]]!==VD.ent[r[3]]), 'El acta es de un estado distinto al de la O.R. que la reporta (la DGRAM es oficina central y no cuenta)'],
    ['Pendientes', n(r => r[7]===iP), 'Validaciones que aún no tienen resultado']].concat(VD.res.indexOf('No válida')>=0 ? [['No válidas', n(r => r[7]===VD.res.indexOf('No válida')), 'El Registro Civil no localizó el acta o la reportó inexistente o no válida']] : []); }
function pintarVa(F, t){
  const P = vaPeriodo(), V = vaFilas(F), l = vaDesglose(F), ent = S.sel ? nombreSel() : S.region ? nombreRegion() : 'todo el país', c = t[IND.va.g], cua = x => '<i style="background:'+x+'"></i>';
  $('sl-ctx').innerHTML = '<span class="k">Estás viendo</span><b>Validación de actas del Registro Civil</b><i>·</i>'+esc(ent)+'<i>·</i>'+P.txt+'<em class="sl-pp">periodo propio de esta base</em>';
  $('sl-corte').innerHTML = '<span>Datos al <b>'+P.f(P.nd-1)+'</b></span><span>corte semanal de su base</span>';
  mover($('sl-big'), V.length, cifraG, SALA.anim.big ? 650 : 1100); SALA.anim.big = true;
  $('sl-cap').innerHTML = 'Solicitudes de validación de actas';
  $('sl-dl').innerHTML = '<b>'+P.txt+'</b> · no sigue al periodo ni al play del tablero';
  desgloseSala('va', F, t, 900);
  const ent2 = S.sel ? (S.sel.t==='n' ? ' de '+nombreSel() : ' en '+nombreSel()) : S.region ? ' de '+nombreRegion() : '';
  $('sl-fr').innerHTML = V.length ? 'Del '+P.f(0)+' al '+P.f(P.nd-1)+' se pidió validar <b>'+miles(V.length)+' actas</b>'+esc(ent2)+': '+Math.round(l[0][1]/V.length*100)+'% de matrimonio. <b>'+miles(l[2][1])+'</b> matrimonios se registraron 30 días o menos antes de la solicitud; es una señal para revisar, no una conclusión.' : 'Sin solicitudes de validación'+esc(ent2)+' en el periodo de esta base.';
  pintarBarrasSala('va', F, null);
  // barra de tiempo propia: solicitudes por día, sin cursor ni play
  const sv = $('sl-tg'), W = Math.max(200, sv.clientWidth), H = Math.max(50, sv.clientHeight), fs = Math.max(10, Math.min(30, uSala()*0.8)), base = H - fs - 6, pw = W/P.nd, v = new Array(P.nd).fill(0);
  V.forEach(r => v[r[0]]++); const mx = Math.max.apply(null, v) || 1, cada = Math.ceil(P.nd*fs*3.2/W); let h = '';
  v.forEach((x,i) => { const bh = Math.max(0.6, x/mx*(base-4)); h += '<rect x="'+(i*pw+1).toFixed(1)+'" y="'+(base-bh).toFixed(1)+'" width="'+Math.max(1, pw-2).toFixed(1)+'" height="'+bh.toFixed(1)+'" rx="2" fill="'+c+'"><title>'+P.f(i)+': '+x+'</title></rect>';
    if (!(i%cada)) h += '<text x="'+(i*pw+pw/2).toFixed(1)+'" y="'+(H-3)+'" text-anchor="middle" font-size="'+fs.toFixed(1)+'" fill="'+t.tinta+'" fill-opacity=".7">'+P.f(i)+'</text>'; });
  sv.setAttribute('viewBox', '0 0 '+W+' '+H); sv.setAttribute('preserveAspectRatio', 'none'); sv.innerHTML = h;
  $('sl-tl').innerHTML = '<span>'+cua(c)+'Solicitudes por día</span><span class="m">periodo propio de la base · el mapa se atenúa porque sigue el periodo del tablero</span>';
  $('sl-fte').textContent = 'Fuente: DGRAM, validación de actas del Registro Civil (corte semanal) · no se publican número de acta, oficialía, libro ni municipio';
}
function docsVig(F){ const d = D.docs; if (!d) return [0,0,0];
  if (F.nd!=null && !Array.isArray(F.nd)){ const r = d.nat && d.nat[F.nd]; return r ? r : [0,0,0]; }
  if (F.ss){ return [F.ss.reduce((a,s) => a+(d.est[s]||0), 0), null, null]; }
  return [d.total, d.h, d.m]; }
const DOCS_ITEM = { ok:F => !!D.docs && (F.nd==null || !Array.isArray(F.nd)), val:F => docsVig(F)[0], nota:'al último corte · no cambia con el periodo',
  rep:F => { const v = docsVig(F), out = []; if (!F.ss && F.nd==null && D.docs.tipos){ const tp = D.docs.tipos.slice().sort((a,b) => b[1]-a[1]), T = tp.reduce((a,x) => a+x[1], 0); const r = tp.slice(0,2).concat([['Otros', T - tp[0][1] - tp[1][1]]]); r.t = 'Tipo'; r.propios = true; out.push(r); }
    if (v[1]!=null){ const r = [['Hombres',v[1]],['Mujeres',v[2]]]; r.t = 'Sexo'; out.push(r); } return out; } };
// Perfiles de la pantalla completa: misma pieza, distinto contenido (Pulso y cada proceso)
const PERFILES = {
  pulso:{ nom:'Pulso migratorio', ctx:'Panorama: regular, irregular y desde EE. UU.', inds:IND_SALA, pan:CUATRO, orden:ORDEN_SALA, cam:['ing','tram','resc','can','rep'] },
  control:{ nom:'Control migratorio', ctx:'Panorama: quienes llegan y quienes son rescatados', dos:true, puntoIng:true, orden:['ing','resc','rech','pres','can','ret'], cam:['ing','rech','resc','pres','can','ret'],
    inds:[['', 'Resumen', 'Panorama', 'Llegadas y rescates en un vistazo'], ['ing', 'Regular · llegan', 'Ingresos', 'Extranjeros y mexicanos que entraron'], ['rech', 'Regular · llegan', 'Rechazos', 'Negados en segunda revisión'],
          ['resc', 'Irregular · rescate y destino', 'Rescatados', 'Rescates (eventos) según las O.R.'], ['pres', 'Irregular · rescate y destino', 'Presentados', 'Ante una estación migratoria (sistema)'],
          ['can', 'Irregular · rescate y destino', 'Canalizados', 'NNA y acompañantes al DIF'], ['ret', 'Irregular · rescate y destino', 'Retornados', 'Asistidos o deportados a su país']],
    pan:[['ing','Ingresos','reg','personas que entraron','Regular · llegan y son revisados'],['rech','Rechazos','reg','en segunda revisión','Regular · llegan y son revisados'],
         ['resc','Rescatados','irr','rescates (eventos)','Irregular · rescate y destino'],['pres','Presentados','irr','en estación (sistema)','Irregular · rescate y destino'],
         ['can','Canalizados','irr','NNA y acompañantes al DIF','Irregular · rescate y destino'],['ret','Retornados','irr','a su país','Irregular · rescate y destino']],
    frase:(F, ent, v) => { const r = rechazoExt(F.ss, F.nd), d = compSala('resc_des', F);
      return (S.dia>=ND ? 'En el periodo' : 'Al '+fechaLarga(S.dia-1))+ent+' entraron <b>'+v('ing')+' personas</b>'+partIng(F.ss, F.nd)+' y se rechazó a <b>'+v('rech')+'</b>'+(r[1] ? ' ('+(r[0]/r[1]*100).toFixed(2)+'% de los extranjeros que llegan por aire o tierra)' : '')+
        '. Hubo <b>'+v('resc')+' rescates</b>'+(d[0]+d[1] ? ': '+Math.round(d[0]/(d[0]+d[1]+d[2])*100)+'% a estación migratoria y '+Math.round(d[1]/(d[0]+d[1]+d[2])*100)+'% al DIF' : '')+', según el reporte de las O.R.'; } }
};
PERFILES.regulacion = { nom:'Regulación migratoria', ctx:'Panorama: trámites del periodo y documentos vigentes', dos:true, mapa:'tram', solo:true, orden:['tram'], cam:['tram'],
  inds:[['', 'Resumen', 'Panorama', 'Trámites y documentos en un vistazo'], ['tram', 'Trámites', 'Trámites', 'Trámites migratorios concluidos'], ['co', 'Trámites', 'No expiden tarjetas', 'Constancias, oficios, permisos y sin expedición'],
    ['va', 'Registro Civil · periodo propio', 'Validación de actas', 'Base nueva: desde el 28 sep 2026']],
  pan:[['tram','Trámites concluidos','reg','en el periodo','Lo que se tramitó en el periodo'], ['docs','Con documento vigente','reg','extranjeros','Lo que hay al corte', DOCS_ITEM]],
  frase:(F, ent, v) => { const r = compSala('tram_res', F), ti = compSala('tram_tipo', F).map((x,i) => [x, D.tramTipos[i]]).filter(x => x[1]!=='Otros').sort((a,b) => b[0]-a[0])[0], dv = docsVig(F)[0];
    const dt = docTram(F), T = dt ? dt.tar+dt.co+dt.sin : 0;
    return (S.dia>=ND ? 'En el periodo' : 'Al '+fechaLarga(S.dia-1))+ent+' se concluyeron <b>'+v('tram')+' trámites</b>'+(T ? ': '+Math.round(dt.tar/T*100)+'% salió con tarjeta y '+Math.round(dt.co/T*100)+'% con constancia u oficio' : (r[0]+r[1] ? ', '+Math.round(r[0]/(r[0]+r[1]+r[2])*100)+'% con resolución positiva' : ''))+(ti && ti[0] ? '; el que más se hace es <b>'+esc(CORTO_TRAM(ti[1]).toLowerCase())+'</b>' : '')+
      '.'+(dv ? ' Al último corte, <b>'+cortoK(dv)+' extranjeros</b> tienen documento migratorio vigente.' : ''); } };
const perfilSala = () => PERFILES[SALA.perfil] || PERFILES.pulso;
// Con un país, la frase empieza por el país («Venezuela: en el periodo entraron…»), que se lee mejor que «en el periodo de Venezuela»
function frasePanorama(F){ const r = frasePanorama0(F); return S.sel && S.sel.t==='n' && !SALA.cmp ? '<b>'+esc(nombreSel())+'</b>: '+r.charAt(0).toLowerCase()+r.slice(1) : r; }
function frasePanorama0(F){
  const ent = S.sel ? (S.sel.t==='n' ? (SALA.cmp ? ' de '+nombreSel() : '') : ' en '+nombreSel()) : S.region ? ' de '+nombreRegion() : '';
  const P = perfilSala(), l = P.pan.filter(x => !x[5] && (F.nd==null || IND[x[0]].nat));
  if (SALA.cmp){ const A = nomRango(SALA.A[0], SALA.A[1]), B = nomRango(SALA.B[0], SALA.B[1]);
    return 'Por día, en '+B+ent+': '+l.map(x => { const n = nFde(x[0], F), a = valRango(x[0], SALA.A[0], SALA.A[1], F.ss, n)/(SALA.A[1]-SALA.A[0]), b = valRango(x[0], SALA.B[0], SALA.B[1], F.ss, n)/(SALA.B[1]-SALA.B[0]);
      return '<b>'+cortoK(b)+' '+x[3]+'</b>'+(a>0 ? ' ('+((b/a-1)*100<0 ? '−' : '+')+Math.abs((b/a-1)*100).toFixed(0)+'%)' : ''); }).join(', ').replace(/, ([^,]*)$/, ' y $1')+' vs. '+A+'.'; }
  const v = x => cortoK(valAcum(x, F.ss, nFde(x, F)));
  if (P.frase) return P.frase(F, ent, v);
  return (S.dia>=ND ? 'En el periodo' : 'Al '+fechaLarga(S.dia-1))+ent+' entraron <b>'+v('ing')+' personas</b>'+partIng(F.ss, F.nd)+', se concluyeron <b>'+v('tram')+' trámites</b>, hubo <b>'+v('resc')+' rescates</b>'+
    (F.nd==null ? ' y <b>'+v('rep')+' mexicanos</b> fueron repatriados desde EE. UU.' : '.');
}
// Abajo a la derecha en Panorama: lo que más cambió (del análisis automático; al comparar, entre los dos periodos)
function cambiosSala(F, t){
  if (SALA.gr){ SALA.gr.dispose(); SALA.gr = null; }
  const el = $('sl-qc'); let l;
  if (SALA.cmp){ const dA = SALA.A[1]-SALA.A[0], dB = SALA.B[1]-SALA.B[0];
    l = perfilSala().cam.filter(x => F.nd==null || IND[x].nat).map(x => { const n = nFde(x, F), a = valRango(x, SALA.A[0], SALA.A[1], F.ss, n), b = valRango(x, SALA.B[0], SALA.B[1], F.ss, n);
      return a>=100 ? { k:x, x:(b/dB)/(a/dA)*100-100, txt:'<b>'+IND[x].n+'</b>: '+cortoK(a/dA)+' → '+cortoK(b/dB)+' por día' } : null; }).filter(Boolean).sort((a,b) => Math.abs(b.x)-Math.abs(a.x)).slice(0,3);
    $('sl-qt').textContent = 'Lo que más cambió'; $('sl-qs').textContent = 'por día, '+nomRango(SALA.B[0], SALA.B[1])+' vs. '+nomRango(SALA.A[0], SALA.A[1]);
  } else {
    l = AVISOS.filter(a => relevante(a) && perfilSala().cam.indexOf(a.k)>=0).slice(0,3).map(a => ({ k:a.k, x:a.t==='pico' ? null : (a.a!=null && a.b ? (a.a/a.b-1)*100 : null), pico:a.t==='pico' ? a.v/Math.max(1,a.med) : null, txt:textoAviso(a) }));
    $('sl-qt').textContent = 'Lo que cambió'; $('sl-qs').textContent = textoCmp();
  }
  el.innerHTML = l.length ? '<div class="sl-cam">'+l.map(c => { const col = t[IND[c.k].g], sube = c.pico ? true : c.x>=0;
    return '<div class="sl-ci" style="--c:'+col+'"><span class="k">'+IND[c.k].n+'</span><span class="x '+(c.pico ? 'pico' : sube ? 'sube' : 'baja')+'">'+(c.pico ? '×'+c.pico.toFixed(1) : (sube ? '▲ ' : '▼ ')+Math.abs(c.x).toFixed(Math.abs(c.x)<10 ? 1 : 0)+'%')+'</span><p>'+c.txt+'</p></div>'; }).join('')+'</div>'
    : '<p class="sl-nada">Sin cambios relevantes en la comparación.</p>';
}
// Debajo de la cifra de un indicador: su desglose del periodo
const CORTO_TRAM = t => t.replace('Expedición tarjeta de residente por renovación','Renovación de residencia').replace('Notificación cambio de domicilio por parte de residentes','Cambio de domicilio').replace('Expedición documento migratorio por canje','Canje de documento')
  .replace('Regularización por razones humanitarias','Regularización humanitaria').replace('Regularización por unidad familiar','Regularización familiar').replace('Reposición documento migratorio','Reposición de documento')
  .replace('Regularización por documento vencido o actividades no autorizadas','Regularización por documento vencido').replace('Tarjeta visitante regional','Visitante regional');
function desgloseSala(k, F, t, dur){
  const z = key => compSala(key, F); let l = [], tit = 'Por vía de ingreso';
  if (k==='ing'){ const v = z('ing_via'); l = [['Vía aérea',v[0]],['Vía terrestre',v[1]],['Vía marítima',v[2]]]; }
  else if (k==='tram'){ tit = 'Principales trámites'; l = z('tram_tipo').map((x,i) => [CORTO_TRAM(D.tramTipos[i]), x, D.tramTipos[i]]).filter(r => r[1]>0 && r[2]!=='Otros').sort((a,b) => b[1]-a[1]).slice(0,5); }
  else if (k==='resc'){ tit = 'Condición y destino'; const a = z('resc_rei'), d = z('resc_des'); l = [['Primera vez',a[0]],['Reincidentes',a[1]],['A estación migratoria',d[0]],['Al DIF',d[1]],['Sin destino',d[2]]]; }
  else if (k==='can'){ tit = 'Quiénes'; const v = z('can_nna'), a = z('can_ad'), g = f => v.reduce((s,x,i) => s+(f(i) ? x : 0), 0);
    l = [['Adultos',a[0]+a[1],'Adultos que acompañan a NNA'],['NNA',g(() => true)],['NNA acompañados',g(i => i%3===0),null,1],['NNA no acompañados',g(i => i%3===1),null,1],['NNA separados',g(i => i%3===2),null,1]]; }
  else if (k==='rech'){ tit = 'Segunda revisión'; const v = z('rech_det'); l = [['Casos revisados',v[0]+v[1]],['Internación',v[0]],['Rechazo',v[1]]]; }
  else if (k==='pres'){ tit = 'Principales estaciones'; l = z('pres_est').map((x,i) => [nomEst(i), x]).filter(r => r[1]>0).sort((a,b) => b[1]-a[1]).slice(0,5); }
  else if (k==='ret'){ tit = 'Tipo de retorno'; const v = z('ret_tipo'); l = [['Retorno asistido',v[1]],['Deportación',v[0]]]; }
  else if (k==='co'){ tit = 'Qué documento salió'; const v = coRango(P0, P0+Math.min(S.dia, ND), F.ss, F.nd, true); l = coFilas().nom.map((x,i) => [NOM_CO[x] || x, v[i]]).sort((a,b) => b[1]-a[1]); }
  else if (k==='va'){ tit = 'Tipo de acta y señales'; l = vaDesglose(F); }
  else if (k==='cbp'){ tit = 'Quiénes y cómo'; const x = cbpTotal(F); l = (F.nd==null ? [['Otros países',x.v-x.mx],['Mexicanos',x.mx]] : []).concat([['Patrulla Fronteriza',x.ag[0],'Entre puertos (USBP)'],['Puertos de entrada',x.ag[1],'Oficina de Operaciones de Campo (OFO)'],['Citas CBP ONE',x.ag[2]]]); }
  else if (k==='rep'){ tit = 'Quiénes y por dónde'; const v = comp('rep_comp', F.ss, null); l = [['Adultos',v[0]+v[1]],['NNA',v[2]+v[3]],['Vía aérea (PRIM)',v[7],'Vía aérea: vuelos del Procedimiento de Repatriación al Interior de México (personas, no vuelos)'],['Vía terrestre',v[6]]]; }
  const G = $('sl-g'), key = k+'|'+l.map(x => x[0]).join(), c = t[IND[k].g];
  if (G.dataset.k!==key){ G.dataset.k = key; G.innerHTML = '<div class="sl-gt">'+tit+(k==='va' ? ' · periodo propio' : SALA.cmp ? ' · '+esc(nomRango(SALA.B[0], SALA.B[1])) : ' · periodo completo')+'</div>'+
    l.map((x,i) => '<div class="sl-m sl-e" style="--d:'+(.28+i*.05)+'s"><div class="v" style="color:'+c+'" data-m="'+i+'">0</div><div class="n"'+(x[2] ? ' title="'+esc(x[2])+'"' : '')+'>'+esc(x[0])+'</div><div class="d"></div></div>').join(''); }
  const tot = k==='cbp' ? cbpTotal(F).v || 1 : k==='va' ? l[0][1]+l[1][1] : k==='rep' ? l[0][1]+l[1][1] : k==='can' ? l[0][1]+l[1][1] : k==='resc' ? l[0][1]+l[1][1] : k==='rech' ? l[0][1] : l.reduce((a,x) => a+x[1], 0) || 1;
  const base = k==='tram' ? compSala('tram_tipo', F).reduce((a,x) => a+x, 0) : k==='pres' ? compSala('pres_est', F).reduce((a,x) => a+x, 0) : tot;
  const nnaT = k==='can' ? l[1][1] : 0;
  l.forEach((x,i) => { const el = G.querySelector('[data-m="'+i+'"]'); if (!el) return; mover(el, x[1], cifraG, dur);
    el.parentNode.querySelector('.d').textContent = x[3] ? (nnaT ? Math.round(x[1]/nnaT*100)+'% de los NNA' : '') : (k==='rech' && i===0) ? 'segunda revisión' : base ? (x[1]/base*100<1 && x[1]>0 ? (x[1]/base*100).toFixed(2) : Math.round(x[1]/base*100))+'% '+(k==='rech' ? 'de los revisados' : 'del total') : ''; });
  if (k==='tram' && SALA.perfil==='regulacion'){ const dt = docTram(F); let n = G.querySelector('.sl-gn'); if (!n){ n = document.createElement('div'); n.className = 'sl-gn'; G.appendChild(n); }
    const T = dt ? dt.tar+dt.co+dt.sin : 0; n.innerHTML = T ? 'Documento que salió: <b>'+Math.round(dt.tar/T*100)+'%</b> tarjeta · <b>'+Math.round(dt.co/T*100)+'%</b> constancia u oficio ('+dt.otros.filter(x => x[1]>0).sort((a,b) => b[1]-a[1]).map(x => esc(x[0].toLowerCase().replace('s.r.e.','S.R.E.'))+' '+cortoK(x[1])).join(', ')+') · <b>'+Math.round(dt.sin/T*100)+'%</b> sin expedición' : ''; }
  if (k==='rech'){ const r = rechazoExt(F.ss, F.nd); let n = G.querySelector('.sl-gn'); if (!n){ n = document.createElement('div'); n.className = 'sl-gn'; G.appendChild(n); }
    n.innerHTML = r[1] ? 'Tasa de rechazo: <b>'+(r[0]/r[1]*100).toFixed(2)+'%</b> de los extranjeros que llegan por aire o tierra (sin mexicanos ni cruceros, como en Control migratorio).' : ''; }
}
function fraseSala(k, F, nF, pa, pb, otros){
  const ent = S.sel ? (S.sel.t==='n' ? ' de '+nombreSel() : ' en '+nombreSel()) : S.region ? ' de '+nombreRegion() : '';
  if (SALA.cmp){
    const A = nomRango(SALA.A[0], SALA.A[1]), B = nomRango(SALA.B[0], SALA.B[1]);
    if (!pa) return 'En '+B+' hubo '+cortoK(pb)+' '+PALABRA[k]+ent+' por día; en '+A+' no hubo registros.';
    const x = (pb/pa-1)*100, dir = Math.abs(x)<0.5 ? 'igual que' : Math.abs(x).toFixed(0)+'% '+(x<0 ? 'menos que' : 'más que');
    const cam = otros.map(o => { const n = nFde(o, F), a = valRango(o, SALA.A[0], SALA.A[1], F.ss, n)/(SALA.A[1]-SALA.A[0]), b = valRango(o, SALA.B[0], SALA.B[1], F.ss, n)/(SALA.B[1]-SALA.B[0]); return [o, a, b, a>0 ? (b/a-1)*100 : 0]; })
      .filter(c => c[1]*(SALA.A[1]-SALA.A[0])>=100).sort((a,b) => Math.abs(b[3])-Math.abs(a[3]))[0];
    return 'En '+B+' hubo <b>'+cortoK(pb)+' '+PALABRA[k]+ent+' por día</b>, '+dir+' en '+A+'.'+(cam && Math.abs(cam[3])>=5 ? ' Lo que más cambió: <b>'+PALABRA[cam[0]]+'</b> ('+(cam[3]<0 ? '−' : '+')+Math.abs(cam[3]).toFixed(0)+'%).' : '');
  }
  if (k==='co'){ const v = valAcum(k, F.ss, nF), dt = docTram(F), T = dt ? dt.tar+dt.co+dt.sin : 0;
    return (S.dia>=ND ? 'En el periodo' : 'Al '+fechaLarga(S.dia-1))+ent+' <b>'+cortoK(v)+' trámites no expidieron tarjeta</b>'+(T ? ': el '+Math.round(v/T*100)+'% de los trámites concluidos (constancias, oficios, permisos o sin documento).' : '.'); }
  const v = valAcum(k, F.ss, nF), top = AVISOS.find(a => relevante(a) && a.k===k) || AVISOS.find(relevante);
  return (S.dia>=ND ? 'En el periodo' : 'Al '+fechaLarga(S.dia-1))+' se registraron <b>'+cortoK(v)+' '+PALABRA[k]+ent+'</b>'+(k==='ing' ? partIng(F.ss, nF) : '')+'.'+(top && S.dia>=ND ? ' Lo que más cambió ('+ventanaCmp()+'): '+textoAviso(top).replace(/\s*\([^)]*\)\.?$/, '.') : '');
}
// Barras verticales: en un periodo, los 8 con más registros; al comparar, el cambio por día de cada uno.
// Con un país elegido se reparte por estado (O.R.); si no, por nacionalidad. Repatriados siempre por estado.
function opcionesPor(k){ if (k==='rep') return [['e','O.R.'],['p','Punto']]; if (k==='cbp') return (S.sel && S.sel.t==='n' ? [] : [['n','Nacionalidad']]).concat([['s','Sector']]); const l = [];
  if (!(S.sel && S.sel.t==='n')) l.push(['n','Nacionalidad']); if (!(S.sel && S.sel.t!=='n')) l.push(['e','O.R.']);
  if (k==='ing' && perfilSala().puntoIng && !S.sel) l.push(['p','Punto']); return l; }
function pintarBarrasSala(k, F, nF){
  const ops = opcionesPor(k), por = ops.some(o => o[0]===SALA.por[k]) ? SALA.por[k] : ops[0][0];
  const porEst = por==='e', porPto = por==='p', t = TM[S.tema], cs = getComputedStyle($('sala'));
  const INK = t.tinta, I2 = cs.getPropertyValue('--s-ink2').trim(), LN = cs.getPropertyValue('--s-grid').trim(), VC = t[IND[k].g], RC = t.irr;
  const ssF = F.ss, lista = [];
  if (porPto){ (k==='rep' ? D.repPuntos : D.puntos).forEach((pt,i) => lista.push([pt.n, null, null, pt])); }
  else if (porEst){ for (let s=0;s<NS;s++){ if (ssF && ssF.indexOf(s)<0) continue; lista.push([ESTC[s], s, null]); } }
  else { const l = F.nd==null ? null : (Array.isArray(F.nd) ? F.nd : [F.nd]); for (let n=0;n<OT;n++){ if (l && l.indexOf(n)<0) continue; lista.push([D.nats[n][0], null, n]); } }
  const nomCorto = s => s.replace('Estados Unidos','EE. UU.').replace('Ciudad de México','CDMX').replace('Edo. de México','Edomex').replace('Quintana Roo','Q. Roo').replace('Baja California S.','BCS').replace('Baja California','B. C.').replace('Indonesia','Indon.').replace('Filipinas','Filip.').replace('República Dominicana','Rep. Dom.');
  let datos, tit, sub, cmp = SALA.cmp && k!=='va';
  if (por==='s'){ const nom = D.cbp.sectores.map(P => P.n);
    if (cmp){ const dA = SALA.A[1]-SALA.A[0], dB = SALA.B[1]-SALA.B[0], A = cbpSec(SALA.A[0], SALA.A[1], nF), B = cbpSec(SALA.B[0], SALA.B[1], nF), mx = Math.max(1, ...A.map(x => x.v));
      datos = nom.map((n,i) => [n, A[i].v/dA, B[i].v/dB, A[i].v]).filter(x => x[3]>=Math.max(60, mx*0.01)).map(x => [x[0], x[1], x[2], (x[2]/x[1]-1)*100]).sort((a,b) => b[3]-a[3]);
      tit = 'Cambio por sector'; sub = PALABRA[k]+' por día, '+nomRango(SALA.B[0], SALA.B[1])+' vs. '+nomRango(SALA.A[0], SALA.A[1]); }
    else { const X = cbpAhora(F), r = nom.map((n,i) => [n, X[i].v]).filter(x => x[1]>0).sort((a,b) => b[1]-a[1]), tot = r.reduce((s,x) => s+x[1], 0);
      datos = r.slice(0,9).map(x => [x[0], x[1], tot]); tit = 'Por sector de la frontera'; sub = PALABRA[k]+' · '+datos.length+' sectores'+(S.dia<ND ? ' hasta el '+fechaDia(S.dia-1) : ''); } }
  else if (k==='va'){ const V = vaFilas(F), DV = window.IANAMI_REG.va_dic, c = {}; V.forEach(r => { const x = porEst ? DV.ofr[r[2]] : DV.n[r[4]]; c[x] = (c[x]||0) + 1; });
    datos = Object.entries(c).sort((a,b) => b[1]-a[1]).slice(0,8).map(x => [x[0], x[1], V.length]); tit = porEst ? 'Por O.R.' : 'Por nacionalidad'; sub = 'solicitudes de validación · periodo propio de la base'; }
  else if (cmp){ const dA = SALA.A[1]-SALA.A[0], dB = SALA.B[1]-SALA.B[0];
    const r = lista.map(x => { if (x[3]){ const a = puntoRango(x[3], SALA.A[0], SALA.A[1]), b = puntoRango(x[3], SALA.B[0], SALA.B[1]); return [x[0], a/dA, b/dB, a]; }
      const ss = x[1]!=null ? [x[1]] : ssF, n = x[2]!=null ? x[2] : nF, a = valRango(k, SALA.A[0], SALA.A[1], ss, n), b = valRango(k, SALA.B[0], SALA.B[1], ss, n); return [x[0], a/dA, b/dB, a]; });
    const mx = Math.max(...r.map(x => x[3]), 1);
    datos = r.filter(x => x[3]>=Math.max(60, mx*0.01)).sort((a,b) => b[2]-a[2]).slice(0,8).map(x => [x[0], x[1], x[2], (x[2]/x[1]-1)*100]).sort((a,b) => b[3]-a[3]);
    tit = 'Cambio por '+(porPto ? (k==='rep' ? 'punto de repatriación' : 'punto de internación') : porEst ? 'O.R.' : 'nacionalidad'); sub = PALABRA[k]+' por día, '+nomRango(SALA.B[0], SALA.B[1])+' vs. '+nomRango(SALA.A[0], SALA.A[1])+' · solo los que tuvieron al menos 60 registros antes';
  } else {
    const nna = k==='can';                                     // canalizados: sobre el total de NNA
    const val = x => x[3] ? suma(x[3].wk, 0, semDe(S.dia)+1)*sinMxPunto(x[3]) : nna ? suma(comp('can_nna', porEst ? [x[1]] : ssF, porEst ? nF : x[2]), 0, 12) : porEst ? valAcum(k, [x[1]], nF) : valAcum(k, ssF, x[2]);
    const r = lista.map(x => [x[0], val(x)]).filter(x => x[1]>0).sort((a,b) => b[1]-a[1]);
    const tot = r.reduce((s,x) => s+x[1], 0); datos = r.slice(0,8).map(x => [x[0], x[1], tot]);
    tit = (porPto ? (k==='rep' ? 'Por punto de repatriación' : 'Por punto de internación') : porEst ? 'Por O.R.' : 'Por nacionalidad')+(nna ? ' · NNA' : ''); sub = PALABRA[k]+' · los '+datos.length+' con más registros'+(S.dia<ND ? ' hasta el '+fechaDia(S.dia-1) : '');
  }
  if (ops.length>1 && !cmp) tit = 'Top '+datos.length+(k==='can' ? ' · NNA' : '');
  $('sl-qt').innerHTML = esc(tit)+(ops.length>1 ? '<span class="sl-por" role="group" aria-label="Ver la gráfica por">'+ops.map(o => '<button type="button" data-por="'+o[0]+'" class="'+(o[0]===por ? 'on' : '')+'" aria-pressed="'+(o[0]===por)+'">'+o[1]+'</button>').join('')+'</span>' : '');
  $('sl-qs').textContent = sub;
  const el = $('sl-qc'); if (!datos.length){ if (SALA.gr){ SALA.gr.dispose(); SALA.gr = null; } el.innerHTML = '<p class="sl-nada">Sin registros suficientes para comparar.</p>'; return; }
  if (!SALA.gr || SALA.gr.getDom()!==el){ el.innerHTML = ''; SALA.gr = echarts.init(el); }
  const fam = 'Barlow Condensed, Barlow, sans-serif', BIG = 'Big Shoulders Display, Barlow Condensed, sans-serif', f = Math.max(0.72, uSala()/16), fz = n => Math.round(n*f*10)/10;
  let op;
  if (cmp){ const mxp = Math.max(10, ...datos.map(d => d[3])), mnp = Math.min(0, ...datos.map(d => d[3])), paso = [5,10,25,50,100,200,500,1000].find(x => (mxp-mnp)/x<=5) || 2000;
    op = { yAxis:{ type:'value', min:Math.floor(mnp/paso)*paso, max:Math.ceil(mxp/paso)*paso, interval:paso, splitLine:{ lineStyle:{ color:LN } }, axisLabel:{ color:I2, fontFamily:fam, fontSize:fz(12), formatter:v => (v>0?'+':'')+v+'%' } },
      series:[{ type:'bar', barMaxWidth:30, data:datos.map(d => ({ value:+d[3].toFixed(1), itemStyle:{ color:d[3]>=0 ? VC : RC, borderRadius:d[3]>=0 ? [4,4,0,0] : [0,0,4,4] }, label:{ position:d[3]>=0 ? 'top' : 'bottom' } })),
        label:{ show:true, color:INK, fontFamily:BIG, fontWeight:900, fontSize:fz(17), formatter:p => (p.value>0?'+':'')+Math.round(p.value)+'%' } }],
      tooltip:{ trigger:'axis', axisPointer:{ type:'shadow' }, formatter:p => { const d = datos[p[0].dataIndex]; return '<b>'+esc(d[0])+'</b><br>'+cortoK(d[1])+' → '+cortoK(d[2])+' por día'; } } };
  } else {
    op = { yAxis:{ type:'value', splitLine:{ lineStyle:{ color:LN } }, axisLabel:{ color:I2, fontFamily:fam, fontSize:fz(12), formatter:v => cortoK(v) } },
      series:[{ type:'bar', barMaxWidth:30, data:datos.map(d => d[1]), itemStyle:{ color:VC, borderRadius:[4,4,0,0] },
        label:{ show:true, position:'top', color:INK, fontFamily:BIG, fontWeight:800, fontSize:fz(16), formatter:p => cortoK(p.value) } }],
      tooltip:{ trigger:'axis', axisPointer:{ type:'shadow' }, formatter:p => { const d = datos[p[0].dataIndex]; return '<b>'+esc(d[0])+'</b><br>'+miles(d[1])+' · '+pct(d[1], d[2])+'% del total'; } } };
  }
  SALA.gr.setOption(Object.assign({ animationDuration:900, animationDurationUpdate:S.play ? 180 : 600, animationEasing:'cubicOut', textStyle:{ fontFamily:fam },
    grid:{ left:fz(46), right:8, top:fz(30), bottom:fz(cmp ? 50 : 34) },
    xAxis:{ type:'category', data:datos.map(d => nomCorto(d[0])), axisLine:{ lineStyle:{ color:I2 } }, axisTick:{ show:false }, splitLine:{ show:true, lineStyle:{ color:LN } },
      axisLabel:{ color:INK, fontFamily:fam, fontSize:fz(13), fontWeight:600, interval:0, lineHeight:fz(15), hideOverlap:false, overflow:'truncate', width:Math.max(40, el.clientWidth/datos.length - 4), rich:{ s:{ color:I2, fontSize:fz(11), fontFamily:fam, fontWeight:500 } },
        formatter:(v,i) => cmp ? v+'\n{s|'+cortoK(datos[i][2])+'/día}' : v } } }, op), true);
}
// Barra de tiempo de la sala: el indicador hacia arriba y un segundo indicador hacia abajo, cada uno con su escala.
// Al comparar, la línea punteada es el promedio por día del periodo de referencia.
function pintarTiempoSala(k, F){
  const sv = $('sl-tg'); if (!sv) return; const W = Math.max(200, sv.clientWidth), H = Math.max(50, sv.clientHeight), t = TM[S.tema], pw = W/ND;
  const fs = Math.max(10, Math.min(30, uSala()*0.8)), base = H - fs - 6, mid = Math.round(base*0.64), alto1 = mid - 2, alto2 = base - mid - 2;
  const solo = perfilSala().solo, k2 = k==='resc' ? 'ing' : 'resc', capas = solo ? [[k, base-2, base-4, 1]] : [[k, mid, alto1, 1], [k2, mid+1, alto2, -1]];
  const serie = x => { if (x==='co') return coDiario(F); const d = diario(x, IND[x].nat || F.nd==null ? F : { ss:F.ss, n:null, nd:null });
    if (sinMx(x, F.nd)){ const m = diario(x, { ss:F.ss, n:MX, nd:MX }); return d.map((v,i) => Math.max(0, v - m[i])); } return d; };
  let h = '';
  const cada = Math.ceil(MESES_INI.length*fs*4.4/W);
  MESES_INI.forEach((m,i) => { const x = (m[0]*pw).toFixed(1); h += '<line x1="'+x+'" y1="0" x2="'+x+'" y2="'+base+'" stroke="'+t.tinta+'" stroke-opacity=".14"/>'+(i%cada ? '' : '<text x="'+(m[0]*pw+5).toFixed(1)+'" y="'+(H-3)+'" font-size="'+fs.toFixed(1)+'" font-weight="600" fill="'+t.tinta+'" fill-opacity=".65" font-family="Barlow Condensed, Barlow, sans-serif">'+esc(m[1])+'</text>'); });
  capas.forEach(c => { const x = c[0], d = serie(x), mx = Math.max.apply(null, d) || 1, col = t[IND[x].g], U = finDatos(x);
    d.forEach((v,i) => { if (i>=U) return; const bh = Math.max(0.6, v/mx*c[2]); h += '<rect x="'+(i*pw+0.4).toFixed(1)+'" y="'+(c[3]>0 ? c[1]-bh : c[1]).toFixed(1)+'" width="'+Math.max(1,pw-1.2).toFixed(1)+'" height="'+bh.toFixed(1)+'" rx="1" fill="'+col+'" fill-opacity="'+(i<S.dia ? 0.85 : 0.22)+'"/>'; });
    if (SALA.cmp && c[3]>0){ const a = valRango(x, SALA.A[0], SALA.A[1], F.ss, nFde(x, F))/(SALA.A[1]-SALA.A[0]), y = c[1]-Math.min(c[2], a/mx*c[2]);
      if (a>0) h += '<line x1="0" y1="'+y.toFixed(1)+'" x2="'+W+'" y2="'+y.toFixed(1)+'" stroke="'+t.tinta+'" stroke-width="1.4" stroke-dasharray="5 4" stroke-opacity=".8"/><text x="'+(W-4)+'" y="'+Math.max(fs, y-4).toFixed(1)+'" text-anchor="end" font-size="'+(fs*0.92).toFixed(1)+'" font-weight="600" fill="'+t.tinta+'" font-family="Barlow Condensed, Barlow, sans-serif">promedio por día en '+esc(nomRango(SALA.A[0], SALA.A[1]))+'</text>'; }
  });
  if (!solo) h += '<line x1="0" y1="'+(mid+0.5)+'" x2="'+W+'" y2="'+(mid+0.5)+'" stroke="'+t.tinta+'" stroke-opacity=".3"/>';
  temporadas().forEach(x => { const a = Math.max(0, indiceDe(x[0])), b = Math.min(ND, indiceDe(x[1])+1); if (b<=a) return;
    h += '<rect x="'+(a*pw).toFixed(1)+'" y="'+(base+1)+'" width="'+Math.max(3,(b-a)*pw).toFixed(1)+'" height="3" rx="1.5" fill="'+COLOR_TEMP[x[3]]+'"><title>'+esc(x[2])+'</title></rect>'; });
  h += '<g id="sl-cur"><line x1="0" y1="0" x2="0" y2="'+base+'" stroke="'+t.tinta+'" stroke-width="2"/><circle cx="0" cy="'+(base-2)+'" r="5" fill="'+t.tinta+'" stroke="'+t.mar+'" stroke-width="2"/></g>';
  sv.setAttribute('viewBox', '0 0 '+W+' '+H); sv.setAttribute('preserveAspectRatio', 'none'); sv.innerHTML = h; moverCursor(S.play ? S.t : S.dia);
  sv.setAttribute('aria-valuemin', 1); sv.setAttribute('aria-valuemax', ND); sv.setAttribute('aria-valuenow', S.dia); sv.setAttribute('aria-valuetext', 'al '+fechaLarga(S.dia-1));
  const cua = c => '<i style="background:'+c+'"></i>';
  $('sl-tl').innerHTML = '<span>'+cua(t[IND[k].g])+IND[k].n+' por día</span>'+(solo ? '' : '<span>'+cua(t[IND[k2].g])+IND[k2].n+' por día</span>')+'<span class="m">'+(solo ? '' : 'cada uno con su escala · ')+'estados: '+(S.ind ? IND[S.ind].n.toLowerCase() : (perfilSala().mapa ? IND[perfilSala().mapa].n.toLowerCase() : 'rescatados'))+(S.dia<ND || S.play ? ', promedio de 7 días' : ', periodo completo')+'</span>'+
    temporadasEnPeriodo().map(x => '<span class="m"><i style="background:'+COLOR_TEMP[x[1]]+'"></i>'+esc(x[0])+'</span>').join('');
  $('sl-pl').innerHTML = S.play ? '<svg width="16" height="16" viewBox="0 0 16 16"><path d="M3.5 2.5h3v11h-3zM9.5 2.5h3v11h-3z" fill="currentColor"/></svg>' : '<svg width="16" height="16" viewBox="0 0 16 16"><path d="M4.5 2.5v11l9-5.5z" fill="currentColor"/></svg>';
  $('sl-pl').setAttribute('aria-label', S.play ? 'Pausar' : 'Reproducir el periodo');
  $('sl-todo').hidden = S.dia>=ND && !S.play;
}

// En pantalla completa, las etiquetas del mapa que caerían debajo de las cifras, la frase o la gráfica no se dibujan
function tapasSala(){ const lz = $('lz').getBoundingClientRect(); SALA.tapas = ['#sala .sl-a','#sala .sl-fr','#sala .sl-q','#sala .sl-t','#sala .sl-h','#sala .sl-ctx','#m-her'].map(q => document.querySelector(q)).filter(Boolean)
  .map(el => { const r = el.getBoundingClientRect(); return [r.left-lz.left-8, r.top-lz.top-6, r.right-lz.left+8, r.bottom-lz.top+6]; }); }
function tapaEtiqueta(x){ const px = chart.convertToPixel('geo', [x.value[0], x.value[1]]); if (!px) return false;
  const w = String(x.et).length*6.6*E + 14, r = { x:px[0]-8, y:px[1]-10*E, width:w + (x.symbolSize||10)/2, height:20*E };   // la etiqueta va a la derecha del círculo
  return SALA.tapas.some(t => r.x < t[2] && r.x+r.width > t[0] && r.y < t[3] && r.y+r.height > t[1]); }
// En pantalla completa el destino del vuelo se acomoda en la zona libre (entre las cifras y la gráfica), algo más alejado
// Vista de inicio de la pantalla completa: América y Europa, con México a la vista entre las cifras y la gráfica
function volarSala(){ SALA.fijo = true; volar([-88, 22], zoomPara(195, 108)); }
function encuadreSala(c, zr){
  const g = chart.getOption().geo[0], lz = $('lz'), W = lz.clientWidth, H = lz.clientHeight, z = zr*0.64;
  const p1 = chart.convertToPixel('geo', g.center), p2 = chart.convertToPixel('geo', [g.center[0]+1, g.center[1]-1]); if (!p1 || !p2) return [c, z];
  const k = (z*KMX())/g.zoom, gx = (p2[0]-p1[0])*k, gy = (p2[1]-p1[1])*k;            // píxeles por grado al zoom de llegada
  return [[c[0] + 0.03*W/gx, c[1] - 0.09*H/gy], z];
}
function ayudaHerramientas(){
  const tip = document.createElement('div'); tip.className = 'her-tip'; tip.id = 'her-tip'; tip.hidden = true; tip.setAttribute('role','tooltip'); $('lz').appendChild(tip);
  document.querySelectorAll('#m-her button').forEach(b => { if (b.title){ b.dataset.tip = b.title; b.removeAttribute('title'); } });
  let esp = 0;
  const mostrar = (b, dur) => { const nom = b.getAttribute('aria-label') || '', on = b.getAttribute('aria-pressed');
    const des = (b.dataset.tip || '').replace(new RegExp('^'+nom.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'[:,]?\\s*','i'), '');
    tip.innerHTML = '<b>'+esc(nom)+'</b>'+(des && des.toLowerCase()!==nom.toLowerCase() ? '<span>'+esc(des)+'</span>' : '')+(on!=null ? '<em class="'+(on==='true' ? 'on' : '')+'">'+(on==='true' ? 'Encendido' : 'Apagado')+'</em>' : '');
    tip.hidden = false; const r = b.getBoundingClientRect(), z = $('lz').getBoundingClientRect();
    tip.style.top = (r.top - z.top + r.height/2)+'px'; tip.style.right = (z.right - r.left + 10)+'px';
    clearTimeout(esp); if (dur) esp = setTimeout(() => { tip.hidden = true; }, dur); };
  const her = $('m-her');
  her.addEventListener('pointerover', e => { const b = e.target.closest('button'); if (b && e.pointerType==='mouse') mostrar(b); });
  her.addEventListener('pointerout', e => { const b = e.target.closest('button'); if (b && e.pointerType==='mouse' && !b.contains(e.relatedTarget)) tip.hidden = true; });
  her.addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; if (b.dataset.a==='sala'){ tip.hidden = true; return; } const tactil = e.pointerType==='touch' || e.pointerType==='pen' || PUNTERO==='touch'; setTimeout(() => mostrar(b, tactil ? 1800 : 0), 40); });
  her.addEventListener('focusin', e => { const b = e.target.closest('button'); if (b && b.matches(':focus-visible')) mostrar(b); });
  her.addEventListener('focusout', () => { tip.hidden = true; });
}
// Repatriados por punto entre los días a y b de las bases completas (los puntos traen semanas)
function puntoRango(pt, a, b){ const w = D0.wks.find(o => o.obj===pt); if (!w) return 0; const E0 = D0.ends; let t = 0;
  for (let i=0; i<E0.length; i++){ const wa = i ? E0[i-1] : 0, wb = E0[i], x = Math.max(wa,a), y = Math.min(wb,b); if (y>x) t += w.wk[i]*(y-x)/(wb-wa); } return t*sinMxPunto(pt); }
// Los puntos de internación cuentan a todos, igual que «Ingresos» (extranjeros + mexicanos): no se descuenta nada
function sinMxPunto(pt){ return 1; }
// Ficha anclada: al elegir un país o un estado, una ventanita translúcida con sus datos clave, unida por una línea al lugar
function fichaDatos(){
  const sel = S.sel; if (!sel || (sel.t!=='n' && sel.t!=='e')) return null;
  const F = filtro(), ks = S.ind ? [S.ind] : (SALA.on && perfilSala().mapa ? [perfilSala().mapa] : ['ing','resc']), nat = sel.t==='n', xy = nat ? xyNat(sel.i) : xyEst(sel.i); if (!xy) return null;
  const filas = ks.filter(k => nat ? IND[k].nat : true).map(k => { const n = nat ? sel.i : nFde(k, F), ss = nat ? F.ss : [sel.i], v = (SALA.on ? valAcum : acum)(k, ss, n), va = variaTxt(diario(k, nat ? {ss:F.ss, n:sel.i, nd:sel.i} : {ss:[sel.i], n:null, nd:null}));
    return '<div class="fi-r"><span>'+esc(SALA.on ? cap1(PALABRA[k]) : IND[k].n)+'</span><b>'+corto(v)+'</b>'+(va ? '<em class="'+(va.indexOf('▲')===0 ? 'sube' : 'baja')+'">'+va+'</em>' : '')+'</div>'; }).join('');
  const det = detalleFicha(ks[0], sel, F);
  const k0 = ks[0], top = nat ? topEsts(s => sumaSem(k0, 0, NW-1, [s], sel.i), 1)[0] : (IND[k0].nat ? topNats(n => sumaSem(k0, 0, NW-1, [sel.i], n), 1)[0] : null);
  const dest = top ? (nat ? 'Principal O.R.: <b>'+esc(ESTC[top[0]])+'</b>' : 'Principal nacionalidad: <b>'+esc(D.nats[top[0]][0])+'</b>') : '';
  return { xy:xy, col:TM[S.tema][IND[ks[0]].g], html:'<button type="button" class="fi-x" aria-label="Quitar">×</button><span class="fi-k">'+(nat ? 'País' : 'Estado · O.R.')+'</span><b class="fi-n">'+esc(nombreSel())+'</b>'+filas+(dest ? '<span class="fi-d">'+dest+'</span>' : '')+det+(nat ? lineaIdx(sel.i) : '')+'<span class="fi-c">'+(alFinal() ? 'periodo completo' : 'al '+fechaDia(S.dia-1))+' · '+esc(textoCmp())+'</span>' };
}
// El dato que más dice de cada indicador para el lugar elegido
function detalleFicha(k, sel, F){
  const nat = sel.t==='n', ss = nat ? F.ss : [sel.i], n = nat ? sel.i : nFde(k, F), linea = (a, b) => '<span class="fi-d">'+a+': <b>'+esc(b)+'</b></span>';
  const mayor = (v, nombres) => { let i = -1, m = 0; v.forEach((x,j) => { if (x>m){ m = x; i = j; } }); const T = v.reduce((a,x) => a+x, 0); return i<0 ? null : nombres[i]+' ('+Math.round(m/Math.max(T,1)*100)+'%)'; };
  if (k==='ing'){ const v = comp('ing_via', ss, n), via = mayor(v, ['aérea','terrestre','marítima']);
    let pto = null; if (nat && D.ingPunto && D.ingPunto[sel.i]){ const l = D.ingPunto[sel.i].filter(x => !F.ss || F.ss.indexOf(D.puntos[x[0]].s)>=0).sort((a,b) => b[1]-a[1]); if (l[0]) pto = D.puntos[l[0][0]].n; }
    if (!nat){ const l = D.puntos.map((p,i) => [p, p.s===sel.i ? suma(p.wk,0,NW) : 0]).filter(x => x[1]>0).sort((a,b) => b[1]-a[1]); if (l[0]) pto = l[0][0].n; }
    return (via ? linea('Principal vía', via) : '')+(pto ? linea('Principal punto de internación', pto) : ''); }
  if (k==='tram'){ const v = comp('tram_tipo', ss, n).map((x,i) => [x, D.tramTipos[i]]).filter(x => x[1]!=='Otros').sort((a,b) => b[0]-a[0])[0]; return v && v[0]>0 ? linea('Trámite que más se hace', CORTO_TRAM(v[1])) : ''; }
  if (k==='resc'){ const a = comp('resc_rei', ss, n), d = comp('resc_des', ss, n), T = a[0]+a[1], D2 = d[0]+d[1]+d[2];
    return T ? '<span class="fi-d">Reincidentes: <b>'+Math.round(a[1]/T*100)+'%</b>'+(D2 ? ' · a estación migratoria: <b>'+Math.round(d[0]/D2*100)+'%</b>' : '')+'</span>' : ''; }
  if (k==='can'){ const v = comp('can_nna', ss, n), N = v.reduce((a,x) => a+x, 0), na = v.reduce((a,x,i) => a+(i%3===1 ? x : 0), 0); return N ? linea('NNA no acompañados', Math.round(na/N*100)+'% de los NNA') : ''; }
  if (k==='rep' && !nat){ const l = D.repPuntos.map(p => [p, p.s===sel.i ? suma(p.wk,0,NW) : 0]).filter(x => x[1]>0).sort((a,b) => b[1]-a[1]); return l[0] ? linea('Principal punto de repatriación', l[0][0].n) : ''; }
  return '';
}
function pintarFicha(){
  let el = $('ficha'); const d = fichaDatos();
  const sala = SALA.on && $('sala'), columna = sala && getComputedStyle(sala).overflowY==='auto';
  if (!d || $('lz').clientWidth<700 || columna){ if (el) el.hidden = true; FICHA.xy = null; return; }
  if (!el){ el = document.createElement('div'); el.id = 'ficha'; el.className = 'ficha'; el.setAttribute('role','status');
    el.addEventListener('click', e => { if (e.target.closest('.fi-x')) fijarSel(null, false); }); }
  const padre = sala || $('lz'); if (el.parentNode!==padre) padre.insertBefore(el, sala ? sala.querySelector('.sl-h') : null);   // en pantalla completa, debajo de la barra y sus menús
  if (el._h!==d.html){ el._h = d.html; el.innerHTML = d.html; } FICHA.xy = d.xy; FICHA.col = d.col; el.style.setProperty('--fc', d.col); el.hidden = false;
}
const FICHA = { xy:null };
// Cada cuadro: la ficha sigue al lugar en el mapa y se acomoda donde no tape nada; la línea la une con el punto
function moverFicha(){
  const el = $('ficha'); if (!el || el.hidden || !FICHA.xy) return;
  const vis = CAM.vuela ? 0 : CAM.vis; el.style.opacity = vis.toFixed(2); if (vis<0.05) return;
  const pa = chart.convertToPixel('geo', FICHA.xy); if (!pa) return;
  const W = $('lz').clientWidth, H = $('lz').clientHeight, w = el.offsetWidth, h = el.offsetHeight, m = 12;
  const tapas = (SALA.on && SALA.tapas ? SALA.tapas : []).concat([[ $('m-her').offsetLeft-6, 0, W, H ]].filter(() => !SALA.on && false));
  const choca = (x, y) => x<m || y<m || x+w>W-56 || y+h>H-m || tapas.some(t => x < t[2] && x+w > t[0] && y < t[3] && y+h > t[1]);
  const lugares = [[pa[0]+44, pa[1]-h-34], [pa[0]-w-44, pa[1]-h-34], [pa[0]+44, pa[1]+30], [pa[0]-w-44, pa[1]+30], [pa[0]+60, pa[1]-h/2], [pa[0]-w-60, pa[1]-h/2]];
  let p = lugares.find(q => !choca(q[0], q[1])) || lugares[0];
  p = [Math.max(m, Math.min(W-w-56, p[0])), Math.max(m, Math.min(H-h-m, p[1]))];
  el.style.transform = 'translate('+Math.round(p[0])+'px,'+Math.round(p[1])+'px)';
  // conector: del lugar al centro del borde más cercano de la ficha, con un quiebre corto antes de entrar
  const L = p[0], T2 = p[1], Rr = p[0]+w, B = p[1]+h, izq = pa[0] < L, der = pa[0] > Rr, lado = izq || der;
  const ex = izq ? L : der ? Rr : Math.max(L+16, Math.min(Rr-16, pa[0])), ey = lado ? Math.max(T2+16, Math.min(B-16, pa[1])) : (pa[1] < T2 ? T2 : B);
  const qx = lado ? ex + (izq ? -18 : 18)*E : ex, qy = lado ? ey : ey + (pa[1] < T2 ? -18 : 18)*E;
  const c = FICHA.col || TM[S.tema].tinta, ahora = performance.now(), pul = reducido() ? 0.5 : (Math.sin(ahora/520)+1)/2;
  ctxF.save(); ctxF.lineCap = 'round'; ctxF.lineJoin = 'round';
  ctxF.globalAlpha = 0.55*vis; ctxF.strokeStyle = c; ctxF.lineWidth = 1.4*E;
  ctxF.beginPath(); ctxF.moveTo(pa[0], pa[1]); ctxF.lineTo(qx, qy); ctxF.lineTo(ex, ey); ctxF.stroke();
  ctxF.globalAlpha = (0.18 + 0.16*pul)*vis; ctxF.fillStyle = c; ctxF.beginPath(); ctxF.arc(pa[0], pa[1], (7 + 5*pul)*E, 0, 6.283); ctxF.fill();   // halo que respira
  ctxF.globalAlpha = vis; ctxF.beginPath(); ctxF.arc(pa[0], pa[1], 3.4*E, 0, 6.283); ctxF.fill();
  ctxF.globalAlpha = 0.9*vis; ctxF.beginPath(); ctxF.arc(ex, ey, 2.4*E, 0, 6.283); ctxF.fill();
  ctxF.restore();
}
const alfa = (c, a) => /^#/.test(c) ? 'rgba('+hex(c).join(',')+','+a+')' : c;

/* ==== [12] ARRANQUE =============================================== */
function iniciar(){
  escala();
  // Copia desplazada 360° de lo que queda al este del corte, para que Asia y Oceanía aparezcan a la izquierda
  const mover = g => JSON.parse(JSON.stringify(g), (k,v) => Array.isArray(v) && typeof v[0]==='number' && v.length===2 ? [v[0]-360, v[1]] : v);
  const lonMax = f => { let m = -999; JSON.stringify(f.geometry.coordinates).replace(/\[(-?[\d.]+),/g, (x,l) => { m = Math.max(m, +l); return x; }); return m; };
  const copias = GEO.features.filter(f => f.properties.t==='p' && lonMax(f) > CORTE).map(f => ({ type:'Feature', properties:{ key:'W_'+f.properties.key, t:'w' }, geometry:mover(f.geometry) }));
  echarts.registerMap('ianami', { type:'FeatureCollection', features:GEO.features.concat(copias) });
  chart = echarts.init($('lienzo'), null, {renderer:'canvas'});
  if (window.innerWidth<=620 && window.innerHeight>window.innerWidth){ S.modoVista = 'mx'; S.zoom = 1; S.centro = VISTA_MX.c; }   // teléfono vertical: arranca en México
  else { S.modoVista = 'mx'; S.zoom = VISTA_MX.z; S.centro = VISTA_MX.c; }
  chart.setOption(opcionBase());

  if (!(D.caravanas || []).length) $('b-car').hidden = true;
  let tocado = null;
  chart.on('click', p => {
    const clave = (p.seriesId || '')+':'+(p.dataIndex!=null ? p.dataIndex : p.name);
    if (TACTIL && tocado!==clave){ tocado = clave; return; }       // primer toque: solo la tarjeta; segundo toque: selecciona
    tocado = null;
    const mismo = sel => S.sel && S.sel.t===sel.t && S.sel.i===sel.i && S.sel.a===sel.a && S.sel.q===sel.q;      // segundo clic en lo mismo: se quita
    const elegirMapa = (sel, volar) => mismo(sel) ? fijarSel(null, false) : fijarSel(sel, volar);
    if (p.seriesId==='bub' || p.seriesId==='lat') elegirMapa({t:'n', i:p.data.nat}, false);
    else if (p.seriesId==='pts'){ if (!SALA.on) irPunto(p.data.pTipo, p.data.pt); }   // en la Infografía el punto solo muestra su globo
    else if (p.seriesId==='car'){ S.carSel = p.data.fin!=null ? p.data.fin : null; pintarMapa(); }
    else if (p.name && p.name.indexOf('MX_')===0){ const s = ECLAVE.indexOf(p.name); if (s<0) return;
      if (S.agr!=='e' && AGR[S.agr].de[s]>=0) elegirMapa({t:'g', a:S.agr, q:AGR[S.agr].de[s]}, false); else elegirMapa({t:'e', i:s}, false); }
    else if (p.name && /^(W_)?P_\d+$/.test(p.name)){ const n = natDePais(p.name); if (n>=0) elegirMapa({t:'n', i:n}, true); }
  });
  // clic en el mar (fuera de países, estados y círculos): quita la selección; si se arrastró el mapa, no
  { let x0 = 0, y0 = 0; const zr = chart.getZr();
    zr.on('mousedown', e => { x0 = e.offsetX; y0 = e.offsetY; });
    zr.on('click', e => { if (e.target || !S.sel || Math.hypot(e.offsetX-x0, e.offsetY-y0) > 5) return; fijarSel(null, false); }); }
  let espera = 0;
  chart.on('georoam', () => { S.modoVista = 'libre'; clearTimeout(espera); espera = setTimeout(() => { const z = chart.getOption().geo[0].zoom/KMX(); if (Math.abs(z-S.zoom)/S.zoom > 0.04){ S.zoom = z; pintarMapa(); } }, 160); });
  new ResizeObserver(() => { const cambio = escala(); reencuadrar(); ajustarLienzo(); if (cambio) rehacerMapa(); else { pintarTiempo(); if (SALA.on){ if (SALA.gr) SALA.gr.resize(); pintarSala(true); } } }).observe($('lz'));
  window.addEventListener('resize', () => { if (escala()) rehacerMapa(); ajustarAlto(); pintarAnalisis(); });
  if (window.innerHeight<=520) S.kpiModo = 'compacto';        // teléfono acostado: indicadores compactos
  ajustarLienzo();

  $('m-her').addEventListener('click', e => { const b = e.target.closest('[data-a]'); if (b) herramienta(b.dataset.a); });
  $('play').addEventListener('click', reproducir);
  $('vertodo').addEventListener('click', verTodo);
  ayudaHerramientas();
  document.addEventListener('keydown', e => { if (e.key==='Escape' && SALA.on && !SALA.compartida && !(window.IANAMI_CONSULTA && document.getElementById('cq') && !document.getElementById('cq').hidden)){ const p = $('sl-pop'); if (p && !p.hidden) p.hidden = true; else cerrarSala(); } });
  document.addEventListener('fullscreenchange', () => { if (!document.fullscreenElement && SALA.on && !SALA.compartida) cerrarSala(); });   // la liga compartida no se cierra al salir de pantalla completa
  // «?completa» en la dirección (pantallas táctiles de sala): el navegador no deja entrar solo a pantalla completa,
  // así que el primer toque, clic o tecla la activa; si alguien sale, el siguiente toque vuelve a entrar
  if (/[?&](ver|per)=/.test(location.search)) setTimeout(abrirLigaVista, 0);   // liga de «Copiar liga»: la misma vista
  if (/[?&]informe=/.test(location.search)) setTimeout(() => irA('analizar'), 0);
  if (/[?&]arma=/.test(location.search)) setTimeout(() => irA('arma'), 0);   // liga compartida de «Arma tu informe»   // liga compartida de un informe: abre Analizar y el informe
  if (/[?&#]completa\b/i.test(location.search+location.hash)){ const ir = () => { if (!document.fullscreenElement && document.documentElement.requestFullscreen) document.documentElement.requestFullscreen().catch(() => {}); };
    addEventListener('pointerdown', ir, true); addEventListener('keydown', ir, true); }
  $('tgraf').addEventListener('pointermove', tipTiempo); $('tgraf').addEventListener('pointerleave', () => tipTiempo(null)); $('tgraf').addEventListener('pointerup', e => { if (e.pointerType==='touch') setTimeout(() => tipTiempo(null), 1800); });
  const tg = $('tgraf'); let arr = false, pend = 0;
  const arrastre = e => { const d = diaDesdeX(e); cancelAnimationFrame(pend); pend = requestAnimationFrame(() => fijarDia(d)); };
  tg.addEventListener('pointerdown', e => { arr = true; tg.setPointerCapture(e.pointerId); if (S.play){ S.play = false; } arrastre(e); });
  tg.addEventListener('pointermove', e => { if (arr) arrastre(e); });
  tg.addEventListener('pointerup', () => { arr = false; pintarTodo(); });
  tg.addEventListener('keydown', e => { if (e.key==='ArrowLeft'){ fijarDia(S.dia-1); e.preventDefault(); } if (e.key==='ArrowRight'){ fijarDia(S.dia+1); e.preventDefault(); } });
  document.addEventListener('click', e => {
    const T = q => e.target.closest(q);
    if (T('[data-menu-dir]')){ menuDir(CON_HOVER ? true : $('menu-dir').hidden); return; }
    if (T('[data-menu-inf]')){ menuInf(CON_HOVER ? true : $('menu-inf').hidden); return; }
    const inf = T('[data-inf]'); if (inf){ menuInf(false); irA(inf.dataset.inf); return; }
    if (!T('#menu-inf')) menuInf(false);
    const di = T('[data-dir]'); if (di){ S.dir = +di.dataset.dir; menuDir(false); irA('dir'); return; }
    if (!T('#menu-dir')) menuDir(false);
    const vi = T('[data-vista]'); if (vi){ irA(vi.dataset.vista); return; }
    const av = T('[data-av]'); if (av){ abrirAviso(+av.dataset.av); return; }
    if (T('[data-cerrar]')){ fijarSel(null); return; }
    if (T('[data-cerrar-region]')){ S.region = null; pintarTodo(); return; }
    if (T('#plegar')){ S.kpiModo = S.kpiModo==='tarjetas'?'compacto':'tarjetas'; pintarKpis(); ajustarAlto(); return; }
    const bf = T('[data-sel-func]'); if (bf){ const g = bf.dataset.selGrupo, fn = +bf.dataset.selFunc; S.funcSel[g] = fn; pintarKpis(); return; }
    const bv = T('[data-volver-grupo]'); if (bv){ const g = bv.dataset.volverGrupo; S.funcSel[g] = null; pintarKpis(); return; }
    const cm = T('[data-cmp]'); if (cm){ S.cmp = cm.dataset.cmp==='aa' ? 'aa' : +cm.dataset.cmp; pintarTodo(); return; }
    const pe = T('[data-per]'); if (pe){ S.per = pe.dataset.per; cambiarPeriodo(); return; }
    if (T('[data-tipx]')){ mostrarTip(null); return; }
    if (T('[data-tipayx]')){ ayuda(null, null); return; }
    const ib = T('[data-itxt]'); if (ib){ const p = $('rg-pop'); if (p && !p.hidden && ayudaFija && p.dataset.cual===ib.dataset.itxt) ayuda(null, null); else { ayuda(ib, true); $('rg-pop').dataset.cual = ib.dataset.itxt; } return; }
    const k = T('[data-k]'); if (k){ const kk = k.dataset.k, touch = PUNTERO==='touch'; fijarInd(kk); if (touch) mostrarTip(document.querySelector('.kc[data-k="'+kk+'"]'), true); return; }
    const ag = T('[data-agr]'); if (ag){ const v = ag.dataset.agr;      // Mundo y Estado: datos generales; Cinturón y CECO: agrupan
      S.agr = v==='m' ? 'e' : v; if (S.sel && S.sel.t==='g' && (v==='m' || v==='e' || S.sel.a!==S.agr)) S.sel = null;
      if (v==='m') herramienta('mundo'); else if (v==='e') herramienta('mx'); else acercarSiMundo();
      pintarTodo(); return; }
    const enCard = T('#bajo .barra[data-n], #bajo .barra[data-e], #bajo .barra[data-g]');   // barra de una tarjeta: filtra ahí mismo; otro clic en la misma la quita
    if (enCard){ const d = enCard.dataset, sel = d.n!=null ? {t:'n', i:+d.n} : d.e!=null ? {t:'e', i:+d.e} : {t:'g', a:d.g[0], q:+d.g.slice(1)};
      const igual = S.sel && S.sel.t===sel.t && (sel.t==='g' ? S.sel.a===sel.a && S.sel.q===sel.q : S.sel.i===sel.i);
      if (igual) fijarSel(null, false); else fijarSel(sel, false, true); return; }
    const gg = T('[data-g]'); if (gg){ fijarSel({t:'g', a:gg.dataset.g[0], q:+gg.dataset.g.slice(1)}, true); return; }
    const n = T('[data-n]'); if (n){ fijarSel({t:'n', i:+n.dataset.n}, true); return; }
    const es = T('[data-e]'); if (es){ fijarSel({t:'e', i:+es.dataset.e}, true); return; }
    const tp = T('[data-top]'); if (tp){ S.topModo = tp.dataset.top; pintarBajo(); marcarFiltro(); return; }
    const r = T('[data-r]'); if (r){ elegir(+r.dataset.r); return; }
    const cz = T('[data-cruce]'); if (cz){ const q = cz.dataset.cruce.split(':'); S.cruce[q[0]] = +q[1]; pintarBajo(); marcarFiltro(); return; }
    if (!T('.busca') && $('res')) $('res').hidden = true;
  });
  document.addEventListener('change', e => {               // región de origen: filtra las nacionalidades del mapa
    const id = e.target.id;
    if (id==='per-anio'){ S.anio = +e.target.value; S.mes = 0; cambiarPeriodo(); return; }
    if (id==='per-mes'){ S.mes = +e.target.value; cambiarPeriodo(); return; }
    if (id==='cmp-sel'){ const v = e.target.value; S.cmp = v==='sem' || v==='aa' ? v : +v; pintarTodo(); return; }
    if (id==='per-desde' || id==='per-hasta'){ S[id.slice(4)] = e.target.value; if (S.desde>S.hasta){ const x = S.desde; S.desde = S.hasta; S.hasta = x; } cambiarPeriodo(); return; }
    if (id!=='region') return;
    S.region = e.target.value || null; if (S.region) prepararVuelo(); pintarTodo();
    if (S.region) volarConMexico(REGIONES[S.region][1]);
  });
  document.addEventListener('mouseover', e => { const k = e.target.closest('.kc[data-k]'); if (k) mostrarTip(k); const ib = e.target.closest('[data-itxt]'); if (ib && PUNTERO==='mouse' && !ayudaFija) ayuda(ib, false); });
  document.addEventListener('mouseout', e => { const ib = e.target.closest('[data-itxt]'); if (ib && !ib.contains(e.relatedTarget)) ayuda(null); });
  document.addEventListener('pointerdown', e => { if (!e.target.closest('#rg-pop, [data-itxt]')) ayuda(null, null); }, true);
  document.addEventListener('mouseout', e => { const k = e.target.closest('.kc[data-k]'); if (k && !k.contains(e.relatedTarget) && PUNTERO!=='touch') mostrarTip(null); });
  window.addEventListener('scroll', () => mostrarTip(null), {passive:true});
  document.addEventListener('pointerdown', e => { if (e.pointerType==='touch' && !e.target.closest('.kc[data-k], #kpi-tip')) mostrarTip(null); }, true);
  if ($('buscar')) $('buscar').addEventListener('input', buscar);
  if ($('buscar')) $('buscar').addEventListener('keydown', e => { if (e.key==='Enter'){ elegir(0); e.preventDefault(); } if (e.key==='Escape' && $('res')){ $('res').hidden = true; } });
  { const r = rangoPeriodo(); aplicarPeriodo(r[0], r[1]); }       // periodo inicial: Sheinbaum
  if ($('corte')) $('corte').textContent = 'Datos al '+fechaISO(D.corte);
  $('tgraf').setAttribute('aria-valuemax', ND);
  pintarNav();
  pintarTodo();
  ajustarAlto();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(ajustarAlto);
  iniciarConsulta();
  requestAnimationFrame(animar);
}
if (window.echarts && D && GEO) iniciar();
else document.getElementById('lienzo').innerHTML = '<p style="padding:24px">No se pudo cargar el mapa.</p>';
})();
