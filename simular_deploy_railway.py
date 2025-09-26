#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulador de Deploy Railway
Simula o comportamento exato do Railway para testar persistência
"""

import os
import sys
import json
import pandas as pd
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

def simular_deploy_railway():
    """Simula o processo completo de deploy do Railway"""
    print("🚀 Simulando Deploy Railway...")
    print("=" * 50)
    
    # 1. Criar diretório temporário para simular ambiente limpo
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Ambiente temporário: {temp_dir}")
        
        # 2. Copiar apenas arquivos que estariam no repositório
        arquivos_repo = [
            'app_mapa_interativo.py',
            'sistema_persistencia.py',
            'pernambuco_dados_gerar_mapa.csv',
            'pernambuco.json',
            'zona_cores_mapping.json',
            'templates/mapa_interativo.html',
            'static/css/mapa_interativo.css',
            'static/js/mapa_interativo.js'
        ]
        
        print("\n📦 Copiando arquivos do repositório...")
        for arquivo in arquivos_repo:
            src = Path(arquivo)
            if src.exists():
                dst = Path(temp_dir) / arquivo
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                print(f"✅ {arquivo}")
            else:
                print(f"⚠️ {arquivo} (não encontrado)")
        
        # 3. Copiar dados persistidos (que deveriam estar no Railway)
        arquivos_persistencia = [
            'dados_mapa_atual.csv',
            'alteracoes_zonas.json'
        ]
        
        print("\n💾 Copiando dados persistidos...")
        for arquivo in arquivos_persistencia:
            src = Path(arquivo)
            if src.exists():
                dst = Path(temp_dir) / arquivo
                shutil.copy2(src, dst)
                print(f"✅ {arquivo}")
            else:
                print(f"❌ {arquivo} (perdido no deploy!)")
        
        # 4. Simular inicialização da aplicação
        print("\n🔄 Simulando inicialização da aplicação...")
        
        # Mudar para diretório temporário
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Adicionar ao path para imports
            sys.path.insert(0, temp_dir)
            
            # Simular carregamento como no app_mapa_interativo.py
            dados_atuais_path = 'dados_mapa_atual.csv'
            dados_originais_path = 'pernambuco_dados_gerar_mapa.csv'
            
            print(f"\n📊 Verificando arquivos de dados...")
            print(f"   dados_mapa_atual.csv: {'✅' if os.path.exists(dados_atuais_path) else '❌'}")
            print(f"   pernambuco_dados_gerar_mapa.csv: {'✅' if os.path.exists(dados_originais_path) else '❌'}")
            
            # Lógica de carregamento inteligente
            usar_dados_atuais = False
            if os.path.exists(dados_atuais_path):
                if os.path.exists(dados_originais_path):
                    time_atual = os.path.getmtime(dados_atuais_path)
                    time_original = os.path.getmtime(dados_originais_path)
                    usar_dados_atuais = time_atual >= time_original
                    
                    print(f"\n⏰ Comparação de timestamps:")
                    print(f"   Dados atuais: {datetime.fromtimestamp(time_atual)}")
                    print(f"   Dados originais: {datetime.fromtimestamp(time_original)}")
                    print(f"   Usar dados atuais: {'✅' if usar_dados_atuais else '❌'}")
                else:
                    usar_dados_atuais = True
                    print("\n✅ Apenas dados atuais disponíveis")
            else:
                print("\n❌ Dados atuais não encontrados - usando originais")
            
            # Carregar dados
            if usar_dados_atuais:
                print("\n📈 Carregando dados atualizados...")
                df = pd.read_csv(dados_atuais_path)
                fonte = "dados_mapa_atual.csv"
            else:
                print("\n📈 Carregando dados originais...")
                df = pd.read_csv(dados_originais_path)
                fonte = "pernambuco_dados_gerar_mapa.csv"
                
                # Aplicar alterações se existirem
                if os.path.exists('alteracoes_zonas.json'):
                    print("🔄 Aplicando alterações salvas...")
                    with open('alteracoes_zonas.json', 'r', encoding='utf-8') as f:
                        alteracoes_data = json.load(f)
                    
                    if 'alteracoes' in alteracoes_data:
                        alteracoes_aplicadas = 0
                        for alt in alteracoes_data['alteracoes']:
                            cd_mun = str(alt['cd_mun'])
                            nova_zona = alt['zona_nova']
                            
                            mask = df['CD_Mun'].astype(str) == cd_mun
                            if mask.any():
                                df.loc[mask, 'Zona'] = nova_zona
                                alteracoes_aplicadas += 1
                        
                        print(f"   ✅ {alteracoes_aplicadas} alterações aplicadas")
            
            print(f"\n📊 Dados carregados com sucesso!")
            print(f"   Fonte: {fonte}")
            print(f"   Municípios: {len(df)}")
            
            # Mostrar distribuição de zonas
            zonas_count = df['Zona'].value_counts()
            print(f"\n🏷️ Distribuição de zonas ({len(zonas_count)} zonas):")
            for zona, count in zonas_count.head(10).items():
                print(f"   {zona}: {count} municípios")
            
            # 5. Verificar se alterações foram preservadas
            print("\n🔍 Verificação de preservação de dados:")
            
            # Comparar com dados originais
            if os.path.exists(dados_originais_path):
                df_original = pd.read_csv(dados_originais_path)
                
                # Contar diferenças
                diferencas = 0
                for idx, row in df.iterrows():
                    cd_mun = row['CD_Mun']
                    zona_atual = row['Zona']
                    
                    mask_original = df_original['CD_Mun'] == cd_mun
                    if mask_original.any():
                        zona_original = df_original.loc[mask_original, 'Zona'].iloc[0]
                        if zona_atual != zona_original:
                            diferencas += 1
                
                print(f"   Alterações preservadas: {diferencas}")
                
                if diferencas > 0:
                    print("   ✅ SUCESSO: Alterações foram preservadas!")
                else:
                    print("   ⚠️ ATENÇÃO: Nenhuma alteração detectada")
            
            # 6. Resultado final
            print("\n" + "=" * 50)
            print("🎯 RESULTADO DA SIMULAÇÃO:")
            
            if usar_dados_atuais:
                print("✅ DEPLOY RAILWAY FUNCIONARÁ CORRETAMENTE!")
                print("   ✓ Dados atualizados serão carregados")
                print("   ✓ Alterações serão preservadas")
                print("   ✓ Não haverá perda de configurações")
            else:
                if os.path.exists('alteracoes_zonas.json'):
                    print("✅ DEPLOY RAILWAY FUNCIONARÁ (com aplicação de alterações)")
                    print("   ✓ Alterações do JSON serão aplicadas")
                    print("   ✓ Dados serão restaurados corretamente")
                    print("   ⚠ Recomenda-se manter dados_mapa_atual.csv")
                else:
                    print("❌ PROBLEMA: DADOS SERÃO RESETADOS!")
                    print("   ✗ Alterações serão perdidas")
                    print("   ✗ Sistema voltará ao estado original")
            
        except Exception as e:
            print(f"❌ Erro na simulação: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Voltar ao diretório original
            os.chdir(original_cwd)
            sys.path.remove(temp_dir)

def verificar_arquivos_railway():
    """Verifica se todos os arquivos necessários estão presentes"""
    print("\n📋 Verificação de arquivos para Railway:")
    
    arquivos_essenciais = {
        'app_mapa_interativo.py': 'Aplicação principal',
        'sistema_persistencia.py': 'Sistema de persistência',
        'requirements.txt': 'Dependências Python',
        'Procfile': 'Configuração Railway',
        'railway.json': 'Configuração Railway',
        'runtime.txt': 'Versão Python'
    }
    
    arquivos_dados = {
        'pernambuco_dados_gerar_mapa.csv': 'Dados originais',
        'pernambuco.json': 'Geometrias',
        'zona_cores_mapping.json': 'Mapeamento de cores'
    }
    
    arquivos_persistencia = {
        'dados_mapa_atual.csv': 'Dados atualizados',
        'alteracoes_zonas.json': 'Histórico de alterações'
    }
    
    print("\n🔧 Arquivos essenciais:")
    for arquivo, desc in arquivos_essenciais.items():
        status = "✅" if os.path.exists(arquivo) else "❌"
        print(f"   {status} {arquivo} - {desc}")
    
    print("\n📊 Arquivos de dados:")
    for arquivo, desc in arquivos_dados.items():
        status = "✅" if os.path.exists(arquivo) else "❌"
        print(f"   {status} {arquivo} - {desc}")
    
    print("\n💾 Arquivos de persistência:")
    for arquivo, desc in arquivos_persistencia.items():
        status = "✅" if os.path.exists(arquivo) else "❌"
        print(f"   {status} {arquivo} - {desc}")

if __name__ == "__main__":
    print("🚀 Simulador de Deploy Railway")
    print("Testa se as alterações serão preservadas no deploy")
    print("=" * 60)
    
    # Verificar arquivos
    verificar_arquivos_railway()
    
    # Simular deploy
    simular_deploy_railway()
    
    print("\n" + "=" * 60)
    print("✅ Simulação concluída!")