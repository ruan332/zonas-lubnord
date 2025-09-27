#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para inicializar o sistema principal com extensão Multi-UF
Executa o app_mapa_interativo.py com funcionalidades multi-UF adicionadas
"""

import sys
import os

# Adicionar o diretório atual ao path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def inicializar_sistema_com_multi_uf():
    """
    Inicializa o sistema principal com a extensão Multi-UF
    """
    try:
        print("🚀 Inicializando Sistema de Mapa Interativo com Multi-UF...")
        
        # Importar componentes do sistema principal
        from app_mapa_interativo import app, socketio, gerenciador
        from extensao_multi_uf import inicializar_extensao_multi_uf
        
        # Inicializar extensão Multi-UF
        extensao = inicializar_extensao_multi_uf(app, socketio, gerenciador)
        
        if extensao:
            print("✅ Sistema Multi-UF integrado com sucesso!")
            
            # Listar UFs disponíveis
            try:
                from gerenciador_ufs import gerenciador_ufs
                ufs_disponiveis = gerenciador_ufs.listar_ufs_ativas()
                print(f"🗺️  UFs disponíveis: {[uf['codigo'] for uf in ufs_disponiveis]}")
                
                # Verificar se Alagoas está disponível
                alagoas_disponivel = any(uf['codigo'] == 'AL' for uf in ufs_disponiveis)
                if alagoas_disponivel:
                    print("✅ Alagoas está configurado e disponível!")
                else:
                    print("⚠️ Alagoas não está disponível no sistema")
                    
            except Exception as e:
                print(f"⚠️ Erro ao verificar UFs: {e}")
            
            return app, socketio, gerenciador, extensao
        else:
            print("❌ Falha ao integrar sistema Multi-UF")
            return app, socketio, gerenciador, None
            
    except Exception as e:
        print(f"❌ Erro ao inicializar sistema: {e}")
        raise

def executar_servidor():
    """
    Executa o servidor com Multi-UF
    """
    try:
        # Inicializar sistema
        app, socketio, gerenciador, extensao = inicializar_sistema_com_multi_uf()
        
        # Configurações do servidor
        from dotenv import load_dotenv
        load_dotenv()
        
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 5001))
        debug = os.getenv('FLASK_ENV', 'production') != 'production'
        
        print(f"\n🌍 Servidor Multi-UF iniciando...")
        print(f"📍 Endereço: http://{host}:{port}")
        print(f"🔧 Modo: {'Desenvolvimento' if debug else 'Produção'}")
        print(f"🗺️ Sistema: Mapa Interativo Multi-UF")
        
        if extensao:
            print(f"✅ Extensão Multi-UF: Ativa")
        else:
            print(f"⚠️ Extensão Multi-UF: Inativa (modo tradicional)")
        
        print(f"\n🚀 Acesse: http://localhost:{port}")
        print("📱 Interface com seletor de UF disponível!")
        
        # Executar servidor
        socketio.run(app, host=host, port=port, debug=debug)
        
    except KeyboardInterrupt:
        print("\n🛑 Servidor interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao executar servidor: {e}")
        raise

if __name__ == '__main__':
    executar_servidor()
