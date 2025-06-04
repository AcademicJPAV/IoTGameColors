import keyboard
import pyautogui
import threading
import time
import sys
import os
import utils_functions

# Constantes de Arquivos
PASTA_DATASET = "dataset"
PREFIXO = "img"  # Altere para o elemento desejado (pyro, hydro, etc.)
PASTA_LABELS = "dataset"

# Constantes para o novo modo de captura
HOTKEY_CAPTURA = "'"  # Tecla para iniciar/parar a captura
INTERVALO_CAPTURA = 0.2  # Segundos entre cada captura no loop
HOTKEY_SAIR = "\\"  # Tecla para finalizar o script


# Mapeamento de prefixos para IDs de classe YOLO (começando de 0)
CLASS_MAP = {"pyro": 0, "hydro": 1, "electro": 2, "cryo": 3, "dendro": 4}

# Constantes de Resolução Base para cálculo de proporções
BASE_LARGURA_TELA = 1920
BASE_ALTURA_TELA = 1080

# Constantes de Captura Manual (Proporções baseadas em BASE_LARGURA_TELA x BASE_ALTURA_TELA)
PONTO_INICIAL_X_PROP = 757 / BASE_LARGURA_TELA
PONTO_INICIAL_Y_PROP = 923 / BASE_ALTURA_TELA
COMPRIMENTO_ROI_PROP = 380 / BASE_LARGURA_TELA  # Proporção da largura da tela
LARGURA_ROI_PROP = 80 / BASE_ALTURA_TELA  # Proporção da altura da tela

# Constantes de Captura Por Quadrado (Proporções)
# Estes são fornecidos como proporções, mas não são usados ativamente no fluxo principal de captura/processamento.
PONTO_CENTRAL_X_PROP = 840 / BASE_LARGURA_TELA
PONTO_CENTRAL_Y_PROP = 922 / BASE_ALTURA_TELA
TAMANHO_LADO_PROP = (
    60 / BASE_LARGURA_TELA
)  # Lado do quadrado como proporção da largura da tela

# Constantes de Rotulação (Valores de pixel originais dentro da ROI de referência)
# PONTO_DE_ROTULACAO original era (72, 45) dentro da ROI de 380x80
PONTO_ROTULACAO_X_ORIGINAL = 72
PONTO_ROTULACAO_Y_ORIGINAL = 45
# TAMANHO_LADO_ROTULACAO original era 41
TAMANHO_LADO_ROTULACAO_ORIGINAL = 41
# DESLOCAMENTO_ROTULACAO original era 43
DESLOCAMENTO_ROTULACAO_X_ORIGINAL = 43

# Dimensões da ROI original (Captura Manual) que servem de referência para as proporções de rotulação
LARGURA_BASE_ROI_ROTULACAO = 380
ALTURA_BASE_ROI_ROTULACAO = 80

# Constantes de Rotulação (Proporções relativas às dimensões da ROI de referência)
PONTO_ROTULACAO_X_PROP = PONTO_ROTULACAO_X_ORIGINAL / LARGURA_BASE_ROI_ROTULACAO
PONTO_ROTULACAO_Y_PROP = PONTO_ROTULACAO_Y_ORIGINAL / ALTURA_BASE_ROI_ROTULACAO
TAMANHO_LADO_ROTULACAO_PROP = (
    TAMANHO_LADO_ROTULACAO_ORIGINAL / LARGURA_BASE_ROI_ROTULACAO
)
DESLOCAMENTO_ROTULACAO_X_PROP = (
    DESLOCAMENTO_ROTULACAO_X_ORIGINAL / LARGURA_BASE_ROI_ROTULACAO
)


# Variáveis globais para o estado da captura de tela
capturando_ativo_global = False
thread_captura_global = None
parar_modo_captura_flag = False  # Flag para sair do loop do modo de captura

# Variáveis globais que serão inicializadas em main()
ROI = None
contador = 0  # Será inicializado corretamente pela função proximo_numero


