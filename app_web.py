from flask import Flask, render_template, jsonify, request, send_file
import pandas as pd
import json
import os
import shutil
from datetime import datetime
from sistema_persistencia import SistemaPersistencia
from analise_cenarios import AnalisadorCenarios
from mapa_interativo_pernambuco import MapaInterativoPernambuco

app = Flask(__name__)

class GerenciadorZonas:
    def __init__(self):
        self.arquivo_dados = "dados_mapa_pernambuco.csv"
        self.arquivo_cores = "zona_cores_mapping.json"
        self.dados_originais = None
        self.dados_atuais = None
        self.cores_zonas = None
        self.historico_alteracoes = []
        
        # Inicializar sistema de persistência
        self.persistencia = SistemaPersistencia()
        self.analisador = AnalisadorCenarios()
        
        self.carregar_dados_iniciais()
    
    def carregar_dados_iniciais(self):
        """Carrega os dados iniciais"""
        self.dados_originais = pd.read_csv('dados_mapa_pernambuco.csv')
        self.dados_atuais = self.dados_originais.copy()
        
        with open('zona_cores_mapping.json', 'r', encoding='utf-8') as f:
            self.zona_cores = json.load(f)
    
    def obter_municipios(self):
        """Retorna lista de municípios com suas zonas atuais"""
        return self.dados_atuais[['CD_Mun', 'Cidade', 'Zona', 'Cor', 'UF', 'Mesorregião Geográfica']].to_dict('records')
    
    def obter_zonas_disponiveis(self):
        """Retorna lista de zonas disponíveis"""
        return list(self.zona_cores.keys())
    
    def alterar_zona_municipio(self, cd_mun, nova_zona):
        """Altera a zona de um município"""
        try:
            # Verificar se o município existe
            if cd_mun not in self.dados_atuais['CD_Mun'].astype(str).values:
                return False, "Município não encontrado"
            
            # Verificar se a zona existe
            if nova_zona not in self.zona_cores:
                return False, "Zona não encontrada"
            
            # Obter dados atuais do município
            idx = self.dados_atuais[self.dados_atuais['CD_Mun'].astype(str) == str(cd_mun)].index[0]
            zona_anterior = self.dados_atuais.loc[idx, 'Zona']
            cidade = self.dados_atuais.loc[idx, 'Cidade']
            
            # Verificar se a zona realmente mudou
            if zona_anterior == nova_zona:
                return False, "A zona já é a mesma"
            
            # Alterar zona
            self.dados_atuais.loc[idx, 'Zona'] = nova_zona
            self.dados_atuais.loc[idx, 'Cor'] = self.zona_cores[nova_zona]
            
            # Salvar alteração no sistema de persistência
            sucesso = self.persistencia.salvar_alteracao(
                cd_mun=cd_mun,
                cidade=cidade,
                zona_anterior=zona_anterior,
                zona_nova=nova_zona,
                usuario="WebInterface"
            )
            
            if sucesso:
                # Aplicar alterações aos dados
                self.persistencia.aplicar_alteracoes_aos_dados()
                
                # Registrar alteração no histórico
                alteracao = {
                    'timestamp': datetime.now().isoformat(),
                    'cd_mun': cd_mun,
                    'cidade': cidade,
                    'zona_anterior': zona_anterior,
                    'zona_nova': nova_zona,
                    'tipo': 'alteracao_zona'
                }
                self.historico_alteracoes.append(alteracao)
                
                return True, "Zona alterada com sucesso"
            else:
                return False, "Erro ao salvar alteração"
            
        except Exception as e:
            return False, f"Erro ao alterar zona: {str(e)}"
    
    def salvar_alteracoes(self, nome_arquivo=None):
        """Salva todas as alterações permanentemente"""
        try:
            # Aplicar alterações aos dados
            sucesso = self.persistencia.aplicar_alteracoes_aos_dados()
            
            if sucesso:
                # Criar backup
                backup_path = self.persistencia.criar_backup()
                
                # Se nome_arquivo foi especificado, também salvar nesse arquivo
                if nome_arquivo:
                    self.dados_atuais.to_csv(nome_arquivo, index=False, encoding='utf-8')
                    nome_historico = nome_arquivo.replace('.csv', '_historico.json')
                    with open(nome_historico, 'w', encoding='utf-8') as f:
                        json.dump(self.historico_alteracoes, f, ensure_ascii=False, indent=2)
                    return nome_arquivo, nome_historico
                else:
                    return True, f"Alterações salvas com sucesso. Backup criado em: {backup_path}"
            else:
                return False, "Erro ao aplicar alterações"
                
        except Exception as e:
            return False, f"Erro ao salvar: {str(e)}"
    
    def carregar_alteracoes(self, nome_arquivo=None):
        """Carrega alterações do sistema de persistência ou de arquivo"""
        try:
            if nome_arquivo:
                self.dados_atuais = pd.read_csv(nome_arquivo)
                return True, "Alterações carregadas com sucesso"
            else:
                alteracoes_data = self.persistencia.carregar_alteracoes()
                return alteracoes_data.get("alteracoes", [])
        except Exception as e:
            if nome_arquivo:
                return False, f"Erro ao carregar alterações: {str(e)}"
            else:
                print(f"Erro ao carregar alterações: {e}")
                return []
    
    def resetar_dados(self):
        """Reseta todos os dados para o estado original"""
        try:
            sucesso = self.persistencia.resetar_alteracoes()
            
            if sucesso:
                # Recarregar dados originais
                self.carregar_dados_iniciais()
                self.historico_alteracoes = []
                return True, "Dados resetados com sucesso"
            else:
                return False, "Erro ao resetar dados"
                
        except Exception as e:
            return False, f"Erro ao resetar: {str(e)}"
    
    def obter_estatisticas(self):
        """Retorna estatísticas das zonas"""
        stats = self.dados_atuais.groupby('Zona').size().to_dict()
        total = len(self.dados_atuais)
        
        estatisticas = []
        for zona, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            estatisticas.append({
                'zona': zona,
                'municipios': count,
                'percentual': round((count / total) * 100, 1),
                'cor': self.zona_cores.get(zona, '#CCCCCC')
            })
        
        return estatisticas

