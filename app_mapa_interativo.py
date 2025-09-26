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
        """Carrega todos os dados necessários da base original com sistema robusto de fallback"""
        try:
            # Carregar dados dos municípios da base original
            dados_originais_path = 'pernambuco_dados_gerar_mapa.csv'
            
            # Verificar se arquivo base existe, se não, criar um arquivo base padrão
            if not os.path.exists(dados_originais_path):
                print(f"⚠️ Arquivo base não encontrado: {dados_originais_path}")
                print(f"🔄 Tentando criar arquivo base padrão...")
                
                # Tentar criar arquivo base padrão a partir de backup ou dados mínimos
                if not self._criar_arquivo_base_padrao(dados_originais_path):
                    raise FileNotFoundError(f"Não foi possível criar ou encontrar arquivo base: {dados_originais_path}")
            
            # Carregar dados com tratamento robusto de erros
            self.dados_municipios = self._carregar_dados_com_fallback(dados_originais_path)
            
            print(f"✅ Dados originais carregados: {len(self.dados_municipios)} municípios")
            print(f"📁 Fonte: {dados_originais_path}")
            print(f"📊 Colunas disponíveis: {list(self.dados_municipios.columns)}")
            
            # Carregar geometrias
            self.geometrias = gpd.read_file('pernambuco.json')
            self.geometrias['id'] = self.geometrias['id'].astype(str)
            print(f"✅ Geometrias carregadas: {len(self.geometrias)} polígonos")
            
            # Carregar cores das zonas
            with open('zona_cores_mapping.json', 'r', encoding='utf-8') as f:
                self.zona_cores = json.load(f)
            print(f"✅ Cores carregadas: {len(self.zona_cores)} zonas")
            
            # Aplicar alterações salvas se existirem (após carregar cores)
            self._aplicar_alteracoes_salvas()
            
            # Verificar integridade dos dados carregados
            self._verificar_integridade_dados()
            
            # Mesclar dados com geometrias
            self.preparar_dados_mapa()
            
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            raise
    
    def _criar_arquivo_base_padrao(self, caminho_arquivo):
        """Cria um arquivo base padrão se não existir"""
        try:
            # Tentar encontrar backup mais recente
            backup_dir = 'backups'
            if os.path.exists(backup_dir):
                backups = []
                for item in os.listdir(backup_dir):
                    backup_path = os.path.join(backup_dir, item)
                    if os.path.isdir(backup_path):
                        arquivo_backup = os.path.join(backup_path, 'pernambuco_dados_gerar_mapa.csv')
                        if os.path.exists(arquivo_backup):
                            backups.append((arquivo_backup, os.path.getmtime(arquivo_backup)))
                
                if backups:
                    # Usar backup mais recente
                    backup_mais_recente = max(backups, key=lambda x: x[1])[0]
                    import shutil
                    shutil.copy2(backup_mais_recente, caminho_arquivo)
                    print(f"✅ Arquivo base restaurado do backup: {backup_mais_recente}")
                    return True
            
            # Se não há backup, criar arquivo mínimo com estrutura básica
            print(f"⚠️ Nenhum backup encontrado, criando arquivo base mínimo...")
            dados_minimos = {
                'UF': ['PE'],
                'Mesorregião Geográfica': ['Metropolitana de Recife'],
                'CD_Mun': ['2611606'],
                'Cidade': ['Recife'],
                'Zona': ['Zona Recife'],
                'SELL OUT ANUAL': [0],
                'SELL OUT MÊS': [0],
                'POTENCIAL ANUAL': [0],
                'POTENCIAL MÊS': [0],
                'POPULAÇÃO ': [1000000],
                'PDV': [1000],
                '%SHARE': [0.0]
            }
            
            df_minimo = pd.DataFrame(dados_minimos)
            df_minimo.to_csv(caminho_arquivo, index=False)
            print(f"✅ Arquivo base mínimo criado: {caminho_arquivo}")
            print(f"⚠️ ATENÇÃO: Arquivo contém apenas dados mínimos. Faça upload da base completa quando possível.")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar arquivo base padrão: {e}")
            return False
    
    def _carregar_dados_com_fallback(self, caminho_arquivo):
        """Carrega dados com tratamento robusto de erros e fallbacks"""
        try:
            # Tentar carregar normalmente
            dados = pd.read_csv(caminho_arquivo)
            
            # Validar estrutura mínima
            colunas_essenciais = ['CD_Mun', 'Cidade', 'Zona']
            colunas_faltantes = [col for col in colunas_essenciais if col not in dados.columns]
            
            if colunas_faltantes:
                print(f"⚠️ Colunas essenciais faltantes: {colunas_faltantes}")
                # Adicionar colunas faltantes com valores padrão
                for col in colunas_faltantes:
                    if col == 'CD_Mun':
                        dados[col] = range(1, len(dados) + 1)
                    elif col == 'Cidade':
                        dados[col] = [f'Município_{i}' for i in range(1, len(dados) + 1)]
                    elif col == 'Zona':
                        dados[col] = 'Sem Zona'
                print(f"✅ Colunas essenciais adicionadas com valores padrão")
            
            # Tratar valores NaN em colunas críticas
            if 'CD_Mun' in dados.columns:
                dados['CD_Mun'] = dados['CD_Mun'].fillna(0).astype(str)
            if 'Cidade' in dados.columns:
                dados['Cidade'] = dados['Cidade'].fillna('Município não identificado')
            if 'Zona' in dados.columns:
                dados['Zona'] = dados['Zona'].fillna('Sem Zona')
            
            # Tratar colunas numéricas
            colunas_numericas = ['SELL OUT ANUAL', 'POTENCIAL ANUAL', 'PDV', '%SHARE', 'POPULAÇÃO ']
            for col in colunas_numericas:
                if col in dados.columns:
                    dados[col] = pd.to_numeric(dados[col], errors='coerce').fillna(0)
            
            print(f"✅ Dados carregados e validados com sucesso")
            return dados
            
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            print(f"🔄 Tentando fallback com dados mínimos...")
            
            # Fallback: criar DataFrame mínimo
            dados_fallback = pd.DataFrame({
                'UF': ['PE'],
                'CD_Mun': ['0000000'],
                'Cidade': ['Dados não disponíveis'],
                'Zona': ['Sem Zona'],
                'SELL OUT ANUAL': [0],
                'POTENCIAL ANUAL': [0],
                'PDV': [0],
                '%SHARE': [0.0]
            })
            
            print(f"⚠️ Usando dados de fallback mínimos")
            return dados_fallback
    
    def _aplicar_alteracoes_salvas(self):
        """Aplica alterações salvas do arquivo JSON aos dados carregados"""
        try:
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
    
    def _verificar_integridade_dados(self):
        """Verifica integridade dos dados carregados"""
        try:
            print(f"\n🔍 Verificando integridade dos dados...")
            print(f"📊 Total de municípios: {len(self.dados_municipios)}")
            
            # Verificar colunas essenciais
            colunas_essenciais = ['CD_Mun', 'Cidade', 'Zona', 'PDV', 'SELL OUT ANUAL', 'POTENCIAL ANUAL', '%SHARE']
            colunas_presentes = []
            colunas_ausentes = []
            
            for col in colunas_essenciais:
                if col in self.dados_municipios.columns:
                    colunas_presentes.append(col)
                else:
                    colunas_ausentes.append(col)
            
            print(f"✅ Colunas presentes: {colunas_presentes}")
            if colunas_ausentes:
                print(f"⚠️ Colunas ausentes: {colunas_ausentes}")
            
            # Verificar dados de PDV e Share
            if 'PDV' in self.dados_municipios.columns:
                total_pdv = self.dados_municipios['PDV'].sum()
                municipios_com_pdv = (self.dados_municipios['PDV'] > 0).sum()
                print(f"📍 Total PDV: {total_pdv:,.0f}")
                print(f"🏘️ Municípios com PDV > 0: {municipios_com_pdv}")
            
            if '%SHARE' in self.dados_municipios.columns:
                share_medio = self.dados_municipios['%SHARE'].mean()
                municipios_com_share = (self.dados_municipios['%SHARE'] > 0).sum()
                print(f"📊 Share médio: {share_medio:.4f}%")
                print(f"📈 Municípios com Share > 0: {municipios_com_share}")
            
            print(f"✅ Verificação de integridade concluída")
            
        except Exception as e:
            print(f"⚠️ Erro na verificação de integridade: {e}")
    

    
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
        
        # Atualizar cores (tratar 'Sem Zona' especialmente)
        def obter_cor_zona(zona):
            if zona == 'Sem Zona':
                return '#CCCCCC'
            return self.zona_cores.get(zona, '#CCCCCC')
        
        self.dados_completos['Cor'] = self.dados_completos['Zona'].apply(obter_cor_zona)
        
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
                        "cd_mun": str(row['id']) if pd.notna(row['id']) else '',
                        "cidade": str(row['Cidade']) if pd.notna(row['Cidade']) else 'Município não identificado',
                        "zona": str(row['Zona']) if pd.notna(row['Zona']) else 'Sem Zona',
                        "cor": str(row['Cor']) if pd.notna(row['Cor']) else '#CCCCCC',
                        "uf": str(row.get('UF', 'PE')) if pd.notna(row.get('UF')) else 'PE',
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
        """Altera zona de um município e retorna dados atualizados"""
        try:
            # Verificar se município existe
            mask = self.dados_municipios['CD_Mun'].astype(str) == str(cd_mun)
            if not mask.any():
                return False, "Município não encontrado", None
            
            # Verificar se zona existe (permitir 'Sem Zona' sempre)
            if nova_zona != 'Sem Zona' and nova_zona not in self.zona_cores:
                return False, "Zona não encontrada", None
            
            # Obter dados atuais
            idx = self.dados_municipios[mask].index[0]
            zona_anterior = self.dados_municipios.loc[idx, 'Zona']
            cidade = self.dados_municipios.loc[idx, 'Cidade']
            
            # Alterar zona
            self.dados_municipios.loc[idx, 'Zona'] = nova_zona
            # Definir cor (usar cor padrão para 'Sem Zona')
            if nova_zona == 'Sem Zona':
                self.dados_municipios.loc[idx, 'Cor'] = '#CCCCCC'
            else:
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
                
        except Exception as e:
            return False, f"Erro: {str(e)}", None
    
    def obter_estatisticas(self):
        """Retorna estatísticas das zonas"""
        try:
            # Verificar se existem colunas de SELL OUT ANUAL e POTENCIAL ANUAL
            tem_sell_out = 'SELL OUT ANUAL' in self.dados_municipios.columns
            tem_potencial = 'POTENCIAL ANUAL' in self.dados_municipios.columns
            tem_pdv = 'PDV' in self.dados_municipios.columns
            
            # Agregação básica sempre funciona
            agg_dict = {'CD_Mun': 'count'}
            
            if tem_sell_out and tem_potencial:
                # Calcular share como SELL OUT ANUAL / POTENCIAL ANUAL
                self.dados_municipios['Share_Calculado'] = (
                    self.dados_municipios['SELL OUT ANUAL'] / 
                    self.dados_municipios['POTENCIAL ANUAL'] * 100
                ).fillna(0)
                agg_dict['Share_Calculado'] = 'mean'
            elif 'SHARE_CALCULADO' in self.dados_municipios.columns:
                agg_dict['SHARE_CALCULADO'] = 'mean'
            
            # Adicionar PDV apenas se existir
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
                
                # Adicionar share se disponível
                if 'Share_Calculado' in row:
                    stat_item['share_medio'] = round(float(row['Share_Calculado']), 2)
                elif 'SHARE_CALCULADO' in row:
                    stat_item['share_medio'] = round(float(row['SHARE_CALCULADO']), 2)
                
                # Adicionar PDV se disponível
                if tem_pdv and 'PDV' in row:
                    stat_item['total_pdv'] = int(row['PDV'])
                
                stats_dict[zona] = stat_item
            
            return stats_dict
            
        except Exception as e:
            print(f"❌ Erro ao calcular estatísticas: {e}")
            # Retornar estatísticas básicas em caso de erro
            stats_basicas = {}
            for zona in self.zona_cores.keys():
                municipios_zona = self.dados_municipios[self.dados_municipios['Zona'] == zona]
                stats_basicas[zona] = {
                    'total_municipios': len(municipios_zona),
                    'cor': self.zona_cores.get(zona, '#CCCCCC'),
                    'percentual': round((len(municipios_zona) / len(self.dados_municipios)) * 100, 1)
                }
            return stats_basicas
    
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

