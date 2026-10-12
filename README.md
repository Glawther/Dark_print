# Dark_print

Plataforma de produção audiovisual e automação de canais faceless para YouTube Shorts, TikTok e Instagram Reels.

O **Dark_print** transforma uma ideia, tema ou roteiro em um vídeo vertical pronto para publicação, com locução neural, trilha sonora, efeitos sonoros (SFX) procedurais nos cortes, acervo de imagens e vídeos em domínio público e sincronização dinâmica de legendas.

---

## Principais Funcionalidades

### 1. Motor Híbrido de Mídia (Zero Chaves Obrigatórias)
- **Internet Archive & Prelinger Archives:** Busca automatizada de filmes históricos, documentários e gravações em domínio público via API oficial do archive.org.
- **NASA Image & Video Library:** Vídeos e imagens espaciais em alta resolução.
- **Wikimedia Commons & Openverse:** Acervo livre sob licenças Creative Commons.
- **Pexels & Pixabay:** Integração direta com suporte a banco de b-roll comercial.

### 2. Design de Som e SFX Procedurais
- **Síntese de Áudio Nativa:** Gera arquivos WAV de 16-bit 44.1kHz sem downloads externos usando a biblioteca padrão do Python (`wave`, `struct`, `math`).
- **Transições Automáticas:** Efeito *whoosh* antecipado em 50ms antes de cada corte de cena.
- **Impacto no Gancho:** Impacto sub-bass 808 posicionado exatamente no segundo 1.0 para retenção de atenção.
- **Transientes Mecânicos:** Sons de clique de câmera e *risers* de tensão progressivos.

### 3. Catálogo Musical Incompetech (Kevin MacLeod)
- **Mais de 1.400 faixas** com cache local em disco (`storage/cache/incompetech_pieces.json`).
- **Fallback Offline:** Biblioteca integrada com os 22 maiores clássicos virais (*Sneaky Snitch*, *Cipher*, *Carefree*, *Darkest Child*, etc.).
- **Filtro Avançado:** Busca por clima/humor (*feel*), gênero e faixa de BPM.
- **Atribuição CC-BY 4.0 Automática:** Formatação pronta para inserção na descrição do vídeo, evitando reivindicações de direitos autorais.

### 4. Diagnóstico de Retenção & Estrutura de Ganchos
- **Análise de Cadência Neural:** Medição de palavras por segundo e estimativa de duração real.
- **Diagnóstico de Ganchos (0-3s):** Pontuação de lacunas de curiosidade e termos de alto impacto.
- **Variações A/B de Abertura:** Gera 3 alternativas de gancho (Curiosidade, Urgência e Contraintuitivo) aplicáveis com um clique.

### 5. Funil de Monetização & Comentários Fixados
- **Gatilhos de Direct (ManyChat):** Gera cópia de comentário fixado com palavras-chave de disparo automático para entrega de materiais gratuitos (lead magnets).
- **Ponte para Vídeo Longo:** Conversão do tráfego do formato curto para documentários longos de 20 minutos no YouTube.
- **Avisos de Transparência:** Disclaimers de conformidade com FTC e CONAR para links de afiliados.
- **Estimador de RPM:** Projeção de receitas para audiências Tier 1 e América Latina.

### 6. Piloto Automático (Autopilot Background Engine)
- Execução agendada em segundo plano com perfis configuráveis por canal/nicho.
- Publicação automática integrada para TikTok e YouTube Shorts.

### 7. Interface Pro NLE & Terminal Diagnóstico
- Painel em tema escuro com estética de suíte profissional de edição (estilo DaVinci Resolve / Linear).
- **Terminal Drawer:** Console retrátil em tempo real no rodapé com coloração de logs por nível (`[INFO]`, `[SUCCESS]`, `[WARN]`, `[ERROR]`).
- **Atalho Global:** Pressione `Ctrl + ~` (ou `Ctrl + \``) para abrir ou fechar o console a qualquer momento.