# Instância global do gerenciador
gerenciador = GerenciadorZonas()

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/municipios')
def api_municipios():
    """API para obter lista de municípios"""
    municipios = gerenciador.obter_municipios()
    return jsonify(municipios)

@app.route('/api/zonas')
def api_zonas():
    """API para obter zonas disponíveis"""
    zonas = gerenciador.obter_zonas_disponiveis()
    return jsonify(zonas)

@app.route('/api/alterar_zona', methods=['POST'])
def api_alterar_zona():
    """API para alterar zona de município"""
    data = request.get_json()
    cd_mun = data.get('cd_mun')
    nova_zona = data.get('nova_zona')
    
    sucesso, mensagem = gerenciador.alterar_zona_municipio(cd_mun, nova_zona)
    
    return jsonify({
        'sucesso': sucesso,
        'mensagem': mensagem
    })

@app.route('/api/estatisticas')
def api_estatisticas():
    """API para obter estatísticas"""
    stats = gerenciador.obter_estatisticas()
    return jsonify(stats)

@app.route('/api/historico')
def api_historico():
    """API para obter histórico de alterações"""
    return jsonify(gerenciador.historico_alteracoes)

@app.route('/api/salvar', methods=['POST'])
def api_salvar():
    """API para salvar alterações"""
    try:
        arquivo_dados, arquivo_historico = gerenciador.salvar_alteracoes()
        return jsonify({
            'sucesso': True,
            'mensagem': 'Alterações salvas com sucesso',
            'arquivo_dados': arquivo_dados,
            'arquivo_historico': arquivo_historico
        })
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao salvar: {str(e)}'
        })

