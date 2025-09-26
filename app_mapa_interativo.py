#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação Web com Mapa Interativo em Tempo Real
Permite edição de zonas diretamente no mapa sem gerar arquivos
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

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mapa_interativo_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

class GerenciadorMapaInterativo:
    def __init__(self):
        self.persistencia = SistemaPersistencia()
        self.carregar_dados_iniciais()
        
    def carregar_dados_iniciais(self):
        """Carrega todos os dados necessários"""
        try:
            # Carregar dados dos municípios
            self.dados_municipios = pd.read_csv('pernambuco_dados_gerar_mapa.csv')
            print(f"✅ Dados carregados: {len(self.dados_municipios)} municípios")
            
            # Carregar geometrias
            self.geometrias = gpd.read_file('pernambuco.json')
            self.geometrias['id'] = self.geometrias['id'].astype(str)
            print(f"✅ Geometrias carregadas: {len(self.geometrias)} polígonos")
            
            # Carregar cores das zonas
            with open('zona_cores_mapping.json', 'r', encoding='utf-8') as f:
                self.zona_cores = json.load(f)
            print(f"✅ Cores carregadas: {len(self.zona_cores)} zonas")
            
            # Mesclar dados com geometrias
            self.preparar_dados_mapa()
            
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            raise
    
    def preparar_dados_mapa(self):
        """Prepara dados mesclados para o mapa"""
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
        self.dados_completos['Cor'] = self.dados_completos['Zona'].map(self.zona_cores).fillna('#CCCCCC')
        
        print(f"✅ Dados preparados: {len(self.dados_completos)} registros")
    
    def obter_dados_geojson(self):
        """Retorna dados no formato GeoJSON para o mapa com dados de Share"""
        # Calcular Share se as colunas necessárias existirem
        tem_sell_out = 'SELL OUT ANUAL' in self.dados_completos.columns
        tem_potencial = 'POTENCIAL ANUAL' in self.dados_completos.columns
        
        if tem_sell_out and tem_potencial:
            # Calcular Share como SELL OUT ANUAL / POTENCIAL ANUAL * 100
            self.dados_completos['Share_Calculado'] = (
                self.dados_completos['SELL OUT ANUAL'] / 
                self.dados_completos['POTENCIAL ANUAL'] * 100
            ).fillna(0)
        elif 'SHARE_CALCULADO' in self.dados_completos.columns:
            # Usar coluna existente se disponível
            self.dados_completos['Share_Calculado'] = self.dados_completos['SHARE_CALCULADO'].fillna(0)
        else:
            # Definir Share como 0 se não houver dados
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
                        "cd_mun": row['id'],
                        "cidade": row['Cidade'],
                        "zona": row['Zona'],
                        "cor": row['Cor'],
                        "uf": row.get('UF', 'PE'),
                        "mesorregiao": row.get('Mesorregião Geográfica', 'N/A'),
                        "share": round(float(row['Share_Calculado']), 2),
                        "sell_out": float(row.get('SELL OUT ANUAL', 0)),
                        "potencial": float(row.get('POTENCIAL ANUAL', 0)),
                        "pdv": float(row.get('PDV', 0)),
                        "populacao": float(row.get('POPULAÇÃO', 0))
                    },
                    "geometry": json.loads(gpd.GeoSeries([row['geometry']]).to_json())['features'][0]['geometry']
                }
                geojson_data["features"].append(feature)
        
        return geojson_data
    
    def alterar_zona_municipio(self, cd_mun, nova_zona):
        """Altera zona de um município e retorna dados atualizados"""
        try:
            # Verificar se município existe
            mask = self.dados_municipios['CD_Mun'].astype(str) == str(cd_mun)
            if not mask.any():
                return False, "Município não encontrado", None
            
            # Verificar se zona existe
            if nova_zona not in self.zona_cores:
                return False, "Zona não encontrada", None
            
            # Obter dados atuais
            idx = self.dados_municipios[mask].index[0]
            zona_anterior = self.dados_municipios.loc[idx, 'Zona']
            cidade = self.dados_municipios.loc[idx, 'Cidade']
            
            # Alterar zona
            self.dados_municipios.loc[idx, 'Zona'] = nova_zona
            self.dados_municipios.loc[idx, 'Cor'] = self.zona_cores[nova_zona]
            
            # Salvar alteração
            sucesso = self.persistencia.salvar_alteracao(
                cd_mun=cd_mun,
                cidade=cidade,
                zona_anterior=zona_anterior,
                zona_nova=nova_zona,
                usuario="MapaInterativo"
            )
            
            if sucesso:
                # Atualizar dados preparados
                self.preparar_dados_mapa()
                
                # Retornar dados atualizados do município
                municipio_atualizado = {
                    'cd_mun': cd_mun,
                    'cidade': cidade,
                    'zona_anterior': zona_anterior,
                    'zona_nova': nova_zona,
                    'cor_nova': self.zona_cores[nova_zona]
                }
                
                return True, "Zona alterada com sucesso", municipio_atualizado
            else:
                return False, "Erro ao salvar alteração", None
                
        except Exception as e:
            return False, f"Erro: {str(e)}", None
    
    def obter_estatisticas(self):
        """Retorna estatísticas das zonas"""
        # Verificar se existem colunas de SELL OUT ANUAL e POTENCIAL ANUAL
        tem_sell_out = 'SELL OUT ANUAL' in self.dados_municipios.columns
        tem_potencial = 'POTENCIAL ANUAL' in self.dados_municipios.columns
        tem_pdv = 'PDV' in self.dados_municipios.columns
        
        if tem_sell_out and tem_potencial:
            # Calcular share como SELL OUT ANUAL / POTENCIAL ANUAL
            self.dados_municipios['Share_Calculado'] = (
                self.dados_municipios['SELL OUT ANUAL'] / 
                self.dados_municipios['POTENCIAL ANUAL'] * 100
            ).fillna(0)
            
            stats = self.dados_municipios.groupby('Zona').agg({
                'CD_Mun': 'count',
                'Share_Calculado': 'mean',
                'PDV': 'sum' if tem_pdv else 'count'
            }).rename(columns={'CD_Mun': 'total_municipios'})
        else:
            # Usar SHARE_CALCULADO se disponível
            if 'SHARE_CALCULADO' in self.dados_municipios.columns:
                stats = self.dados_municipios.groupby('Zona').agg({
                    'CD_Mun': 'count',
                    'SHARE_CALCULADO': 'mean',
                    'PDV': 'sum' if tem_pdv else 'count'
                }).rename(columns={'CD_Mun': 'total_municipios', 'SHARE_CALCULADO': 'Share_Calculado'})
            else:
                stats = self.dados_municipios.groupby('Zona').agg({
                    'CD_Mun': 'count',
                    'PDV': 'sum' if tem_pdv else 'count'
                }).rename(columns={'CD_Mun': 'total_municipios'})
        
        stats_dict = {}
        for zona, row in stats.iterrows():
            stat_item = {
                'total_municipios': int(row['total_municipios']),
                'cor': self.zona_cores.get(zona, '#CCCCCC'),
                'percentual': round((row['total_municipios'] / len(self.dados_municipios)) * 100, 1)
            }
            
            # Adicionar share se disponível
            if 'Share_Calculado' in row:
                stat_item['share_medio'] = round(row['Share_Calculado'], 2)
            
            # Adicionar PDV se disponível
            if tem_pdv:
                stat_item['total_pdv'] = int(row['PDV'])
            
            stats_dict[zona] = stat_item
        
        return stats_dict
    
    def alterar_cor_zona(self, nome_zona, nova_cor):
        """Altera a cor de uma zona"""
        try:
            # Verificar se a zona existe
            if nome_zona not in self.zona_cores:
                return False, "Zona não encontrada"
            
            # Validar formato da cor (hexadecimal)
            if not nova_cor.startswith('#') or len(nova_cor) != 7:
                return False, "Formato de cor inválido. Use formato #RRGGBB"
            
            # Atualizar cor no mapeamento
            cor_anterior = self.zona_cores[nome_zona]
            self.zona_cores[nome_zona] = nova_cor
            
            # Salvar no arquivo
            with open('zona_cores_mapping.json', 'w', encoding='utf-8') as f:
                json.dump(self.zona_cores, f, indent=2, ensure_ascii=False)
            
            # Atualizar dados dos municípios
            mask = self.dados_municipios['Zona'] == nome_zona
            self.dados_municipios.loc[mask, 'Cor'] = nova_cor
            
            # Atualizar dados preparados
            self.preparar_dados_mapa()
            
            print(f"✅ Cor da zona '{nome_zona}' alterada de {cor_anterior} para {nova_cor}")
            
            return True, f"Cor da zona '{nome_zona}' alterada com sucesso"
            
        except Exception as e:
            print(f"❌ Erro ao alterar cor da zona: {e}")
            return False, f"Erro ao alterar cor: {str(e)}"

