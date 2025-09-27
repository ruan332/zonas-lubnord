#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerenciador de UFs para Sistema Multi-Estado
Gerencia carregamento dinâmico de dados por estado
"""

import os
import json
import pandas as pd
import geopandas as gpd
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class GerenciadorUFs:
    """
    Classe responsável por gerenciar múltiplas UFs no sistema
    """
    
    def __init__(self, base_path: str = "dados_ufs"):
        """
        Inicializa o gerenciador de UFs
        
        Args:
            base_path: Caminho base para os dados das UFs
        """
        self.base_path = base_path
        self.configuracao_path = os.path.join(base_path, "configuracao_ufs.json")
        self.ufs_disponiveis = {}
        self.uf_atual = None
        self.dados_cache = {}
        
        self._carregar_configuracao()
    
    def _carregar_configuracao(self):
        """Carrega a configuração das UFs disponíveis"""
        try:
            if os.path.exists(self.configuracao_path):
                with open(self.configuracao_path, 'r', encoding='utf-8') as f:
                    self.ufs_disponiveis = json.load(f)
                print(f"✅ Configuração carregada: {len(self.ufs_disponiveis)} UFs disponíveis")
            else:
                print(f"⚠️ Arquivo de configuração não encontrado: {self.configuracao_path}")
                self.ufs_disponiveis = {}
        except Exception as e:
            print(f"❌ Erro ao carregar configuração: {e}")
            self.ufs_disponiveis = {}
    
    def listar_ufs_ativas(self) -> List[Dict]:
        """
        Lista todas as UFs ativas e disponíveis
        
        Returns:
            Lista de dicionários com informações das UFs
        """
        ufs_ativas = []
        for codigo, config in self.ufs_disponiveis.items():
            if config.get('ativo', False):  # Corrigido: 'ativo' em vez de 'ativa'
                ufs_ativas.append({
                    'codigo': codigo,
                    'nome': config['nome'],
                    'diretorio': config['diretorio']
                })
        
        return sorted(ufs_ativas, key=lambda x: x['nome'])
    
    def validar_uf(self, codigo_uf: str) -> bool:
        """
        Valida se uma UF está disponível e ativa
        
        Args:
            codigo_uf: Código da UF (ex: 'PE', 'AL')
            
        Returns:
            True se a UF estiver disponível e ativa
        """
        return (codigo_uf in self.ufs_disponiveis and 
                self.ufs_disponiveis[codigo_uf].get('ativo', False))  # Corrigido: 'ativo' em vez de 'ativa'
    
    def carregar_dados_uf(self, codigo_uf: str) -> Dict:
        """
        Carrega todos os dados de uma UF específica
        
        Args:
            codigo_uf: Código da UF
            
        Returns:
            Dicionário com todos os dados da UF
        """
        if not self.validar_uf(codigo_uf):
            raise ValueError(f"UF {codigo_uf} não está disponível ou ativa")
        
        # Verificar cache
        if codigo_uf in self.dados_cache:
            print(f"📋 Usando dados em cache para {codigo_uf}")
            return self.dados_cache[codigo_uf]
        
        config = self.ufs_disponiveis[codigo_uf]
        uf_path = os.path.join(self.base_path, config['diretorio'])
        
        try:
            # Carregar dados dos municípios
            municipios_path = os.path.join(uf_path, "dados_municipios.csv")
            municipios = pd.read_csv(municipios_path)
            print(f"✅ {codigo_uf}: {len(municipios)} municípios carregados")
            
            # Carregar geometrias
            geometrias_path = os.path.join(uf_path, "geometrias.json")
            with open(geometrias_path, 'r', encoding='utf-8') as f:
                geometrias = json.load(f)
            print(f"✅ {codigo_uf}: {len(geometrias['features'])} geometrias carregadas")
            
            # Carregar cores das zonas
            cores_path = os.path.join(uf_path, "zona_cores.json")
            with open(cores_path, 'r', encoding='utf-8') as f:
                zona_cores = json.load(f)
            print(f"✅ {codigo_uf}: {len(zona_cores)} cores de zonas carregadas")
            
            # Carregar histórico de alterações
            alteracoes_path = os.path.join(uf_path, "alteracoes.json")
            if os.path.exists(alteracoes_path):
                with open(alteracoes_path, 'r', encoding='utf-8') as f:
                    alteracoes = json.load(f)
            else:
                alteracoes = {"alteracoes": [], "ultima_atualizacao": datetime.now().isoformat()}
            print(f"✅ {codigo_uf}: Histórico de alterações carregado")
            
            # Montar estrutura de dados
            dados_uf = {
                'codigo': codigo_uf,
                'nome': config['nome'],
                'municipios': municipios,
                'geometrias': geometrias,
                'zona_cores': zona_cores,
                'alteracoes': alteracoes
            }
            
            # Processar dados para o mapa
            dados_uf['dados_processados'] = self._processar_dados_mapa(dados_uf)
            
            # Armazenar no cache
            self.dados_cache[codigo_uf] = dados_uf
            self.uf_atual = codigo_uf
            
            print(f"🎉 {codigo_uf} ({config['nome']}) carregado com sucesso!")
            return dados_uf
            
        except Exception as e:
            print(f"❌ Erro ao carregar {codigo_uf}: {e}")
            raise
    
    def _processar_dados_mapa(self, dados_uf: Dict) -> gpd.GeoDataFrame:
        """
        Processa dados para o mapa, fazendo merge entre geometrias e dados dos municípios
        
        Args:
            dados_uf: Dados da UF carregados
            
        Returns:
            GeoDataFrame com dados processados para o mapa
        """
        try:
            # Converter geometrias JSON para GeoDataFrame
            geometrias_json = dados_uf['geometrias']
            gdf = gpd.GeoDataFrame.from_features(geometrias_json['features'])
            gdf['id'] = gdf['id'].astype(str)
            
            # Obter dados dos municípios
            municipios = dados_uf['municipios'].copy()
            municipios['CD_Mun'] = municipios['CD_Mun'].astype(str)
            
            # Fazer merge pelos códigos dos municípios
            dados_mapa = gdf.merge(
                municipios, 
                left_on='id', 
                right_on='CD_Mun', 
                how='left'
            )
            
            # REGRA: Municípios com geometria mas sem dados devem aparecer como "Sem Zona"
            # Identificar registros sem dados (NaN em colunas essenciais)
            sem_dados = dados_mapa['Cidade'].isna()
            
            if sem_dados.any():
                print(f"📍 Encontrados {sem_dados.sum()} municípios com geometria mas sem dados")
                
                # Preencher dados básicos para municípios sem dados
                dados_mapa.loc[sem_dados, 'Cidade'] = dados_mapa.loc[sem_dados, 'name']  # Usar nome da geometria
                dados_mapa.loc[sem_dados, 'Zona'] = 'Sem Zona'
                dados_mapa.loc[sem_dados, 'UF'] = dados_uf['codigo']
                dados_mapa.loc[sem_dados, 'CD_Mun'] = dados_mapa.loc[sem_dados, 'id']
                
                # Preencher valores numéricos com 0
                colunas_numericas = ['SELL OUT ANUAL', 'SELL OUT MÊS', 'POTENCIAL ANUAL', 'POTENCIAL MÊS', 'POPULAÇÃO ', 'PDV', '%SHARE']
                for col in colunas_numericas:
                    if col in dados_mapa.columns:
                        dados_mapa.loc[sem_dados, col] = 0.0
                
                # Preencher outras colunas de texto
                if 'Mesorregião Geográfica' in dados_mapa.columns:
                    dados_mapa.loc[sem_dados, 'Mesorregião Geográfica'] = 'Não Classificado'
                
                print(f"✅ Municípios configurados como 'Sem Zona':")
                for idx in dados_mapa[sem_dados].index:
                    nome = dados_mapa.loc[idx, 'Cidade']
                    codigo = dados_mapa.loc[idx, 'id']
                    print(f"   • {codigo}: {nome}")
            
            # Adicionar cores das zonas (incluindo "Sem Zona")
            zona_cores = dados_uf['zona_cores'].copy()
            if 'Sem Zona' not in zona_cores:
                zona_cores['Sem Zona'] = '#CCCCCC'  # Cinza para "Sem Zona"
            
            dados_mapa['cor_zona'] = dados_mapa['Zona'].map(zona_cores)
            
            # Preencher valores ausentes de cor
            dados_mapa['cor_zona'] = dados_mapa['cor_zona'].fillna('#CCCCCC')
            
            # Converter colunas numéricas para tipos Python nativos (JSON serializáveis)
            colunas_numericas = ['SELL OUT ANUAL', 'SELL OUT MÊS', 'POTENCIAL ANUAL', 'POTENCIAL MÊS', 'POPULAÇÃO ', 'PDV', '%SHARE']
            for col in colunas_numericas:
                if col in dados_mapa.columns:
                    dados_mapa[col] = dados_mapa[col].astype(float)
            
            print(f"✅ Dados processados: {len(dados_mapa)} registros no mapa")
            return dados_mapa
            
        except Exception as e:
            print(f"❌ Erro ao processar dados do mapa: {e}")
            raise
    
    def obter_estatisticas_uf(self, codigo_uf: str) -> Dict:
        """
        Obtém estatísticas de uma UF
        
        Args:
            codigo_uf: Código da UF
            
        Returns:
            Dicionário com estatísticas da UF
        """
        if codigo_uf not in self.dados_cache:
            self.carregar_dados_uf(codigo_uf)
        
        dados = self.dados_cache[codigo_uf]
        municipios = dados['municipios']
        
        # Converter valores pandas para tipos Python nativos (JSON serializáveis)
        estatisticas = {
            'total_municipios': int(len(municipios)),
            'zonas': sorted(municipios['Zona'].unique().tolist()),
            'total_zonas': int(municipios['Zona'].nunique()),
            'distribuicao_zonas': {k: int(v) for k, v in municipios['Zona'].value_counts().to_dict().items()},
            'populacao_total': int(municipios.get('POPULAÇÃO ', pd.Series([0])).sum()),
            'sell_out_total': float(municipios.get('SELL OUT ANUAL', pd.Series([0])).sum()),
            'potencial_total': float(municipios.get('POTENCIAL ANUAL', pd.Series([0])).sum())
        }
        
        return estatisticas
    
    def salvar_alteracao(self, codigo_uf: str, municipio_id: str, zona_anterior: str, zona_nova: str) -> bool:
        """
        Salva uma alteração de zona para um município
        
        Args:
            codigo_uf: Código da UF
            municipio_id: ID do município
            zona_anterior: Zona anterior
            zona_nova: Nova zona
            
        Returns:
            True se salvou com sucesso
        """
        try:
            config = self.ufs_disponiveis[codigo_uf]
            alteracoes_path = os.path.join(self.base_path, config['diretorio'], "alteracoes.json")
            
            # Carregar alterações existentes
            if os.path.exists(alteracoes_path):
                with open(alteracoes_path, 'r', encoding='utf-8') as f:
                    alteracoes = json.load(f)
            else:
                alteracoes = {"alteracoes": []}
            
            # Adicionar nova alteração
            nova_alteracao = {
                "municipio_id": municipio_id,
                "zona_anterior": zona_anterior,
                "zona_nova": zona_nova,
                "timestamp": datetime.now().isoformat(),
                "usuario": "sistema"
            }
            
            alteracoes["alteracoes"].append(nova_alteracao)
            alteracoes["ultima_atualizacao"] = datetime.now().isoformat()
            
            # Salvar arquivo
            with open(alteracoes_path, 'w', encoding='utf-8') as f:
                json.dump(alteracoes, f, indent=2, ensure_ascii=False)
            
            # Atualizar cache se existir
            if codigo_uf in self.dados_cache:
                self.dados_cache[codigo_uf]['alteracoes'] = alteracoes
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar alteração: {e}")
            return False

# Instância global do gerenciador
gerenciador_ufs = GerenciadorUFs()
