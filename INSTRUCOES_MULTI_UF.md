
# INSTRUÇÕES DE USO - SISTEMA MULTI-UF

## 🚀 Como Executar

### Opção 1: Sistema Integrado (Recomendado)
```bash
python inicializar_multi_uf.py
```

### Opção 2: Sistema Original com Extensão
1. Adicione ao seu template HTML existente:
```html
<!-- No <head> -->
<script src="/static/js/multi_uf_extension.js"></script>

<!-- No <body>, antes do conteúdo principal -->
<!-- Inclua o conteúdo de templates/multi_uf_header.html -->
```

## 🎯 Funcionalidades Disponíveis

### APIs REST
- `GET /api/ufs_disponiveis` - Lista UFs disponíveis
- `GET /api/carregar_uf/<codigo>` - Carrega UF específica
- `GET /api/info_uf_atual` - Info da UF atual

### Eventos WebSocket
- `carregar_uf` - Carregar UF via WebSocket
- `obter_ufs_disponiveis` - Obter lista de UFs

### JavaScript
```javascript
// Carregar UF programaticamente
multiUFExtension.carregarUFProgramaticamente('AL');

// Obter UF atual
const ufAtual = multiUFExtension.obterUFAtual();

// Escutar mudanças de UF
document.addEventListener('ufCarregada', (e) => {
    console.log('Nova UF carregada:', e.detail);
});
```

## 🗺️ Estados Disponíveis
- PE - Pernambuco (padrão)
- AL - Alagoas (configurado)
- SE - Sergipe (quando configurado)

## 🔧 Configuração
- Arquivos de configuração: `dados_ufs/configuracao_ufs.json`
- Dados por UF: `dados_ufs/<UF>/`
- Cores das zonas: `dados_ufs/<UF>/zona_cores.json`

## 📱 Interface
O seletor de UF aparece automaticamente no header da página.
Selecione um estado para carregar seus dados e visualizar no mapa.

## 🐛 Troubleshooting
- Verifique se todos os arquivos de dados estão presentes
- Confirme se o gerenciador_ufs.py está funcionando
- Teste as APIs individualmente se houver problemas