@app.route('/api/cidades_zona/<nome_zona>')
def api_cidades_zona(nome_zona):
    """API para obter cidades vinculadas a uma zona específica"""
    try:
        # Filtrar cidades da zona
        cidades_zona = gerenciador.dados_municipios[
            gerenciador.dados_municipios['Zona'] == nome_zona
        ].copy()
        
        # Preparar dados das cidades
        cidades_list = []
        for _, cidade in cidades_zona.iterrows():
            cidades_list.append({
                'cd_mun': str(cidade['CD_Mun']),
                'nome': cidade['Cidade'],
                'uf': cidade.get('UF', 'PE'),
                'zona': cidade['Zona']
            })
        
        return jsonify({
            'sucesso': True,
            'cidades': cidades_list,
            'total': len(cidades_list),
            'zona': nome_zona
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        })

@app.route('/api/cidades_disponiveis')
def api_cidades_disponiveis():
    """API para obter todas as cidades disponíveis com suas zonas atuais"""
    try:
        # Obter todas as cidades
        todas_cidades = gerenciador.dados_municipios.copy()
        
        # Preparar dados das cidades
        cidades_list = []
        for _, cidade in todas_cidades.iterrows():
            zona_atual = cidade.get('Zona', 'Sem Zona')
            # Definir cor correta para a zona
            if zona_atual == 'Sem Zona':
                cor_zona = '#CCCCCC'
            else:
                cor_zona = gerenciador.zona_cores.get(zona_atual, '#CCCCCC')
            
            cidades_list.append({
                'cd_mun': str(cidade['CD_Mun']),
                'nome': cidade['Cidade'],
                'uf': cidade.get('UF', 'PE'),
                'zona_atual': zona_atual,
                'cor_zona': cor_zona
            })
        
        # Ordenar por nome
        cidades_list.sort(key=lambda x: x['nome'])
        
        return jsonify({
            'sucesso': True,
            'cidades': cidades_list,
            'total': len(cidades_list)
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        })

