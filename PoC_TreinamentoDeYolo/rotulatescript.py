from PIL import Image, ImageDraw
import os

PONTO_DE_ROTULACAO = (72, 45)  # Ponto central da área de captura para rotulação
TAMANHO_LADO_ROTULACAO = 41  # Tamanho do lado do quadrado em pixels (ajuste conforme necessário)
DESLOCAMENTO_ROTULACAO = 43  # Deslocamento para cada iteração de rotulação

PASTA_DATASET = "dataset"

# Calcular ROI baseada no ponto central e tamanho
def calcular_roi(centro, tamanho):
    x, y = centro
    meio = tamanho // 2
    return (x - meio, y - meio, x + meio, y + meio)

# Calcular ROI baseada no ponto central e tamanho
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



if __name__ == "__main__":
    # Obter o diretório atual
    pasta_atual = os.getcwd()
    pasta_dataset_completa = os.path.join(pasta_atual, PASTA_DATASET)

    # Verificar e criar pasta se necessário
    if not os.path.exists(pasta_dataset_completa):
        os.makedirs(pasta_dataset_completa)
        print(f"Pasta '{pasta_dataset_completa}' criada!")

    # Caminho completo da imagem
    caminho_imagem = os.path.join(pasta_dataset_completa, "pyro_0036.png")

    # Verificar se a imagem existe
    if not os.path.exists(caminho_imagem):
        print(f"Imagem não encontrada no caminho: {caminho_imagem}")
    else:
        # Abrir a imagem existente
        imagem = Image.open(caminho_imagem)

        # Coordenadas e tamanho do quadrado
        for i in range(0, 6):
            print(f"Coordenadas do ponto de rotulacao: {PONTO_DE_ROTULACAO}, Tamanho do lado: {TAMANHO_LADO_ROTULACAO}")
            coordenadas_rotulacao = PONTO_DE_ROTULACAO
            coordenadas_rotulacao = (coordenadas_rotulacao[0] + i * DESLOCAMENTO_ROTULACAO, coordenadas_rotulacao[1])
            tamanho_lado = TAMANHO_LADO_ROTULACAO
            imagem_com_contorno = desenhar_contorno(imagem, coordenadas_rotulacao, tamanho_lado)

            # Desenhar o contorno na imagem

            # Salvar ou exibir a imagem
            caminho_saida = os.path.join(pasta_dataset_completa, "pyro_0036_comcontorno.png")
            imagem_com_contorno.save(caminho_saida)

        imagem_com_contorno.show()