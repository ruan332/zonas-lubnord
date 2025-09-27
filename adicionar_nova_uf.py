#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para adicionar nova UF ao sistema
Facilita a criação de estrutura e arquivos para novas Unidades Federativas
"""

import os
import json
import pandas as pd
from pathlib import Path
from gerenciador_multi_uf import GerenciadorMultiUF

def main():
    print("🗺️ Script para Adicionar Nova UF")
    print("=" * 50)
    
    # Inicializar gerenciador
    gerenciador = GerenciadorMultiUF()
    
    # Listar UFs existentes
    print("\n📋 UFs já cadastradas:")
    ufs_existentes = gerenciador.obter_ufs_disponiveis()
    for uf in ufs_existentes:
        status_icon = "✅" if uf['status'] == 'ativo' else "⚠️"
        print(f"  {status_icon} {uf['codigo']} - {uf['nome']} ({uf['total_municipios']} municípios)")
    
    print("\n" + "=" * 50)
    
    # Solicitar informações da nova UF
    while True:
        codigo_uf = input("\n🏷️ Digite o código da UF (ex: SP, RJ, MG): ").strip().upper()
        
        if not codigo_uf:
            print("❌ Código da UF é obrigatório!")
            continue
        
        if len(codigo_uf) != 2:
            print("❌ Código da UF deve ter exatamente 2 caracteres!")
            continue
        
        if codigo_uf in [uf['codigo'] for uf in ufs_existentes]:
            print(f"❌ UF {codigo_uf} já existe no sistema!")
            continue
        
        break
    
    nome_uf = input(f"📍 Digite o nome completo da UF {codigo_uf}: ").strip()
    if not nome_uf:
        print("❌ Nome da UF é obrigatório!")
        return
    
    # Confirmar criação
    print(f"\n📝 Resumo da nova UF:")
    print(f"   Código: {codigo_uf}")
    print(f"   Nome: {nome_uf}")
    print(f"   Diretório: dados_ufs/{codigo_uf}/")
    
    confirmar = input("\n✅ Confirma a criação? (s/N): ").strip().lower()
    if confirmar not in ['s', 'sim', 'y', 'yes']:
        print("❌ Operação cancelada.")
        return
    
    # Criar UF
    print(f"\n🔄 Criando UF {codigo_uf}...")
    sucesso = gerenciador.adicionar_uf(codigo_uf, nome_uf)
    
    if sucesso:
        print(f"✅ UF {nome_uf} ({codigo_uf}) criada com sucesso!")
        
        # Mostrar próximos passos
        config_uf = gerenciador.ufs_disponiveis[codigo_uf]
        diretorio_uf = gerenciador.diretorio_base / config_uf.diretorio
        
        print(f"\n📁 Arquivos criados em: {diretorio_uf}")
        print(f"   📄 {config_uf.arquivo_dados} (dados dos municípios)")
        print(f"   🗺️ {config_uf.arquivo_geometrias} (geometrias GeoJSON)")
        print(f"   🎨 {config_uf.arquivo_cores} (cores das zonas)")
        print(f"   💾 alteracoes_zonas.json (histórico de alterações)")
        
        print(f"\n📋 PRÓXIMOS PASSOS:")
        print(f"1. Substitua o arquivo {config_uf.arquivo_dados} pelos dados reais da UF")
        print(f"2. Substitua o arquivo {config_uf.arquivo_geometrias} pelo GeoJSON real da UF")
        print(f"3. Ajuste as zonas e cores no arquivo {config_uf.arquivo_cores}")
        print(f"4. Execute o sistema multi-UF: python app_mapa_multi_uf.py")
        
        # Perguntar se quer criar arquivo de exemplo
        criar_exemplo = input(f"\n📝 Criar arquivo CSV de exemplo com estrutura correta? (s/N): ").strip().lower()
        if criar_exemplo in ['s', 'sim', 'y', 'yes']:
            criar_arquivo_exemplo(diretorio_uf, config_uf.arquivo_dados, codigo_uf, nome_uf)
        
    else:
        print(f"❌ Erro ao criar UF {codigo_uf}")

def criar_arquivo_exemplo(diretorio_uf, nome_arquivo, codigo_uf, nome_uf):
    """Cria arquivo CSV de exemplo com estrutura completa"""
    try:
        # Dados de exemplo mais completos
        dados_exemplo = {
            'UF': [codigo_uf] * 5,
            'Mesorregião Geográfica': [
                'Região Metropolitana',
                'Região Norte',
                'Região Sul',
                'Região Leste',
                'Região Oeste'
            ],
            'CD_Mun': [
                f'{codigo_uf}00001',
                f'{codigo_uf}00002', 
                f'{codigo_uf}00003',
                f'{codigo_uf}00004',
                f'{codigo_uf}00005'
            ],
            'Cidade': [
                f'Capital {nome_uf}',
                f'Município Norte',
                f'Município Sul',
                f'Município Leste',
                f'Município Oeste'
            ],
            'Zona': [
                'Zona Central',
                'Zona Norte',
                'Zona Sul',
                'Zona Leste',
                'Zona Oeste'
            ],
            'SELL OUT ANUAL': [150000, 80000, 120000, 90000, 70000],
            'SELL OUT MÊS': [12500, 6667, 10000, 7500, 5833],
            'POTENCIAL ANUAL': [200000, 100000, 150000, 110000, 90000],
            'POTENCIAL MÊS': [16667, 8333, 12500, 9167, 7500],
            'POPULAÇÃO ': [1500000, 300000, 450000, 350000, 250000],
            'PDV': [2500, 800, 1200, 900, 600],
            '%SHARE': [75.0, 80.0, 80.0, 81.8, 77.8]
        }
        
        df_exemplo = pd.DataFrame(dados_exemplo)
        arquivo_exemplo = diretorio_uf / nome_arquivo
        df_exemplo.to_csv(arquivo_exemplo, index=False)
        
        print(f"✅ Arquivo de exemplo criado: {arquivo_exemplo}")
        print(f"   📊 {len(df_exemplo)} municípios de exemplo")
        print(f"   📋 Colunas: {', '.join(df_exemplo.columns)}")
        
    except Exception as e:
        print(f"❌ Erro ao criar arquivo de exemplo: {e}")

def listar_ufs_sistema():
    """Lista todas as UFs do sistema com detalhes"""
    print("\n🗺️ Listagem Completa de UFs no Sistema")
    print("=" * 60)
    
    gerenciador = GerenciadorMultiUF()
    ufs = gerenciador.obter_ufs_disponiveis()
    
    if not ufs:
        print("❌ Nenhuma UF encontrada no sistema")
        return
    
    for uf in ufs:
        status_icon = "✅" if uf['status'] == 'ativo' else "⚠️"
        print(f"\n{status_icon} {uf['codigo']} - {uf['nome']}")
        print(f"   📊 Municípios: {uf['total_municipios']}")
        print(f"   📁 Status: {uf['status'].title()}")
        
        # Mostrar detalhes dos arquivos se UF estiver ativa
        if uf['status'] == 'ativo' and uf['codigo'] in gerenciador.ufs_disponiveis:
            config = gerenciador.ufs_disponiveis[uf['codigo']]
            diretorio = gerenciador.diretorio_base / config.diretorio
            print(f"   📂 Diretório: {diretorio}")
            
            # Verificar arquivos
            arquivos = [
                (config.arquivo_dados, "Dados"),
                (config.arquivo_geometrias, "Geometrias"),
                (config.arquivo_cores, "Cores"),
                ("alteracoes_zonas.json", "Alterações")
            ]
            
            for arquivo, descricao in arquivos:
                caminho = diretorio / arquivo
                if caminho.exists():
                    tamanho = caminho.stat().st_size
                    print(f"   ✅ {descricao}: {arquivo} ({tamanho:,} bytes)")
                else:
                    print(f"   ❌ {descricao}: {arquivo} (não encontrado)")

def verificar_estrutura_uf():
    """Verifica estrutura de uma UF específica"""
    print("\n🔍 Verificação de Estrutura de UF")
    print("=" * 40)
    
    gerenciador = GerenciadorMultiUF()
    ufs = gerenciador.obter_ufs_disponiveis()
    
    if not ufs:
        print("❌ Nenhuma UF encontrada no sistema")
        return
    
    print("UFs disponíveis:")
    for i, uf in enumerate(ufs, 1):
        print(f"  {i}. {uf['codigo']} - {uf['nome']}")
    
    try:
        escolha = int(input("\nEscolha uma UF (número): ")) - 1
        if 0 <= escolha < len(ufs):
            uf_escolhida = ufs[escolha]
            verificar_uf_detalhada(gerenciador, uf_escolhida['codigo'])
        else:
            print("❌ Escolha inválida")
    except ValueError:
        print("❌ Digite um número válido")

def verificar_uf_detalhada(gerenciador, codigo_uf):
    """Verifica estrutura detalhada de uma UF"""
    if codigo_uf not in gerenciador.ufs_disponiveis:
        print(f"❌ UF {codigo_uf} não encontrada")
        return
    
    config = gerenciador.ufs_disponiveis[codigo_uf]
    diretorio = gerenciador.diretorio_base / config.diretorio
    
    print(f"\n🔍 Verificando UF {config.nome} ({codigo_uf})")
    print(f"📂 Diretório: {diretorio}")
    
    # Verificar arquivo de dados
    arquivo_dados = diretorio / config.arquivo_dados
    print(f"\n📄 Arquivo de Dados: {config.arquivo_dados}")
    if arquivo_dados.exists():
        try:
            df = pd.read_csv(arquivo_dados)
            print(f"   ✅ Arquivo existe ({arquivo_dados.stat().st_size:,} bytes)")
            print(f"   📊 {len(df)} registros")
            print(f"   📋 Colunas: {', '.join(df.columns)}")
            
            # Verificar colunas essenciais
            colunas_essenciais = ['UF', 'CD_Mun', 'Cidade', 'Zona']
            colunas_faltantes = [col for col in colunas_essenciais if col not in df.columns]
            if colunas_faltantes:
                print(f"   ⚠️ Colunas essenciais faltantes: {', '.join(colunas_faltantes)}")
            else:
                print(f"   ✅ Todas as colunas essenciais presentes")
                
        except Exception as e:
            print(f"   ❌ Erro ao ler arquivo: {e}")
    else:
        print(f"   ❌ Arquivo não encontrado")
    
    # Verificar arquivo de geometrias
    arquivo_geo = diretorio / config.arquivo_geometrias
    print(f"\n🗺️ Arquivo de Geometrias: {config.arquivo_geometrias}")
    if arquivo_geo.exists():
        try:
            with open(arquivo_geo, 'r') as f:
                geo_data = json.load(f)
            print(f"   ✅ Arquivo existe ({arquivo_geo.stat().st_size:,} bytes)")
            if 'features' in geo_data:
                print(f"   🗺️ {len(geo_data['features'])} features")
            else:
                print(f"   ⚠️ Estrutura GeoJSON inválida")
        except Exception as e:
            print(f"   ❌ Erro ao ler arquivo: {e}")
    else:
        print(f"   ❌ Arquivo não encontrado")
    
    # Verificar arquivo de cores
    arquivo_cores = diretorio / config.arquivo_cores
    print(f"\n🎨 Arquivo de Cores: {config.arquivo_cores}")
    if arquivo_cores.exists():
        try:
            with open(arquivo_cores, 'r') as f:
                cores_data = json.load(f)
            print(f"   ✅ Arquivo existe ({arquivo_cores.stat().st_size:,} bytes)")
            print(f"   🎨 {len(cores_data)} zonas configuradas")
            for zona, cor in cores_data.items():
                print(f"      • {zona}: {cor}")
        except Exception as e:
            print(f"   ❌ Erro ao ler arquivo: {e}")
    else:
        print(f"   ❌ Arquivo não encontrado")

if __name__ == "__main__":
    print("🗺️ Utilitário de Gestão de UFs")
    print("=" * 40)
    print("1. Adicionar nova UF")
    print("2. Listar UFs do sistema")
    print("3. Verificar estrutura de UF")
    print("0. Sair")
    
    while True:
        try:
            opcao = input("\nEscolha uma opção: ").strip()
            
            if opcao == "1":
                main()
            elif opcao == "2":
                listar_ufs_sistema()
            elif opcao == "3":
                verificar_estrutura_uf()
            elif opcao == "0":
                print("👋 Até logo!")
                break
            else:
                print("❌ Opção inválida")
                
        except KeyboardInterrupt:
            print("\n👋 Até logo!")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")
