# IoT Game Colors

## Descrição do Projeto

Este projeto utiliza um modelo de detecção de objetos (YOLOv12) para identificar elementos visuais específicos em um jogo (como *debuffs* de status) em tempo real. Com base nas detecções, ele se comunica com o Home Assistant para controlar dispositivos de IoT, como luzes inteligentes, criando uma experiência de imersão.

O fluxo de trabalho do projeto é dividido em cinco etapas principais:

1.  [**Captura de Imagens para Treinamento:**](#etapa-1-captura-de-imagens-para-treinamento) Coleta de imagens da tela do jogo para criar um dataset.
2.  [**Correção de Labels:**](#etapa-2-correção-de-labels) Ajuste e correção dos rótulos gerados para o dataset.
3. [**Preparação do Dataset e Treinamento:**](#etapa-31-divisão-do-dataset)
   1.  [**Divisão do Dataset:**](#etapa-31-divisão-do-dataset) Separação das imagens e rótulos em conjuntos de treino, validação e teste.
   2.  [**Treinamento do Modelo:**](#etapa-32-treinamento-do-modelo) Uso do dataset para treinar o modelo YOLO.
4.  [**Execução do Modelo:**](#etapa-4-execução-e-automação) Execução do modelo treinado para detecção em tempo real e automação.

---

## Pré-requisitos

- Python 3.13.2
- Git
- Uma instância do Home Assistant (para a funcionalidade completa)

### Instalação de Dependências

Clone o repositório e instale as dependências necessárias. É recomendado criar um ambiente virtual.

```bash
# Clone o repositório (substitua pela URL do seu repo)
git clone https://github.com/AcademicJPAV/IoTGameColors.git
cd IoTGameColors

# Crie e ative um ambiente virtual (opcional, mas recomendado)
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# Instale as dependências
pip install -r requirements_projeto_inteiro.txt
```

---

## Etapa 1: Captura de Imagens para Treinamento

Nesta etapa, usamos o script `capturescript.py` para criar o dataset de imagens que será usado para treinar o modelo.

**Localização:** [`Etapa01_CapturaDeImagensParaTreino/`](Etapa01_CapturaDeImagensParaTreino/)

### Configuração

Antes de executar, configure as constantes no início do arquivo `capturescript.py`:

- `PASTA_DATASET` e `PASTA_LABELS`: Pastas para salvar as imagens e os rótulos.
- `PREFIXO`: Um nome para o tipo de imagem que você está capturando (ex: "pyro", "hydro"). Isso será usado no nome do arquivo.
- `CLASS_MAP`: Um dicionário que mapeia o `PREFIXO` para um ID de classe numérico (ex: `{"pyro": 0}`).
- **Constantes de ROI e Rotulação:** Ajuste as proporções (`_PROP`) para definir a área de captura (ROI) e onde os rótulos de detecção serão gerados dentro dessa ROI.

### Execução

Execute o script a partir da pasta raiz do projeto:

```bash
python Etapa01_CapturaDeImagensParaTreino/capturescript.py
```

O script apresentará um menu:

1.  **Entrar no modo de captura de tela:**
    - Inicia um modo interativo para captura contínua.
    - Pressione a tecla definida em `HOTKEY_CAPTURA` (padrão: `'`) para iniciar e parar a captura de imagens da ROI definida.
    - Pressione `HOTKEY_SAIR` (padrão: `\`) para voltar ao menu principal.
2.  **Processar imagem existente:**
    - Permite recortar uma imagem já existente (por exemplo, um print da tela inteira) usando a mesma ROI e gerar o rótulo correspondente.
3.  **Sair:** Finaliza o script.

O script nomeia os arquivos de forma incremental (ex: `pyro_0001.png`, `pyro_0001.txt`) para cada `PREFIXO`.

---

## Etapa 2: Correção de Labels

Este script (`corrige_labels.py`) é um utilitário para corrigir os IDs de classe nos arquivos de rótulo `.txt` gerados na etapa anterior. Ele é útil se você capturou imagens para várias classes e precisa garantir que cada uma tenha o ID correto.

**Localização:** [`Etapa02_Correcao_De_Labels/`](Etapa02_Correcao_De_Labels/)

### Estrutura de Pastas Esperada

O script espera que seus dados estejam organizados em uma pasta `data`, com subpastas nomeadas de acordo com as classes. Por exemplo:

```
Etapa02_Correcao_De_Labels/
└── data/
    ├── Pyro_.../
    │   ├── img_0001.png
    │   └── img_0001.txt
    └── Hydro_.../
        ├── img_0002.png
        └── img_0002.txt
```

### Execução

Execute o script a partir de sua pasta:

```bash
cd Etapa02_Correcao_De_Labels
python corrige_labels.py
cd ..
```

O script irá ler o nome de cada subpasta, extrair a classe (ex: "Pyro"), encontrar o ID correspondente no `mapLabels` e reescrever o primeiro número de cada linha nos arquivos `.txt` com o ID correto.

---

## Etapa 3.1: Divisão do Dataset

Antes de treinar, o dataset precisa ser dividido em conjuntos de treino, validação e teste. O script `separarEmTreinoValETeste.py` automatiza esse processo de forma estratificada, garantindo que a proporção de classes seja semelhante em todos os conjuntos.

**Localização:** [`Etapa03_TreinamentoDoModelo/`](Etapa03_TreinamentoDoModelo/)

### Configuração

Abra o arquivo `separarEmTreinoValETeste.py` e ajuste as seguintes constantes:

-   `SOURCE_DIR`: Caminho para a pasta que contém **todas** as suas imagens e labels capturados.
-   `OUTPUT_DIR`: Caminho para a pasta onde o dataset dividido (`train/`, `val/`, `test/`) será criado.
-   `TEST_SPLIT_RATIO` e `VALIDATION_SPLIT_RATIO`: Proporções para dividir os dados.

### Execução

Execute o script a partir da pasta raiz do projeto:

```bash
python Etapa03_TreinamentoDoModelo/separarEmTreinoValETeste.py
```

Ao final, a pasta definida em `OUTPUT_DIR` conterá a estrutura de pastas pronta para o treinamento.

## Etapa 3.2: Treinamento do Modelo
Nesta etapa, o modelo YOLOv12 é treinado usando o dataset preparado na etapa anterior. O script `trainyolov12.py` cuida de todo o processo de treinamento, incluindo a criação do arquivo de configuração necessário para o YOLO.

**Localização:** [`Etapa03_TreinamentoDoModelo/`](Etapa03_TreinamentoDoModelo/)

### Organização do Dataset

Com o dataset organizado, o script `trainyolov12.py` cuida de todo o processo de treinamento. Ele primeiro cria o arquivo de configuração `.yaml` necessário para o YOLO e, em seguida, inicia o treinamento.

### Configuração

No arquivo `trainyolov12.py`, configure os parâmetros de treinamento:

-   `DATASET_DIR`: Deve ser o mesmo caminho do `OUTPUT_DIR` da etapa anterior.
-   `CLASS_NAMES`: A lista de nomes das classes, na ordem correta dos IDs.
-   `PRETRAINED_MODEL`: O modelo base a ser usado (ex: `yolov12n.pt`).
-   `EPOCHS`: O número de épocas para o treinamento.
-   `IMAGE_SIZE`: O tamanho das imagens a serem usadas no treinamento.

### Execução

Para iniciar o treinamento, execute:

```bash
python Etapa03_TreinamentoDoModelo/trainyolov12.py
```

O script irá criar o arquivo `.yaml`, carregar o modelo e iniciar o treinamento. Os resultados, incluindo o modelo treinado (`best.pt`), serão salvos na pasta `runs/detect/treino_yolov12_iot_colors_resultado`. Este arquivo `best.pt` é o que será usado na Etapa 4.

---

## Etapa 4: Execução e Automação

Nesta etapa, o modelo treinado é usado para detecção em tempo real. O script principal, `IotGameColorsScript.py`, integra a detecção com o Home Assistant.

**Localização:** [`Etapa04_ExecucaoModelo/`](Etapa04_ExecucaoModelo/)

### Configuração

1.  **Modelo:** Coloque seu modelo treinado no caminho especificado pela constante `MODEL_PATH` em `IotGameColorsScript.py`.
2.  **Home Assistant:**
    - Crie um arquivo `.env` na raiz do projeto com suas credenciais:
      ```
      HOME_ASSISTANT_URL=http://<seu-home-assistant-ip>:<sua-porta-caso-necessario>
      HOME_ASSISTANT_TOKEN=<seu-token-de-longa-duração>
      ```
    - Alternativamente, o script pedirá essas informações interativamente se o arquivo `.env` não for encontrado.

### Execução

Execute o script principal:

```bash
python Etapa04_ExecucaoModelo/IotGameColorsScript.py
```

O script irá guiá-lo através de um menu interativo:

1.  **Configuração do Home Assistant:** Conecta-se à sua instância e lista os dispositivos de iluminação disponíveis (áreas ou luzes individuais). Você escolherá qual alvo controlar.
2.  **Menu Principal:**
    - **Avaliar Métricas do Modelo:** Testa a performance do modelo no conjunto de teste definido no seu arquivo `.yaml`.
    - **Iniciar Detecção com Controle de Luz:** Inicia o processo de detecção.
3.  **Configuração da Detecção:**
    - **Alvo de Captura:** Escolha entre capturar um monitor inteiro ou uma janela de aplicativo específica.
    - **Modo de Captura:** Escolha entre desenhar uma área de recorte (ROI) manualmente ou usar uma ROI automática.
    - **Modo de Execução:**
        - **Debug:** Mostra uma janela com a detecção em tempo real.
        - **Produção:** Roda em segundo plano, sem visualização, para melhor performance. Você pode definir um limite de FPS.

Uma vez iniciado, o script detectará os elementos na área selecionada e enviará comandos para o Home Assistant, alterando a cor da sua luz de acordo com o "debuff" detectado no jogo.

### Script Inicial (`IotGameColorsScriptInicial.py`)

Este é um script mais simples, sem a integração com o Home Assistant. É útil para testar rapidamente o modelo e as funcionalidades de captura de tela. Ele oferece as opções de avaliar o modelo ou iniciar a detecção em tempo real, permitindo selecionar um monitor e desenhar uma ROI.