@socketio.on('remover_cidade_zona')
def handle_remover_cidade_zona(data):
    """Handler WebSocket para remover cidade de uma zona"""
    cd_mun = data.get('cd_mun')
    zona_atual = data.get('zona_atual')
    
    try:
        print(f"🗑️ Iniciando remoção de cidade da zona: {cd_mun} da zona {zona_atual}")
        
        # Validações
        if not cd_mun:
            print(f"❌ Erro: Código do município é obrigatório")
            emit('erro_cidade', {'mensagem': 'Código do município é obrigatório'})
            return
        
        # Verificar se a cidade existe
        cidade_mask = gerenciador.dados_municipios['CD_Mun'].astype(str) == str(cd_mun)
        if not cidade_mask.any():
            print(f"❌ Erro: Cidade {cd_mun} não encontrada")
            emit('erro_cidade', {'mensagem': 'Cidade não encontrada'})
            return
        
        cidade_info = gerenciador.dados_municipios[cidade_mask].iloc[0]
        print(f"📍 Cidade encontrada: {cidade_info['Cidade']} (zona atual: {cidade_info.get('Zona', 'N/A')})")
        
        # Remover da zona (definir como 'Sem Zona')
        print(f"🔄 Alterando zona de {cidade_info['Cidade']} para 'Sem Zona'")
        sucesso, mensagem, municipio_atualizado = gerenciador.alterar_zona_municipio(cd_mun, 'Sem Zona')
        
        if sucesso:
            print(f"✅ Remoção bem-sucedida: {cidade_info['Cidade']} agora está em 'Sem Zona'")
            
            # Emitir atualização para todos os clientes
            socketio.emit('cidade_removida_zona', {
                'sucesso': True,
                'cd_mun': cd_mun,
                'cidade': cidade_info['Cidade'],
                'zona_anterior': zona_atual,
                'mensagem': f"Cidade {cidade_info['Cidade']} removida da zona {zona_atual}"
            })
            
            # Emitir estatísticas atualizadas
            stats = gerenciador.obter_estatisticas()
            socketio.emit('estatisticas_atualizadas', {
                'estatisticas': stats
            })
            
            print(f"✅ Cidade {cidade_info['Cidade']} removida da zona {zona_atual}")
        else:
            print(f"❌ Falha na remoção: {mensagem}")
            emit('erro_cidade', {
                'sucesso': False,
                'mensagem': mensagem
            })
            
    except Exception as e:
        print(f"❌ Erro ao remover cidade da zona: {e}")
        emit('erro_cidade', {'mensagem': f'Erro ao remover cidade: {str(e)}'})

