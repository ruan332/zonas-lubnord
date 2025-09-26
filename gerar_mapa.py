import geopandas as gpd
import folium
from folium import features
from folium import plugins
import pandas as pd

# Carregar o JSON
gdf_json = gpd.read_file('pb.json')

# Verificar se o GeoDataFrame está correto
if 'geometry' not in gdf_json.columns:
    raise ValueError("O arquivo JSON não contém a coluna 'geometry'. Verifique o formato do arquivo.")

# Carregar a base de dados com as zonas e cidades
clientes_data = pd.read_excel('pb_atual.xlsx', engine='openpyxl')

def centralizar_mapa_na_capital(gdf_json, nome_capital):
    # Localizar a geometria da capital
    capital_geojson = gdf_json[gdf_json['name'].str.lower() == nome_capital.lower()]
    
    if not capital_geojson.empty:
        # Calcular o centroide da geometria da capital
        capital_centroide = capital_geojson['geometry'].iloc[0].centroid
        return [capital_centroide.y, capital_centroide.x]
    else:
        raise ValueError(f"Capital '{nome_capital}' não encontrada no arquivo JSON.")

def gerar_mapa(zoom_start=8):
    # Nome da capital do estado
    nome_capital = "João Pessoa"  # Substitua pelo nome correto da capital, se necessário
    
    # Centralizar o mapa na capital
    try:
        capital_coords = centralizar_mapa_na_capital(gdf_json, nome_capital)
    except ValueError as e:
        print(e)
        print("Usando coordenadas padrão para centralizar o mapa.")
        capital_coords = [-5.0, -36.5]  # Coordenadas padrão
    
    # Criar o mapa centralizado na capital
    m = folium.Map(location=capital_coords, zoom_start=zoom_start)

    # Criar um grupo de folhas para o GeoJson
    geojson_group = folium.FeatureGroup(name='Zonas')

    # Criar um dicionário para mapear Zona para Cor
    zona_cor_mapping = {}

    # Iterar sobre os dados das cidades
    for index, row in clientes_data.iterrows():
        cd_mun = str(row['CD_Mun'])  # Certificar que o código do município é uma string
        zona = row['Zona']
        cor_texto = row['Cor']  # Assumindo que a coluna 'Cor' contém os códigos de cores em formato hexadecimal

        # Mapear Zona para Cor
        zona_cor_mapping[zona] = cor_texto

        # Encontrar todas as geometrias correspondentes ao código do município no JSON
        cidades_geojson = gdf_json[gdf_json['id'] == cd_mun]

        # Verificar se há geometrias encontradas
        if not cidades_geojson.empty:
            # Iterar sobre as geometrias
            for _, cidade_geojson in cidades_geojson.iterrows():
                # Adicionar GeoJson ao grupo com o estilo da zona
                features.GeoJson(
                    cidade_geojson['geometry'],
                    style_function=lambda feature, cor_texto=cor_texto: {
                        'fillColor': cor_texto,
                        'color': 'black',
                        'weight': 0.5,
                        'fillOpacity': 0.7,
                    },
                    highlight_function=lambda x: {'weight': 2, 'fillOpacity': 0.3},
                    name=str(cd_mun)
                ).add_to(geojson_group)
        else:
            print(f"Nenhum resultado encontrado para o código do município: {cd_mun}")

    # Adicionar o grupo de GeoJson ao mapa
    geojson_group.add_to(m)

    # Adicionar controle de camadas (layers control) ao mapa
    folium.LayerControl().add_to(m)

    # Adicionar legenda dinâmica
    legend_html = '''
         <div style="position: fixed; 
                     top: 10px; left: 10px; width: auto; height: auto;
                     padding: 10px;
                     border:2px solid grey; z-index:9999; font-size:14px;
                     background-color:white;
                     ">&nbsp; <b>Legenda das Zonas</b> <br>
    '''
    
    # Ordenar as zonas alfabeticamente
    zonas_ordenadas = sorted(zona_cor_mapping.items(), key=lambda item: item[0])
    
    for zona, cor_texto in zonas_ordenadas:
        legend_html += f'&nbsp; <i style="background:{cor_texto}; width:20px; height:20px; display:inline-block;"></i> {zona} <br>'
    
    legend_html += '</div>'
    
    # Adicionar legenda ao mapa
    m.get_root().html.add_child(folium.Element(legend_html))

    # Salvar o mapa como um arquivo HTML
    m.save('pb_atual.html')

    print(f"Mapa Gerado com Sucesso!")

# Chamada da função principal com valor padrão de zoom
gerar_mapa()
