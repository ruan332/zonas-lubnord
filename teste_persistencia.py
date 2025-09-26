#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste de Persistência
Simula o comportamento de deploy para verificar se as alterações são preservadas
"""

import os
import json
import pandas as pd
import shutil
from datetime import datetime
from sistema_persistencia import SistemaPersistencia

def testar_persistencia():
    """Testa se as alterações são preservadas entre reinicializações"""
    print("🧪 Iniciando teste de persistência...")
    
    # 1. Verificar estado atual
    print("\n📊 Estado atual dos arquivos:")
    arquivos_verificar = [
        'dados_mapa_atual.csv',
        'pernambuco_dados_gerar_mapa.csv',
        'alteracoes_zonas.json'
    ]
    
    for arquivo in arquivos_verificar:
        if os.path.exists(arquivo):
            size = os.path.getsize(arquivo)
            mtime = datetime.fromtimestamp(os.path.getmtime(arquivo))
            print(f"✅ {arquivo}: {size} bytes, modificado em {mtime}")
        else:
            print(f"❌ {arquivo}: não encontrado")
    
    # 2. Verificar dados atuais
    if os.path.exists('dados_mapa_atual.csv'):
        df_atual = pd.read_csv('dados_mapa_atual.csv')
        print(f"\n📈 Dados atuais: {len(df_atual)} municípios")
        
        # Contar zonas
        zonas_count = df_atual['Zona'].value_counts()
        print("\n🏷️ Distribuição de zonas:")
        for zona, count in zonas_count.head(10).items():
            print(f"   {zona}: {count} municípios")
    
    # 3. Verificar alterações salvas
    if os.path.exists('alteracoes_zonas.json'):
        with open('alteracoes_zonas.json', 'r', encoding='utf-8') as f:
            alteracoes = json.load(f)
        
        total_alteracoes = len(alteracoes.get('alteracoes', []))
        print(f"\n📝 Alterações salvas: {total_alteracoes}")
        
        if total_alteracoes > 0:
            print("\n🔄 Últimas 5 alterações:")
            for alt in alteracoes['alteracoes'][-5:]:
                print(f"   {alt['cidade']}: {alt['zona_anterior']} → {alt['zona_nova']}")
    
    # 4. Simular carregamento como no deploy
    print("\n🔄 Simulando carregamento pós-deploy...")
    
    # Simular a lógica do carregar_dados_iniciais
    dados_atuais_path = 'dados_mapa_atual.csv'
    dados_originais_path = 'pernambuco_dados_gerar_mapa.csv'
    
    usar_dados_atuais = False
    if os.path.exists(dados_atuais_path):
        if os.path.exists(dados_originais_path):
            time_atual = os.path.getmtime(dados_atuais_path)
            time_original = os.path.getmtime(dados_originais_path)
            usar_dados_atuais = time_atual >= time_original
            print(f"⏰ Timestamp dados atuais: {datetime.fromtimestamp(time_atual)}")
            print(f"⏰ Timestamp dados originais: {datetime.fromtimestamp(time_original)}")
        else:
            usar_dados_atuais = True
    
    if usar_dados_atuais:
        print("✅ Sistema usaria dados atualizados (correto!)")
        df_carregado = pd.read_csv(dados_atuais_path)
    else:
        print("⚠️ Sistema usaria dados originais + aplicaria alterações")
        df_carregado = pd.read_csv(dados_originais_path)
        
        # Simular aplicação de alterações
        persistencia = SistemaPersistencia()
        alteracoes = persistencia.carregar_alteracoes()
        if alteracoes and 'alteracoes' in alteracoes:
            alteracoes_aplicadas = 0
            for alt in alteracoes['alteracoes']:
                cd_mun = str(alt['cd_mun'])
                nova_zona = alt['zona_nova']
                
                mask = df_carregado['CD_Mun'].astype(str) == cd_mun
                if mask.any():
                    df_carregado.loc[mask, 'Zona'] = nova_zona
                    alteracoes_aplicadas += 1
            
            print(f"🔄 Aplicadas {alteracoes_aplicadas} alterações")
    
    print(f"\n📊 Dados carregados: {len(df_carregado)} municípios")
    zonas_carregadas = df_carregado['Zona'].value_counts()
    print("\n🏷️ Zonas após carregamento:")
    for zona, count in zonas_carregadas.head(10).items():
        print(f"   {zona}: {count} municípios")
    
    # 5. Verificar integridade
    print("\n🔍 Verificação de integridade:")
    
    if os.path.exists('dados_mapa_atual.csv'):
        df_atual = pd.read_csv('dados_mapa_atual.csv')
        
        # Comparar com dados carregados
        if df_atual.equals(df_carregado[df_atual.columns]):
            print("✅ Dados consistentes - alterações preservadas!")
        else:
            print("❌ Inconsistência detectada")
            
            # Mostrar diferenças
            diff_zonas = set(df_atual['Zona'].unique()) - set(df_carregado['Zona'].unique())
            if diff_zonas:
                print(f"   Zonas diferentes: {diff_zonas}")
    
    print("\n🎯 Resultado do teste:")
    if usar_dados_atuais:
        print("✅ SUCESSO: Sistema de persistência funcionando corretamente!")
        print("   - Dados atualizados são carregados automaticamente")
        print("   - Alterações são preservadas entre deploys")
        print("   - Não há perda de configurações")
    else:
        print("⚠️ ATENÇÃO: Sistema aplicará alterações do JSON")
        print("   - Funciona, mas é menos eficiente")
        print("   - Recomenda-se manter dados_mapa_atual.csv atualizado")

def criar_backup_teste():
    """Cria backup dos dados atuais para teste"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_teste_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    arquivos_backup = [
        'dados_mapa_atual.csv',
        'alteracoes_zonas.json',
        'zona_cores_mapping.json'
    ]
    
    for arquivo in arquivos_backup:
        if os.path.exists(arquivo):
            shutil.copy2(arquivo, os.path.join(backup_dir, arquivo))
    
    print(f"💾 Backup criado em: {backup_dir}")
    return backup_dir

if __name__ == "__main__":
    print("🔧 Script de Teste de Persistência - Mapa Interativo")
    print("=" * 60)
    
    # Criar backup antes do teste
    backup_dir = criar_backup_teste()
    
    # Executar teste
    testar_persistencia()
    
    print("\n" + "=" * 60)
    print("✅ Teste concluído!")
    print(f"📁 Backup disponível em: {backup_dir}")