@socketio.on('adicionar_cidades_zona')
def handle_adicionar_cidades_zona(data):
    """Handler WebSocket para adicionar múltiplas cidades a uma zona"""
    cidades_selecionadas = data.get('cidades_selecionadas', [])
    zona_destino = data.get('zona_destino')
    
    try:
        # Validações
        if not zona_destino:
            emit('erro_cidade', {'mensagem': 'Zona de destino é obrigatória'})
            return
            
        if not cidades_selecionadas:
            emit('erro_cidade', {'mensagem': 'Nenhuma cidade selecionada'})
            return
        
        if zona_destino not in gerenciador.zona_cores:
            emit('erro_cidade', {'mensagem': 'Zona de destino não existe'})
            return
        
        cidades_adicionadas = []
        cidades_com_erro = []
        
        # Processar cada cidade selecionada
        for cd_mun in cidades_selecionadas:
            try:
                # Verificar se a cidade existe
                cidade_mask = gerenciador.dados_municipios['CD_Mun'].astype(str) == str(cd_mun)
                if not cidade_mask.any():
                    cidades_com_erro.append({'cd_mun': cd_mun, 'erro': 'Cidade não encontrada'})
                    continue
                
                cidade_info = gerenciador.dados_municipios[cidade_mask].iloc[0]
                zona_anterior = cidade_info.get('Zona', 'Sem Zona')
                
                # Alterar zona da cidade (com transferência automática)
                sucesso, mensagem, municipio_atualizado = gerenciador.alterar_zona_municipio(cd_mun, zona_destino)
                
                if sucesso:
                    cidades_adicionadas.append({
                        'cd_mun': cd_mun,
                        'nome': cidade_info['Cidade'],
                        'zona_anterior': zona_anterior,
                        'zona_nova': zona_destino
                    })
                else:
                    cidades_com_erro.append({'cd_mun': cd_mun, 'nome': cidade_info['Cidade'], 'erro': mensagem})
                    
            except Exception as e:
                cidades_com_erro.append({'cd_mun': cd_mun, 'erro': str(e)})
        
        # Emitir resultado para todos os clientes
        if cidades_adicionadas:
            socketio.emit('cidades_adicionadas_zona', {
                'sucesso': True,
                'zona_destino': zona_destino,
                'cidades_adicionadas': cidades_adicionadas,
                'total_adicionadas': len(cidades_adicionadas),
                'mensagem': f"{len(cidades_adicionadas)} cidade(s) adicionada(s) à zona {zona_destino}"
            })
            
            # Emitir estatísticas atualizadas
            stats = gerenciador.obter_estatisticas()
            socketio.emit('estatisticas_atualizadas', {
                'estatisticas': stats
            })
            
            print(f"✅ {len(cidades_adicionadas)} cidade(s) adicionada(s) à zona {zona_destino}")
        
        # Emitir erros se houver
        if cidades_com_erro:
            emit('erro_cidade', {
                'sucesso': False,
                'mensagem': f"{len(cidades_com_erro)} cidade(s) não puderam ser adicionadas",
                'erros': cidades_com_erro
            })
            
    except Exception as e:
        print(f"❌ Erro ao adicionar cidades à zona: {e}")
        emit('erro_cidade', {'mensagem': f'Erro ao adicionar cidades: {str(e)}'})

