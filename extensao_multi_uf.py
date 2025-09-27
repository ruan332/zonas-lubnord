#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extensão Multi-UF para o Sistema Principal
Adiciona funcionalidades multi-UF ao app_mapa_interativo.py existente
"""

from flask import jsonify, request
from flask_socketio import emit
import pandas as pd
from gerenciador_ufs import gerenciador_ufs

class ExtensaoMultiUF:
    """
    Classe que estende o sistema principal com funcionalidades multi-UF
    """
    
    def __init__(self, app, socketio, gerenciador_principal):
        self.app = app
        self.socketio = socketio
        self.gerenciador = gerenciador_principal
        self.registrar_rotas()
        self.registrar_eventos_websocket()
    
    def registrar_rotas(self):
        """Registra as rotas multi-UF no app Flask"""
        
        @self.app.route('/api/ufs_disponiveis')
        def api_ufs_disponiveis():
            """API para obter UFs disponíveis no sistema multi-UF"""
            try:
                if hasattr(self.gerenciador, 'modo_multi_uf') and self.gerenciador.modo_multi_uf:
                    ufs = gerenciador_ufs.listar_ufs_ativas()
                    return jsonify({
                        'sucesso': True,
                        'ufs': ufs,
                        'uf_atual': getattr(self.gerenciador, 'uf_atual', 'PE'),
                        'modo_multi_uf': True
                    })
                else:
                    return jsonify({
                        'sucesso': True,
                        'ufs': [{'codigo': 'PE', 'nome': 'Pernambuco', 'diretorio': 'PE'}],
                        'uf_atual': 'PE',
                        'modo_multi_uf': False
                    })
            except Exception as e:
                return jsonify({
                    'sucesso': False,
                    'erro': str(e)
                })
        
        @self.app.route('/api/carregar_uf/<codigo_uf>')
        def api_carregar_uf(codigo_uf):
            """API para carregar uma UF específica"""
            try:
                codigo_uf = codigo_uf.upper()
                
                if not hasattr(self.gerenciador, 'modo_multi_uf') or not self.gerenciador.modo_multi_uf:
                    return jsonify({
                        'sucesso': False,
                        'erro': 'Sistema multi-UF não está ativo'
                    })
                
                # Usar método de carregamento se existir, senão implementar aqui
                if hasattr(self.gerenciador, 'carregar_uf'):
                    sucesso = self.gerenciador.carregar_uf(codigo_uf)
                else:
                    sucesso = self._carregar_uf_manual(codigo_uf)
                
                if sucesso:
                    # Obter estatísticas da UF carregada
                    stats = gerenciador_ufs.obter_estatisticas_uf(codigo_uf)
                    
                    return jsonify({
                        'sucesso': True,
                        'uf': codigo_uf,
                        'nome': getattr(self.gerenciador, 'dados_uf_atual', {}).get('nome', codigo_uf),
                        'estatisticas': stats,
                        'zonas': list(self.gerenciador.zona_cores.keys()),
                        'cores': self.gerenciador.zona_cores
                    })
                else:
                    return jsonify({
                        'sucesso': False,
                        'erro': f'Não foi possível carregar a UF {codigo_uf}'
                    })
                    
            except Exception as e:
                return jsonify({
                    'sucesso': False,
                    'erro': str(e)
                })
        
        @self.app.route('/api/info_uf_atual')
        def api_info_uf_atual():
            """API para obter informações da UF atualmente carregada"""
            try:
                uf_atual = getattr(self.gerenciador, 'uf_atual', 'PE')
                
                if hasattr(self.gerenciador, 'modo_multi_uf') and self.gerenciador.modo_multi_uf:
                    stats = gerenciador_ufs.obter_estatisticas_uf(uf_atual)
                    nome_uf = getattr(self.gerenciador, 'dados_uf_atual', {}).get('nome', uf_atual)
                else:
                    # Estatísticas básicas para modo tradicional
                    stats = {
                        'total_municipios': len(self.gerenciador.dados_municipios),
                        'zonas': list(self.gerenciador.zona_cores.keys()),
                        'total_zonas': len(self.gerenciador.zona_cores)
                    }
                    nome_uf = 'Pernambuco'
                
                return jsonify({
                    'sucesso': True,
                    'uf_atual': uf_atual,
                    'nome': nome_uf,
                    'estatisticas': stats,
                    'modo_multi_uf': hasattr(self.gerenciador, 'modo_multi_uf') and self.gerenciador.modo_multi_uf
                })
                
            except Exception as e:
                return jsonify({
                    'sucesso': False,
                    'erro': str(e)
                })
    
    def registrar_eventos_websocket(self):
        """Registra eventos WebSocket para multi-UF"""
        
        @self.socketio.on('carregar_uf')
        def handle_carregar_uf(data):
            """Carrega uma UF via WebSocket"""
            try:
                codigo_uf = data.get('uf', '').upper()
                
                if not hasattr(self.gerenciador, 'modo_multi_uf') or not self.gerenciador.modo_multi_uf:
                    emit('uf_carregada', {
                        'sucesso': False, 
                        'erro': 'Sistema multi-UF não está ativo'
                    })
                    return
                
                # Usar método de carregamento se existir
                if hasattr(self.gerenciador, 'carregar_uf'):
                    sucesso = self.gerenciador.carregar_uf(codigo_uf)
                else:
                    sucesso = self._carregar_uf_manual(codigo_uf)
                
                if sucesso:
                    # Emitir dados atualizados para o cliente
                    emit('uf_carregada', {
                        'sucesso': True,
                        'uf': codigo_uf,
                        'nome': getattr(self.gerenciador, 'dados_uf_atual', {}).get('nome', codigo_uf),
                        'zonas': list(self.gerenciador.zona_cores.keys()),
                        'cores': self.gerenciador.zona_cores
                    })
                    
                    # Emitir dados do mapa atualizados
                    emit('dados_mapa_atualizados', {
                        'dados': self.gerenciador.obter_dados_mapa_geojson()
                    })
                else:
                    emit('uf_carregada', {
                        'sucesso': False,
                        'erro': f'Erro ao carregar {codigo_uf}'
                    })
                    
            except Exception as e:
                emit('uf_carregada', {
                    'sucesso': False,
                    'erro': str(e)
                })
        
        @self.socketio.on('obter_ufs_disponiveis')
        def handle_obter_ufs():
            """Obtém lista de UFs disponíveis via WebSocket"""
            try:
                if hasattr(self.gerenciador, 'modo_multi_uf') and self.gerenciador.modo_multi_uf:
                    ufs = gerenciador_ufs.listar_ufs_ativas()
                    emit('ufs_disponiveis', {
                        'sucesso': True,
                        'ufs': ufs,
                        'uf_atual': getattr(self.gerenciador, 'uf_atual', 'PE')
                    })
                else:
                    emit('ufs_disponiveis', {
                        'sucesso': True,
                        'ufs': [{'codigo': 'PE', 'nome': 'Pernambuco'}],
                        'uf_atual': 'PE'
                    })
            except Exception as e:
                emit('ufs_disponiveis', {
                    'sucesso': False,
                    'erro': str(e)
                })
    
    def _carregar_uf_manual(self, codigo_uf):
        """Carrega UF manualmente se o método não existir no gerenciador"""
        try:
            if not gerenciador_ufs.validar_uf(codigo_uf):
                return False
            
            # Carregar dados da UF
            dados_uf = gerenciador_ufs.carregar_dados_uf(codigo_uf)
            
            # Atualizar gerenciador principal
            self.gerenciador.uf_atual = codigo_uf
            self.gerenciador.dados_uf_atual = dados_uf
            self.gerenciador.dados_municipios = dados_uf['municipios'].copy()
            self.gerenciador.zona_cores = dados_uf['zona_cores']
            
            # Converter geometrias
            import geopandas as gpd
            geometrias_json = dados_uf['geometrias']
            self.gerenciador.geometrias = gpd.GeoDataFrame.from_features(geometrias_json['features'])
            self.gerenciador.geometrias['id'] = self.gerenciador.geometrias['id'].astype(str)
            
            # Aplicar alterações se existirem
            if hasattr(self.gerenciador, '_aplicar_alteracoes_salvas_multi_uf'):
                self.gerenciador._aplicar_alteracoes_salvas_multi_uf()
            
            # Preparar dados do mapa
            if hasattr(self.gerenciador, 'preparar_dados_mapa'):
                self.gerenciador.preparar_dados_mapa()
            
            print(f"✅ UF {codigo_uf} carregada manualmente via extensão")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar UF {codigo_uf} manualmente: {e}")
            return False
    
    def ativar_modo_multi_uf(self):
        """Ativa o modo multi-UF no gerenciador principal"""
        try:
            self.gerenciador.modo_multi_uf = True
            self.gerenciador.uf_atual = getattr(self.gerenciador, 'uf_atual', 'PE')
            self.gerenciador.dados_uf_atual = None
            
            # Sobrescrever método obter_dados_geojson para usar dados multi-UF
            self._sobrescrever_metodos_gerenciador()
            
            print("✅ Modo Multi-UF ativado via extensão")
            return True
        except Exception as e:
            print(f"❌ Erro ao ativar modo Multi-UF: {e}")
            return False
    
    def _sobrescrever_metodos_gerenciador(self):
        """Sobrescreve métodos do gerenciador para usar dados multi-UF"""
        
        # Salvar método original
        if not hasattr(self.gerenciador, '_obter_dados_geojson_original'):
            self.gerenciador._obter_dados_geojson_original = self.gerenciador.obter_dados_geojson
        
        def obter_dados_geojson_multi_uf():
            """Versão multi-UF do obter_dados_geojson"""
            try:
                # Se tem dados UF atual, usar dados processados
                if hasattr(self.gerenciador, 'dados_uf_atual') and self.gerenciador.dados_uf_atual:
                    dados_uf = self.gerenciador.dados_uf_atual
                    
                    if 'dados_processados' in dados_uf:
                        dados_processados = dados_uf['dados_processados']
                        
                        # Converter para GeoJSON
                        features = []
                        for _, row in dados_processados.iterrows():
                            if row['geometry'] is not None:
                                # Função auxiliar para tratar valores None/NaN
                                def safe_value(value, default=''):
                                    if pd.isna(value) or value is None:
                                        return default
                                    return value
                                
                                def safe_float(value, default=0.0):
                                    try:
                                        if pd.isna(value) or value is None:
                                            return default
                                        return float(value)
                                    except (ValueError, TypeError):
                                        return default
                                
                                feature = {
                                    'type': 'Feature',
                                    'properties': {
                                        'CD_Mun': str(safe_value(row.get('CD_Mun', row['id']))),
                                        'Cidade': str(safe_value(row['Cidade'], 'Município não identificado')),
                                        'Zona': str(safe_value(row['Zona'], 'Sem Zona')),
                                        'Cor': str(safe_value(row['cor_zona'], '#CCCCCC')),
                                        'UF': str(safe_value(row.get('UF', ''))),
                                        'SELL_OUT_ANUAL': safe_float(row.get('SELL OUT ANUAL', 0)),
                                        'POTENCIAL_ANUAL': safe_float(row.get('POTENCIAL ANUAL', 0)),
                                        'PDV': safe_float(row.get('PDV', 0)),
                                        'SHARE': round((safe_float(row.get('SELL OUT ANUAL', 0)) / safe_float(row.get('POTENCIAL ANUAL', 1)) * 100) if safe_float(row.get('POTENCIAL ANUAL', 0)) > 0 else 0, 2)
                                    },
                                    'geometry': row['geometry'].__geo_interface__ if hasattr(row['geometry'], '__geo_interface__') else row['geometry']
                                }
                                features.append(feature)
                        
                        return {
                            'type': 'FeatureCollection',
                            'features': features
                        }
                
                # Fallback para método original
                return self.gerenciador._obter_dados_geojson_original()
                
            except Exception as e:
                print(f"❌ Erro em obter_dados_geojson_multi_uf: {e}")
                # Fallback para método original em caso de erro
                return self.gerenciador._obter_dados_geojson_original()
        
        # Substituir método
        self.gerenciador.obter_dados_geojson = obter_dados_geojson_multi_uf
        print("🔄 Método obter_dados_geojson sobrescrito para usar dados multi-UF")

def inicializar_extensao_multi_uf(app, socketio, gerenciador):
    """
    Função para inicializar a extensão multi-UF
    
    Args:
        app: Instância do Flask
        socketio: Instância do SocketIO
        gerenciador: Instância do GerenciadorMapaInterativo
    
    Returns:
        Instância da ExtensaoMultiUF
    """
    try:
        extensao = ExtensaoMultiUF(app, socketio, gerenciador)
        extensao.ativar_modo_multi_uf()
        
        print("🔌 Extensão Multi-UF inicializada com sucesso!")
        print("📍 Novas rotas disponíveis:")
        print("   • GET /api/ufs_disponiveis")
        print("   • GET /api/carregar_uf/<codigo_uf>")
        print("   • GET /api/info_uf_atual")
        print("🔗 Novos eventos WebSocket:")
        print("   • carregar_uf")
        print("   • obter_ufs_disponiveis")
        
        return extensao
        
    except Exception as e:
        print(f"❌ Erro ao inicializar extensão Multi-UF: {e}")
        return None
