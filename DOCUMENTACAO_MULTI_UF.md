# 📋 Documentação - Sistema Multi-UF

## 🎯 Visão Geral

O sistema foi expandido para suportar múltiplas Unidades Federativas (UFs), permitindo que você trabalhe com dados de diferentes estados de forma organizada e independente.

## 📁 Estrutura de Arquivos

### Estrutura Geral
```
zonas-lubnord/
├── dados_ufs/                          # Diretório principal das UFs
│   ├── configuracao_ufs.json          # Configuração de todas as UFs
│   ├── PE/                             # Diretório de Pernambuco
│   │   ├── pernambuco_dados_gerar_mapa.csv
│   │   ├── pernambuco.json
│   │   ├── zona_cores_mapping.json
│   │   └── alteracoes_zonas.json
│   ├── SP/                             # Diretório de São Paulo (exemplo)
│   │   ├── sp_dados_gerar_mapa.csv
│   │   ├── sp.json
│   │   ├── zona_cores_mapping_sp.json
│   │   └── alteracoes_zonas.json
│   └── [NOVA_UF]/                      # Diretório para nova UF
│       ├── [uf]_dados_gerar_mapa.csv
│       ├── [uf].json
│       ├── zona_cores_mapping_[uf].json
│       └── alteracoes_zonas.json
├── gerenciador_multi_uf.py            # Gerenciador de múltiplas UFs
├── app_mapa_multi_uf.py               # Aplicação principal multi-UF
├── adicionar_nova_uf.py               # Script para adicionar UFs
└── templates/
    └── mapa_multi_uf.html             # Interface multi-UF
```

## 📊 Estrutura de Dados Necessária

### 1. Arquivo CSV de Dados (`[uf]_dados_gerar_mapa.csv`)

**Colunas Obrigatórias:**
- `UF`: Código da Unidade Federativa (ex: PE, SP, RJ)
- `CD_Mun`: Código IBGE do município (string)
- `Cidade`: Nome do município
- `Zona`: Zona atribuída ao município

**Colunas Opcionais (mas recomendadas):**
- `Mesorregião Geográfica`: Região geográfica do município
- `SELL OUT ANUAL`: Vendas anuais
- `SELL OUT MÊS`: Vendas mensais  
- `POTENCIAL ANUAL`: Potencial anual
- `POTENCIAL MÊS`: Potencial mensal
- `POPULAÇÃO `: População do município
- `PDV`: Número de pontos de venda
- `%SHARE`: Percentual de participação

**Exemplo de estrutura:**
```csv
UF,Mesorregião Geográfica,CD_Mun,Cidade,Zona,SELL OUT ANUAL,SELL OUT MÊS,POTENCIAL ANUAL,POTENCIAL MÊS,POPULAÇÃO ,PDV,%SHARE
SP,Região Metropolitana,3550308,São Paulo,Zona Central,500000,41667,650000,54167,12300000,5000,76.9
SP,Região Norte,3518800,Guarulhos,Zona Norte,180000,15000,220000,18333,1400000,1800,81.8
SP,Região Sul,3548708,Santo André,Zona Sul,120000,10000,150000,12500,750000,1200,80.0
```

### 2. Arquivo GeoJSON de Geometrias (`[uf].json`)

Arquivo no formato GeoJSON contendo os polígonos dos municípios da UF.

**Estrutura esperada:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": "3550308",
        "name": "São Paulo"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[longitude, latitude], ...]]
      }
    }
  ]
}
```

**Importante:** O campo `properties.id` deve corresponder ao `CD_Mun` do arquivo CSV.

### 3. Arquivo de Cores das Zonas (`zona_cores_mapping_[uf].json`)

Define as cores de cada zona para visualização no mapa.

**Estrutura:**
```json
{
  "Sem Zona": "#CCCCCC",
  "Zona Central": "#228B22",
  "Zona Norte": "#000080",
  "Zona Sul": "#8B0000",
  "Zona Leste": "#4B0082",
  "Zona Oeste": "#B8860B"
}
```

**Formato das cores:** Hexadecimal (#RRGGBB)

### 4. Arquivo de Alterações (`alteracoes_zonas.json`)

Armazena histórico de alterações de zonas (criado automaticamente).

## 🚀 Como Adicionar uma Nova UF

### Método 1: Usando o Script Automático

1. Execute o script utilitário:
```bash
python adicionar_nova_uf.py
```

2. Escolha a opção "1. Adicionar nova UF"

3. Forneça as informações solicitadas:
   - Código da UF (ex: SP, RJ, MG)
   - Nome completo da UF

4. O script criará automaticamente:
   - Diretório da UF
   - Arquivos base com estrutura correta
   - Configuração no sistema

### Método 2: Manual

1. **Criar diretório da UF:**
```bash
mkdir dados_ufs/SP
```

2. **Criar arquivo de dados** (`sp_dados_gerar_mapa.csv`):
   - Use a estrutura de colunas documentada acima
   - Certifique-se de que os códigos IBGE estão corretos

3. **Obter arquivo GeoJSON** (`sp.json`):
   - Baixe de fontes oficiais (IBGE, etc.)
   - Verifique se os IDs correspondem aos códigos dos municípios

4. **Criar arquivo de cores** (`zona_cores_mapping_sp.json`):
   - Defina as zonas e suas cores
   - Use formato hexadecimal para cores

5. **Registrar no sistema:**
```python
from gerenciador_multi_uf import GerenciadorMultiUF