---

## Estrutura do Projeto

```text
Dark_print/
├── app/
│   ├── controllers/v1/      # Rotas da API FastAPI (SaaS, LLM, Tarefas)
│   ├── models/              # Schemas Pydantic e constantes
│   ├── services/            # Serviços centrais do motor
│   │   ├── autopilot.py     # Agendador e executor de perfis autônomos
│   │   ├── incompetech_bgm.py # Catálogo musical e gerador de licença
│   │   ├── material.py      # Busca híbrida (Archive.org, NASA, Wikimedia)
│   │   ├── monetization_funnel.py # Comentários fixados e cálculos de RPM
│   │   ├── sfx.py           # Síntese procedural de efeitos sonoros
│   │   ├── task.py          # Gerenciador de fila e orquestração de vídeo
│   │   ├── video.py         # Renderização e composição MoviePy/FFmpeg
│   │   └── viral_analytics.py # Análise de retenção e ganchos A/B
│   └── utils/               # Utilitários de sistema, cache e arquivos
├── resource/
│   ├── public/              # Interface Web (HTML, CSS, JS)
│   └── sfx/                 # Arquivos de efeitos sonoros sintetizados
├── test/
│   └── services/            # Bateria de testes unitários e de integração
├── config.toml.example      # Modelo de configurações locais
├── pyproject.toml           # Configuração de dependências do Python
└── start_studio.bat         # Inicializador rápido para Windows
```

---

## Requisitos do Sistema

- **Python:** 3.11 ou superior
- **FFmpeg:** Instalado e acessível no PATH do sistema operacional
- **Git**

---

## Instalação e Execução

### 1. Clonar o Repositório

```bash
git clone https://github.com/Glawther/Dark_print.git
cd Dark_print
```

### 2. Configurar o Ambiente Virtual

Recomendado via `uv`:
```bash
uv sync --frozen
```

Ou via `venv` e `pip`:
```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurar Credenciais (Opcional)

Copie o arquivo de exemplo caso deseje adicionar provedores opcionais de LLM ou APIs pagas:
```bash
cp config.toml.example config.toml
```

> **Nota:** As fontes de mídia livres (Archive.org, NASA, Wikimedia, Openverse) e a síntese de voz gratuita (Edge TTS) funcionam diretamente sem nenhuma chave de API configurada.

### 4. Iniciar o Studio

#### Windows
Execute o inicializador rápido:
```cmd
start_studio.bat
```

#### Linha de Comando (Qualquer Sistema)
```bash
python main.py
```

O servidor iniciará em **`http://127.0.0.1:8080`**. Acesse a URL no navegador para abrir o Painel de Produção.

---

## Executando os Testes

Para executar a bateria de testes automatizados:

```bash
python -m pytest test/services/test_archive_org.py test/services/test_autopilot.py test/services/test_incompetech.py test/services/test_monetization_funnel.py test/services/test_sfx.py test/services/test_viral_analytics.py -v
```

---

## Endpoints Principais da API

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/api/v1/saas/bgm/incompetech` | Pesquisa trilhas musicais por gênero, clima (*feel*) e BPM |
| `POST` | `/api/v1/saas/script/analyze` | Diagnóstico de retenção de roteiro e geração de ganchos A/B |
| `POST` | `/api/v1/saas/monetization/funnel` | Gera cópias de comentários fixados e cálculo de RPM |
| `POST` | `/api/v1/saas/autopilot/profiles` | Cadastra perfil de produção autônoma em segundo plano |
| `POST` | `/api/v1/saas/autopilot/trigger/{id}` | Dispara execução imediata de um perfil do piloto automático |
| `GET` | `/api/v1/saas/tasks/{id}/metadata` | Recupera metadados formatados para publicação do vídeo gerado |

---

## Licença

Este projeto é distribuído sob os termos da licença [MIT](LICENSE).
