import contextlib
import keyboard
import pyautogui
from PIL import ImageGrab, ImageDraw
import threading
import time
import sys
import os

# Constantes de Arquivos
PASTA_DATASET = "dataset"
PREFIXO = "img"  # Altere para o elemento desejado (pyro, hydro, etc.)
PASTA_LABELS = "yolo_labels"

# Constantes para o novo modo de captura
HOTKEY_CAPTURA = "'"  # Tecla para iniciar/parar a captura
INTERVALO_CAPTURA = 0.2  # Segundos entre cada captura no loop
HOTKEY_SAIR = "\\"  # Tecla para finalizar o script


# Mapeamento de prefixos para IDs de classe YOLO (começando de 0)
CLASS_MAP = {"pyro": 0, "hydro": 1, "electro": 2, "cryo": 3, "dendro": 4}


# Constantes de Captura Manual
PONTO_INICIAL = (757, 923)  # Ponto central da área de captura
COMPRIMENTO = 380  # Comprimento do retângulo em pixels (ajuste conforme necessário)
LARGURA = 80  # Largura do retângulo em pixels (ajuste conforme necessário)

# Constantes de Captura Por Quadrado
PONTO_CENTRAL = (840, 922)  # Ponto central da área de captura
TAMANHO_LADO = 60  # Tamanho do lado do quadrado em pixels (ajuste conforme necessário)

# Constantes de Rotulação
PONTO_DE_ROTULACAO = (72, 45)  # Ponto central da área de captura para rotulação
TAMANHO_LADO_ROTULACAO = (
    41  # Tamanho do lado do quadrado em pixels (ajuste conforme necessário)
)
DESLOCAMENTO_ROTULACAO = 43  # Deslocamento para cada iteração de rotulação


# Calcular ROI baseada no ponto central e tamanho
def calcular_roi(centro, tamanho):
    x, y = centro
    meio = tamanho // 2
    return (x - meio, y - meio, x + meio, y + meio)


# Calcular ROI baseada no ponto inicial e dimensões do retângulo
def calcular_roi_manual(x_inicial, y_inicial, comprimento, largura):
    x_final = x_inicial + comprimento
    y_final = y_inicial + largura
    return (x_inicial, y_inicial, x_final, y_final)


def desenhar_contorno(imagem, coordenadas, tamanho_lado):
    """
    Desenha um contorno em formato de quadrado na imagem.

    Args:
        imagem (PIL.Image.Image): A imagem onde o contorno será desenhado.
        coordenadas (tuple): Coordenadas (x, y) do ponto central do quadrado.
        tamanho_lado (int): Tamanho do lado do quadrado.

    Returns:
        PIL.Image.Image: A imagem com o contorno desenhado.
    """
    ROI = calcular_roi(coordenadas, tamanho_lado)

    # Criar objeto de desenho
    draw = ImageDraw.Draw(imagem)

    # Desenhar o contorno
    draw.rectangle(ROI, outline="red", width=1)

    return imagem


def converter_para_yolo(
    largura_da_imagem, altura_da_imagem, coordenadas_em_pixel, id_classe
):
    """
    Converte coordenadas de bounding box em pixel para o formato YOLO.

    Args:
        largura_da_imagem (int): Largura da imagem em pixels.
        altura_da_imagem (int): Altura da imagem em pixels.
        coordenadas_em_pixel (tuple): Uma tupla de 4 elementos representando
                                        (x1, y1, x2, y2) do bounding box em pixel.
        id_classe (int): O ID da classe do objeto.

    Returns:
        str: A linha formatada para o arquivo YOLO (ID_classe centro_x centro_y largura altura).
    """
    x1, y1, x2, y2 = coordenadas_em_pixel

    # Calcular centro em pixel
    centro_x_pixel = (x1 + x2) / 2
    centro_y_pixel = (y1 + y2) / 2

    # Calcular largura e altura em pixel
    largura_pixel = x2 - x1
    altura_pixel = y2 - y1

    # Normalizar os valores
    centro_x_normalizado = centro_x_pixel / largura_da_imagem
    centro_y_normalizado = centro_y_pixel / altura_da_imagem
    largura_normalizada = largura_pixel / largura_da_imagem
    altura_normalizada = altura_pixel / altura_da_imagem

    return f"{id_classe} {centro_x_normalizado:.6f} {centro_y_normalizado:.6f} {largura_normalizada:.6f} {altura_normalizada:.6f}"


def proximo_numero(elemento):
    """
    Verifica o maior número de imagem existente na pasta e retorna o próximo número disponível.

    Args:
        elemento (str): Prefixo do nome do arquivo (ex.: 'pyro').

    Returns:
        int: Próximo número disponível para nomeação.
    """
    arquivos = os.listdir(PASTA_DATASET)
    numeros_existentes = []

    # Filtrar arquivos que correspondem ao padrão de nomeação
    for arquivo in arquivos:
        if arquivo.startswith(f"{elemento}_") and arquivo.endswith(".png"):
            with contextlib.suppress(ValueError, IndexError):
                numero = int(arquivo.split("_")[1].split(".")[0])
                numeros_existentes.append(numero)
    # Determinar o próximo número
    return max(numeros_existentes) + 1 if numeros_existentes else 1


# --- Inicialização ---
# Escolha o método de ROI (descomente o desejado)
# ROI = calcular_roi(PONTO_CENTRAL, TAMANHO_LADO)
# print(f"Capturando região quadrada de {TAMANHO_LADO}x{TAMANHO_LADO} pixels, centrada em {PONTO_CENTRAL}")

