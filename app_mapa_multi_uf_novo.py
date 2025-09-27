#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação Web com Mapa Interativo Multi-UF em Tempo Real
Permite edição de zonas diretamente no mapa com suporte a múltiplos estados
"""

import os
import json
import re
import pandas as pd
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from datetime import datetime
import geopandas as gpd
from gerenciador_ufs import gerenciador_ufs

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mapa_interativo_multi_uf_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

class GerenciadorMapaMultiUF:
    """
    Gerenciador principal do mapa interativo com suporte a múltiplas UFs
    """
    
    def __init__(self):
        self.uf_atual = None
        self.dados_uf_atual = None
        print("🚀 Gerenciador Multi-UF inicializado")
    
    def carregar_uf(self, codigo_uf: str) -> bool:
        """
        Carrega uma UF específica
        
        Args:
            codigo_uf: Código da UF (PE, AL, SE)
            
        Returns:
            True se carregou com sucesso
        """
        try:
            print(f"🔄 Carregando UF: {codigo_uf}")
            self.dados_uf_atual = gerenciador_ufs.carregar_dados_uf(codigo_uf)
            self.uf_atual = codigo_uf
            print(f"✅ UF {codigo_uf} carregada com sucesso")
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar UF {codigo_uf}: {e}")
            return False
    
    def obter_dados_mapa(self) -> dict:
        """
        Obtém os dados formatados para o mapa
        
        Returns:
            Dicionário com dados do mapa
        """
        if not self.dados_uf_atual:
            return {"error": "Nenhuma UF carregada"}
        
        try:
            gdf = self.dados_uf_atual['dados_processados']
            
            # Converter para formato JSON para o mapa
            features = []
            for idx, row in gdf.iterrows():
                if pd.notna(row.get('geometry')):
                    feature = {
                        "type": "Feature",
                        "properties": {
                            "id": str(row.get('id', '')),
                            "name": str(row.get('name', row.get('Cidade', ''))),
                            "zona": str(row.get('Zona', 'Sem Zona')),
                            "cor": str(row.get('cor_zona', '#CCCCCC')),
                            "municipio": str(row.get('Cidade', '')),
                            "cd_mun": str(row.get('CD_Mun', '')),
                            "uf": str(row.get('UF', self.uf_atual)),
                            "populacao": row.get('POPULAÇÃO ', 0),
                            "sell_out": row.get('SELL OUT ANUAL', 0),
                            "potencial": row.get('POTENCIAL ANUAL', 0)
                        },
                        "geometry": row['geometry'].__geo_interface__ if hasattr(row['geometry'], '__geo_interface__') else None
                    }
                    features.append(feature)
            
            return {
                "type": "FeatureCollection",
                "features": features,
                "uf_info": {
                    "codigo": self.uf_atual,
                    "nome": self.dados_uf_atual['nome'],
                    "total_municipios": len(features)
                }
            }
            
        except Exception as e:
            print(f"❌ Erro ao obter dados do mapa: {e}")
            return {"error": str(e)}
    
    def obter_zonas_disponiveis(self) -> list:
        """
        Obtém as zonas disponíveis para a UF atual
        
        Returns:
            Lista de zonas com suas cores
        """
        if not self.dados_uf_atual:
            return []
        
        zona_cores = self.dados_uf_atual['zona_cores']
        return [
            {"nome": zona, "cor": cor}
            for zona, cor in zona_cores.items()
        ]
    
    def alterar_zona_municipio(self, municipio_id: str, nova_zona: str) -> dict:
        """
        Altera a zona de um município
        
        Args:
            municipio_id: ID do município
            nova_zona: Nova zona
            
        Returns:
            Resultado da operação
        """
        if not self.dados_uf_atual:
            return {"success": False, "error": "Nenhuma UF carregada"}
        
        try:
            # Encontrar município atual
            municipios = self.dados_uf_atual['municipios']
            mask = municipios['CD_Mun'].astype(str) == str(municipio_id)
            
            if not mask.any():
                return {"success": False, "error": f"Município {municipio_id} não encontrado"}
            
            zona_anterior = municipios.loc[mask, 'Zona'].iloc[0]
            
            if zona_anterior == nova_zona:
                return {"success": False, "error": "Zona já é a mesma"}
            
            # Salvar alteração usando o gerenciador
            sucesso = gerenciador_ufs.salvar_alteracao(
                self.uf_atual, municipio_id, zona_anterior, nova_zona
            )
            
            if sucesso:
                # Recarregar dados atualizados
                self.dados_uf_atual = gerenciador_ufs.carregar_dados_uf(self.uf_atual)
                
                return {
                    "success": True,
                    "municipio_id": municipio_id,
                    "zona_anterior": zona_anterior,
                    "zona_nova": nova_zona,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": "Erro ao salvar alteração"}
                
        except Exception as e:
            print(f"❌ Erro ao alterar zona: {e}")
            return {"success": False, "error": str(e)}

# Instância global do gerenciador
gerenciador_mapa = GerenciadorMapaMultiUF()

# === ROTAS DA API ===

@app.route('/')
def index():
    """Página principal"""
    return render_template('mapa_multi_uf.html')

@app.route('/api/ufs')
def api_ufs():
    """Retorna lista de UFs disponíveis"""
    try:
        ufs = gerenciador_ufs.listar_ufs_ativas()
        return jsonify({
            "success": True,
            "ufs": ufs,
            "total": len(ufs)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/carregar_uf/<codigo_uf>')
def api_carregar_uf(codigo_uf):
    """Carrega uma UF específica"""
    try:
        sucesso = gerenciador_mapa.carregar_uf(codigo_uf.upper())
        if sucesso:
            estatisticas = gerenciador_ufs.obter_estatisticas_uf(codigo_uf.upper())
            return jsonify({
                "success": True,
                "uf": codigo_uf.upper(),
                "estatisticas": estatisticas
            })
        else:
            return jsonify({"success": False, "error": f"Erro ao carregar UF {codigo_uf}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/dados_mapa')
def api_dados_mapa():
    """Retorna dados do mapa para a UF atual"""
    try:
        dados = gerenciador_mapa.obter_dados_mapa()
        if "error" in dados:
            return jsonify({"success": False, "error": dados["error"]})
        return jsonify({"success": True, "dados": dados})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/zonas')
def api_zonas():
    """Retorna zonas disponíveis para a UF atual"""
    try:
        zonas = gerenciador_mapa.obter_zonas_disponiveis()
        return jsonify({"success": True, "zonas": zonas})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/alterar_zona', methods=['POST'])
def api_alterar_zona():
    """Altera a zona de um município"""
    try:
        dados = request.get_json()
        municipio_id = dados.get('municipio_id')
        nova_zona = dados.get('nova_zona')
        
        if not municipio_id or not nova_zona:
            return jsonify({"success": False, "error": "Parâmetros obrigatórios: municipio_id, nova_zona"})
        
        resultado = gerenciador_mapa.alterar_zona_municipio(municipio_id, nova_zona)
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/estatisticas')
def api_estatisticas():
    """Retorna estatísticas da UF atual"""
    try:
        if not gerenciador_mapa.uf_atual:
            return jsonify({"success": False, "error": "Nenhuma UF carregada"})
        
        estatisticas = gerenciador_ufs.obter_estatisticas_uf(gerenciador_mapa.uf_atual)
        return jsonify({"success": True, "estatisticas": estatisticas})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# === EVENTOS WEBSOCKET ===

@socketio.on('connect')
def handle_connect():
    """Cliente conectado"""
    print(f"🔌 Cliente conectado: {request.sid}")
    emit('status', {'message': 'Conectado ao servidor Multi-UF'})

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado"""
    print(f"🔌 Cliente desconectado: {request.sid}")

