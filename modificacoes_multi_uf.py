#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODIFICAÇÕES PARA INTEGRAR MULTI-UF NO app_mapa_interativo.py

Este arquivo contém todas as modificações necessárias para adicionar
suporte a múltiplas UFs no sistema existente.

INSTRUÇÕES:
1. Adicione os imports no início do arquivo
2. Substitua a classe GerenciadorMapaInterativo
3. Adicione as novas rotas da API
4. Adicione os novos handlers WebSocket
"""

# ==========================================
# 1. IMPORTS ADICIONAIS (adicionar no início)
# ==========================================
import json
from pathlib import Path

# ==========================================
# 2. CLASSE MODIFICADA (substituir a existente)
# ==========================================

class GerenciadorMapaInterativo:
    def __init__(self):
        # Configuração multi-UF
        self.uf_atual = "PE"  # UF padrão
        self.ufs_disponiveis = {}
        self.diretorio_base = Path("dados_ufs")
        
        # Variáveis de dados
        self.dados_municipios = None
        self.geometrias = None
        self.zona_cores = None
        self.dados_completos = None
        
        # Carregar configuração das UFs
        self._carregar_configuracao_ufs()
        
        # Configurar caminhos para UF atual
        self._configurar_caminhos_uf()
        
        # Inicializar sistema de persistência
        self.persistencia = SistemaPersistencia(str(self.arquivo_alteracoes))
        
        # Carregar dados iniciais
        self.carregar_dados_iniciais()
    
    def _carregar_configuracao_ufs(self):
        """Carrega configuração das UFs disponíveis"""
        arquivo_config = self.diretorio_base / "configuracao_ufs.json"
        
        if arquivo_config.exists():
            with open(arquivo_config, 'r', encoding='utf-8') as f:
                self.ufs_disponiveis = json.load(f)
        else:
            print("❌ Arquivo de configuração de UFs não encontrado!")
            # Criar configuração mínima para PE
            self.ufs_disponiveis = {
                "PE": {
                    "codigo": "PE",
                    "nome": "Pernambuco",
                    "ativo": True,
                    "arquivo_dados": "dados_municipios.csv",
                    "arquivo_geometrias": "geometrias.json",
                    "arquivo_cores": "zona_cores.json",
                    "arquivo_alteracoes": "alteracoes.json",
                    "diretorio": "PE"
                }
            }
    
    def _configurar_caminhos_uf(self):
        """Configura caminhos dos arquivos para a UF atual"""
        if self.uf_atual not in self.ufs_disponiveis:
            print(f"❌ UF {self.uf_atual} não encontrada na configuração!")
            return
        
        config_uf = self.ufs_disponiveis[self.uf_atual]
        diretorio_uf = self.diretorio_base / config_uf["diretorio"]
        
        # Definir caminhos dos arquivos
        self.arquivo_dados = diretorio_uf / config_uf["arquivo_dados"]
        self.arquivo_geometrias = diretorio_uf / config_uf["arquivo_geometrias"] 
        self.arquivo_cores = diretorio_uf / config_uf["arquivo_cores"]
        self.arquivo_alteracoes = diretorio_uf / config_uf["arquivo_alteracoes"]
        
        print(f"📁 Caminhos configurados para UF {self.uf_atual}")
        print(f"   Dados: {self.arquivo_dados}")
        print(f"   Geometrias: {self.arquivo_geometrias}")
        print(f"   Cores: {self.arquivo_cores}")
        print(f"   Alterações: {self.arquivo_alteracoes}")
    
    def selecionar_uf(self, codigo_uf):
        """Seleciona uma UF para trabalhar"""
        try:
            if codigo_uf not in self.ufs_disponiveis:
                return False, f"UF {codigo_uf} não disponível"
            
            if not self.ufs_disponiveis[codigo_uf]["ativo"]:
                return False, f"UF {codigo_uf} não está ativa"
            
            print(f"🔄 Alterando UF de {self.uf_atual} para {codigo_uf}")
            
            # Alterar UF atual
            self.uf_atual = codigo_uf
            
            # Reconfigurar caminhos dos arquivos
            self._configurar_caminhos_uf()
            
            # Reconfigurar sistema de persistência
            self.persistencia = SistemaPersistencia(str(self.arquivo_alteracoes))
            
            # Recarregar dados
            self.carregar_dados_iniciais()
            
            config_uf = self.ufs_disponiveis[codigo_uf]
            return True, f"UF {config_uf['nome']} ({codigo_uf}) selecionada com sucesso"
            
        except Exception as e:
            print(f"❌ Erro ao selecionar UF {codigo_uf}: {e}")
            return False, f"Erro ao selecionar UF: {str(e)}"
    
    def obter_ufs_disponiveis(self):
        """Retorna lista de UFs disponíveis"""
        ufs_lista = []
        for codigo, config in self.ufs_disponiveis.items():
            # Verificar se arquivos existem
            diretorio_uf = self.diretorio_base / config["diretorio"]
            arquivo_dados = diretorio_uf / config["arquivo_dados"]
            arquivo_geometrias = diretorio_uf / config["arquivo_geometrias"]
            
            status = "ativo" if (arquivo_dados.exists() and arquivo_geometrias.exists()) else "incompleto"
            
            # Contar municípios se arquivo existe
            total_municipios = 0
            if arquivo_dados.exists():
                try:
                    import pandas as pd
                    df = pd.read_csv(arquivo_dados)
                    total_municipios = len(df)
                except:
                    total_municipios = 0
            
            ufs_lista.append({
                "codigo": codigo,
                "nome": config["nome"],
                "ativo": config["ativo"],
                "status": status,
                "total_municipios": total_municipios
            })
        
        return ufs_lista
    
    def obter_info_uf_atual(self):
        """Retorna informações da UF atual"""
        if self.uf_atual not in self.ufs_disponiveis:
            return None
        
        config = self.ufs_disponiveis[self.uf_atual]
        total_municipios = len(self.dados_municipios) if self.dados_municipios is not None else 0
        total_zonas = len(self.zona_cores) if self.zona_cores else 0
        
        return {
            "codigo": config["codigo"],
            "nome": config["nome"],
            "total_municipios": total_municipios,
            "total_zonas": total_zonas,
            "diretorio": str(self.diretorio_base / config["diretorio"])
        }
    
    def carregar_dados_iniciais(self):
        """Carrega todos os dados necessários da UF atual"""
        try:
            print(f"🔄 Carregando dados da UF {self.uf_atual}...")
            
            # Verificar se arquivos existem
            if not self.arquivo_dados.exists():
                print(f"❌ Arquivo de dados não encontrado: {self.arquivo_dados}")
                raise FileNotFoundError(f"Arquivo de dados não encontrado: {self.arquivo_dados}")
            
            if not self.arquivo_geometrias.exists():
                print(f"❌ Arquivo de geometrias não encontrado: {self.arquivo_geometrias}")
                raise FileNotFoundError(f"Arquivo de geometrias não encontrado: {self.arquivo_geometrias}")
            
            if not self.arquivo_cores.exists():
                print(f"❌ Arquivo de cores não encontrado: {self.arquivo_cores}")
                raise FileNotFoundError(f"Arquivo de cores não encontrado: {self.arquivo_cores}")
            
            # Carregar dados dos municípios
            self.dados_municipios = self._carregar_dados_com_fallback(str(self.arquivo_dados))
            print(f"✅ Dados carregados: {len(self.dados_municipios)} municípios")
            
            # Carregar geometrias
            self.geometrias = gpd.read_file(str(self.arquivo_geometrias))
            self.geometrias['id'] = self.geometrias['id'].astype(str)
            print(f"✅ Geometrias carregadas: {len(self.geometrias)} polígonos")
            
            # Carregar cores das zonas
            with open(str(self.arquivo_cores), 'r', encoding='utf-8') as f:
                self.zona_cores = json.load(f)
            print(f"✅ Cores carregadas: {len(self.zona_cores)} zonas")
            
            # Aplicar alterações salvas
            self._aplicar_alteracoes_salvas()
            
            # Verificar integridade dos dados
            self._verificar_integridade_dados()
            
            # Mesclar dados com geometrias
            self.preparar_dados_mapa()
            
            print(f"✅ UF {self.uf_atual} carregada com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao carregar dados da UF {self.uf_atual}: {e}")
            raise
    
    # MANTER TODOS OS OUTROS MÉTODOS EXISTENTES:
    # - _criar_arquivo_base_padrao
    # - _carregar_dados_com_fallback
    # - _aplicar_alteracoes_salvas
    # - _verificar_integridade_dados
    # - preparar_dados_mapa
    # - obter_dados_geojson
    # - alterar_zona_municipio
    # - obter_estatisticas
    # - alterar_cor_zona
    # (Copiar todos os métodos existentes que não foram modificados acima)

# ==========================================
# 3. NOVAS ROTAS DA API (adicionar no final)
# ==========================================

@app.route('/api/ufs_disponiveis')
def api_ufs_disponiveis():
    """API para obter UFs disponíveis"""
    try:
        ufs_lista = gerenciador.obter_ufs_disponiveis()
        uf_atual_info = gerenciador.obter_info_uf_atual()
        
        return jsonify({
            'sucesso': True,
            'ufs': ufs_lista,
            'uf_atual': uf_atual_info
        })
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        })

@app.route('/api/selecionar_uf/<codigo_uf>')
def api_selecionar_uf(codigo_uf):
    """API para selecionar uma UF"""
    try:
        sucesso, mensagem = gerenciador.selecionar_uf(codigo_uf.upper())
        
        response_data = {
            'sucesso': sucesso,
            'mensagem': mensagem
        }
        
        if sucesso:
            response_data['uf_atual'] = gerenciador.obter_info_uf_atual()
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        })

# ==========================================
# 4. NOVOS HANDLERS WEBSOCKET (adicionar no final)
# ==========================================

@socketio.on('selecionar_uf')
def handle_selecionar_uf(data):
    """Handler WebSocket para seleção de UF"""
    codigo_uf = data.get('codigo_uf', '').upper()
    
    try:
        print(f"🔄 Solicitação para selecionar UF: {codigo_uf}")
        
        sucesso, mensagem = gerenciador.selecionar_uf(codigo_uf)
        
        if sucesso:
            uf_info = gerenciador.obter_info_uf_atual()
            
            print(f"✅ UF {codigo_uf} selecionada via WebSocket")
            
            # Emitir para todos os clientes que a UF foi alterada
            socketio.emit('uf_alterada', {
                'sucesso': True,
                'uf_atual': codigo_uf,
                'uf_info': uf_info,
                'mensagem': mensagem
            })
            
            # Emitir dados atualizados do mapa
            geojson_data = gerenciador.obter_dados_geojson()
            socketio.emit('dados_mapa_atualizados', {
                'dados': geojson_data,
                'total_municipios': len(geojson_data['features'])
            })
            
            # Emitir zonas atualizadas
            socketio.emit('zonas_atualizadas', {
                'zonas': list(gerenciador.zona_cores.keys()),
                'cores': gerenciador.zona_cores
            })
            
            # Emitir estatísticas atualizadas
            stats = gerenciador.obter_estatisticas()
            socketio.emit('estatisticas_atualizadas', {
                'estatisticas': stats
            })
            
        else:
            print(f"❌ Erro ao selecionar UF {codigo_uf}: {mensagem}")
            emit('erro_selecao_uf', {
                'sucesso': False,
                'mensagem': mensagem
            })
            
    except Exception as e:
        print(f"❌ Erro no handler de seleção de UF: {e}")
        emit('erro_selecao_uf', {
            'sucesso': False,
            'mensagem': f'Erro interno: {str(e)}'
        })

@socketio.on('obter_ufs_disponiveis')
def handle_obter_ufs_disponiveis():
    """Handler WebSocket para obter UFs disponíveis"""
    try:
        ufs_lista = gerenciador.obter_ufs_disponiveis()
        uf_atual_info = gerenciador.obter_info_uf_atual()
        
        emit('ufs_disponiveis', {
            'sucesso': True,
            'ufs': ufs_lista,
            'uf_atual': uf_atual_info
        })
        
    except Exception as e:
        emit('erro_ufs', {
            'sucesso': False,
            'mensagem': f'Erro ao obter UFs: {str(e)}'
        })

# ==========================================
# INSTRUÇÕES DE APLICAÇÃO
# ==========================================
"""
COMO APLICAR AS MODIFICAÇÕES:

1. IMPORTS:
   - Adicione "from pathlib import Path" no início do arquivo

2. CLASSE:
   - Substitua toda a classe GerenciadorMapaInterativo pela versão acima
   - Mantenha todos os métodos existentes que não foram modificados

3. ROTAS:
   - Adicione as novas rotas da API no final do arquivo, antes do "if __name__ == '__main__'"

4. WEBSOCKET:
   - Adicione os novos handlers WebSocket no final do arquivo

5. TESTE:
   - Execute: python app_mapa_interativo.py
   - Acesse: http://localhost:5001
   - Verifique se PE carrega normalmente
   - Teste as novas APIs:
     - GET /api/ufs_disponiveis
     - GET /api/selecionar_uf/AL
"""