@app.route('/api/resetar', methods=['POST'])
def api_resetar():
    """API para resetar dados"""
    sucesso, mensagem = gerenciador.resetar_dados()
    return jsonify({
        'sucesso': sucesso,
        'mensagem': mensagem
    })

@app.route('/api/gerar_mapa', methods=['POST'])
def api_gerar_mapa():
    """API para gerar novo mapa com alterações"""
    try:
        # Aplicar alterações aos dados e salvar como dados atuais
        gerenciador.persistencia.aplicar_alteracoes_aos_dados()
        
        # Criar timestamp para o nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Criar instância do gerador de mapas
        gerador = MapaInterativoPernambuco()
        
        # Substituir temporariamente o arquivo que o gerador lê
        arquivo_principal = 'pernambuco_dados_gerar_mapa.csv'
        arquivo_atual = 'dados_mapa_atual.csv'
        
        # Fazer backup do arquivo principal
        if os.path.exists(arquivo_principal):
            os.rename(arquivo_principal, f"{arquivo_principal}.backup_{timestamp}")
        
        # Copiar dados atuais para o arquivo que o gerador espera
        if os.path.exists(arquivo_atual):
            shutil.copy2(arquivo_atual, arquivo_principal)
        else:
            # Se não existe dados_mapa_atual.csv, usar os dados em memória
            gerenciador.dados_atuais.to_csv(arquivo_principal, index=False, encoding='utf-8')
        
        # Gerar mapa
        nome_mapa = f"mapa_editado_{timestamp}.html"
        gerador.gerar_mapa_completo(nome_mapa)
        
        # Restaurar arquivo principal
        if os.path.exists(f"{arquivo_principal}.backup_{timestamp}"):
            os.remove(arquivo_principal)
            os.rename(f"{arquivo_principal}.backup_{timestamp}", arquivo_principal)
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Mapa gerado com sucesso',
            'arquivo_mapa': nome_mapa,
            'timestamp': timestamp
        })
        
    except Exception as e:
        # Tentar restaurar backup em caso de erro
        try:
            arquivo_principal = 'pernambuco_dados_gerar_mapa.csv'
            backup_file = f"{arquivo_principal}.backup_{timestamp}"
            if os.path.exists(backup_file):
                if os.path.exists(arquivo_principal):
                    os.remove(arquivo_principal)
                os.rename(backup_file, arquivo_principal)
        except:
            pass
            
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao gerar mapa: {str(e)}'
        })

@app.route('/mapa/<nome_arquivo>')
def visualizar_mapa(nome_arquivo):
    """Serve arquivos de mapa"""
    try:
        return send_file(nome_arquivo)
    except:
        return "Arquivo não encontrado", 404

