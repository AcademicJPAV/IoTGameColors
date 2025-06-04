import os
import contextlib
from PIL import ImageDraw, ImageGrab, Image
import pyautogui


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
    roi_coords = calcular_roi(coordenadas, tamanho_lado)

    # Criar objeto de desenho
    draw = ImageDraw.Draw(imagem)

    # Desenhar o contorno
    draw.rectangle(roi_coords, outline="red", width=1)

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


def proximo_numero(elemento, pasta_dataset):
    """
    Verifica o maior número de imagem existente na pasta e retorna o próximo número disponível.

    Args:
        elemento (str): Prefixo do nome do arquivo (ex.: 'pyro').
        pasta_dataset (str): Caminho para a pasta onde as imagens são salvas.

    Returns:
        int: Próximo número disponível para nomeação.
    """
    if not os.path.exists(pasta_dataset):
        return 1  # Retorna 1 se a pasta não existe

    arquivos = os.listdir(pasta_dataset)
    numeros_existentes = []

    # Filtrar arquivos que correspondem ao padrão de nomeação
    for arquivo in arquivos:
        if arquivo.startswith(f"{elemento}_") and arquivo.endswith(".png"):
            with contextlib.suppress(ValueError, IndexError):
                numero = int(arquivo.split("_")[1].split(".")[0])
                numeros_existentes.append(numero)
    # Determinar o próximo número
    return max(numeros_existentes) + 1 if numeros_existentes else 1


def gerar_arquivo_yolo_label(
    caminho_imagem_salva,
    id_classe_atual,
    largura_img,
    altura_img,
    pasta_labels,
    ponto_rotulacao_x_prop,
    ponto_rotulacao_y_prop,
    tamanho_lado_rotulacao_prop,
    deslocamento_rotulacao_x_prop,
):
    """
    Gera um arquivo de rótulo YOLO para a imagem capturada com base nas constantes de rotulação.

    Args:
        caminho_imagem_salva (str): Caminho completo para o arquivo de imagem salvo.
        id_classe_atual (int): ID da classe para os objetos detectados.
        largura_img (int): Largura da imagem capturada.
        altura_img (int): Altura da imagem capturada.
        pasta_labels (str): Caminho para a pasta onde os arquivos de label serão salvos.
        ponto_rotulacao_x_prop (float): Proporção X do ponto inicial de rotulação.
        ponto_rotulacao_y_prop (float): Proporção Y do ponto inicial de rotulação.
        tamanho_lado_rotulacao_prop (float): Proporção do tamanho do lado do quadrado de rotulação.
        deslocamento_rotulacao_x_prop (float): Proporção do deslocamento X entre rótulos.
    """
    nome_base_arquivo = os.path.splitext(os.path.basename(caminho_imagem_salva))[0]
    caminho_arquivo_label = os.path.join(pasta_labels, f"{nome_base_arquivo}.txt")

    yolo_labels = []

    for i in range(6):
        # Calcular o centro do objeto em pixels usando proporções e dimensões da imagem atual
        centro_x_obj_pixel = int(
            (ponto_rotulacao_x_prop + i * deslocamento_rotulacao_x_prop) * largura_img
        )
        centro_y_obj_pixel = int(ponto_rotulacao_y_prop * altura_img)

        # Calcular o tamanho do lado do quadrado de rotulação em pixels
        lado_rotulacao_pixel = int(tamanho_lado_rotulacao_prop * largura_img)

        coords_pixel_obj = calcular_roi(
            (centro_x_obj_pixel, centro_y_obj_pixel), lado_rotulacao_pixel
        )
        yolo_string = converter_para_yolo(
            largura_img,
            altura_img,
            coords_pixel_obj,
            id_classe_atual,
        )
        yolo_labels.append(yolo_string)

    with open(caminho_arquivo_label, "w") as f:
        for label_line in yolo_labels:
            f.write(label_line + "\n")
    print(f"Arquivo de rótulo YOLO salvo em: {caminho_arquivo_label}")


