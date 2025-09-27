/**
 * Extensão JavaScript para Multi-UF
 * Adiciona seletor de UF ao sistema existente
 */

class MultiUFExtension {
    constructor() {
        this.ufAtual = 'PE';
        this.ufsDisponiveis = [];
        this.modoMultiUF = false;
        this.inicializar();
    }

    inicializar() {
        console.log('🔌 Inicializando extensão Multi-UF...');
        
        // Aguardar DOM estar pronto
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.configurar());
        } else {
            this.configurar();
        }
    }

    configurar() {
        this.criarSeletorUF();
        this.carregarUfsDisponiveis();
        this.configurarEventosWebSocket();
        
        console.log('✅ Extensão Multi-UF configurada');
    }

    criarSeletorUF() {
        // Encontrar local para inserir o seletor (header ou navbar)
        const header = document.querySelector('.navbar') || 
                      document.querySelector('header') || 
                      document.querySelector('.container-fluid') ||
                      document.body;

        if (!header) {
            console.warn('⚠️ Não foi possível encontrar local para o seletor UF');
            return;
        }

        // Criar container do seletor
        const seletorContainer = document.createElement('div');
        seletorContainer.id = 'multi-uf-selector';
        seletorContainer.className = 'multi-uf-selector';
        seletorContainer.innerHTML = `
            <div class="uf-selector-wrapper">
                <label for="uf-select" class="uf-label">
                    <i class="fas fa-map-marker-alt"></i> Estado:
                </label>
                <select id="uf-select" class="uf-select">
                    <option value="">Carregando...</option>
                </select>
                <div id="uf-loading" class="uf-loading" style="display: none;">
                    <i class="fas fa-spinner fa-spin"></i>
                </div>
            </div>
        `;

        // Adicionar estilos
        this.adicionarEstilos();

        // Inserir no início do header
        header.insertBefore(seletorContainer, header.firstChild);

        // Configurar evento de mudança
        const select = document.getElementById('uf-select');
        select.addEventListener('change', (e) => {
            const novaUF = e.target.value;
            if (novaUF && novaUF !== this.ufAtual) {
                this.carregarUF(novaUF);
            }
        });

        console.log('✅ Seletor UF criado');
    }

    adicionarEstilos() {
        const style = document.createElement('style');
        style.textContent = `
            .multi-uf-selector {
                background: rgba(255, 255, 255, 0.95);
                padding: 10px 15px;
                border-radius: 8px;
                margin: 10px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                border-left: 4px solid #667eea;
            }
            
            .uf-selector-wrapper {
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
            }
            
            .uf-label {
                font-weight: 600;
                color: #333;
                margin: 0;
                white-space: nowrap;
            }
            
            .uf-label i {
                color: #667eea;
                margin-right: 5px;
            }
            
            .uf-select {
                padding: 8px 12px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                background: white;
                font-size: 14px;
                font-weight: 500;
                color: #333;
                cursor: pointer;
                transition: all 0.3s ease;
                min-width: 150px;
            }
            
            .uf-select:hover {
                border-color: #667eea;
            }
            
            .uf-select:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .uf-loading {
                color: #667eea;
                font-size: 16px;
            }
            
            .uf-loading i {
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            /* Responsivo */
            @media (max-width: 768px) {
                .multi-uf-selector {
                    margin: 5px;
                    padding: 8px 10px;
                }
                
                .uf-selector-wrapper {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 5px;
                }
                
                .uf-select {
                    width: 100%;
                    min-width: auto;
                }
            }
        `;
        
        document.head.appendChild(style);
    }

    async carregarUfsDisponiveis() {
        try {
            const response = await fetch('/api/ufs_disponiveis');
            const data = await response.json();
            
            if (data.sucesso) {
                this.ufsDisponiveis = data.ufs;
                this.ufAtual = data.uf_atual;
                this.modoMultiUF = data.modo_multi_uf;
                
                this.atualizarSeletorUF();
                
                console.log(`✅ UFs carregadas: ${this.ufsDisponiveis.map(uf => uf.codigo).join(', ')}`);
                console.log(`📍 UF atual: ${this.ufAtual}`);
            } else {
                console.error('❌ Erro ao carregar UFs:', data.erro);
                this.mostrarErro('Erro ao carregar estados disponíveis');
            }
        } catch (error) {
            console.error('❌ Erro na requisição:', error);
            this.mostrarErro('Erro de conexão');
        }
    }

    atualizarSeletorUF() {
        const select = document.getElementById('uf-select');
        if (!select) return;

        // Limpar opções
        select.innerHTML = '';

        if (this.ufsDisponiveis.length === 0) {
            select.innerHTML = '<option value="">Nenhuma UF disponível</option>';
            select.disabled = true;
            return;
        }

        // Adicionar opções
        this.ufsDisponiveis.forEach(uf => {
            const option = document.createElement('option');
            option.value = uf.codigo;
            option.textContent = `${uf.codigo} - ${uf.nome}`;
            option.selected = uf.codigo === this.ufAtual;
            select.appendChild(option);
        });

        select.disabled = false;
        
        // Mostrar indicador se não está no modo multi-UF
        if (!this.modoMultiUF) {
            const wrapper = select.parentElement;
            if (wrapper && !wrapper.querySelector('.modo-tradicional')) {
                const indicador = document.createElement('span');
                indicador.className = 'modo-tradicional';
                indicador.innerHTML = '<small style="color: #6c757d;">(Modo tradicional)</small>';
                wrapper.appendChild(indicador);
            }
        }
    }

    async carregarUF(codigoUF) {
        if (!this.modoMultiUF) {
            this.mostrarAviso('Sistema multi-UF não está ativo');
            return;
        }

        this.mostrarCarregando(true);
        
        try {
            console.log(`🔄 Carregando UF: ${codigoUF}`);
            
            const response = await fetch(`/api/carregar_uf/${codigoUF}`);
            const data = await response.json();
            
            if (data.sucesso) {
                this.ufAtual = codigoUF;
                
                console.log(`✅ UF ${codigoUF} carregada:`, data);
                
                // Notificar outros componentes via evento customizado
                const evento = new CustomEvent('ufCarregada', {
                    detail: {
                        uf: codigoUF,
                        nome: data.nome,
                        estatisticas: data.estatisticas,
                        zonas: data.zonas,
                        cores: data.cores
                    }
                });
                document.dispatchEvent(evento);
                
                // Recarregar dados do mapa se a função existir
                if (typeof atualizarMapa === 'function') {
                    atualizarMapa();
                } else if (typeof carregarDadosMapa === 'function') {
                    carregarDadosMapa();
                }
                
                // Atualizar estatísticas se a função existir
                if (typeof atualizarEstatisticas === 'function') {
                    atualizarEstatisticas();
                }
                
                this.mostrarSucesso(`${data.nome} carregado com sucesso!`);
                
            } else {
                console.error('❌ Erro ao carregar UF:', data.erro);
                this.mostrarErro(data.erro);
                
                // Reverter seleção
                const select = document.getElementById('uf-select');
                if (select) {
                    select.value = this.ufAtual;
                }
            }
        } catch (error) {
            console.error('❌ Erro na requisição:', error);
            this.mostrarErro('Erro de conexão ao carregar estado');
            
            // Reverter seleção
            const select = document.getElementById('uf-select');
            if (select) {
                select.value = this.ufAtual;
            }
        } finally {
            this.mostrarCarregando(false);
        }
    }

    configurarEventosWebSocket() {
        // Verificar se socket.io está disponível
        if (typeof io === 'undefined' || typeof socket === 'undefined') {
            console.warn('⚠️ Socket.IO não disponível para eventos Multi-UF');
            return;
        }

        // Escutar eventos de UF carregada
        socket.on('uf_carregada', (data) => {
            console.log('📡 UF carregada via WebSocket:', data);
            
            if (data.sucesso) {
                this.ufAtual = data.uf;
                
                // Atualizar seletor
                const select = document.getElementById('uf-select');
                if (select) {
                    select.value = data.uf;
                }
                
                // Disparar evento customizado
                const evento = new CustomEvent('ufCarregadaWebSocket', {
                    detail: data
                });
                document.dispatchEvent(evento);
                
                this.mostrarSucesso(`${data.nome} carregado via WebSocket!`);
            } else {
                this.mostrarErro(data.erro);
            }
            
            this.mostrarCarregando(false);
        });

        // Escutar dados do mapa atualizados
        socket.on('dados_mapa_atualizados', (data) => {
            console.log('📡 Dados do mapa atualizados via WebSocket');
            
            // Disparar evento para atualizar mapa
            const evento = new CustomEvent('dadosMapaAtualizados', {
                detail: data
            });
            document.dispatchEvent(evento);
        });

        console.log('✅ Eventos WebSocket Multi-UF configurados');
    }

    mostrarCarregando(mostrar) {
        const loading = document.getElementById('uf-loading');
        const select = document.getElementById('uf-select');
        
        if (loading) {
            loading.style.display = mostrar ? 'block' : 'none';
        }
        
        if (select) {
            select.disabled = mostrar;
        }
    }

    mostrarSucesso(mensagem) {
        this.mostrarNotificacao(mensagem, 'success');
    }

    mostrarErro(mensagem) {
        this.mostrarNotificacao(mensagem, 'error');
    }

    mostrarAviso(mensagem) {
        this.mostrarNotificacao(mensagem, 'warning');
    }

    mostrarNotificacao(mensagem, tipo = 'info') {
        // Tentar usar sistema de notificação existente
        if (typeof mostrarAlerta === 'function') {
            mostrarAlerta(mensagem, tipo);
            return;
        }
        
        if (typeof toastr !== 'undefined') {
            toastr[tipo](mensagem);
            return;
        }
        
        // Fallback: console e alert simples
        console.log(`${tipo.toUpperCase()}: ${mensagem}`);
        
        if (tipo === 'error') {
            alert(`Erro: ${mensagem}`);
        }
    }

    // Método público para carregar UF via JavaScript
    carregarUFProgramaticamente(codigoUF) {
        const select = document.getElementById('uf-select');
        if (select) {
            select.value = codigoUF;
            select.dispatchEvent(new Event('change'));
        }
    }

    // Método público para obter UF atual
    obterUFAtual() {
        return {
            codigo: this.ufAtual,
            nome: this.ufsDisponiveis.find(uf => uf.codigo === this.ufAtual)?.nome || this.ufAtual,
            modoMultiUF: this.modoMultiUF
        };
    }
}

// Inicializar extensão quando o script for carregado
let multiUFExtension;

// Aguardar carregamento completo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        multiUFExtension = new MultiUFExtension();
    });
} else {
    multiUFExtension = new MultiUFExtension();
}

// Expor globalmente para uso em outros scripts
window.MultiUFExtension = MultiUFExtension;
window.multiUFExtension = multiUFExtension;