# Novos endpoints para funcionalidades de persistência
@app.route('/api/backups')
def listar_backups():
    """Lista todos os backups disponíveis"""
    try:
        backups = gerenciador.persistencia.listar_backups()
        return jsonify({
            'success': True,
            'backups': backups
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/backup/criar', methods=['POST'])
def criar_backup():
    """Cria um novo backup"""
    try:
        data = request.get_json()
        nome_backup = data.get('nome_backup')
        
        backup_path = gerenciador.persistencia.criar_backup(nome_backup)
        
        return jsonify({
            'success': True,
            'message': 'Backup criado com sucesso',
            'backup_path': backup_path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/backup/restaurar', methods=['POST'])
def restaurar_backup():
    """Restaura um backup específico"""
    try:
        data = request.get_json()
        nome_backup = data.get('nome_backup')
        
        if not nome_backup:
            return jsonify({
                'success': False,
                'error': 'Nome do backup é obrigatório'
            }), 400
        
        sucesso = gerenciador.persistencia.restaurar_backup(nome_backup)
        
        if sucesso:
            # Recarregar dados após restaurar
            gerenciador.carregar_dados()
            
            return jsonify({
                'success': True,
                'message': 'Backup restaurado com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao restaurar backup'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/relatorio/exportar')
def exportar_relatorio():
    """Exporta relatório das alterações"""
    try:
        formato = request.args.get('formato', 'json')
        arquivo_relatorio = gerenciador.persistencia.exportar_relatorio(formato)
        
        return send_file(
            arquivo_relatorio,
            as_attachment=True,
            download_name=arquivo_relatorio
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/alteracoes/completas')
def obter_alteracoes_completas():
    """Obtém todas as alterações com estatísticas"""
    try:
        alteracoes_data = gerenciador.persistencia.carregar_alteracoes()
        
        return jsonify({
            'success': True,
            'data': alteracoes_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Rotas para análise de cenários
@app.route('/api/cenarios', methods=['GET'])
def listar_cenarios():
    """Lista todos os cenários disponíveis"""
    try:
        cenarios = gerenciador.analisador.listar_cenarios()
        return jsonify({'success': True, 'cenarios': cenarios})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cenarios', methods=['POST'])
def criar_cenario():
    """Cria um novo cenário"""
    try:
        data = request.get_json()
        nome = data.get('nome')
        descricao = data.get('descricao', '')
        tipo = data.get('tipo', 'atual')  # 'atual' ou 'original'
        
        if not nome:
            return jsonify({'success': False, 'error': 'Nome do cenário é obrigatório'})
        
        # Escolher dados base
        if tipo == 'original':
            dados_base = gerenciador.dados_originais
        else:
            dados_base = gerenciador.dados_atuais
        
        sucesso = gerenciador.analisador.criar_cenario(nome, dados_base, descricao)
        
        if sucesso:
            return jsonify({'success': True, 'message': f'Cenário "{nome}" criado com sucesso'})
        else:
            return jsonify({'success': False, 'error': 'Erro ao criar cenário'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cenarios/<nome_cenario>', methods=['DELETE'])
def remover_cenario(nome_cenario):
    """Remove um cenário"""
    try:
        sucesso = gerenciador.analisador.remover_cenario(nome_cenario)
        
        if sucesso:
            return jsonify({'success': True, 'message': f'Cenário "{nome_cenario}" removido'})
        else:
            return jsonify({'success': False, 'error': 'Cenário não encontrado'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cenarios/<nome_cenario>/relatorio', methods=['GET'])
def gerar_relatorio_cenario(nome_cenario):
    """Gera relatório detalhado de um cenário"""
    try:
        relatorio = gerenciador.analisador.gerar_relatorio_cenario(nome_cenario)
        return jsonify({'success': True, 'relatorio': relatorio})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cenarios/comparar', methods=['POST'])
def comparar_cenarios():
    """Compara dois cenários"""
    try:
        data = request.get_json()
        cenario1 = data.get('cenario1')
        cenario2 = data.get('cenario2')
        
        if not cenario1 or not cenario2:
            return jsonify({'success': False, 'error': 'Dois cenários são necessários para comparação'})
        
        comparacao = gerenciador.analisador.comparar_cenarios(cenario1, cenario2)
        return jsonify({'success': True, 'comparacao': comparacao})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cenarios/<nome_cenario>/exportar', methods=['GET'])
def exportar_cenario(nome_cenario):
    """Exporta um cenário"""
    try:
        formato = request.args.get('formato', 'csv')
        arquivo = gerenciador.analisador.exportar_cenario(nome_cenario, formato)
        
        if arquivo and os.path.exists(arquivo):
            return send_file(arquivo, as_attachment=True)
        else:
            return jsonify({'success': False, 'error': 'Erro ao exportar cenário'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("🚀 Iniciando aplicação web...")
    print("📍 Acesse: http://localhost:5000")
    print("🗺️  Interface de edição de zonas disponível")
    app.run(debug=True, host='0.0.0.0', port=5000)