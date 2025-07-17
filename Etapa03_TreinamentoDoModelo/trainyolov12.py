import os
import yaml
from ultralytics import YOLO
# --- CONFIGURAÇÕES ---

# Caminho para a pasta do dataset final, criada pelo script anterior.
DATASET_DIR = '/content/datasetFinal'

# Nome do arquivo de configuração do dataset que será criado.
DATA_YAML_NAME = 'iot_colors_dataset.yaml'

# Nomes das classes do seu dataset.
# A ordem DEVE ser a mesma dos IDs nos seus arquivos .txt.
CLASS_NAMES = [
    "Pyro",
    "Hydro",
    "Electro",
    "Cryo",
    "Dendro"
]

# Com base na documentação oficial, agora podemos usar os modelos da família v12.
# A escolha do tamanho (n, s, m, l, x) depende do seu objetivo de precisão vs. velocidade.
PRETRAINED_MODEL = 'yolo12n.pt'

# Parâmetros de treinamento.
EPOCHS = 200      # Número de épocas (ciclos de treinamento completos).
IMAGE_SIZE = 380  # Tamanho da imagem para o treinamento.

# --- FIM DAS CONFIGURAÇÕES ---


def create_dataset_yaml(dataset_dir, class_names, yaml_name):
    """Cria o arquivo .yaml de configuração do dataset para o YOLO."""

    yaml_path = os.path.join(dataset_dir, yaml_name)
    if os.path.exists(yaml_path):
        print(f"Arquivo de configuração '{yaml_path}' já existe. Usando o existente.")
        return yaml_path
    # Converte o caminho para um caminho absoluto.
    # Isso elimina qualquer ambiguidade sobre onde o dataset está localizado.
    abs_dataset_dir = os.path.abspath(dataset_dir)

    data = {
        # Usa o caminho absoluto no arquivo de configuração.
        'path': abs_dataset_dir,
        'train': 'train/images',
        'val': 'val/images',  # O YOLO precisa deste caminho, mesmo que a pasta não exista.
        'test': 'test/images', # Opcional, mas bom ter.
        'names': dict(enumerate(class_names)),
    }

    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"Arquivo de configuração do dataset '{yaml_path}' criado com sucesso.")
    return yaml_path


def main():
    """Função principal para treinar e testar o modelo."""

    # 1. Criar o arquivo de configuração do dataset
    data_yaml_path = create_dataset_yaml(DATASET_DIR, CLASS_NAMES, DATA_YAML_NAME)

    # 2. Carregar um modelo YOLOv12 pré-treinado
    print(f"Carregando modelo pré-treinado: {PRETRAINED_MODEL}")
    model = YOLO(PRETRAINED_MODEL)

    # 3. Treinar o modelo
    print(f"\nIniciando o treinamento do modelo com base no {PRETRAINED_MODEL}...")
    model.train(
        data=data_yaml_path,
        epochs=EPOCHS,
        project='runs/detect',
        name='treino_yolov12_iot_colors_resultado',
        workers=26,
        batch=64,
        patience=100,
        imgsz=IMAGE_SIZE
    )

    print("\nTreinamento concluído!")
    print("Verifique a pasta 'runs/detect/treino_yolov12_iot_colors_resultado' para todos os resultados.")
    print("O melhor modelo foi salvo como 'best.pt' dentro dessa pasta.")


if __name__ == '__main__':
    main()