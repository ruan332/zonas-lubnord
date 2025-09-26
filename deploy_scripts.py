#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scripts de Deploy e Configuração
Utilitários para preparar e verificar o ambiente de produção
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def verificar_arquivos_deploy():
    """Verifica se todos os arquivos necessários para deploy estão presentes"""
    arquivos_necessarios = [
        'requirements.txt',
        'Procfile',
        'railway.json',
        '.env.example',
        '.gitignore',
        'runtime.txt',
        'app_mapa_interativo.py',
        'sistema_persistencia.py',
        'pernambuco_dados_gerar_mapa.csv',
        'pernambuco.json',
        'zona_cores_mapping.json',
        'templates/mapa_interativo.html'
    ]
    
    print("🔍 Verificando arquivos necessários para deploy...")
    
    arquivos_faltando = []
    for arquivo in arquivos_necessarios:
        if not Path(arquivo).exists():
            arquivos_faltando.append(arquivo)
            print(f"❌ {arquivo} - FALTANDO")
        else:
            print(f"✅ {arquivo} - OK")
    
    if arquivos_faltando:
        print(f"\n⚠️  {len(arquivos_faltando)} arquivo(s) faltando!")
        return False
    else:
        print("\n🎉 Todos os arquivos necessários estão presentes!")
        return True

def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    print("\n📦 Verificando dependências...")
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().splitlines()
        
        dependencias_faltando = []
        for req in requirements:
            if req.strip() and not req.startswith('#'):
                package = req.split('==')[0].split('>=')[0].split('<=')[0]
                try:
                    __import__(package.replace('-', '_'))
                    print(f"✅ {package} - OK")
                except ImportError:
                    dependencias_faltando.append(package)
                    print(f"❌ {package} - FALTANDO")
        
        if dependencias_faltando:
            print(f"\n⚠️  {len(dependencias_faltando)} dependência(s) faltando!")
            print("Execute: pip install -r requirements.txt")
            return False
        else:
            print("\n🎉 Todas as dependências estão instaladas!")
            return True
            
    except FileNotFoundError:
        print("❌ Arquivo requirements.txt não encontrado!")
        return False

def verificar_configuracao():
    """Verifica configurações do projeto"""
    print("\n⚙️  Verificando configurações...")
    
    # Verificar se o arquivo principal existe e está configurado
    if not Path('app_mapa_interativo.py').exists():
        print("❌ app_mapa_interativo.py não encontrado!")
        return False
    
    # Verificar se os dados essenciais existem
    dados_essenciais = [
        'pernambuco_dados_gerar_mapa.csv',
        'pernambuco.json',
        'zona_cores_mapping.json'
    ]
    
    for arquivo in dados_essenciais:
        if not Path(arquivo).exists():
            print(f"❌ Arquivo de dados {arquivo} não encontrado!")
            return False
        else:
            print(f"✅ {arquivo} - OK")
    
    # Verificar estrutura de pastas
    pastas_necessarias = ['templates', 'backups', 'historico']
    for pasta in pastas_necessarias:
        if not Path(pasta).exists():
            print(f"⚠️  Pasta {pasta} não existe, criando...")
            Path(pasta).mkdir(exist_ok=True)
        print(f"✅ Pasta {pasta} - OK")
    
    print("\n🎉 Configurações verificadas com sucesso!")
    return True

def gerar_env_producao():
    """Gera arquivo .env para produção baseado no .env.example"""
    print("\n🔧 Gerando configurações de produção...")
    
    if not Path('.env.example').exists():
        print("❌ Arquivo .env.example não encontrado!")
        return False
    
    if Path('.env').exists():
        resposta = input("Arquivo .env já existe. Sobrescrever? (s/N): ")
        if resposta.lower() != 's':
            print("Operação cancelada.")
            return False
    
    # Ler template
    with open('.env.example', 'r') as f:
        template = f.read()
    
    # Substituir valores para produção
    env_producao = template.replace('FLASK_ENV=production', 'FLASK_ENV=production')
    env_producao = env_producao.replace('DEBUG=False', 'DEBUG=False')
    env_producao = env_producao.replace('SECRET_KEY=mapa_interativo_2025_production_key_change_this', 
                                       f'SECRET_KEY=mapa_interativo_2025_prod_{os.urandom(16).hex()}')
    
    # Salvar arquivo .env
    with open('.env', 'w') as f:
        f.write(env_producao)
    
    print("✅ Arquivo .env criado com configurações de produção!")
    print("⚠️  IMPORTANTE: Adicione o .env ao .gitignore para não commitá-lo!")
    return True

def testar_aplicacao_local():
    """Testa a aplicação localmente antes do deploy"""
    print("\n🧪 Testando aplicação localmente...")
    
    try:
        # Importar e testar módulos principais
        from app_mapa_interativo import app, gerenciador
        from sistema_persistencia import SistemaPersistencia
        
        print("✅ Importações principais - OK")
        
        # Testar carregamento de dados
        if hasattr(gerenciador, 'dados_municipios') and len(gerenciador.dados_municipios) > 0:
            print(f"✅ Dados carregados - {len(gerenciador.dados_municipios)} municípios")
        else:
            print("❌ Erro no carregamento de dados")
            return False
        
        # Testar configuração Flask
        if app.config.get('SECRET_KEY'):
            print("✅ Configuração Flask - OK")
        else:
            print("❌ Configuração Flask incompleta")
            return False
        
        print("\n🎉 Aplicação testada com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar aplicação: {e}")
        return False

def executar_verificacao_completa():
    """Executa verificação completa do projeto"""
    print("🚀 VERIFICAÇÃO COMPLETA PARA DEPLOY NA RAILWAY")
    print("=" * 50)
    
    verificacoes = [
        ("Arquivos de Deploy", verificar_arquivos_deploy),
        ("Dependências Python", verificar_dependencias),
        ("Configurações", verificar_configuracao),
        ("Teste da Aplicação", testar_aplicacao_local)
    ]
    
    resultados = []
    for nome, funcao in verificacoes:
        print(f"\n{'='*20} {nome} {'='*20}")
        resultado = funcao()
        resultados.append((nome, resultado))
    
    print("\n" + "="*50)
    print("📊 RESUMO DA VERIFICAÇÃO")
    print("="*50)
    
    sucesso_total = True
    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"{nome}: {status}")
        if not resultado:
            sucesso_total = False
    
    if sucesso_total:
        print("\n🎉 PROJETO PRONTO PARA DEPLOY!")
        print("\n📋 Próximos passos:")
        print("1. Commit e push para o GitHub")
        print("2. Conectar repositório na Railway")
        print("3. Configurar variáveis de ambiente")
        print("4. Fazer deploy!")
    else:
        print("\n⚠️  CORRIJA OS PROBLEMAS ANTES DO DEPLOY")
        print("\nConsulte o README_DEPLOY.md para mais informações.")
    
    return sucesso_total

if __name__ == "__main__":
    if len(sys.argv) > 1:
        comando = sys.argv[1]
        if comando == "verificar":
            executar_verificacao_completa()
        elif comando == "env":
            gerar_env_producao()
        elif comando == "test":
            testar_aplicacao_local()
        else:
            print("Comandos disponíveis: verificar, env, test")
    else:
        executar_verificacao_completa()