@socketio.on('carregar_uf')
def handle_carregar_uf(data):
    """Carrega uma UF via WebSocket"""
    try:
        codigo_uf = data.get('uf', '').upper()
        sucesso = gerenciador_mapa.carregar_uf(codigo_uf)
        
        if sucesso:
            dados_mapa = gerenciador_mapa.obter_dados_mapa()
            zonas = gerenciador_mapa.obter_zonas_disponiveis()
            estatisticas = gerenciador_ufs.obter_estatisticas_uf(codigo_uf)
            
            emit('uf_carregada', {
                'success': True,
                'uf': codigo_uf,
                'dados_mapa': dados_mapa,
                'zonas': zonas,
                'estatisticas': estatisticas
            })
        else:
            emit('uf_carregada', {'success': False, 'error': f'Erro ao carregar {codigo_uf}'})
            
    except Exception as e:
        emit('uf_carregada', {'success': False, 'error': str(e)})

@socketio.on('alterar_zona')
def handle_alterar_zona(data):
    """Altera zona via WebSocket"""
    try:
        municipio_id = data.get('municipio_id')
        nova_zona = data.get('nova_zona')
        
        resultado = gerenciador_mapa.alterar_zona_municipio(municipio_id, nova_zona)
        
        if resultado['success']:
            # Emitir atualização para todos os clientes
            dados_atualizados = gerenciador_mapa.obter_dados_mapa()
            socketio.emit('zona_alterada', {
                'success': True,
                'alteracao': resultado,
                'dados_atualizados': dados_atualizados
            })
        else:
            emit('zona_alterada', resultado)
            
    except Exception as e:
        emit('zona_alterada', {'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("🌍 Iniciando Mapa Interativo Multi-UF...")
    print("📍 Acesse: http://localhost:5000")
    
    # Listar UFs disponíveis
    ufs_disponiveis = gerenciador_ufs.listar_ufs_ativas()
    print(f"🗺️  UFs disponíveis: {[uf['codigo'] for uf in ufs_disponiveis]}")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
