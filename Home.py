import streamlit as st
import folium
import pandas as pd
import geopandas as gpd
import fsspec
import hashlib
from streamlit_folium import folium_static


st.set_page_config(page_title="Mapa de Sectores Catastrales", page_icon="🗺️",layout="wide",initial_sidebar_state="collapsed")

# streamlit run D:\Dropbox\Empresa\Urbex\_Proyecto_Reporting\Home.py
# https://streamlit.io/
# pipreqs --encoding utf-8 "D:\Dropbox\Empresa\Urbex\_APP_DigitalOcean"

def main():

    #-------------------------------------------------------------------------#
    # Variables 
    formato = {
               'zoom_start_data_busqueda_default':12,
               'latitud_busqueda_default':4.652652, 
               'longitud_busqueda_default':-74.077899,
               }
    
    for key,value in formato.items():
        if key not in st.session_state: 
            st.session_state[key] = value
       
 
    data = load_data()
    
    #-------------------------------------------------------------------------#
    # Mapa
    m = folium.Map(location=[st.session_state.latitud_busqueda_default, st.session_state.longitud_busqueda_default], zoom_start=st.session_state.zoom_start_data_busqueda_default,tiles="cartodbpositron")
    
    geojson = data2geopandas(data)
    popup   = folium.GeoJsonPopup(
        fields=["popup"],
        aliases=[""],
        localize=True,
        labels=True,
    )
    folium.GeoJson(geojson,style_function=style_function_geojson, highlight_function=lambda feature: {'fillColor': '#e74c3c','color': '#c0392b','weight': 2,'fillOpacity': 0.6,'opacity': 1.0}, popup=popup).add_to(m)
    folium_static(m,width=None,height=700)        

                    
def style_function_color(feature):
    return {
        'fillColor': '#828DEE',
        'color':'#828DEE',
        'weight': 1,
    }

@st.cache_data
def load_data():
    try:
        #---------------------------------------------------------------------#
        # Original: El shape original del barrio catastral
        #   url = 'https://geospatial-data.nyc3.digitaloceanspaces.com/_bogota_shp/sector_catastral.parquet'
        #   with fsspec.open(url) as f:
        #       dataexport = gpd.read_parquet(f)
        #       dataexport.columns = [x.lower() for x in dataexport]
        #   dataexport['wkt'] = dataexport['geometry'].apply(lambda x: x.wkt)
            
        #---------------------------------------------------------------------#
        # Reduccion mapshaper: D:\Dropbox\Empresa\Urbex\_Urbex_General_Data\MySQL_upload\_upload_shape_digital_ocean.py
        url        = 'https://geospatial-data.nyc3.digitaloceanspaces.com/_bogota_shp/_scacodigo_mapshaper.parquet'
        dataexport = pd.read_parquet(url)

        dataexport.rename(columns={'scacodigo': 'precbarrio'}, inplace=True)
        dataexport = dataexport.drop_duplicates(subset='precbarrio', keep='first')
        
        dataexport['filename'] = dataexport['precbarrio'].apply(lambda x: generar_codigo(x))
        dataexport['url']      = dataexport['filename'].apply(lambda x: f'https://etl-urbex.nyc3.digitaloceanspaces.com/_reporting/_bogota_reporting_barrio_html/{x}.html')
        
        if 'geometry' in dataexport: 
            del dataexport['geometry']
        dataexport = pd.DataFrame(dataexport)
        
        return dataexport
    except Exception as e:
        st.error(f"Error cargando los datos: {str(e)}")
        return None
    
def generar_codigo(x):
    hash_sha256 = hashlib.sha256(x.encode()).hexdigest()
    codigo      = hash_sha256[:16]
    return codigo

def style_function_geojson(feature):
    color = feature['properties']['color']
    return {
        'fillColor': color,
        'color': color,
        'weight': 1,
        #'fillOpacity': 0.2,
    }

@st.cache_data(show_spinner=False)
def data2geopandas(data):
    
    geojson   = pd.DataFrame().to_json()
    if 'wkt' in data: 
        data = data[data['wkt'].notnull()]
        
    if not data.empty:
        data['geometry'] = gpd.GeoSeries.from_wkt(data['wkt'])
        data             = gpd.GeoDataFrame(data, geometry='geometry')
        data['color']    = '#5A189A' #'#003F2D'
        data['popup']    = None
        data.index       = range(len(data))
        
        for idx, row in data.iterrows():
            # Crear el contenido del popup
            popup_content = f"""
            <div style="font-family: Arial, sans-serif; min-width: 200px;">
                <h4 style="margin-bottom: 10px; color: #2E86AB;">{row['scanombre']}</h4>
            """
            
            if 'url' in row and pd.notna(row['url']):
                popup_content += f"""
                <div style="margin-top: 10px;">
                    <a href="{row['url']}" target="_blank" 
                       style="background-color: #2E86AB; color: white; padding: 8px 16px; 
                              text-decoration: none; border-radius: 4px; display: inline-block;">
                        📊 Ver Reporte
                    </a>
                </div>
                """
            else:
                popup_content += """
                <div style="margin-top: 10px;">
                    <p style="color: #666; font-style: italic;">Reporte disponible próximamente</p>
                </div>
                """
            popup_content += "</div>"
            data.loc[idx,'popup'] = popup_content

        geojson = data.to_json()
    return geojson

if __name__ == "__main__":
    main()