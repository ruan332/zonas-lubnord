import pandas as pd
import geopandas as gpd
import folium
import json
from folium import plugins
import os

class MapaInterativoPernambuco:
    def __init__(self):
        self.dados_mapa = None
        self.geometria = None
        self.zona_cores = None
        self.mapa = None
        
    def carregar_dados(self):
        """Carrega todos os dados necessários"""
        print("Carregando dados...")
        
        # Carregar dados completos do mapa (com potencial, PDV, share)
        try:
            self.dados_mapa = pd.read_csv('pernambuco_dados_gerar_mapa.csv')
            print("✅ Dados completos carregados (com potencial, PDV, share)")
        except FileNotFoundError:
            # Fallback para dados básicos
            self.dados_mapa = pd.read_csv('dados_mapa_pernambuco.csv')
            print("⚠️ Dados básicos carregados (sem potencial, PDV, share)")
        
        # Carregar geometria
        self.geometria = gpd.read_file('pernambuco.json')
        
        # Carregar mapeamento de cores
        with open('zona_cores_mapping.json', 'r', encoding='utf-8') as f:
            self.zona_cores = json.load(f)
            
        print(f"✅ Dados carregados: {len(self.dados_mapa)} municípios, {len(self.zona_cores)} zonas")
        
    def preparar_dados_mapa(self):
        """Prepara e mescla os dados para o mapa"""
        print("Preparando dados para o mapa...")
        
        # Converter códigos para string para garantir correspondência
        self.dados_mapa['CD_Mun'] = self.dados_mapa['CD_Mun'].astype(str)
        self.geometria['id'] = self.geometria['id'].astype(str)
        
        # Mesclar dados com geometria
        self.geometria = self.geometria.merge(
            self.dados_mapa, 
            left_on='id', 
            right_on='CD_Mun', 
            how='left'
        )
        
        # Preencher valores nulos
        self.geometria['Zona'] = self.geometria['Zona'].fillna('Sem Zona')
        
        # Verificar se temos dados completos ou básicos
        if 'Cidade' in self.geometria.columns:
            self.geometria['Cidade'] = self.geometria['Cidade'].fillna('Município não identificado')
        else:
            # Para dados completos, usar a coluna correta
            self.geometria['Cidade'] = self.geometria['Cidade'].fillna('Município não identificado')
        
        # Atualizar cores com o novo mapeamento
        self.geometria['Cor'] = self.geometria['Zona'].map(self.zona_cores).fillna('#CCCCCC')
        
        print(f"✅ Dados preparados: {len(self.geometria)} geometrias")
        
    def criar_mapa_base(self):
        """Cria o mapa base centrado em Pernambuco"""
        # Coordenadas aproximadas do centro de Pernambuco
        centro_pe = [-8.8137, -36.9541]  # Recife como referência
        
        # Criar mapa base
        self.mapa = folium.Map(
            location=centro_pe,
            zoom_start=7,
            tiles='OpenStreetMap'
        )
        
        # Adicionar diferentes tipos de tiles
        folium.TileLayer(
            tiles='https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}{r}.png',
            attr='Map tiles by Stamen Design, CC BY 3.0 — Map data © OpenStreetMap contributors',
            name='Stamen Terrain'
        ).add_to(self.mapa)
        
        folium.TileLayer(
            tiles='CartoDB positron',
            name='CartoDB Positron'
        ).add_to(self.mapa)
        
        print("✅ Mapa base criado")
        
    def adicionar_camada_zonas(self):
        """Adiciona a camada de zonas coloridas ao mapa"""
        print("Adicionando camada de zonas...")
        
        # Função para estilo de cada feature
        def style_function(feature):
            zona = feature['properties'].get('Zona', 'Sem Zona')
            cor = self.zona_cores.get(zona, '#CCCCCC')
            
            return {
                'fillColor': cor,
                'color': '#000000',
                'weight': 1,
                'fillOpacity': 0.7,
                'opacity': 0.8
            }
        
        # Função para highlight
        def highlight_function(feature):
            return {
                'fillColor': '#ffff00',
                'color': '#000000',
                'weight': 3,
                'fillOpacity': 0.9,
                'opacity': 1.0
            }
        
        # Adicionar camada de zonas
        zona_layer = folium.GeoJson(
            self.geometria,
            style_function=style_function,
            highlight_function=highlight_function,
            tooltip=folium.features.GeoJsonTooltip(
                fields=['Cidade', 'Zona', 'UF'],
                aliases=['Município:', 'Zona:', 'Estado:'],
                style=("background-color: white; color: #333333; font-family: arial; "
                      "font-size: 12px; padding: 10px;")
            ),
            popup=folium.features.GeoJsonPopup(
                fields=['Cidade', 'Zona', 'Mesorregião Geográfica', 'CD_Mun'],
                aliases=['Município:', 'Zona:', 'Mesorregião:', 'Código IBGE:'],
                style=("background-color: white; color: #333333; font-family: arial; "
                      "font-size: 12px; padding: 10px;")
            )
        ).add_to(self.mapa)
        
        print("✅ Camada de zonas adicionada")
        
    def criar_legenda(self):
        """Cria uma legenda interativa para as zonas"""
        print("Criando legenda...")
        
        # Legenda removida conforme solicitado pelo usuário
        # A legenda das zonas não será mais exibida no mapa
        
        print("✅ Legenda removida")
        
    def adicionar_controles(self):
        """Adiciona controles interativos ao mapa"""
        print("Adicionando controles...")
        
        # Controle de camadas
        folium.LayerControl().add_to(self.mapa)
        
        # Plugin de tela cheia
        plugins.Fullscreen().add_to(self.mapa)
        
        # Plugin de medição
        plugins.MeasureControl().add_to(self.mapa)
        
        # Minimap
        minimap = plugins.MiniMap(toggle_display=True)
        self.mapa.add_child(minimap)
        
        print("✅ Controles adicionados")
        
    def adicionar_estatisticas(self):
        """Adiciona painel de estatísticas com dados de potencial, PDV e share"""
        print("Adicionando estatísticas...")
        
        # Verificar se temos dados completos
        tem_dados_completos = all(col in self.dados_mapa.columns for col in ['POTENCIAL MÊS', 'PDV', 'SELL OUT ANUAL', 'POTENCIAL ANUAL'])
        
        # Calcular estatísticas por zona
        if tem_dados_completos:
            # Calcular %share correto: SELL OUT ANUAL / POTENCIAL ANUAL
            self.dados_mapa['SHARE_CALCULADO'] = (self.dados_mapa['SELL OUT ANUAL'] / self.dados_mapa['POTENCIAL ANUAL']) * 100
            
            # Corrigido: usar soma para cálculo correto de Share por zona
            stats_por_zona = self.dados_mapa.groupby('Zona').agg({
                'CD_Mun': 'count',
                'POTENCIAL MÊS': 'sum',
                'PDV': 'sum',
                'SELL OUT ANUAL': 'sum',
                'POTENCIAL ANUAL': 'sum'
            }).round(2)
            
            # Calcular Share correto da zona: (Soma SELL OUT / Soma POTENCIAL) * 100
            stats_por_zona['Share Médio'] = (
                stats_por_zona['SELL OUT ANUAL'] / stats_por_zona['POTENCIAL ANUAL'] * 100
            ).fillna(0).round(2)
            
            stats_por_zona.columns = ['Municípios', 'Potencial Mensal', 'PDV', 'Sell Out Total', 'Potencial Total', 'Share Médio']
        else:
            stats_por_zona = self.dados_mapa.groupby('Zona').size().to_frame('Municípios')
        
        # Ordenar por número de municípios
        stats_por_zona = stats_por_zona.sort_values('Municípios', ascending=False)
        
        # HTML das estatísticas com funcionalidade de colapso
        stats_html = '''
        <div id="stats-panel" style="position: fixed; 
                    top: 10px; right: 10px; width: 350px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 15px; border-radius: 8px;
                    box-shadow: 0 0 20px rgba(0,0,0,0.3);">
        
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h4 style="margin: 0; color: #333;">📊 Resumo das Zonas</h4>
            <button id="toggle-stats" onclick="toggleStats()" 
                    style="background: #2196f3; color: white; border: none; 
                           border-radius: 4px; padding: 5px 10px; cursor: pointer;
                           font-size: 12px; font-weight: bold;">
                ▼ Expandir
            </button>
        </div>
        
        <div id="stats-content" style="display: none; max-height: 400px; overflow-y: auto;">
        '''
        
        for zona, row in stats_por_zona.head(12).iterrows():
            cor = self.zona_cores.get(zona, '#CCCCCC')
            municipios = int(row['Municípios'])
            percentual = (municipios / len(self.dados_mapa)) * 100
            
            stats_html += f'''
            <div style="margin: 8px 0; padding: 8px; border-left: 4px solid {cor}; 
                       background-color: #f8f9fa; border-radius: 4px;">
                <div style="font-weight: bold; color: #333; margin-bottom: 4px;">
                    {zona[:25]}{'...' if len(zona) > 25 else ''}
                </div>
                <div style="font-size: 11px; color: #666;">
                    <div>🏘️ {municipios} municípios ({percentual:.1f}%)</div>
            '''
            
            if tem_dados_completos:
                potencial = row['Potencial Mensal']
                pdv = int(row['PDV'])
                share = row['Share Médio']
                
                stats_html += f'''
                    <div>💧 Potencial: {potencial:,.0f} litros</div>
                    <div>🏪 PDV: {pdv:,}</div>
                    <div>📈 Share: {share:.2f}%</div>
                '''
            
            stats_html += '''
                </div>
            </div>
            '''
        
        # Adicionar totais
        if tem_dados_completos:
            total_potencial = self.dados_mapa['POTENCIAL MÊS'].sum()
            total_pdv = self.dados_mapa['PDV'].sum()
            share_geral = self.dados_mapa['SHARE_CALCULADO'].mean()
            
            stats_html += f'''
            <div style="margin-top: 15px; padding: 10px; background-color: #e3f2fd; 
                       border-radius: 6px; border: 1px solid #2196f3;">
                <div style="font-weight: bold; color: #1976d2; margin-bottom: 6px;">
                    📈 TOTAIS GERAIS
                </div>
                <div style="font-size: 11px; color: #333;">
                    <div>🏘️ Total: {len(self.dados_mapa)} municípios</div>
                    <div>💧 Potencial Total: {total_potencial:,.0f} litros</div>
                    <div>🏪 PDV Total: {total_pdv:,.0f}</div>
                    <div>📈 Share Médio Geral: {share_geral:.2f}%</div>
                </div>
            </div>
            '''
        
        stats_html += '''
        </div>
        
        <script>
        function toggleStats() {
            const content = document.getElementById('stats-content');
            const button = document.getElementById('toggle-stats');
            
            if (content.style.display === 'none') {
                content.style.display = 'block';
                button.innerHTML = '▲ Ocultar';
                button.style.background = '#f44336';
            } else {
                content.style.display = 'none';
                button.innerHTML = '▼ Expandir';
                button.style.background = '#2196f3';
            }
        }
        
        // Responsividade para dispositivos móveis
        function adjustStatsPanel() {
            const panel = document.getElementById('stats-panel');
            if (window.innerWidth <= 768) {
                panel.style.width = '90%';
                panel.style.right = '5%';
                panel.style.left = '5%';
                panel.style.top = '10px';
            } else {
                panel.style.width = '350px';
                panel.style.right = '10px';
                panel.style.left = 'auto';
                panel.style.top = '10px';
            }
        }
        
        // Aplicar ajustes na inicialização e redimensionamento
        window.addEventListener('load', adjustStatsPanel);
        window.addEventListener('resize', adjustStatsPanel);
        </script>
        
        </div>
        '''
        
        # Adicionar estatísticas ao mapa
        self.mapa.get_root().html.add_child(folium.Element(stats_html))
        
        print("✅ Estatísticas adicionadas")
        
    def gerar_mapa_completo(self, nome_arquivo='mapa_pernambuco_interativo.html'):
        """Gera o mapa completo"""
        print("=== GERANDO MAPA INTERATIVO DE PERNAMBUCO ===")
        
        # Executar todas as etapas
        self.carregar_dados()
        self.preparar_dados_mapa()
        self.criar_mapa_base()
        self.adicionar_camada_zonas()
        self.criar_legenda()
        self.adicionar_controles()
        self.adicionar_estatisticas()
        
        # Salvar mapa
        self.mapa.save(nome_arquivo)
        
        print(f"✅ MAPA GERADO COM SUCESSO: {nome_arquivo}")
        print(f"📂 Arquivo salvo em: {os.path.abspath(nome_arquivo)}")
        
        return nome_arquivo
        
    def gerar_relatorio(self):
        """Gera relatório das zonas"""
        print("\n=== RELATÓRIO DAS ZONAS ===")
        
        # Estatísticas gerais
        total_municipios = len(self.dados_mapa)
        total_zonas = len(self.zona_cores)
        
        print(f"📊 Total de municípios: {total_municipios}")
        print(f"🎯 Total de zonas: {total_zonas}")
        
        # Estatísticas por zona
        print(f"\n📈 Distribuição por zona:")
        stats_zona = self.dados_mapa.groupby('Zona').agg({
            'Cidade': 'count',
            'Mesorregião Geográfica': 'nunique'
        }).round(2)
        
        stats_zona.columns = ['Municípios', 'Mesorregiões']
        stats_zona['Percentual'] = (stats_zona['Municípios'] / total_municipios * 100).round(1)
        stats_zona = stats_zona.sort_values('Municípios', ascending=False)
        
        for zona, row in stats_zona.iterrows():
            cor = self.zona_cores.get(zona, '#CCCCCC')
            print(f"   {zona}: {row['Municípios']} municípios ({row['Percentual']}%) - {cor}")
        
        return stats_zona

def main():
    """Função principal"""
    # Criar instância do gerador de mapas
    gerador = MapaInterativoPernambuco()
    
    # Gerar mapa
    arquivo_mapa = gerador.gerar_mapa_completo()
    
    # Gerar relatório
    gerador.gerar_relatorio()
    
    print(f"\n🎉 PROCESSO CONCLUÍDO!")
    print(f"📁 Abra o arquivo '{arquivo_mapa}' no seu navegador para visualizar o mapa")

if __name__ == "__main__":
    main()