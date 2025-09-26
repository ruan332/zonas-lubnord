import pandas as pd

# Mapeamento dos códigos incorretos para os corretos baseado na pesquisa
correcoes_codigos = {
    '2500502': '2600609',  # Alagoinha - PE (código correto: 2600609)
    '2301208': '2601052',  # Aracoiaba - PE (código correto: 2601052) 
    '2102002': '2602209',  # Bom Jardim - PE (código correto: 2602209)
    '1501600': '2602308',  # Bonito - PE (código correto: 2602308)
    '2401800': '2602506',  # Brejinho - PE (código correto: 2602506)
    '1703826': '2603108',  # Cachoeirinha - PE (código correto: 2603108)
    '2303808': '2604304',  # Cedro - PE (código correto: 2604304)
    '2504504': '2604601',  # Condado - PE (código correto: 2604601)
    '2105450': '2608057',  # Jatobá - PE (código correto: 2608057)
    '2205532': '2608404',  # Jurema - PE (código correto: 2608404)
    '2403251': '2610400',  # Parnamirim - PE (código correto: 2610400)
    '2510907': '2610707',  # Paulista - PE (código correto: 2610707)
    '1506104': '2611408',  # Primavera - PE (código correto: 2611408)
    '2513000': '2612109',  # Salgadinho - PE (código correto: 2612109)
    '2411205': '2612455',  # Santa Cruz - PE (código correto: 2612455)
    '2209203': '2612554',  # Santa Filomena - PE (código correto: 2612554)
    '2111706': '2613800',  # São Vicente Ferrer - PE (código correto: 2613800)
    '2516805': '2615706'   # Triunfo - PE (código correto: 2615706)
}

def corrigir_codigos_ibge():
    """Corrige os códigos IBGE incorretos no arquivo CSV"""
    
    # Carregar o arquivo CSV
    arquivo_csv = 'pernambuco_dados_gerar_mapa.csv'
    df = pd.read_csv(arquivo_csv)
    
    print(f"Total de registros no arquivo: {len(df)}")
    print(f"Códigos a serem corrigidos: {len(correcoes_codigos)}")
    
    # Contador de correções realizadas
    correcoes_realizadas = 0
    
    # Aplicar as correções
    for codigo_incorreto, codigo_correto in correcoes_codigos.items():
        # Verificar se o código incorreto existe no DataFrame
        mask = df['CD_Mun'].astype(str) == codigo_incorreto
        if mask.any():
            municipio = df.loc[mask, 'Cidade'].iloc[0]
            print(f"Corrigindo: {municipio} - {codigo_incorreto} → {codigo_correto}")
            df.loc[mask, 'CD_Mun'] = int(codigo_correto)
            correcoes_realizadas += 1
        else:
            print(f"Código {codigo_incorreto} não encontrado no arquivo")
    
    # Salvar o arquivo corrigido
    df.to_csv(arquivo_csv, index=False)
    
    print(f"\nCorreções realizadas: {correcoes_realizadas}")
    print(f"Arquivo '{arquivo_csv}' atualizado com sucesso!")
    
    # Mostrar alguns registros corrigidos para verificação
    print("\nVerificando alguns registros corrigidos:")
    for codigo_correto in ['2600609', '2601052', '2602209', '2602308', '2602506']:
        mask = df['CD_Mun'] == int(codigo_correto)
        if mask.any():
            municipio = df.loc[mask, 'Cidade'].iloc[0]
            zona = df.loc[mask, 'Zona'].iloc[0]
            print(f"  {codigo_correto} - {municipio} - {zona}")

if __name__ == "__main__":
    corrigir_codigos_ibge()