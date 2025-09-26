import pandas as pd
import json

def gerar_cores_zonas():
    """Gera um mapeamento de cores para cada zona"""
    # Paleta de cores distintas e visualmente agradáveis
    cores_disponiveis = [
        '#FF6B6B',  # Vermelho coral
        '#4ECDC4',  # Turquesa
        '#45B7D1',  # Azul claro
        '#96CEB4',  # Verde menta
        '#FFEAA7',  # Amarelo suave
        '#DDA0DD',  # Roxo claro
        '#98D8C8',  # Verde água
        '#F7DC6F',  # Amarelo ouro
        '#BB8FCE',  # Lavanda
        '#85C1E9',  # Azul céu
        '#F8C471',  # Laranja suave
        '#82E0AA'   # Verde claro
    ]
    
    # Ler os dados
    df = pd.read_csv('pernambuco_dados_gerar_mapa.csv')
    
    # Obter zonas únicas
    zonas_unicas = sorted(df['Zona'].unique())
    print(f"Zonas encontradas ({len(zonas_unicas)}):")
    for i, zona in enumerate(zonas_unicas, 1):
        print(f"{i:2d}. {zona}")
    
    # Mapear cores para zonas
    zona_cor_mapping = {}
    for i, zona in enumerate(zonas_unicas):
        cor = cores_disponiveis[i % len(cores_disponiveis)]
        zona_cor_mapping[zona] = cor
        print(f"   {zona} -> {cor}")
    
    return zona_cor_mapping

def criar_dados_otimizados():
    """Cria arquivo de dados otimizado com cores"""
    print("=== PREPARANDO DADOS OTIMIZADOS ===")
    
    # Ler dados originais
    df = pd.read_csv('pernambuco_dados_gerar_mapa.csv')
    
    # Gerar mapeamento de cores
    zona_cor_mapping = gerar_cores_zonas()
    
    # Adicionar coluna de cor
    df['Cor'] = df['Zona'].map(zona_cor_mapping)
    
    # Criar versão simplificada para o mapa
    df_mapa = df[['CD_Mun', 'Cidade', 'Zona', 'Cor', 'UF', 'Mesorregião Geográfica']].copy()
    
    # Salvar dados otimizados
    df_mapa.to_csv('dados_mapa_pernambuco.csv', index=False, encoding='utf-8')
    
    # Salvar mapeamento de cores em JSON
    with open('zona_cores_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(zona_cor_mapping, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== ARQUIVOS CRIADOS ===")
    print("1. dados_mapa_pernambuco.csv - Dados otimizados para o mapa")
    print("2. zona_cores_mapping.json - Mapeamento de cores das zonas")
    
    print(f"\n=== ESTATÍSTICAS ===")
    print(f"Total de municípios: {len(df_mapa)}")
    print(f"Total de zonas: {len(zona_cor_mapping)}")
    
    # Mostrar amostra dos dados
    print(f"\n=== AMOSTRA DOS DADOS OTIMIZADOS ===")
    print(df_mapa.head())
    
    return df_mapa, zona_cor_mapping

def validar_dados_geometria():
    """Valida se os códigos de município existem no arquivo de geometria"""
    print("\n=== VALIDAÇÃO COM GEOMETRIA ===")
    
    try:
        # Ler dados do mapa
        df_mapa = pd.read_csv('dados_mapa_pernambuco.csv')
        
        # Ler geometria
        import geopandas as gpd
        gdf_geo = gpd.read_file('pernambuco.json')
        
        # Converter códigos para string para comparação
        codigos_mapa = set(df_mapa['CD_Mun'].astype(str))
        codigos_geo = set(gdf_geo['id'].astype(str))
        
        # Verificar correspondência
        codigos_encontrados = codigos_mapa.intersection(codigos_geo)
        codigos_faltantes = codigos_mapa - codigos_geo
        
        print(f"Códigos no arquivo de dados: {len(codigos_mapa)}")
        print(f"Códigos no arquivo de geometria: {len(codigos_geo)}")
        print(f"Códigos correspondentes: {len(codigos_encontrados)}")
        print(f"Códigos sem geometria: {len(codigos_faltantes)}")
        
        if codigos_faltantes:
            print(f"Códigos sem geometria: {sorted(list(codigos_faltantes))[:10]}...")
        
        return len(codigos_faltantes) == 0
        
    except Exception as e:
        print(f"Erro na validação: {e}")
        return False

if __name__ == "__main__":
    # Executar preparação dos dados
    df_mapa, zona_cor_mapping = criar_dados_otimizados()
    
    # Validar com geometria
    validacao_ok = validar_dados_geometria()
    
    if validacao_ok:
        print("\n✅ DADOS PREPARADOS COM SUCESSO!")
    else:
        print("\n⚠️  ATENÇÃO: Alguns códigos de município não possuem geometria correspondente")
    
    print("\nPróximo passo: Desenvolver o script principal do mapa interativo")