@app.route('/api/download_base_atualizada')
def api_download_base_atualizada():
    """API para download da base de dados atualizada com todas as alterações aplicadas"""
    try:
        from flask import make_response
        from datetime import datetime
        import io
        
        # Obter dados atuais com todas as alterações aplicadas
        dados_atualizados = gerenciador.dados_municipios.copy()
        
        # Definir ordem preferencial das colunas para o CSV
        colunas_preferenciais = [
            'UF', 'Mesorregião Geográfica', 'CD_Mun', 'Cidade', 'Zona',
            'SELL OUT ANUAL', 'SELL OUT MÊS', 'POTENCIAL ANUAL', 'POTENCIAL MÊS',
            'POPULAÇÃO ', 'PDV', '%SHARE'
        ]
        
        # Identificar colunas disponíveis na ordem preferencial
        colunas_para_exportar = []
        for col in colunas_preferenciais:
            if col in dados_atualizados.columns:
                colunas_para_exportar.append(col)
        
        # Adicionar outras colunas que não estão na lista preferencial (exceto 'Cor')
        for col in dados_atualizados.columns:
            if col not in colunas_para_exportar and col != 'Cor':
                colunas_para_exportar.append(col)
        
        # Preparar dados para exportação
        dados_exportacao = dados_atualizados[colunas_para_exportar].copy()
        
        # Converter para CSV em memória
        output = io.StringIO()
        dados_exportacao.to_csv(output, index=False, encoding='utf-8')
        csv_content = output.getvalue()
        output.close()
        
        # Criar resposta com headers apropriados para download
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pernambuco_dados_atualizada_{timestamp}.csv"
        
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Length'] = len(csv_content.encode('utf-8'))
        
        print(f"📥 Download da base atualizada: {filename} ({len(dados_exportacao)} registros, {len(colunas_para_exportar)} colunas)")
        
        return response
        
    except Exception as e:
        print(f"❌ Erro ao gerar download da base atualizada: {e}")
        return jsonify({
            'sucesso': False,
            'erro': f'Erro ao gerar download: {str(e)}'
        }), 500

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