# ROI Manual (ativo por padrão no script original)
ROI = calcular_roi_manual(PONTO_INICIAL[0], PONTO_INICIAL[1], COMPRIMENTO, LARGURA)
print(
    f"Capturando região retangular de {COMPRIMENTO}x{LARGURA} pixels, iniciando em {PONTO_INICIAL}"
)

# Verificar e criar pasta se necessário
if not os.path.exists(PASTA_DATASET):
    os.makedirs(PASTA_DATASET)
    print(f"Pasta '{PASTA_DATASET}' criada!")

if not os.path.exists(PASTA_LABELS):
    os.makedirs(PASTA_LABELS)
    print(f"Pasta '{PASTA_LABELS}' criada!")

contador = proximo_numero(PREFIXO)

print(f"ROI calculada: {ROI}")
print(f"Próximo número para {PREFIXO}: {contador:04d}")
print(
    f"Pressione '{HOTKEY_CAPTURA}' para INICIAR/PARAR a captura (Mantenha o Genshin Impact em primeiro plano)"
)
print(f"Pressione '{HOTKEY_SAIR}' para sair do script")


def gerar_arquivo_yolo_label(
    caminho_imagem_salva, id_classe_atual, largura_img, altura_img
):
    """
    Gera um arquivo de rótulo YOLO para a imagem capturada com base nas constantes de rotulação.

    Args:
        caminho_imagem_salva (str): Caminho completo para o arquivo de imagem salvo.
        id_classe_atual (int): ID da classe para os objetos detectados.
        largura_img (int): Largura da imagem capturada.
        altura_img (int): Altura da imagem capturada.
    """
    nome_base_arquivo = os.path.splitext(os.path.basename(caminho_imagem_salva))[0]
    caminho_arquivo_label = os.path.join(PASTA_LABELS, f"{nome_base_arquivo}.txt")

    yolo_labels = []

    for i in range(6):
        centro_x_obj = PONTO_DE_ROTULACAO[0] + i * DESLOCAMENTO_ROTULACAO
        centro_y_obj = PONTO_DE_ROTULACAO[1]
        coords_pixel_obj = calcular_roi(
            (centro_x_obj, centro_y_obj), TAMANHO_LADO_ROTULACAO
        )
        yolo_string = converter_para_yolo(
            largura_img, altura_img, coords_pixel_obj, id_classe_atual
        )
        yolo_labels.append(yolo_string)

    with open(caminho_arquivo_label, "w") as f:
        for label_line in yolo_labels:
            f.write(label_line + "\n")
    print(f"Arquivo de rótulo YOLO salvo em: {caminho_arquivo_label}")


capturando_ativo = False
thread_captura = None


def capturar_screenshot():
    global contador
    try:
        # Capturar ROI
        screenshot = ImageGrab.grab(bbox=ROI)

        # Salvar imagem
        nome_arquivo = f"{PREFIXO}_{contador:04d}.png"
        caminho_completo = os.path.join(PASTA_DATASET, nome_arquivo)
        screenshot.save(caminho_completo, "PNG")

        print(f"Captura {nome_arquivo} salva!")

        # Gerar arquivo de rótulo YOLO
        id_classe = CLASS_MAP.get(
            PREFIXO, 0
        )  # Default para a classe 0 se PREFIXO não estiver no MAP
        gerar_arquivo_yolo_label(
            caminho_completo, id_classe, screenshot.width, screenshot.height
        )

        print(f"Posição do mouse: {pyautogui.position()}")
        contador += 1
    except Exception as e:
        print(f"Erro na captura: {str(e)}")


def loop_de_captura():
    global capturando_ativo
    print("Loop de captura INICIADO.")
    while capturando_ativo:
        capturar_screenshot()
        time.sleep(INTERVALO_CAPTURA)  # Ajuste o delay conforme necessário
    print("Loop de captura PARADO.")


def alternar_captura():
    global capturando_ativo, thread_captura, contador
    capturando_ativo = not capturando_ativo
    if capturando_ativo:
        # Opcional: resetar contador a cada início de loop.
        # Se desejar que o contador continue de onde parou entre sessões de loop, comente a linha abaixo.
        # contador = proximo_numero(PREFIXO)
        # print(f"Contador (re)iniciado para {PREFIXO}: {contador:04d}")

        print(f"Captura ATIVADA. Pressione '{HOTKEY_CAPTURA}' novamente para parar.")
        if thread_captura is None or not thread_captura.is_alive():
            thread_captura = threading.Thread(target=loop_de_captura, daemon=True)
            thread_captura.start()
    else:
        print(
            f"Captura DESATIVADA. Pressione '{HOTKEY_CAPTURA}' novamente para iniciar."
        )
        # A thread_captura irá parar por conta própria ao checar o valor de 'capturando_ativo'


def sair_script():
    global capturando_ativo, thread_captura
    print("Saindo do script...")
    capturando_ativo = False  # Sinaliza para o loop de captura parar

    if thread_captura and thread_captura.is_alive():
        print("Aguardando a thread de captura finalizar...")
        # Espera um pouco mais que um ciclo de captura para garantir que a thread termine
        thread_captura.join(timeout=INTERVALO_CAPTURA + 0.5)
        if thread_captura.is_alive():
            print("Timeout ao esperar a thread de captura. Forçando saída.")

    print("Removendo hotkeys...")
    keyboard.unhook_all()  # Remove todos os hotkeys

    print("Script finalizado.")
    sys.exit(0)  # Termina o processo Python


# Registrar hotkey
keyboard.add_hotkey(HOTKEY_CAPTURA, alternar_captura)
print("Script rodando em segundo plano...")

keyboard.wait(HOTKEY_SAIR)

sair_script