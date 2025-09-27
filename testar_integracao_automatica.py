#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da integração automática da extensão Multi-UF
"""

import requests
import time

def testar_integracao_automatica():
    """
    Testa se a integração automática da extensão Multi-UF funcionou
    """
    print("🧪 TESTE DA INTEGRAÇÃO AUTOMÁTICA MULTI-UF")
    print("=" * 60)
    
    base_url = "http://localhost:5001"
    
    try:
        # Aguardar um pouco para o servidor inicializar
        print("⏳ Aguardando inicialização do servidor...")
        time.sleep(3)
        
        # 1. Testar API de UFs disponíveis
        print("1️⃣ Testando API de UFs disponíveis...")
        
        response = requests.get(f"{base_url}/api/ufs_disponiveis", timeout=10)
        if response.status_code == 200:
            dados = response.json()
            
            print(f"   📋 Resposta da API:")
            print(f"      • Sucesso: {dados.get('sucesso')}")
            print(f"      • Modo Multi-UF: {dados.get('modo_multi_uf')}")
            print(f"      • UF Atual: {dados.get('uf_atual')}")
            
            ufs = dados.get('ufs', [])
            print(f"      • UFs Disponíveis: {len(ufs)}")
            
            for uf in ufs:
                print(f"         - {uf.get('codigo')}: {uf.get('nome')}")
            
            if len(ufs) >= 3:
                print("   ✅ Extensão Multi-UF carregada com sucesso!")
                print("   ✅ Todas as UFs estão disponíveis")
                return True
            else:
                print(f"   ❌ Apenas {len(ufs)} UFs disponíveis (esperado: 3)")
                return False
                
        else:
            print(f"   ❌ Erro na API: {response.status_code}")
            
            # Tentar verificar se a rota existe
            try:
                response_404 = requests.get(f"{base_url}/api/ufs_disponiveis")
                if response_404.status_code == 404:
                    print("   ❌ Rota /api/ufs_disponiveis não encontrada")
                    print("   ❌ Extensão Multi-UF NÃO foi carregada")
            except:
                pass
                
            return False
        
    except requests.exceptions.ConnectionError:
        print("   ❌ Não foi possível conectar ao servidor")
        print("   💡 Execute: python app_mapa_interativo.py")
        return False
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        return False

def instrucoes_teste_completo():
    """
    Instruções para teste completo
    """
    print(f"\n" + "=" * 60)
    print("📋 INSTRUÇÕES PARA TESTE COMPLETO")
    print("=" * 60)
    
    print("🚀 COMO TESTAR A CORREÇÃO:")
    
    print(f"\n1️⃣ Parar servidor atual (se estiver rodando):")
    print("   • Pressione Ctrl+C no terminal do servidor")
    
    print(f"\n2️⃣ Iniciar com integração automática:")
    print("   python app_mapa_interativo.py")
    
    print(f"\n3️⃣ Observar mensagens de inicialização:")
    print("   ✅ Deve aparecer:")
    print("      • ✅ Extensão Multi-UF carregada automaticamente!")
    print("      • 🗺️ UFs disponíveis: ['AL', 'PE', 'SE']")
    print("      • 🗺️ Mapa interativo com sistema Multi-UF integrado")
    
    print(f"\n4️⃣ Testar interface:")
    print("   • Acesse: http://localhost:5001")
    print("   • Clique no seletor de UF")
    print("   • Deve mostrar 3 opções: AL, PE, SE")
    
    print(f"\n5️⃣ Testar funcionalidade:")
    print("   • Selecione AL (Alagoas)")
    print("   • Mapa deve mudar para Alagoas")
    print("   • Estatísticas devem atualizar")
    print("   • Teste download multi-UF")

def comparar_metodos():
    """
    Compara os diferentes métodos de execução
    """
    print(f"\n" + "=" * 60)
    print("🔄 COMPARAÇÃO DOS MÉTODOS DE EXECUÇÃO")
    print("=" * 60)
    
    print("📊 MÉTODOS DISPONÍVEIS:")
    
    print(f"\n1️⃣ python app_mapa_interativo.py (NOVO - RECOMENDADO)")
    print("   ✅ Extensão Multi-UF carregada automaticamente")
    print("   ✅ Seletor com 3 UFs (PE, AL, SE)")
    print("   ✅ Compatível com deploy (Procfile atual)")
    print("   ✅ Funciona independentemente")
    
    print(f"\n2️⃣ python inicializar_multi_uf.py (ANTIGO)")
    print("   ✅ Extensão Multi-UF carregada manualmente")
    print("   ✅ Seletor com 3 UFs (PE, AL, SE)")
    print("   ⚠️ Requer arquivo separado")
    print("   ⚠️ Mais complexo para deploy")
    
    print(f"\n3️⃣ python app_mapa_multi_uf.py (ALTERNATIVO)")
    print("   ✅ Sistema Multi-UF nativo")
    print("   ✅ Seletor com 3 UFs (PE, AL, SE)")
    print("   ❌ Requer mudança no Procfile")
    print("   ❌ Sem fallback automático")
    
    print(f"\n🎯 RECOMENDAÇÃO FINAL:")
    print("   Use: python app_mapa_interativo.py")
    print("   • Melhor compatibilidade")
    print("   • Deploy sem mudanças")
    print("   • Funcionalidade completa")

if __name__ == "__main__":
    print("🚀 TESTE DA INTEGRAÇÃO AUTOMÁTICA MULTI-UF")
    
    sucesso = testar_integracao_automatica()
    instrucoes_teste_completo()
    comparar_metodos()
    
    if sucesso:
        print(f"\n🎯 INTEGRAÇÃO AUTOMÁTICA FUNCIONANDO!")
        print("   Agora o app_mapa_interativo.py tem Multi-UF completo")
        print("   Pronto para deploy sem mudanças no Procfile")
    else:
        print(f"\n❌ PROBLEMAS NA INTEGRAÇÃO")
        print("   Verificar se o servidor está rodando com as correções")
