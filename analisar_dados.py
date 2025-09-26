import pandas as pd

# Ler a aba específica
df = pd.read_excel('pernambuco_dados.xlsx', sheet_name='gerar_mapa')

print('=== ANÁLISE DETALHADA DA ABA GERAR_MAPA ===')
print(f'Total de registros: {len(df)}')
print(f'Total de colunas: {len(df.columns)}')

print('\n=== COLUNAS DISPONÍVEIS ===')
for i, col in enumerate(df.columns, 1):
    print(f'{i:2d}. {col}')

print('\n=== ANÁLISE DAS ZONAS ===')
zonas_unicas = df['Zona'].unique()
print(f'Zonas únicas ({len(zonas_unicas)}): {sorted(zonas_unicas)}')

print('\n=== CONTAGEM POR ZONA ===')
contagem_zonas = df['Zona'].value_counts().sort_index()
print(contagem_zonas)

print('\n=== ANÁLISE DOS CÓDIGOS DE MUNICÍPIO ===')
print(f'Códigos únicos de município: {len(df["CD_Mun"].unique())}')
print(f'Primeiro código: {df["CD_Mun"].min()}')
print(f'Último código: {df["CD_Mun"].max()}')

print('\n=== AMOSTRA DOS DADOS ===')
print(df[['CD_Mun', 'Cidade', 'Zona', 'UF', 'Mesorregião Geográfica']].head(10))

print('\n=== VERIFICAÇÃO DE DADOS FALTANTES ===')
print(df.isnull().sum())

print('\n=== ESTATÍSTICAS BÁSICAS ===')
print(f'Estados únicos: {df["UF"].unique()}')
print(f'Mesorregiões únicas: {len(df["Mesorregião Geográfica"].unique())}')

# Salvar dados em CSV para facilitar manipulação
df.to_csv('pernambuco_dados_gerar_mapa.csv', index=False, encoding='utf-8')
print('\n=== ARQUIVO CSV CRIADO ===')
print('Dados salvos em: pernambuco_dados_gerar_mapa.csv')