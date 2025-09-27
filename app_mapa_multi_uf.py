#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação Web com Mapa Interativo Multi-UF
Permite trabalhar com múltiplas Unidades Federativas
"""

import os
import json
import re
import pandas as pd
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from datetime import datetime
import geopandas as gpd
from sistema_persistencia import SistemaPersistencia
from gerenciador_multi_uf import GerenciadorMultiUF

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mapa_interativo_multi_uf_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

class GerenciadorMapaMultiUF:
    def __init__(self):
        self.gerenciador_uf = GerenciadorMultiUF()
        self.persistencia = None
        self.dados_municipios = None
        self.geometrias = None
        self.zona_cores = None
        self.dados_completos = None
        
        # Tentar selecionar PE como padrão
        if "PE" in self.gerenciador_uf.ufs_disponiveis:
            self.selecionar_uf("PE")
    
    def selecionar_uf(self, codigo_uf: str) -> bool:
        """Seleciona uma UF para trabalhar"""
        try:
            if not self.gerenciador_uf.selecionar_uf(codigo_uf):
                return False
            
            # Obter dados da UF selecionada
            self.dados_municipios, self.geometrias, self.zona_cores = self.gerenciador_uf.obter_dados_uf_atual()
            
            # Configurar sistema de persistência para a UF atual
            config_uf = self.gerenciador_uf.ufs_disponiveis[codigo_uf]
            diretorio_uf = self.gerenciador_uf.diretorio_base / config_uf.diretorio
            arquivo_alteracoes = diretorio_uf / "alteracoes_zonas.json"
            
            self.persistencia = SistemaPersistencia(str(arquivo_alteracoes))
            
            # Aplicar alterações salvas
            self._aplicar_alteracoes_salvas()
            
            # Preparar dados para o mapa
            self.preparar_dados_mapa()
            
            print(f"✅ UF {config_uf.nome} ({codigo_uf}) selecionada e carregada")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao selecionar UF {codigo_uf}: {e}")
            return False
    
    def _aplicar_alteracoes_salvas(self):
        """Aplica alterações salvas do arquivo JSON aos dados carregados"""
        try:
            if not self.persistencia:
                return
                
            alteracoes = self.persistencia.carregar_alteracoes()
            if alteracoes and 'alteracoes' in alteracoes:
                alteracoes_aplicadas = 0
                for alt in alteracoes['alteracoes']:
                    cd_mun = str(alt['cd_mun'])
                    nova_zona = alt['zona_nova']
                    
                    # Encontrar e atualizar o município
                    mask = self.dados_municipios['CD_Mun'].astype(str) == cd_mun
                    if mask.any():
                        self.dados_municipios.loc[mask, 'Zona'] = nova_zona
                        if nova_zona in self.zona_cores:
                            self.dados_municipios.loc[mask, 'Cor'] = self.zona_cores[nova_zona]
                        alteracoes_aplicadas += 1
                
                if alteracoes_aplicadas > 0:
                    print(f"🔄 Aplicadas {alteracoes_aplicadas} alterações salvas")
                    
        except Exception as e:
            print(f"⚠️ Erro ao aplicar alterações salvas: {e}")
    
    def preparar_dados_mapa(self):
        """Prepara dados mesclados para o mapa"""
        if self.dados_municipios is None or self.geometrias is None:
            return
            
        # Converter códigos para string
        self.dados_municipios['CD_Mun'] = self.dados_municipios['CD_Mun'].astype(str)
        
        # Mesclar geometrias com dados
        self.dados_completos = self.geometrias.merge(
            self.dados_municipios,
            left_on='id',
            right_on='CD_Mun',
            how='left'
        )
        
        # Preencher valores nulos
        self.dados_completos['Zona'] = self.dados_completos['Zona'].fillna('Sem Zona')
        self.dados_completos['Cidade'] = self.dados_completos['Cidade'].fillna('Município não identificado')
        
        # Atualizar cores
        def obter_cor_zona(zona):
            if zona == 'Sem Zona':
                return '#CCCCCC'
            return self.zona_cores.get(zona, '#CCCCCC')
        
        self.dados_completos['Cor'] = self.dados_completos['Zona'].apply(obter_cor_zona)
        
        print(f"✅ Dados preparados: {len(self.dados_completos)} registros")
    
    def obter_dados_geojson(self):
        """Retorna dados no formato GeoJSON para o mapa"""
        if self.dados_completos is None:
            return {"type": "FeatureCollection", "features": []}
        
        # Calcular Share se as colunas necessárias existirem
        tem_sell_out = 'SELL OUT ANUAL' in self.dados_completos.columns
        tem_potencial = 'POTENCIAL ANUAL' in self.dados_completos.columns
        
        if tem_sell_out and tem_potencial:
            self.dados_completos['Share_Calculado'] = (
                self.dados_completos['SELL OUT ANUAL'] / 
                self.dados_completos['POTENCIAL ANUAL'] * 100
            ).fillna(0)
        else:
            self.dados_completos['Share_Calculado'] = 0
        
        # Converter para GeoJSON
        geojson_data = {
            "type": "FeatureCollection",
            "features": []
        }
        
        for _, row in self.dados_completos.iterrows():
            if pd.notna(row['geometry']):
                feature = {
                    "type": "Feature",
                    "properties": {
                        "cd_mun": str(row['id']) if pd.notna(row['id']) else '',
                        "cidade": str(row['Cidade']) if pd.notna(row['Cidade']) else 'Município não identificado',
                        "zona": str(row['Zona']) if pd.notna(row['Zona']) else 'Sem Zona',
                        "cor": str(row['Cor']) if pd.notna(row['Cor']) else '#CCCCCC',
                        "uf": str(row.get('UF', '')) if pd.notna(row.get('UF')) else '',
                        "mesorregiao": str(row.get('Mesorregião Geográfica', 'N/A')) if pd.notna(row.get('Mesorregião Geográfica')) else 'N/A',
                        "share": round(float(row['Share_Calculado']) if pd.notna(row['Share_Calculado']) else 0, 2),
                        "sell_out": float(row.get('SELL OUT ANUAL', 0)) if pd.notna(row.get('SELL OUT ANUAL')) else 0,
                        "potencial": float(row.get('POTENCIAL ANUAL', 0)) if pd.notna(row.get('POTENCIAL ANUAL')) else 0,
                        "pdv": float(row.get('PDV', 0)) if pd.notna(row.get('PDV')) else 0,
                        "populacao": float(row.get('POPULAÇÃO', 0)) if pd.notna(row.get('POPULAÇÃO')) else 0
                    },
                    "geometry": json.loads(gpd.GeoSeries([row['geometry']]).to_json())['features'][0]['geometry']
                }
                geojson_data["features"].append(feature)
        
        return geojson_data
    
    def alterar_zona_municipio(self, cd_mun, nova_zona):
        """Altera zona de um município"""
        try:
            if self.dados_municipios is None or self.zona_cores is None:
                return False, "Nenhuma UF selecionada", None
            
            # Verificar se município existe
            mask = self.dados_municipios['CD_Mun'].astype(str) == str(cd_mun)
            if not mask.any():
                return False, "Município não encontrado", None
            
            # Verificar se zona existe
            if nova_zona != 'Sem Zona' and nova_zona not in self.zona_cores:
                return False, "Zona não encontrada", None
            
            # Obter dados atuais
            idx = self.dados_municipios[mask].index[0]
            zona_anterior = self.dados_municipios.loc[idx, 'Zona']
            cidade = self.dados_municipios.loc[idx, 'Cidade']
            
            # Alterar zona
            self.dados_municipios.loc[idx, 'Zona'] = nova_zona
            if nova_zona == 'Sem Zona':
                self.dados_municipios.loc[idx, 'Cor'] = '#CCCCCC'
            else:
                self.dados_municipios.loc[idx, 'Cor'] = self.zona_cores[nova_zona]
            
            # Salvar alteração
            if self.persistencia:
                sucesso = self.persistencia.salvar_alteracao(
                    cd_mun=cd_mun,
                    cidade=cidade,
                    zona_anterior=zona_anterior,
                    zona_nova=nova_zona,
                    usuario="MapaInterativo"
                )
                
                if sucesso:
                    self.preparar_dados_mapa()
                    
                    cor_nova = '#CCCCCC' if nova_zona == 'Sem Zona' else self.zona_cores[nova_zona]
                    municipio_atualizado = {
                        'cd_mun': cd_mun,
                        'cidade': cidade,
                        'zona_anterior': zona_anterior,
                        'zona_nova': nova_zona,
                        'cor_nova': cor_nova
                    }
                    
                    return True, "Zona alterada com sucesso", municipio_atualizado
                else:
                    return False, "Erro ao salvar alteração", None
            else:
                return False, "Sistema de persistência não disponível", None
                
        except Exception as e:
            return False, f"Erro: {str(e)}", None
    
    def obter_estatisticas(self):
        """Retorna estatísticas das zonas"""
        try:
            if self.dados_municipios is None or self.zona_cores is None:
                return {}
            
            # Verificar colunas disponíveis
            tem_sell_out = 'SELL OUT ANUAL' in self.dados_municipios.columns
            tem_potencial = 'POTENCIAL ANUAL' in self.dados_municipios.columns
            tem_pdv = 'PDV' in self.dados_municipios.columns
            
            # Agregação básica
            agg_dict = {'CD_Mun': 'count'}
            if tem_sell_out:
                agg_dict['SELL OUT ANUAL'] = 'sum'
            if tem_potencial:
                agg_dict['POTENCIAL ANUAL'] = 'sum'
            if tem_pdv:
                agg_dict['PDV'] = 'sum'
            
            stats = self.dados_municipios.groupby('Zona').agg(agg_dict)
            stats = stats.rename(columns={'CD_Mun': 'total_municipios'})
            
            stats_dict = {}
            for zona, row in stats.iterrows():
                stat_item = {
                    'total_municipios': int(row['total_municipios']),
                    'cor': self.zona_cores.get(zona, '#CCCCCC'),
                    'percentual': round((row['total_municipios'] / len(self.dados_municipios)) * 100, 1)
                }
                
                # Calcular share
                if tem_sell_out and tem_potencial:
                    sell_out_total = float(row['SELL OUT ANUAL'])
                    potencial_total = float(row['POTENCIAL ANUAL'])
                    if potencial_total > 0:
                        share_zona = (sell_out_total / potencial_total) * 100
                        stat_item['share_medio'] = round(share_zona, 2)
                    else:
                        stat_item['share_medio'] = 0.0
                
                if tem_pdv and 'PDV' in row:
                    stat_item['total_pdv'] = int(row['PDV'])
                
                stats_dict[zona] = stat_item
            
            return stats_dict
            
        except Exception as e:
            print(f"❌ Erro ao calcular estatísticas: {e}")
            return {}

# Instância global do gerenciador
gerenciador = GerenciadorMapaMultiUF()

@app.route('/')
def index():
    """Página principal com mapa interativo"""
    return render_template('mapa_multi_uf.html')

@app.route('/api/ufs_disponiveis')
def api_ufs_disponiveis():
    """API para obter UFs disponíveis"""
    try:
        ufs = gerenciador.gerenciador_uf.obter_ufs_disponiveis()
        uf_atual = gerenciador.gerenciador_uf.obter_info_uf_atual()
        
        return jsonify({
            'sucesso': True,
            'ufs_disponiveis': ufs,
            'uf_atual': uf_atual
        })
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        })

@app.route('/api/selecionar_uf/<codigo_uf>')
def api_selecionar_uf(codigo_uf):
    """API para selecionar uma UF"""
    try:
        sucesso = gerenciador.selecionar_uf(codigo_uf.upper())
        
        if sucesso:
            uf_info = gerenciador.gerenciador_uf.obter_info_uf_atual()
            return jsonify({
                'sucesso': True,
                'mensagem': f'UF {codigo_uf} selecionada com sucesso',
                'uf_info': uf_info
            })
        else:
            return jsonify({
                'sucesso': False,
                'erro': f'Erro ao selecionar UF {codigo_uf}'
            })
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        })

@app.route('/api/dados_mapa')
def api_dados_mapa():
    """API para obter dados do mapa em formato GeoJSON"""
    try:
        geojson_data = gerenciador.obter_dados_geojson()
        return jsonify({
            'sucesso': True,
            'dados': geojson_data,
            'total_municipios': len(geojson_data['features'])
        })
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        })

@app.route('/api/zonas')
def api_zonas():
    """API para obter zonas disponíveis"""
    try:
        if gerenciador.zona_cores is None:
            return jsonify({
                'sucesso': False,
                'erro': 'Nenhuma UF selecionada'
            })
        
        return jsonify({
            'sucesso': True,
            'zonas': list(gerenciador.zona_cores.keys()),
            'cores': gerenciador.zona_cores
        })
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        })

@app.route('/api/estatisticas')
def api_estatisticas():
    """API para obter estatísticas"""
    try:
        stats = gerenciador.obter_estatisticas()
        total_geral = len(gerenciador.dados_municipios) if gerenciador.dados_municipios is not None else 0
        
        return jsonify({
            'sucesso': True,
            'estatisticas': stats,
            'total_geral': total_geral
        })
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        })

@socketio.on('alterar_zona')
def handle_alterar_zona(data):
    """Handler WebSocket para alteração de zona em tempo real"""
    cd_mun = data.get('cd_mun')
    nova_zona = data.get('nova_zona')
    
    sucesso, mensagem, municipio_atualizado = gerenciador.alterar_zona_municipio(cd_mun, nova_zona)
    
    if sucesso:
        socketio.emit('zona_alterada', {
            'sucesso': True,
            'municipio': municipio_atualizado,
            'mensagem': mensagem
        })
        
        stats = gerenciador.obter_estatisticas()
        socketio.emit('estatisticas_atualizadas', {
            'estatisticas': stats
        })
    else:
        emit('erro_alteracao', {
            'sucesso': False,
            'mensagem': mensagem
        })

@socketio.on('selecionar_uf')
def handle_selecionar_uf(data):
    """Handler WebSocket para seleção de UF"""
    codigo_uf = data.get('codigo_uf', '').upper()
    
    try:
        sucesso = gerenciador.selecionar_uf(codigo_uf)
        
        if sucesso:
            uf_info = gerenciador.gerenciador_uf.obter_info_uf_atual()
            
            # Emitir para todos os clientes que a UF foi alterada
            socketio.emit('uf_selecionada', {
                'sucesso': True,
                'codigo_uf': codigo_uf,
                'uf_info': uf_info,
                'mensagem': f'UF {uf_info["nome"]} selecionada'
            })
            
            # Emitir dados atualizados
            geojson_data = gerenciador.obter_dados_geojson()
            socketio.emit('dados_mapa_atualizados', {
                'dados': geojson_data
            })
            
            # Emitir zonas atualizadas
            socketio.emit('zonas_atualizadas', {
                'zonas': list(gerenciador.zona_cores.keys()),
                'cores': gerenciador.zona_cores
            })
            
            # Emitir estatísticas atualizadas
            stats = gerenciador.obter_estatisticas()
            socketio.emit('estatisticas_atualizadas', {
                'estatisticas': stats
            })
            
        else:
            emit('erro_selecao_uf', {
                'sucesso': False,
                'mensagem': f'Erro ao selecionar UF {codigo_uf}'
            })
            
    except Exception as e:
        emit('erro_selecao_uf', {
            'sucesso': False,
            'mensagem': f'Erro: {str(e)}'
        })

@socketio.on('connect')
def handle_connect():
    """Handler para conexão WebSocket"""
    print(f"Cliente conectado: {request.sid}")
    emit('conectado', {'mensagem': 'Conectado ao servidor de mapa interativo multi-UF'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handler para desconexão WebSocket"""
    print(f"Cliente desconectado: {request.sid}")

if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Configurações do servidor
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5002))
    debug = os.getenv('FLASK_ENV', 'production') != 'production'
    
    print("🚀 Iniciando aplicação de mapa interativo multi-UF...")
    print(f"📍 Servidor: {host}:{port}")
    print(f"🌍 Ambiente: {os.getenv('FLASK_ENV', 'production')}")
    print("🗺️ Mapa interativo com suporte a múltiplas UFs")
    
    socketio.run(app, host=host, port=port, debug=debug)
