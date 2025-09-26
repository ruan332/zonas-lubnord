"""
Módulo de Análise e Comparação de Cenários
Permite comparar diferentes configurações de zonas e analisar impactos
"""

import pandas as pd
import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

class AnalisadorCenarios:
    def __init__(self, dados_originais_path: str = "dados_mapa_pernambuco.csv",
                 cores_mapping_path: str = "zona_cores_mapping.json"):
        self.dados_originais_path = dados_originais_path
        self.cores_mapping_path = cores_mapping_path
        self.dados_originais = None
        self.cores_zonas = None
        self.cenarios = {}
        
        self.carregar_dados_base()
    
    def carregar_dados_base(self):
        """Carrega dados base e mapeamento de cores"""
        try:
            self.dados_originais = pd.read_csv(self.dados_originais_path)
            
            with open(self.cores_mapping_path, 'r', encoding='utf-8') as f:
                self.cores_zonas = json.load(f)
                
        except Exception as e:
            print(f"Erro ao carregar dados base: {e}")
    
    def criar_cenario(self, nome_cenario: str, dados_cenario: pd.DataFrame, 
                     descricao: str = "") -> bool:
        """
        Cria um novo cenário para análise
        
        Args:
            nome_cenario: Nome identificador do cenário
            dados_cenario: DataFrame com os dados do cenário
            descricao: Descrição opcional do cenário
            
        Returns:
            bool: True se criou com sucesso
        """
        try:
            self.cenarios[nome_cenario] = {
                'dados': dados_cenario.copy(),
                'descricao': descricao,
                'criado_em': datetime.now().isoformat(),
                'estatisticas': self._calcular_estatisticas_cenario(dados_cenario)
            }
            return True
        except Exception as e:
            print(f"Erro ao criar cenário: {e}")
            return False
    
    def _calcular_estatisticas_cenario(self, dados: pd.DataFrame) -> Dict[str, Any]:
        """Calcula estatísticas básicas de um cenário"""
        stats = {}
        
        # Distribuição por zona
        distribuicao_zonas = dados.groupby('Zona').agg({
            'CD_Mun': 'count',
            'POPULAÇÃO': 'sum',
            'SELL OUT ANUAL': 'sum',
            'POTENCIAL ANUAL': 'sum',
            'PDV': 'sum'
        }).round(2)
        
        stats['distribuicao_zonas'] = distribuicao_zonas.to_dict('index')
        
        # Métricas gerais
        stats['total_municipios'] = len(dados)
        stats['total_populacao'] = dados['POPULAÇÃO'].sum()
        stats['total_sell_out'] = dados['SELL OUT ANUAL'].sum()
        stats['total_potencial'] = dados['POTENCIAL ANUAL'].sum()
        stats['total_pdv'] = dados['PDV'].sum()
        
        # Eficiência por zona (Sell Out / Potencial)
        zona_eficiencia = dados.groupby('Zona').apply(
            lambda x: (x['SELL OUT ANUAL'].sum() / x['POTENCIAL ANUAL'].sum() * 100) 
            if x['POTENCIAL ANUAL'].sum() > 0 else 0
        ).round(2)
        stats['eficiencia_por_zona'] = zona_eficiencia.to_dict()
        
        # Share médio por zona
        share_medio = dados.groupby('Zona')['%SHARE'].mean().round(2)
        stats['share_medio_por_zona'] = share_medio.to_dict()
        
        return stats
    
    def comparar_cenarios(self, cenario1: str, cenario2: str) -> Dict[str, Any]:
        """
        Compara dois cenários
        
        Args:
            cenario1: Nome do primeiro cenário
            cenario2: Nome do segundo cenário
            
        Returns:
            Dict com análise comparativa
        """
        if cenario1 not in self.cenarios or cenario2 not in self.cenarios:
            return {"erro": "Um ou ambos cenários não encontrados"}
        
        stats1 = self.cenarios[cenario1]['estatisticas']
        stats2 = self.cenarios[cenario2]['estatisticas']
        
        comparacao = {
            'cenarios': {
                'cenario1': {'nome': cenario1, 'descricao': self.cenarios[cenario1]['descricao']},
                'cenario2': {'nome': cenario2, 'descricao': self.cenarios[cenario2]['descricao']}
            },
            'metricas_gerais': {},
            'mudancas_por_zona': {},
            'municipios_alterados': []
        }
        
        # Comparar métricas gerais
        metricas = ['total_municipios', 'total_populacao', 'total_sell_out', 'total_potencial', 'total_pdv']
        for metrica in metricas:
            valor1 = stats1.get(metrica, 0)
            valor2 = stats2.get(metrica, 0)
            diferenca = valor2 - valor1
            percentual = (diferenca / valor1 * 100) if valor1 != 0 else 0
            
            comparacao['metricas_gerais'][metrica] = {
                'cenario1': valor1,
                'cenario2': valor2,
                'diferenca': diferenca,
                'percentual_mudanca': round(percentual, 2)
            }
        
        # Identificar municípios que mudaram de zona
        dados1 = self.cenarios[cenario1]['dados']
        dados2 = self.cenarios[cenario2]['dados']
        
        merged = dados1.merge(dados2, on='CD_Mun', suffixes=('_c1', '_c2'))
        municipios_alterados = merged[merged['Zona_c1'] != merged['Zona_c2']]
        
        comparacao['municipios_alterados'] = municipios_alterados[
            ['CD_Mun', 'Cidade_c1', 'Zona_c1', 'Zona_c2', 'POPULAÇÃO_c1', 'SELL OUT ANUAL_c1']
        ].to_dict('records')
        
        # Análise de mudanças por zona
        for zona in set(list(stats1['distribuicao_zonas'].keys()) + list(stats2['distribuicao_zonas'].keys())):
            zona_stats1 = stats1['distribuicao_zonas'].get(zona, {})
            zona_stats2 = stats2['distribuicao_zonas'].get(zona, {})
            
            comparacao['mudancas_por_zona'][zona] = {
                'municipios': {
                    'antes': zona_stats1.get('CD_Mun', 0),
                    'depois': zona_stats2.get('CD_Mun', 0),
                    'diferenca': zona_stats2.get('CD_Mun', 0) - zona_stats1.get('CD_Mun', 0)
                },
                'populacao': {
                    'antes': zona_stats1.get('POPULAÇÃO', 0),
                    'depois': zona_stats2.get('POPULAÇÃO', 0),
                    'diferenca': zona_stats2.get('POPULAÇÃO', 0) - zona_stats1.get('POPULAÇÃO', 0)
                },
                'sell_out': {
                    'antes': zona_stats1.get('SELL OUT ANUAL', 0),
                    'depois': zona_stats2.get('SELL OUT ANUAL', 0),
                    'diferenca': zona_stats2.get('SELL OUT ANUAL', 0) - zona_stats1.get('SELL OUT ANUAL', 0)
                }
            }
        
        return comparacao
    
    def gerar_relatorio_cenario(self, nome_cenario: str) -> Dict[str, Any]:
        """Gera relatório detalhado de um cenário"""
        if nome_cenario not in self.cenarios:
            return {"erro": "Cenário não encontrado"}
        
        cenario = self.cenarios[nome_cenario]
        dados = cenario['dados']
        
        relatorio = {
            'nome_cenario': nome_cenario,
            'descricao': cenario['descricao'],
            'criado_em': cenario['criado_em'],
            'resumo_executivo': {},
            'analise_detalhada': {},
            'recomendacoes': []
        }
        
        # Resumo executivo
        stats = cenario['estatisticas']
        relatorio['resumo_executivo'] = {
            'total_municipios': stats['total_municipios'],
            'zonas_ativas': len(stats['distribuicao_zonas']),
            'populacao_total': stats['total_populacao'],
            'sell_out_total': stats['total_sell_out'],
            'potencial_total': stats['total_potencial'],
            'eficiencia_geral': round(stats['total_sell_out'] / stats['total_potencial'] * 100, 2) if stats['total_potencial'] > 0 else 0
        }
        
        # Análise detalhada por zona
        for zona, zona_stats in stats['distribuicao_zonas'].items():
            eficiencia = stats['eficiencia_por_zona'].get(zona, 0)
            share_medio = stats['share_medio_por_zona'].get(zona, 0)
            
            relatorio['analise_detalhada'][zona] = {
                'municipios': zona_stats['CD_Mun'],
                'populacao': zona_stats['POPULAÇÃO'],
                'sell_out': zona_stats['SELL OUT ANUAL'],
                'potencial': zona_stats['POTENCIAL ANUAL'],
                'pdv': zona_stats['PDV'],
                'eficiencia': eficiencia,
                'share_medio': share_medio,
                'cor': self.cores_zonas.get(zona, '#CCCCCC')
            }
        
        # Gerar recomendações baseadas na análise
        relatorio['recomendacoes'] = self._gerar_recomendacoes(stats)
        
        return relatorio
    
    def _gerar_recomendacoes(self, stats: Dict[str, Any]) -> List[str]:
        """Gera recomendações baseadas nas estatísticas"""
        recomendacoes = []
        
        # Analisar eficiência por zona
        eficiencias = stats['eficiencia_por_zona']
        if eficiencias:
            zona_menos_eficiente = min(eficiencias.items(), key=lambda x: x[1])
            zona_mais_eficiente = max(eficiencias.items(), key=lambda x: x[1])
            
            if zona_menos_eficiente[1] < 50:
                recomendacoes.append(
                    f"A zona '{zona_menos_eficiente[0]}' apresenta baixa eficiência ({zona_menos_eficiente[1]:.1f}%). "
                    "Considere revisar a estratégia comercial ou redistribuir municípios."
                )
            
            if zona_mais_eficiente[1] > 80:
                recomendacoes.append(
                    f"A zona '{zona_mais_eficiente[0]}' apresenta excelente performance ({zona_mais_eficiente[1]:.1f}%). "
                    "Considere replicar as estratégias desta zona em outras regiões."
                )
        
        # Analisar distribuição de municípios
        distribuicao = stats['distribuicao_zonas']
        municipios_por_zona = [zona_data['CD_Mun'] for zona_data in distribuicao.values()]
        
        if municipios_por_zona:
            media_municipios = np.mean(municipios_por_zona)
            desvio_padrao = np.std(municipios_por_zona)
            
            if desvio_padrao > media_municipios * 0.5:
                recomendacoes.append(
                    "Há grande variação no número de municípios por zona. "
                    "Considere rebalancear para otimizar a gestão territorial."
                )
        
        # Analisar potencial vs sell out
        if stats['total_potencial'] > 0:
            utilizacao_potencial = stats['total_sell_out'] / stats['total_potencial'] * 100
            if utilizacao_potencial < 60:
                recomendacoes.append(
                    f"A utilização do potencial total está em {utilizacao_potencial:.1f}%. "
                    "Há oportunidades significativas de crescimento."
                )
        
        return recomendacoes
    
    def exportar_cenario(self, nome_cenario: str, formato: str = "csv") -> str:
        """Exporta um cenário para arquivo"""
        if nome_cenario not in self.cenarios:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if formato.lower() == "csv":
            arquivo = f"cenario_{nome_cenario}_{timestamp}.csv"
            self.cenarios[nome_cenario]['dados'].to_csv(arquivo, index=False)
        
        elif formato.lower() == "json":
            arquivo = f"cenario_{nome_cenario}_{timestamp}.json"
            dados_export = {
                'nome': nome_cenario,
                'descricao': self.cenarios[nome_cenario]['descricao'],
                'criado_em': self.cenarios[nome_cenario]['criado_em'],
                'dados': self.cenarios[nome_cenario]['dados'].to_dict('records'),
                'estatisticas': self.cenarios[nome_cenario]['estatisticas']
            }
            
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados_export, f, indent=2, ensure_ascii=False)
        
        return arquivo
    
    def listar_cenarios(self) -> List[Dict[str, Any]]:
        """Lista todos os cenários disponíveis"""
        cenarios_info = []
        
        for nome, cenario in self.cenarios.items():
            info = {
                'nome': nome,
                'descricao': cenario['descricao'],
                'criado_em': cenario['criado_em'],
                'total_municipios': cenario['estatisticas']['total_municipios'],
                'zonas_ativas': len(cenario['estatisticas']['distribuicao_zonas'])
            }
            cenarios_info.append(info)
        
        return sorted(cenarios_info, key=lambda x: x['criado_em'], reverse=True)
    
    def remover_cenario(self, nome_cenario: str) -> bool:
        """Remove um cenário"""
        if nome_cenario in self.cenarios:
            del self.cenarios[nome_cenario]
            return True
        return False
    
    def criar_cenario_a_partir_de_alteracoes(self, nome_cenario: str, 
                                           alteracoes: List[Dict[str, Any]], 
                                           descricao: str = "") -> bool:
        """
        Cria um cenário aplicando uma lista de alterações aos dados originais
        
        Args:
            nome_cenario: Nome do cenário
            alteracoes: Lista de alterações no formato [{'cd_mun': '123', 'nova_zona': 'Zona A'}, ...]
            descricao: Descrição do cenário
            
        Returns:
            bool: True se criou com sucesso
        """
        try:
            dados_cenario = self.dados_originais.copy()
            
            # Aplicar alterações
            for alteracao in alteracoes:
                cd_mun = alteracao.get('cd_mun')
                nova_zona = alteracao.get('nova_zona')
                
                if cd_mun and nova_zona:
                    mask = dados_cenario['CD_Mun'].astype(str) == str(cd_mun)
                    if mask.any():
                        dados_cenario.loc[mask, 'Zona'] = nova_zona
                        # Atualizar cor se disponível
                        if nova_zona in self.cores_zonas:
                            dados_cenario.loc[mask, 'Cor'] = self.cores_zonas[nova_zona]
            
            return self.criar_cenario(nome_cenario, dados_cenario, descricao)
            
        except Exception as e:
            print(f"Erro ao criar cenário a partir de alterações: {e}")
            return False

# Exemplo de uso
if __name__ == "__main__":
    # Inicializar analisador
    analisador = AnalisadorCenarios()
    
    print("🔍 Analisador de Cenários Inicializado")
    print(f"📊 Dados originais carregados: {len(analisador.dados_originais)} municípios")
    print(f"🎨 Zonas disponíveis: {len(analisador.cores_zonas)}")
    
    # Criar cenário exemplo (dados originais)
    analisador.criar_cenario(
        "Original", 
        analisador.dados_originais, 
        "Configuração original das zonas"
    )
    
    # Listar cenários
    cenarios = analisador.listar_cenarios()
    print(f"📋 Cenários disponíveis: {len(cenarios)}")
    
    for cenario in cenarios:
        print(f"  - {cenario['nome']}: {cenario['total_municipios']} municípios")