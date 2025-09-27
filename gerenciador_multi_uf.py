#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerenciador Multi-UF para Mapa Interativo
Permite trabalhar com múltiplas Unidades Federativas
"""

import os
import json
import pandas as pd
import geopandas as gpd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ConfigUF:
    """Configuração de uma UF"""
    codigo: str  # Ex: 'PE', 'SP', 'RJ'
    nome: str    # Ex: 'Pernambuco', 'São Paulo', 'Rio de Janeiro'
    arquivo_dados: str  # Ex: 'pernambuco_dados_gerar_mapa.csv'
    arquivo_geometrias: str  # Ex: 'pernambuco.json'
    arquivo_cores: str  # Ex: 'zona_cores_mapping_pe.json'
    diretorio: str  # Ex: 'dados/PE'

class GerenciadorMultiUF:
    """Gerenciador para múltiplas UFs"""
    
    def __init__(self, diretorio_base: str = "dados_ufs"):
        self.diretorio_base = Path(diretorio_base)
        self.ufs_disponiveis: Dict[str, ConfigUF] = {}
        self.uf_atual: Optional[str] = None
        self.dados_uf_atual = None
        self.geometrias_uf_atual = None
        self.zona_cores_uf_atual = None
        
        # Criar diretório base se não existir
        self.diretorio_base.mkdir(exist_ok=True)
        
        # Carregar configurações das UFs
        self._carregar_configuracoes_ufs()
        
        # Migrar dados existentes de PE se necessário
        self._migrar_dados_pe_existentes()
    
    def _carregar_configuracoes_ufs(self):
        """Carrega configurações das UFs disponíveis"""
        arquivo_config = self.diretorio_base / "configuracao_ufs.json"
        
        if arquivo_config.exists():
            with open(arquivo_config, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            for uf_code, uf_info in config_data.items():
                self.ufs_disponiveis[uf_code] = ConfigUF(**uf_info)
        else:
            # Criar configuração padrão para PE
            self._criar_configuracao_padrao()
    
    def _criar_configuracao_padrao(self):
        """Cria configuração padrão com Pernambuco"""
        config_pe = ConfigUF(
            codigo="PE",
            nome="Pernambuco",
            arquivo_dados="pernambuco_dados_gerar_mapa.csv",
            arquivo_geometrias="pernambuco.json",
            arquivo_cores="zona_cores_mapping.json",
            diretorio="PE"
        )
        
        self.ufs_disponiveis["PE"] = config_pe
        self._salvar_configuracoes()
    
    def _migrar_dados_pe_existentes(self):
        """Migra dados existentes de PE para nova estrutura"""
        if "PE" not in self.ufs_disponiveis:
            return
        
        config_pe = self.ufs_disponiveis["PE"]
        diretorio_pe = self.diretorio_base / config_pe.diretorio
        diretorio_pe.mkdir(exist_ok=True)
        
        # Lista de arquivos para migrar
        arquivos_migrar = [
            ("pernambuco_dados_gerar_mapa.csv", config_pe.arquivo_dados),
            ("pernambuco.json", config_pe.arquivo_geometrias),
            ("zona_cores_mapping.json", config_pe.arquivo_cores),
            ("alteracoes_zonas.json", "alteracoes_zonas.json")
        ]
        
        for arquivo_origem, arquivo_destino in arquivos_migrar:
            caminho_origem = Path(arquivo_origem)
            caminho_destino = diretorio_pe / arquivo_destino
            
            if caminho_origem.exists() and not caminho_destino.exists():
                import shutil
                shutil.copy2(caminho_origem, caminho_destino)
                print(f"✅ Migrado: {arquivo_origem} -> {caminho_destino}")
    
    def _salvar_configuracoes(self):
        """Salva configurações das UFs"""
        arquivo_config = self.diretorio_base / "configuracao_ufs.json"
        
        config_data = {}
        for uf_code, config in self.ufs_disponiveis.items():
            config_data[uf_code] = {
                "codigo": config.codigo,
                "nome": config.nome,
                "arquivo_dados": config.arquivo_dados,
                "arquivo_geometrias": config.arquivo_geometrias,
                "arquivo_cores": config.arquivo_cores,
                "diretorio": config.diretorio
            }
        
        with open(arquivo_config, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def adicionar_uf(self, codigo: str, nome: str, 
                     arquivo_dados: str = None, 
                     arquivo_geometrias: str = None,
                     arquivo_cores: str = None) -> bool:
        """
        Adiciona uma nova UF ao sistema
        
        Args:
            codigo: Código da UF (ex: 'SP', 'RJ')
            nome: Nome da UF (ex: 'São Paulo', 'Rio de Janeiro')
            arquivo_dados: Nome do arquivo CSV com dados (opcional)
            arquivo_geometrias: Nome do arquivo JSON com geometrias (opcional)
            arquivo_cores: Nome do arquivo JSON com cores das zonas (opcional)
        
        Returns:
            bool: True se adicionou com sucesso
        """
        try:
            # Definir nomes padrão se não fornecidos
            if not arquivo_dados:
                arquivo_dados = f"{codigo.lower()}_dados_gerar_mapa.csv"
            if not arquivo_geometrias:
                arquivo_geometrias = f"{codigo.lower()}.json"
            if not arquivo_cores:
                arquivo_cores = f"zona_cores_mapping_{codigo.lower()}.json"
            
            # Criar configuração
            config_uf = ConfigUF(
                codigo=codigo,
                nome=nome,
                arquivo_dados=arquivo_dados,
                arquivo_geometrias=arquivo_geometrias,
                arquivo_cores=arquivo_cores,
                diretorio=codigo
            )
            
            # Criar diretório da UF
            diretorio_uf = self.diretorio_base / config_uf.diretorio
            diretorio_uf.mkdir(exist_ok=True)
            
            # Criar arquivos base se não existirem
            self._criar_arquivos_base_uf(config_uf)
            
            # Adicionar à lista de UFs disponíveis
            self.ufs_disponiveis[codigo] = config_uf
            
            # Salvar configurações
            self._salvar_configuracoes()
            
            print(f"✅ UF {nome} ({codigo}) adicionada com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao adicionar UF {codigo}: {e}")
            return False
    
    def _criar_arquivos_base_uf(self, config: ConfigUF):
        """Cria arquivos base para uma nova UF"""
        diretorio_uf = self.diretorio_base / config.diretorio
        
        # Arquivo de dados base (CSV)
        arquivo_dados = diretorio_uf / config.arquivo_dados
        if not arquivo_dados.exists():
            dados_base = pd.DataFrame({
                'UF': [config.codigo],
                'Mesorregião Geográfica': ['Região Central'],
                'CD_Mun': ['0000000'],
                'Cidade': ['Município Exemplo'],
                'Zona': ['Zona Central'],
                'SELL OUT ANUAL': [0],
                'SELL OUT MÊS': [0],
                'POTENCIAL ANUAL': [0],
                'POTENCIAL MÊS': [0],
                'POPULAÇÃO ': [100000],
                'PDV': [100],
                '%SHARE': [0.0]
            })
            dados_base.to_csv(arquivo_dados, index=False)
            print(f"✅ Criado arquivo de dados base: {arquivo_dados}")
        
        # Arquivo de cores das zonas
        arquivo_cores = diretorio_uf / config.arquivo_cores
        if not arquivo_cores.exists():
            cores_base = {
                "Sem Zona": "#CCCCCC",
                "Zona Central": "#228B22",
                "Zona Norte": "#000080",
                "Zona Sul": "#8B0000",
                "Zona Leste": "#4B0082",
                "Zona Oeste": "#B8860B"
            }
            with open(arquivo_cores, 'w', encoding='utf-8') as f:
                json.dump(cores_base, f, indent=2, ensure_ascii=False)
            print(f"✅ Criado arquivo de cores base: {arquivo_cores}")
        
        # Arquivo de geometrias (precisa ser fornecido pelo usuário)
        arquivo_geometrias = diretorio_uf / config.arquivo_geometrias
        if not arquivo_geometrias.exists():
            geometrias_base = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "id": "0000000",
                            "name": "Município Exemplo"
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [-40.0, -8.0],
                                [-39.0, -8.0],
                                [-39.0, -7.0],
                                [-40.0, -7.0],
                                [-40.0, -8.0]
                            ]]
                        }
                    }
                ]
            }
            with open(arquivo_geometrias, 'w', encoding='utf-8') as f:
                json.dump(geometrias_base, f, indent=2, ensure_ascii=False)
            print(f"⚠️ Criado arquivo de geometrias exemplo: {arquivo_geometrias}")
            print(f"   IMPORTANTE: Substitua por arquivo GeoJSON real da UF {config.codigo}")
        
        # Arquivo de alterações
        arquivo_alteracoes = diretorio_uf / "alteracoes_zonas.json"
        if not arquivo_alteracoes.exists():
            alteracoes_base = {
                "alteracoes": [],
                "ultima_atualizacao": None
            }
            with open(arquivo_alteracoes, 'w', encoding='utf-8') as f:
                json.dump(alteracoes_base, f, indent=2, ensure_ascii=False)
    
    def selecionar_uf(self, codigo_uf: str) -> bool:
        """
        Seleciona uma UF para trabalhar
        
        Args:
            codigo_uf: Código da UF (ex: 'PE', 'SP')
        
        Returns:
            bool: True se selecionou com sucesso
        """
        try:
            if codigo_uf not in self.ufs_disponiveis:
                print(f"❌ UF {codigo_uf} não está disponível")
                return False
            
            config = self.ufs_disponiveis[codigo_uf]
            diretorio_uf = self.diretorio_base / config.diretorio
            
            # Verificar se arquivos existem
            arquivo_dados = diretorio_uf / config.arquivo_dados
            arquivo_geometrias = diretorio_uf / config.arquivo_geometrias
            arquivo_cores = diretorio_uf / config.arquivo_cores
            
            if not arquivo_dados.exists():
                print(f"❌ Arquivo de dados não encontrado: {arquivo_dados}")
                return False
            
            if not arquivo_geometrias.exists():
                print(f"❌ Arquivo de geometrias não encontrado: {arquivo_geometrias}")
                return False
            
            if not arquivo_cores.exists():
                print(f"❌ Arquivo de cores não encontrado: {arquivo_cores}")
                return False
            
            # Carregar dados da UF
            self.dados_uf_atual = pd.read_csv(arquivo_dados)
            self.geometrias_uf_atual = gpd.read_file(arquivo_geometrias)
            
            with open(arquivo_cores, 'r', encoding='utf-8') as f:
                self.zona_cores_uf_atual = json.load(f)
            
            self.uf_atual = codigo_uf
            
            print(f"✅ UF {config.nome} ({codigo_uf}) selecionada")
            print(f"📊 Municípios carregados: {len(self.dados_uf_atual)}")
            print(f"🗺️ Geometrias carregadas: {len(self.geometrias_uf_atual)}")
            print(f"🎨 Zonas disponíveis: {len(self.zona_cores_uf_atual)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao selecionar UF {codigo_uf}: {e}")
            return False
    
    def obter_ufs_disponiveis(self) -> List[Dict[str, str]]:
        """Retorna lista de UFs disponíveis"""
        return [
            {
                "codigo": config.codigo,
                "nome": config.nome,
                "total_municipios": self._contar_municipios(config) if self._verificar_arquivos_uf(config) else 0,
                "status": "ativo" if self._verificar_arquivos_uf(config) else "incompleto"
            }
            for config in self.ufs_disponiveis.values()
        ]
    
    def _verificar_arquivos_uf(self, config: ConfigUF) -> bool:
        """Verifica se todos os arquivos necessários da UF existem"""
        diretorio_uf = self.diretorio_base / config.diretorio
        
        arquivos_necessarios = [
            config.arquivo_dados,
            config.arquivo_geometrias,
            config.arquivo_cores
        ]
        
        return all((diretorio_uf / arquivo).exists() for arquivo in arquivos_necessarios)
    
    def _contar_municipios(self, config: ConfigUF) -> int:
        """Conta municípios de uma UF"""
        try:
            diretorio_uf = self.diretorio_base / config.diretorio
            arquivo_dados = diretorio_uf / config.arquivo_dados
            
            if arquivo_dados.exists():
                dados = pd.read_csv(arquivo_dados)
                return len(dados)
            return 0
        except:
            return 0
    
    def obter_dados_uf_atual(self) -> Tuple[Optional[pd.DataFrame], Optional[gpd.GeoDataFrame], Optional[Dict]]:
        """Retorna dados da UF atualmente selecionada"""
        if not self.uf_atual:
            return None, None, None
        
        return self.dados_uf_atual, self.geometrias_uf_atual, self.zona_cores_uf_atual
    
    def obter_info_uf_atual(self) -> Optional[Dict]:
        """Retorna informações da UF atual"""
        if not self.uf_atual:
            return None
        
        config = self.ufs_disponiveis[self.uf_atual]
        return {
            "codigo": config.codigo,
            "nome": config.nome,
            "total_municipios": len(self.dados_uf_atual) if self.dados_uf_atual is not None else 0,
            "total_zonas": len(self.zona_cores_uf_atual) if self.zona_cores_uf_atual else 0,
            "diretorio": str(self.diretorio_base / config.diretorio)
        }