def capturar_screenshot():
    global contador, ROI, PASTA_DATASET, PREFIXO, CLASS_MAP, PASTA_LABELS
    global \
        PONTO_ROTULACAO_X_PROP, \
        PONTO_ROTULACAO_Y_PROP, \
        TAMANHO_LADO_ROTULACAO_PROP, \
        DESLOCAMENTO_ROTULACAO_X_PROP

    novo_contador = utils_functions.capturar_e_processar_screenshot(
        roi_bbox=ROI,
        pasta_dataset=PASTA_DATASET,
        prefixo=PREFIXO,
        contador_atual=contador,
        class_map=CLASS_MAP,
        pasta_labels=PASTA_LABELS,
        label_ponto_x_prop=PONTO_ROTULACAO_X_PROP,
        label_ponto_y_prop=PONTO_ROTULACAO_Y_PROP,
        label_tamanho_lado_prop=TAMANHO_LADO_ROTULACAO_PROP,
        label_deslocamento_x_prop=DESLOCAMENTO_ROTULACAO_X_PROP,
    )
    contador = novo_contador


def loop_de_captura_wrapper():
    global capturando_ativo_global
    print("Loop de captura INICIADO.")
    while capturando_ativo_global:
        capturar_screenshot()
        time.sleep(INTERVALO_CAPTURA)  # Ajuste o delay conforme necessário
    print("Loop de captura PARADO.")


def alternar_captura_wrapper():
    global capturando_ativo_global, thread_captura_global, contador
    capturando_ativo_global = not capturando_ativo_global
    if capturando_ativo_global:
        print(f"Captura ATIVADA. Pressione '{HOTKEY_CAPTURA}' novamente para parar.")
        if thread_captura_global is None or not thread_captura_global.is_alive():
            thread_captura_global = threading.Thread(
                target=loop_de_captura_wrapper, daemon=True
            )
            thread_captura_global.start()
    else:
        print(
            f"Captura DESATIVADA. Pressione '{HOTKEY_CAPTURA}' novamente para iniciar."
        )


def sinalizar_parada_modo_captura():
    global parar_modo_captura_flag, capturando_ativo_global, thread_captura_global
    print("Sinalizando para sair do modo de captura...")
    capturando_ativo_global = False  # Sinaliza para o loop de captura parar

    if thread_captura_global and thread_captura_global.is_alive():
        print("Aguardando a thread de captura finalizar...")
        thread_captura_global.join(timeout=INTERVALO_CAPTURA + 0.5)
        if thread_captura_global.is_alive():
            print("Timeout ao esperar a thread de captura.")

    parar_modo_captura_flag = True


def iniciar_modo_captura_tela():
    global \
        capturando_ativo_global, \
        thread_captura_global, \
        parar_modo_captura_flag, \
        contador, \
        ROI

    capturando_ativo_global = False
    thread_captura_global = None
    parar_modo_captura_flag = False

    print("\n--- Modo de Captura de Tela ---")
    print(f"ROI para captura: {ROI}")
    print(f"Próximo número para {PREFIXO}: {contador:04d}")
    print(f"Pressione '{HOTKEY_CAPTURA}' para INICIAR/PARAR a captura.")
    print(f"Pressione '{HOTKEY_SAIR}' para RETORNAR AO MENU PRINCIPAL.")

    hotkeys_modo_captura = []
    try:
        hotkeys_modo_captura.extend(
            (
                keyboard.add_hotkey(HOTKEY_CAPTURA, alternar_captura_wrapper),
                keyboard.add_hotkey(HOTKEY_SAIR, sinalizar_parada_modo_captura),
            )
        )
        print("Modo de captura ativo. Aguardando comandos...")
        while not parar_modo_captura_flag:
            time.sleep(0.1)

    finally:
        print("Saindo do modo de captura.")
        for hk in hotkeys_modo_captura:
            keyboard.remove_hotkey(hk)

        # Garante que a thread de captura pare se estiver ativa ao sair
        if capturando_ativo_global:
            capturando_ativo_global = False
            if thread_captura_global and thread_captura_global.is_alive():
                thread_captura_global.join(timeout=INTERVALO_CAPTURA + 0.1)
        print("Retornando ao menu principal.")