def capturar_e_processar_screenshot(
    roi_bbox,
    pasta_dataset,
    prefixo,
    contador_atual,
    class_map,
    pasta_labels,
    label_ponto_x_prop,
    label_ponto_y_prop,
    label_tamanho_lado_prop,
    label_deslocamento_x_prop,
):
    """
    Captura uma screenshot de uma ROI, salva e gera o arquivo de rótulo YOLO.

    Retorna:
        int: O próximo número do contador.
    """
    try:
        # Capturar ROI
        screenshot = ImageGrab.grab(bbox=roi_bbox)

        # Salvar imagem
        nome_arquivo = f"{prefixo}_{contador_atual:04d}.png"
        caminho_completo = os.path.join(pasta_dataset, nome_arquivo)
        screenshot.save(caminho_completo, "PNG")

        print(f"Captura {nome_arquivo} salva!")

        # Gerar arquivo de rótulo YOLO
        id_classe = class_map.get(
            prefixo, 0
        )  # Default para a classe 0 se PREFIXO não estiver no MAP
        gerar_arquivo_yolo_label(
            caminho_completo,
            id_classe,
            screenshot.width,
            screenshot.height,
            pasta_labels,
            label_ponto_x_prop,
            label_ponto_y_prop,
            label_tamanho_lado_prop,
            label_deslocamento_x_prop,
        )

        print(f"Posição do mouse: {pyautogui.position()}")
        return contador_atual + 1
    except Exception as e:
        print(f"Erro na captura: {str(e)}")
        return contador_atual


def processar_imagem_para_yolo(
    caminho_imagem_absoluto,
    pasta_dataset,
    prefixo,
    contador_atual,
    class_map,
    pasta_labels,
    crop_ponto_inicial_x_prop,
    crop_ponto_inicial_y_prop,
    crop_comprimento_prop,
    crop_largura_prop,
    label_ponto_x_prop,
    label_ponto_y_prop,
    label_tamanho_lado_prop,
    label_deslocamento_x_prop,
):
    """
    Processa uma imagem existente: recorta, salva e gera o arquivo de rótulo YOLO.

    Retorna:
        int: O próximo número do contador.
    """
    try:
        imagem = Image.open(caminho_imagem_absoluto)
        img_largura_original, img_altura_original = imagem.size

        crop_x_inicial = int(crop_ponto_inicial_x_prop * img_largura_original)
        crop_y_inicial = int(crop_ponto_inicial_y_prop * img_altura_original)
        crop_comprimento = int(crop_comprimento_prop * img_largura_original)
        crop_largura = int(crop_largura_prop * img_altura_original)

        coords_para_crop = calcular_roi_manual(
            crop_x_inicial, crop_y_inicial, crop_comprimento, crop_largura
        )
        imagem_recortada = imagem.crop(coords_para_crop)

        nome_arquivo_base = f"{prefixo}_{contador_atual:04d}"
        nome_arquivo_img = f"{nome_arquivo_base}.png"
        caminho_salvo_img = os.path.join(pasta_dataset, nome_arquivo_img)

        imagem_recortada.save(caminho_salvo_img, "PNG")
        print(f"Imagem original '{caminho_imagem_absoluto}' recortada e salva como '{nome_arquivo_img}' em '{pasta_dataset}'")

        id_classe = class_map.get(prefixo, 0)
        gerar_arquivo_yolo_label(caminho_salvo_img, id_classe, imagem_recortada.width, imagem_recortada.height, pasta_labels, label_ponto_x_prop, label_ponto_y_prop, label_tamanho_lado_prop, label_deslocamento_x_prop)
        return contador_atual + 1
    except Exception as e:
        print(f"Erro ao processar imagem '{caminho_imagem_absoluto}': {e}")
        return contador_atual