# Instância global do gerenciador
gerenciador = GerenciadorMapaInterativo()

@app.route('/')
def index():
    """Página principal com mapa interativo"""
    return render_template('mapa_interativo.html')

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
    return jsonify({
        'sucesso': True,
        'zonas': list(gerenciador.zona_cores.keys()),
        'cores': gerenciador.zona_cores
    })

@app.route('/api/estatisticas')
def api_estatisticas():
    """API para obter estatísticas"""
    try:
        stats = gerenciador.obter_estatisticas()
        return jsonify({
            'sucesso': True,
            'estatisticas': stats,
            'total_geral': len(gerenciador.dados_municipios)
        })
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        })

@app.route('/api/estatisticas_share')
def api_estatisticas_share():
    """API para obter estatísticas detalhadas de Share por zona"""
    try:
        # Calcular Share se necessário
        tem_sell_out = 'SELL OUT ANUAL' in gerenciador.dados_municipios.columns
        tem_potencial = 'POTENCIAL ANUAL' in gerenciador.dados_municipios.columns
        
        if tem_sell_out and tem_potencial:
            gerenciador.dados_municipios['Share_Calculado'] = (
                gerenciador.dados_municipios['SELL OUT ANUAL'] / 
                gerenciador.dados_municipios['POTENCIAL ANUAL'] * 100
            ).fillna(0)
        elif 'SHARE_CALCULADO' in gerenciador.dados_municipios.columns:
            gerenciador.dados_municipios['Share_Calculado'] = gerenciador.dados_municipios['SHARE_CALCULADO'].fillna(0)
        else:
            gerenciador.dados_municipios['Share_Calculado'] = 0
        
        # Estatísticas gerais de Share
        share_geral = {
            'min': float(gerenciador.dados_municipios['Share_Calculado'].min()),
            'max': float(gerenciador.dados_municipios['Share_Calculado'].max()),
            'media': float(gerenciador.dados_municipios['Share_Calculado'].mean()),
            'mediana': float(gerenciador.dados_municipios['Share_Calculado'].median())
        }
        
        # Estatísticas por zona
        stats_por_zona = gerenciador.dados_municipios.groupby('Zona').agg({
            'Share_Calculado': ['min', 'max', 'mean', 'count'],
            'SELL OUT ANUAL': 'sum' if tem_sell_out else 'count',
            'POTENCIAL ANUAL': 'sum' if tem_potencial else 'count'
        }).round(2)
        
        zonas_stats = {}
        for zona in stats_por_zona.index:
            zonas_stats[zona] = {
                'share_min': float(stats_por_zona.loc[zona, ('Share_Calculado', 'min')]),
                'share_max': float(stats_por_zona.loc[zona, ('Share_Calculado', 'max')]),
                'share_medio': float(stats_por_zona.loc[zona, ('Share_Calculado', 'mean')]),
                'total_municipios': int(stats_por_zona.loc[zona, ('Share_Calculado', 'count')]),
                'cor': gerenciador.zona_cores.get(zona, '#CCCCCC')
            }
            
            if tem_sell_out:
                zonas_stats[zona]['sell_out_total'] = float(stats_por_zona.loc[zona, ('SELL OUT ANUAL', 'sum')])
            if tem_potencial:
                zonas_stats[zona]['potencial_total'] = float(stats_por_zona.loc[zona, ('POTENCIAL ANUAL', 'sum')])
        
        return jsonify({
            'sucesso': True,
            'share_geral': share_geral,
            'zonas': zonas_stats,
            'total_municipios': len(gerenciador.dados_municipios)
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
        # Emitir atualização para todos os clientes conectados
        socketio.emit('zona_alterada', {
            'sucesso': True,
            'municipio': municipio_atualizado,
            'mensagem': mensagem
        })
        
        # Emitir estatísticas atualizadas
        stats = gerenciador.obter_estatisticas()
        socketio.emit('estatisticas_atualizadas', {
            'estatisticas': stats
        })
    else:
        # Emitir erro apenas para o cliente que fez a requisição
        emit('erro_alteracao', {
            'sucesso': False,
            'mensagem': mensagem
        })

@socketio.on('alterar_cor_zona')
def handle_alterar_cor_zona(data):
    """Handler WebSocket para alteração de cor de zona em tempo real"""
    nome_zona = data.get('nome_zona')
    nova_cor = data.get('nova_cor')
    
    print(f"🎨 Alterando cor da zona '{nome_zona}' para '{nova_cor}'")
    
    sucesso, mensagem = gerenciador.alterar_cor_zona(nome_zona, nova_cor)
    
    if sucesso:
        # Emitir atualização para todos os clientes conectados
        socketio.emit('cor_zona_alterada', {
            'sucesso': True,
            'nome_zona': nome_zona,
            'nova_cor': nova_cor,
            'mensagem': mensagem
        })
        
        # Emitir estatísticas atualizadas com novas cores
        stats = gerenciador.obter_estatisticas()
        socketio.emit('estatisticas_atualizadas', {
            'estatisticas': stats
        })
        
        print(f"✅ Cor da zona '{nome_zona}' alterada com sucesso")
    else:
        # Emitir erro apenas para o cliente que fez a requisição
        emit('erro_cor', {
            'sucesso': False,
            'mensagem': mensagem
        })
        
        print(f"❌ Erro ao alterar cor da zona '{nome_zona}': {mensagem}")

@socketio.on('connect')
def handle_connect():
    """Handler para conexão WebSocket"""
    print(f"Cliente conectado: {request.sid}")
    emit('conectado', {'mensagem': 'Conectado ao servidor de mapa interativo'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handler para desconexão WebSocket"""
    print(f"Cliente desconectado: {request.sid}")

@socketio.on('criar_zona')
def handle_criar_zona(data):
    """Handler WebSocket para criar nova zona"""
    nome = data.get('nome', '').strip()
    cor = data.get('cor', '').strip()
    
    try:
        # Validações
        if not nome:
            emit('erro_zona', {'mensagem': 'Nome da zona é obrigatório'})
            return
            
        if nome in gerenciador.zona_cores:
            emit('erro_zona', {'mensagem': 'Já existe uma zona com este nome'})
            return
            
        if not re.match(r'^#[0-9A-Fa-f]{6}$', cor):
            emit('erro_zona', {'mensagem': 'Cor inválida. Use formato hexadecimal (#000000)'})
            return
        
        # Adicionar nova zona
        gerenciador.zona_cores[nome] = cor
        
        # Salvar no arquivo
        with open('zona_cores_mapping.json', 'w', encoding='utf-8') as f:
            json.dump(gerenciador.zona_cores, f, indent=2, ensure_ascii=False)
        
        # Atualizar dados preparados
        gerenciador.preparar_dados_mapa()
        
        # Emitir sucesso para todos os clientes
        socketio.emit('zona_criada', {
            'sucesso': True,
            'mensagem': f'Zona "{nome}" criada com sucesso',
            'zona': {
                'nome': nome,
                'cor': cor
            }
        })
        
        print(f"✅ Nova zona criada: {nome} - {cor}")
        
    except Exception as e:
        print(f"❌ Erro ao criar zona: {e}")
        emit('erro_zona', {'mensagem': f'Erro ao criar zona: {str(e)}'})

@socketio.on('editar_zona')
def handle_editar_zona(data):
    """Handler WebSocket para editar zona existente"""
    nome_original = data.get('nome_original', '').strip()
    nome_novo = data.get('nome_novo', '').strip()
    cor = data.get('cor', '').strip()
    
    try:
        # Validações
        if not nome_novo:
            emit('erro_zona', {'mensagem': 'Nome da zona é obrigatório'})
            return
            
        if nome_original not in gerenciador.zona_cores:
            emit('erro_zona', {'mensagem': 'Zona original não encontrada'})
            return
            
        if nome_novo != nome_original and nome_novo in gerenciador.zona_cores:
            emit('erro_zona', {'mensagem': 'Já existe uma zona com este nome'})
            return
            
        if not re.match(r'^#[0-9A-Fa-f]{6}$', cor):
            emit('erro_zona', {'mensagem': 'Cor inválida. Use formato hexadecimal (#000000)'})
            return
        
        # Verificar se há municípios usando esta zona
        municipios_na_zona = gerenciador.dados_municipios[gerenciador.dados_municipios['Zona'] == nome_original]
        
        # Atualizar zona
        if nome_original != nome_novo:
            # Remover zona antiga
            del gerenciador.zona_cores[nome_original]
            # Atualizar municípios que usam esta zona
            mask = gerenciador.dados_municipios['Zona'] == nome_original
            gerenciador.dados_municipios.loc[mask, 'Zona'] = nome_novo
        
        # Definir nova cor
        gerenciador.zona_cores[nome_novo] = cor
        
        # Atualizar cor nos dados dos municípios
        mask = gerenciador.dados_municipios['Zona'] == nome_novo
        gerenciador.dados_municipios.loc[mask, 'Cor'] = cor
        
        # Salvar no arquivo
        with open('zona_cores_mapping.json', 'w', encoding='utf-8') as f:
            json.dump(gerenciador.zona_cores, f, indent=2, ensure_ascii=False)
        
        # Salvar alterações nos municípios se houve mudança de nome
        if nome_original != nome_novo and len(municipios_na_zona) > 0:
            for _, municipio in municipios_na_zona.iterrows():
                gerenciador.persistencia.salvar_alteracao(
                    cd_mun=str(municipio['CD_Mun']),
                    cidade=municipio['Cidade'],
                    zona_anterior=nome_original,
                    zona_nova=nome_novo,
                    usuario="SistemaEdicaoZona"
                )
        
        # Atualizar dados preparados
        gerenciador.preparar_dados_mapa()
        
        # Emitir sucesso para todos os clientes
        socketio.emit('zona_editada', {
            'sucesso': True,
            'mensagem': f'Zona editada com sucesso',
            'zona': {
                'nome_original': nome_original,
                'nome_novo': nome_novo,
                'cor': cor
            }
        })
        
        print(f"✅ Zona editada: {nome_original} -> {nome_novo} - {cor}")
        
    except Exception as e:
        print(f"❌ Erro ao editar zona: {e}")
        emit('erro_zona', {'mensagem': f'Erro ao editar zona: {str(e)}'})

if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Configurações do servidor
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV', 'production') != 'production'
    
    print("🚀 Iniciando aplicação de mapa interativo...")
    print(f"📍 Servidor: {host}:{port}")
    print(f"🌍 Ambiente: {os.getenv('FLASK_ENV', 'production')}")
    print("🗺️ Mapa interativo com edição em tempo real")
    
    socketio.run(app, host=host, port=port, debug=debug)