def modo_processar_imagem():
    global contador, PREFIXO, PASTA_DATASET, PASTA_LABELS, CLASS_MAP
    global \
        PONTO_INICIAL_X_PROP, \
        PONTO_INICIAL_Y_PROP, \
        COMPRIMENTO_ROI_PROP, \
        LARGURA_ROI_PROP
    global \
        PONTO_ROTULACAO_X_PROP, \
        PONTO_ROTULACAO_Y_PROP, \
        TAMANHO_LADO_ROTULACAO_PROP, \
        DESLOCAMENTO_ROTULACAO_X_PROP
    print("\n--- Modo de Processamento de Imagem Existente ---")
    caminho_relativo = input(
        "Digite o caminho relativo da imagem (ex: minha_imagem.png): "
    )
    caminho_absoluto = os.path.abspath(caminho_relativo)

    if not os.path.exists(caminho_absoluto):
        print(f"Erro: Imagem não encontrada em {caminho_absoluto}")
        return

    novo_contador = utils_functions.processar_imagem_para_yolo(
        caminho_imagem_absoluto=caminho_absoluto,
        pasta_dataset=PASTA_DATASET,
        prefixo=PREFIXO,
        contador_atual=contador,
        class_map=CLASS_MAP,
        pasta_labels=PASTA_LABELS,
        crop_ponto_inicial_x_prop=PONTO_INICIAL_X_PROP,
        crop_ponto_inicial_y_prop=PONTO_INICIAL_Y_PROP,
        crop_comprimento_prop=COMPRIMENTO_ROI_PROP,
        crop_largura_prop=LARGURA_ROI_PROP,
        label_ponto_x_prop=PONTO_ROTULACAO_X_PROP,
        label_ponto_y_prop=PONTO_ROTULACAO_Y_PROP,
        label_tamanho_lado_prop=TAMANHO_LADO_ROTULACAO_PROP,
        label_deslocamento_x_prop=DESLOCAMENTO_ROTULACAO_X_PROP,
    )

    if novo_contador > contador:  # Verifica se o processamento foi bem sucedido
        contador = novo_contador
        print(f"Próximo número para {PREFIXO}: {contador:04d}")


def main_menu():
    global contador  # Garante que o contador global seja usado e atualizado

    while True:
        print("\nMenu Principal:")
        print("1. Entrar no modo de captura de tela")
        print("2. Processar imagem existente")
        print("3. Sair")

        escolha = input("Escolha uma opção (1-3): ")

        if escolha == "1":
            iniciar_modo_captura_tela()
        elif escolha == "2":
            modo_processar_imagem()
        elif escolha == "3":
            print("Saindo do script...")
            keyboard.unhook_all()  # Remove todos os hotkeys registrados
            sys.exit(0)
        else:
            print("Opção inválida. Por favor, tente novamente.")


if __name__ == "__main__":
    # --- Inicialização ---
    # Obter dimensões da tela atual para calcular o ROI em pixels
    largura_tela_atual, altura_tela_atual = pyautogui.size()

    # Calcular PONTO_INICIAL em pixels para a tela atual
    roi_x_inicial = int(PONTO_INICIAL_X_PROP * largura_tela_atual)
    roi_y_inicial = int(PONTO_INICIAL_Y_PROP * altura_tela_atual)
    # Calcular COMPRIMENTO e LARGURA do ROI em pixels para a tela atual
    roi_comprimento = int(COMPRIMENTO_ROI_PROP * largura_tela_atual)
    roi_largura = int(LARGURA_ROI_PROP * altura_tela_atual)

    ROI = utils_functions.calcular_roi_manual(
        roi_x_inicial,
        roi_y_inicial,
        roi_comprimento,
        roi_largura,  # pyright: ignore [reportArgumentType]
    )

    if not os.path.exists(PASTA_DATASET):
        os.makedirs(PASTA_DATASET)
        print(f"Pasta '{PASTA_DATASET}' criada!")
    if not os.path.exists(PASTA_LABELS):
        os.makedirs(PASTA_LABELS)
        print(f"Pasta '{PASTA_LABELS}' criada!")

    contador = utils_functions.proximo_numero(
        PREFIXO, PASTA_DATASET
    )  # Inicializa o contador global
    print(
        f"Usando prefixo: {PREFIXO}. Próximo número de arquivo inicial: {contador:04d}"
    )

    main_menu()