gerenciador = GerenciadorMultiUF()
gerenciador.adicionar_uf("SP", "São Paulo")
```

## 🎨 Personalização de Zonas

### Definindo Zonas Personalizadas

Cada UF pode ter suas próprias zonas. Exemplo para São Paulo:

```json
{
  "Sem Zona": "#CCCCCC",
  "Grande São Paulo": "#FF6B6B",
  "Interior Norte": "#4ECDC4", 
  "Interior Sul": "#45B7D1",
  "Litoral": "#96CEB4",
  "Vale do Paraíba": "#FFEAA7",
  "Região de Campinas": "#DDA0DD",
  "Região de Ribeirão Preto": "#98D8C8"
}
```

### Cores Recomendadas

Use cores que tenham bom contraste e sejam distinguíveis:

- **Tons de Verde:** #228B22, #32CD32, #90EE90
- **Tons de Azul:** #000080, #4169E1, #87CEEB  
- **Tons de Vermelho:** #8B0000, #DC143C, #FF6347
- **Tons de Roxo:** #4B0082, #8B008B, #DDA0DD
- **Tons de Laranja:** #FF8C00, #FFA500, #FFD700

## 🔧 Configuração e Uso

### Executando o Sistema Multi-UF

```bash
python app_mapa_multi_uf.py
```

O sistema iniciará na porta 5002 (por padrão).

### Interface de Usuário

1. **Seletor de UF:** Painel lateral esquerdo
2. **Informações da UF:** Detalhes da UF selecionada
3. **Estatísticas:** Por zona da UF atual
4. **Mapa Interativo:** Visualização e edição

### Funcionalidades Disponíveis

- ✅ Seleção de UF em tempo real
- ✅ Carregamento dinâmico de dados
- ✅ Edição de zonas por município
- ✅ Estatísticas por zona
- ✅ Persistência de alterações
- ✅ Interface responsiva

## 📊 Fontes de Dados Recomendadas

### Geometrias (GeoJSON)
- **IBGE:** [Malhas Territoriais](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/)
- **GitHub:** Repositórios com dados do Brasil
- **OpenStreetMap:** Dados abertos

### Códigos IBGE
- **IBGE:** [Códigos de Municípios](https://www.ibge.gov.br/explica/codigos-dos-municipios.php)
- Formato: 7 dígitos (2 da UF + 5 do município)

### Dados Populacionais
- **IBGE:** Censo e estimativas populacionais
- **DataSUS:** Dados de saúde por município

## 🛠️ Manutenção e Troubleshooting

### Verificando Estrutura de UF

```bash
python adicionar_nova_uf.py
# Escolha opção "3. Verificar estrutura de UF"
```

### Problemas Comuns

1. **UF não aparece no seletor:**
   - Verifique se todos os arquivos existem
   - Confirme estrutura do CSV
   - Valide formato do GeoJSON

2. **Mapa não carrega:**
   - Verifique correspondência entre CD_Mun e IDs do GeoJSON
   - Confirme formato das coordenadas

3. **Cores não aparecem:**
   - Valide formato hexadecimal das cores
   - Certifique-se de que zonas existem no CSV

### Logs e Debug

O sistema exibe logs detalhados no console:
- ✅ Operações bem-sucedidas
- ⚠️ Avisos e fallbacks
- ❌ Erros e problemas

## 📈 Expansão Futura

### Funcionalidades Planejadas
- Import/export de dados
- Backup automático por UF
- Relatórios comparativos entre UFs
- API REST para integração
- Dashboard analítico

### Contribuindo

Para adicionar novas funcionalidades:
1. Mantenha compatibilidade com estrutura existente
2. Documente mudanças
3. Teste com múltiplas UFs
4. Preserve dados existentes

## 📞 Suporte

Para dúvidas ou problemas:
1. Consulte esta documentação
2. Execute verificações automáticas
3. Verifique logs do sistema
4. Valide estrutura de dados

---

**Versão:** 1.0  
**Última atualização:** 2025-09-26  
**Compatibilidade:** Python 3.8+
