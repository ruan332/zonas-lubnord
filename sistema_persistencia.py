"""
Sistema de Persistência para Alterações de Zonas
Gerencia salvamento, carregamento e histórico de alterações
"""

import json
import pandas as pd
from datetime import datetime
import os
import shutil
from typing import Dict, List, Any, Optional

class SistemaPersistencia:
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.historico_dir = os.path.join(base_dir, "historico")
        self.backup_dir = os.path.join(base_dir, "backups")
        self.alteracoes_file = os.path.join(base_dir, "alteracoes_zonas.json")
        self.dados_originais = os.path.join(base_dir, "dados_mapa_pernambuco.csv")
        self.dados_atuais = os.path.join(base_dir, "dados_mapa_atual.csv")
        
        # Criar diretórios se não existirem
        os.makedirs(self.historico_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Inicializar arquivo de alterações se não existir
        if not os.path.exists(self.alteracoes_file):
            self._inicializar_alteracoes()
    
    def _inicializar_alteracoes(self):
        """Inicializa o arquivo de alterações"""
        alteracoes_iniciais = {
            "versao": "1.0",
            "criado_em": datetime.now().isoformat(),
            "ultima_atualizacao": datetime.now().isoformat(),
            "alteracoes": [],
            "estatisticas": {
                "total_alteracoes": 0,
                "municipios_alterados": 0,
                "zonas_modificadas": []
            }
        }
        
        with open(self.alteracoes_file, 'w', encoding='utf-8') as f:
            json.dump(alteracoes_iniciais, f, indent=2, ensure_ascii=False)
    
    def salvar_alteracao(self, cd_mun: str, cidade: str, zona_anterior: str, 
                        zona_nova: str, usuario: str = "Sistema") -> bool:
        """
        Salva uma alteração de zona
        
        Args:
            cd_mun: Código do município
            cidade: Nome da cidade
            zona_anterior: Zona anterior
            zona_nova: Nova zona
            usuario: Usuário que fez a alteração
            
        Returns:
            bool: True se salvou com sucesso
        """
        try:
            # Carregar alterações existentes
            with open(self.alteracoes_file, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            # Criar nova alteração
            nova_alteracao = {
                "id": len(dados["alteracoes"]) + 1,
                "timestamp": datetime.now().isoformat(),
                "cd_mun": cd_mun,
                "cidade": cidade,
                "zona_anterior": zona_anterior,
                "zona_nova": zona_nova,
                "usuario": usuario,
                "tipo": "alteracao_zona"
            }
            
            # Adicionar à lista
            dados["alteracoes"].append(nova_alteracao)
            dados["ultima_atualizacao"] = datetime.now().isoformat()
            dados["estatisticas"]["total_alteracoes"] += 1
            
            # Atualizar estatísticas
            if zona_nova not in dados["estatisticas"]["zonas_modificadas"]:
                dados["estatisticas"]["zonas_modificadas"].append(zona_nova)
            
            # Salvar
            with open(self.alteracoes_file, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            
            # Salvar no histórico
            self._salvar_no_historico(nova_alteracao)
            
            return True
            
        except Exception as e:
            print(f"Erro ao salvar alteração: {e}")
            return False
    
    def _salvar_no_historico(self, alteracao: Dict[str, Any]):
        """Salva alteração individual no histórico"""
        data_hoje = datetime.now().strftime("%Y-%m-%d")
        arquivo_historico = os.path.join(self.historico_dir, f"alteracoes_{data_hoje}.json")
        
        # Carregar histórico do dia ou criar novo
        if os.path.exists(arquivo_historico):
            with open(arquivo_historico, 'r', encoding='utf-8') as f:
                historico = json.load(f)
        else:
            historico = {"data": data_hoje, "alteracoes": []}
        
        historico["alteracoes"].append(alteracao)
        
        with open(arquivo_historico, 'w', encoding='utf-8') as f:
            json.dump(historico, f, indent=2, ensure_ascii=False)
    
    def carregar_alteracoes(self) -> Dict[str, Any]:
        """Carrega todas as alterações"""
        try:
            with open(self.alteracoes_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar alterações: {e}")
            return {"alteracoes": [], "estatisticas": {}}
    
    def aplicar_alteracoes_aos_dados(self) -> bool:
        """
        Aplica todas as alterações aos dados originais e salva como dados atuais
        
        Returns:
            bool: True se aplicou com sucesso
        """
        try:
            # Carregar dados originais
            df_original = pd.read_csv(self.dados_originais)
            df_atual = df_original.copy()
            
            # Carregar alterações
            alteracoes = self.carregar_alteracoes()
            
            # Aplicar cada alteração
            for alt in alteracoes["alteracoes"]:
                cd_mun = alt["cd_mun"]
                nova_zona = alt["zona_nova"]
                
                # Encontrar e atualizar o município
                mask = df_atual['CD_Mun'] == cd_mun
                if mask.any():
                    df_atual.loc[mask, 'Zona'] = nova_zona
            
            # Salvar dados atualizados
            df_atual.to_csv(self.dados_atuais, index=False)
            
            return True
            
        except Exception as e:
            print(f"Erro ao aplicar alterações: {e}")
            return False
    
    def criar_backup(self, nome_backup: Optional[str] = None) -> str:
        """
        Cria backup dos dados atuais
        
        Args:
            nome_backup: Nome personalizado para o backup
            
        Returns:
            str: Caminho do backup criado
        """
        if nome_backup is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_backup = f"backup_{timestamp}"
        
        backup_path = os.path.join(self.backup_dir, nome_backup)
        os.makedirs(backup_path, exist_ok=True)
        
        # Copiar arquivos importantes
        arquivos_backup = [
            self.dados_originais,
            self.alteracoes_file
        ]
        
        if os.path.exists(self.dados_atuais):
            arquivos_backup.append(self.dados_atuais)
        
        for arquivo in arquivos_backup:
            if os.path.exists(arquivo):
                nome_arquivo = os.path.basename(arquivo)
                shutil.copy2(arquivo, os.path.join(backup_path, nome_arquivo))
        
        # Criar arquivo de informações do backup
        info_backup = {
            "criado_em": datetime.now().isoformat(),
            "arquivos": [os.path.basename(arq) for arq in arquivos_backup],
            "total_alteracoes": len(self.carregar_alteracoes()["alteracoes"])
        }
        
        with open(os.path.join(backup_path, "info_backup.json"), 'w', encoding='utf-8') as f:
            json.dump(info_backup, f, indent=2, ensure_ascii=False)
        
        return backup_path
    
    def restaurar_backup(self, nome_backup: str) -> bool:
        """
        Restaura um backup específico
        
        Args:
            nome_backup: Nome do backup a restaurar
            
        Returns:
            bool: True se restaurou com sucesso
        """
        try:
            backup_path = os.path.join(self.backup_dir, nome_backup)
            
            if not os.path.exists(backup_path):
                print(f"Backup {nome_backup} não encontrado")
                return False
            
            # Restaurar arquivos
            arquivos_restaurar = [
                ("dados_mapa_pernambuco.csv", self.dados_originais),
                ("alteracoes_zonas.json", self.alteracoes_file),
                ("dados_mapa_atual.csv", self.dados_atuais)
            ]
            
            for nome_arquivo, destino in arquivos_restaurar:
                origem = os.path.join(backup_path, nome_arquivo)
                if os.path.exists(origem):
                    shutil.copy2(origem, destino)
            
            return True
            
        except Exception as e:
            print(f"Erro ao restaurar backup: {e}")
            return False
    
    def listar_backups(self) -> List[Dict[str, Any]]:
        """Lista todos os backups disponíveis"""
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
        
        for item in os.listdir(self.backup_dir):
            backup_path = os.path.join(self.backup_dir, item)
            if os.path.isdir(backup_path):
                info_file = os.path.join(backup_path, "info_backup.json")
                
                if os.path.exists(info_file):
                    try:
                        with open(info_file, 'r', encoding='utf-8') as f:
                            info = json.load(f)
                        info["nome"] = item
                        backups.append(info)
                    except:
                        # Backup sem informações
                        backups.append({
                            "nome": item,
                            "criado_em": "Desconhecido",
                            "arquivos": [],
                            "total_alteracoes": 0
                        })
        
        return sorted(backups, key=lambda x: x.get("criado_em", ""), reverse=True)
    
    def resetar_alteracoes(self) -> bool:
        """
        Reseta todas as alterações, voltando aos dados originais
        
        Returns:
            bool: True se resetou com sucesso
        """
        try:
            # Criar backup antes de resetar
            self.criar_backup("backup_antes_reset")
            
            # Reinicializar alterações
            self._inicializar_alteracoes()
            
            # Remover dados atuais se existirem
            if os.path.exists(self.dados_atuais):
                os.remove(self.dados_atuais)
            
            return True
            
        except Exception as e:
            print(f"Erro ao resetar alterações: {e}")
            return False
    
    def exportar_relatorio(self, formato: str = "json") -> str:
        """
        Exporta relatório das alterações
        
        Args:
            formato: Formato do relatório ('json' ou 'csv')
            
        Returns:
            str: Caminho do arquivo gerado
        """
        alteracoes = self.carregar_alteracoes()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if formato.lower() == "csv":
            # Exportar como CSV
            df_alteracoes = pd.DataFrame(alteracoes["alteracoes"])
            arquivo_saida = f"relatorio_alteracoes_{timestamp}.csv"
            df_alteracoes.to_csv(arquivo_saida, index=False)
            
        else:
            # Exportar como JSON
            arquivo_saida = f"relatorio_alteracoes_{timestamp}.json"
            with open(arquivo_saida, 'w', encoding='utf-8') as f:
                json.dump(alteracoes, f, indent=2, ensure_ascii=False)
        
        return arquivo_saida

# Exemplo de uso
if __name__ == "__main__":
    # Inicializar sistema
    sistema = SistemaPersistencia()
    
    # Exemplo de uso
    print("🔧 Sistema de Persistência Inicializado")
    print(f"📁 Diretório base: {sistema.base_dir}")
    print(f"📚 Histórico: {sistema.historico_dir}")
    print(f"💾 Backups: {sistema.backup_dir}")
    
    # Listar backups existentes
    backups = sistema.listar_backups()
    print(f"📦 Backups disponíveis: {len(backups)}")
    
    for backup in backups:
        print(f"  - {backup['nome']}: {backup.get('criado_em', 'N/A')}")