#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para restaurar dados completos de PDV e Share
Corrige códigos de municípios e preserva todas as colunas originais
"""

import pandas as pd
import json
import os
from datetime import datetime

def restaurar_dados_completos():
    """Restaura dados completos do arquivo original preservando alterações de zona"""
    try:
        print("🔄 Iniciando restauração de dados completos...")
        
        # 1. Carregar dados originais completos
        print("📂 Carregando arquivo original...")
        dados_originais = pd.read_csv('pernambuco_dados_gerar_mapa.csv')
        print(f"✅ Dados originais carregados: {len(dados_originais)} municípios")
        print(f"📊 Colunas disponíveis: {list(dados_originais.columns)}")
        
        # 2. Verificar integridade dos dados
        print("\n🔍 Verificando integridade dos dados...")
        print(f"Total de municípios: {len(dados_originais)}")
        print(f"Municípios únicos: {dados_originais['CD_Mun'].nunique()}")
        print(f"Valores NaN em CD_Mun: {dados_originais['CD_Mun'].isna().sum()}")
        print(f"Valores NaN em PDV: {dados_originais['PDV'].isna().sum()}")
        print(f"Valores NaN em %SHARE: {dados_originais['%SHARE'].isna().sum()}")
        
        # 3. Tratar valores NaN sem remover municípios
        print("\n🛠️ Tratando valores NaN...")
        dados_restaurados = dados_originais.copy()
        
        # Preencher NaN com 0 para colunas numéricas
        colunas_numericas = ['SELL OUT ANUAL', 'SELL OUT MÊS', 'POTENCIAL ANUAL', 'POTENCIAL MÊS', 'PDV', '%SHARE']
        for col in colunas_numericas:
            if col in dados_restaurados.columns:
                dados_restaurados[col] = dados_restaurados[col].fillna(0)
                print(f"  ✓ {col}: NaN preenchidos com 0")
        
        # Preencher NaN com valores padrão para colunas de texto
        dados_restaurados['Cidade'] = dados_restaurados['Cidade'].fillna('Município não identificado')
        dados_restaurados['Zona'] = dados_restaurados['Zona'].fillna('Sem Zona')
        
        # 4. Carregar alterações de zona salvas
        print("\n🔄 Aplicando alterações de zona salvas...")
        alteracoes_aplicadas = 0
        
        if os.path.exists('alteracoes_zonas.json'):
            with open('alteracoes_zonas.json', 'r', encoding='utf-8') as f:
                alteracoes_data = json.load(f)
            
            if 'alteracoes' in alteracoes_data:
                for alt in alteracoes_data['alteracoes']:
                    cd_mun = str(alt['cd_mun'])
                    nova_zona = alt['zona_nova']
                    
                    # Encontrar e atualizar o município
                    mask = dados_restaurados['CD_Mun'].astype(str) == cd_mun
                    if mask.any():
                        dados_restaurados.loc[mask, 'Zona'] = nova_zona
                        alteracoes_aplicadas += 1
                        print(f"  ✓ {alt['cidade']}: {alt['zona_anterior']} → {nova_zona}")
                
                print(f"✅ {alteracoes_aplicadas} alterações de zona aplicadas")
        else:
            print("ℹ️ Nenhum arquivo de alterações encontrado")
        
        # 5. Carregar cores das zonas
        print("\n🎨 Aplicando cores das zonas...")
        if os.path.exists('zona_cores_mapping.json'):
            with open('zona_cores_mapping.json', 'r', encoding='utf-8') as f:
                zona_cores = json.load(f)
            
            # Adicionar coluna de cor
            dados_restaurados['Cor'] = dados_restaurados['Zona'].map(zona_cores).fillna('#CCCCCC')
            print(f"✅ Cores aplicadas para {len(zona_cores)} zonas")
        else:
            print("⚠️ Arquivo de cores não encontrado, usando cor padrão")
            dados_restaurados['Cor'] = '#CCCCCC'
        
        # 6. Calcular Share se necessário
        print("\n📊 Calculando Share...")
        if '%SHARE' not in dados_restaurados.columns:
            # Calcular Share como (SELL OUT ANUAL / POTENCIAL ANUAL) * 100
            dados_restaurados['Share_Calculado'] = (
                dados_restaurados['SELL OUT ANUAL'] / 
                dados_restaurados['POTENCIAL ANUAL'] * 100
            ).fillna(0)
            print("✅ Share calculado a partir de SELL OUT e POTENCIAL")
        else:
            # Usar coluna %SHARE existente
            dados_restaurados['Share_Calculado'] = dados_restaurados['%SHARE'].fillna(0)
            print("✅ Share obtido da coluna %SHARE original")
        
        # 7. Organizar colunas na ordem preferencial
        print("\n📋 Organizando colunas...")
        colunas_preferenciais = [
            'UF', 'Mesorregião Geográfica', 'CD_Mun', 'Cidade', 'Zona',
            'SELL OUT ANUAL', 'SELL OUT MÊS', 'POTENCIAL ANUAL', 'POTENCIAL MÊS',
            'POPULAÇÃO ', 'PDV', '%SHARE', 'Cor', 'Share_Calculado'
        ]
        
        # Identificar colunas disponíveis na ordem preferencial
        colunas_finais = []
        for col in colunas_preferenciais:
            if col in dados_restaurados.columns:
                colunas_finais.append(col)
        
        # Adicionar outras colunas que não estão na lista preferencial
        for col in dados_restaurados.columns:
            if col not in colunas_finais:
                colunas_finais.append(col)
        
        dados_finais = dados_restaurados[colunas_finais].copy()
        
        # 8. Salvar dados restaurados
        print("\n💾 Salvando dados restaurados...")
        dados_finais.to_csv('dados_mapa_atual.csv', index=False)
        
        # 9. Criar backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_dados_restaurados_{timestamp}.csv'
        dados_finais.to_csv(backup_filename, index=False)
        
        # 10. Relatório final
        print("\n📊 RELATÓRIO DE RESTAURAÇÃO:")
        print(f"✅ Total de municípios restaurados: {len(dados_finais)}")
        print(f"✅ Colunas preservadas: {len(colunas_finais)}")
        print(f"✅ Alterações de zona aplicadas: {alteracoes_aplicadas}")
        print(f"✅ Arquivo principal: dados_mapa_atual.csv")
        print(f"✅ Backup criado: {backup_filename}")
        
        # Verificar dados de PDV e Share
        total_pdv = dados_finais['PDV'].sum() if 'PDV' in dados_finais.columns else 0
        share_medio = dados_finais['Share_Calculado'].mean() if 'Share_Calculado' in dados_finais.columns else 0
        
        print(f"\n📈 DADOS RESTAURADOS:")
        print(f"📍 Total PDV: {total_pdv:,.0f}")
        print(f"📊 Share médio: {share_medio:.2f}%")
        print(f"🏘️ Municípios com PDV > 0: {(dados_finais['PDV'] > 0).sum() if 'PDV' in dados_finais.columns else 0}")
        print(f"📈 Municípios com Share > 0: {(dados_finais['Share_Calculado'] > 0).sum() if 'Share_Calculado' in dados_finais.columns else 0}")
        
        print("\n🎉 RESTAURAÇÃO CONCLUÍDA COM SUCESSO!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante restauração: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    restaurar_dados_completos()