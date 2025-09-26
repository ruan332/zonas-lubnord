#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para identificar municípios que não foram identificados no mapa
"""

import pandas as pd
import json

def verificar_municipios_nao_identificados():
    """Verifica quais municípios não foram identificados no mapa"""
    
    print("=== VERIFICAÇÃO DE MUNICÍPIOS NÃO IDENTIFICADOS ===")
    
    try:
        # Carregar dados dos municípios
        print("Carregando dados dos municípios...")
        dados_municipios = pd.read_csv('pernambuco_dados_gerar_mapa.csv')
        print(f"✅ Dados carregados: {len(dados_municipios)} municípios")
        
        # Carregar geometria
        print("Carregando geometria...")
        with open('pernambuco.json', 'r', encoding='utf-8') as f:
            geometria_data = json.load(f)
        
        # Extrair IDs da geometria
        ids_geometria = []
        for feature in geometria_data['features']:
            if 'properties' in feature and 'id' in feature['properties']:
                ids_geometria.append(int(feature['properties']['id']))
        
        print(f"✅ Geometria carregada: {len(ids_geometria)} municípios")
        
        # Comparar dados
        print("\n=== ANÁLISE DE CORRESPONDÊNCIA ===")
        
        # Municípios nos dados mas não na geometria
        municipios_dados = set(dados_municipios['CD_Mun'].astype(int))
        municipios_geometria = set(ids_geometria)
        
        # Municípios sem geometria
        sem_geometria = municipios_dados - municipios_geometria
        
        # Municípios com geometria mas sem dados
        sem_dados = municipios_geometria - municipios_dados
        
        # Municípios com correspondência
        com_correspondencia = municipios_dados & municipios_geometria
        
        print(f"📊 Municípios nos dados: {len(municipios_dados)}")
        print(f"📊 Municípios na geometria: {len(municipios_geometria)}")
        print(f"✅ Com correspondência: {len(com_correspondencia)}")
        print(f"❌ Sem geometria: {len(sem_geometria)}")
        print(f"⚠️  Sem dados: {len(sem_dados)}")
        
        # Detalhar municípios sem geometria
        if sem_geometria:
            print(f"\n=== MUNICÍPIOS SEM GEOMETRIA ({len(sem_geometria)}) ===")
            municipios_sem_geo = dados_municipios[dados_municipios['CD_Mun'].isin(sem_geometria)]
            for _, row in municipios_sem_geo.iterrows():
                print(f"❌ {row['CD_Mun']} - {row['Cidade']} - {row['Zona']}")
        
        # Detalhar municípios sem dados
        if sem_dados:
            print(f"\n=== MUNICÍPIOS SEM DADOS ({len(sem_dados)}) ===")
            for cd_mun in sorted(sem_dados):
                print(f"⚠️  {cd_mun} - (Geometria disponível mas sem dados)")
        
        # Verificar se há municípios marcados como "Sem Zona"
        print(f"\n=== MUNICÍPIOS COM PROBLEMAS DE ZONA ===")
        sem_zona = dados_municipios[dados_municipios['Zona'].isna() | (dados_municipios['Zona'] == '')]
        if len(sem_zona) > 0:
            print(f"⚠️  Municípios sem zona definida: {len(sem_zona)}")
            for _, row in sem_zona.iterrows():
                print(f"   {row['CD_Mun']} - {row['Cidade']}")
        else:
            print("✅ Todos os municípios têm zona definida")
        
        # Resumo final
        print(f"\n=== RESUMO FINAL ===")
        print(f"✅ Municípios processados com sucesso: {len(com_correspondencia)}")
        print(f"❌ Municípios não identificados no mapa: {len(sem_geometria)}")
        print(f"⚠️  Geometrias sem dados: {len(sem_dados)}")
        
        taxa_sucesso = (len(com_correspondencia) / len(municipios_dados)) * 100
        print(f"📈 Taxa de sucesso: {taxa_sucesso:.1f}%")
        
        return {
            'total_dados': len(municipios_dados),
            'total_geometria': len(municipios_geometria),
            'com_correspondencia': len(com_correspondencia),
            'sem_geometria': list(sem_geometria),
            'sem_dados': list(sem_dados),
            'taxa_sucesso': taxa_sucesso
        }
        
    except Exception as e:
        print(f"❌ Erro ao verificar municípios: {e}")
        return None

if __name__ == "__main__":
    resultado = verificar_municipios_nao_identificados()