import os
import shutil
import glob
from collections import Counter
from sklearn.model_selection import train_test_split

# --- CONFIGURAÇÕES ---
# Modifique estes caminhos de acordo com sua estrutura de pastas

# Caminho para a pasta que contém TODAS as suas imagens e labels juntos.
# Exemplo: 'C:/Users/SeuUsuario/Desktop/yolo_dataset_completo/'
SOURCE_DIR = 'C:\\Users\\juand\\git\\pessoal\\IoTGameColors\\Etapa03_TreinamentoDoModelo\\dataset'

# Caminho para a pasta onde o dataset dividido (train\\val\\test) será criado.
# Exemplo: 'C:\\Users\\SeuUsuario\\Desktop\\dataset_yolo_dividido\\'
OUTPUT_DIR = 'C:\\Users\\juand\\git\\pessoal\\IoTGameColors\\Etapa03_TreinamentoDoModelo\\datasetFinal'

# Proporção da divisão. O restante irá para o treino.
# 0.3 significa 30% para teste e 70% para treino.
TEST_SPLIT_RATIO = 0.3

# Proporção da validação (opcional). Será retirado do conjunto de treino.
# 0.1 significa 10% do treino original irá para validação.
# Se não quiser um conjunto de validação, coloque 0.
VALIDATION_SPLIT_RATIO = 0.1

# Extensão dos seus arquivos de imagem (ex: '.jpg', '.png')
IMAGE_EXTENSION = '.png'

# --- FIM DAS CONFIGURAÇÕES ---


def get_class_stats(label_files):
    """Lê todos os arquivos de label e conta a frequência de cada classe."""
    class_counts = Counter()
    for label_file in label_files:
        # Adicionamos uma verificação para pular imagens que não têm um label correspondente
        if not os.path.exists(label_file):
            continue
        with open(label_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    class_id = int(line.strip().split()[0])
                    class_counts[class_id] += 1
                except (IndexError, ValueError):
                    # Silenciamos este aviso para não poluir a saída, mas você pode reativá-lo se precisar
                    # print(f"Aviso: Linha mal formatada ou vazia no arquivo {label_file}")
                    continue
    return class_counts

def get_label_path_from_image_path(image_path, image_extension):
    """
    Converte um caminho de imagem para o caminho de label correspondente.
    Assume que as imagens estão em uma pasta 'images' e os labels em uma
    pasta 'labels' no mesmo nível.
    Ex: .../dataset/images/img1.png -> .../dataset/labels/img1.txt
    """
    path_with_label_folder = image_path.replace(f"{os.sep}images{os.sep}", f"{os.sep}labels{os.sep}")
    base_name = os.path.splitext(path_with_label_folder)[0]
    return f'{base_name}.txt'

def get_image_stratify_key(label_file, class_rarity):
    """Determina a chave de estratificação para uma imagem (a classe mais rara nela)."""
    if not os.path.exists(label_file):
        # Retorna um valor especial para imagens sem label, para que sejam tratadas juntas.
        return -1 

    with open(label_file, 'r') as f:
        classes_in_image = set()
        for line in f:
            try:
                class_id = int(line.strip().split()[0])
                classes_in_image.add(class_id)
            except (IndexError, ValueError):
                continue

    if not classes_in_image:
        return -1 # Imagem com arquivo de label vazio

    return min(
        classes_in_image,
        key=lambda class_id: class_rarity.get(class_id, float('inf')),
    )


def main():
    """Função principal que executa a divisão estratificada."""
    print("Iniciando a divisão estratificada do dataset...")

    # Validação dos caminhos
    if not os.path.isdir(SOURCE_DIR):
        print(f"ERRO: O diretório de origem '{SOURCE_DIR}' não existe.")
        return
        
    # Encontrar todos os arquivos de imagem
    image_paths = glob.glob(os.path.join(SOURCE_DIR, f'**\\*{IMAGE_EXTENSION}'), recursive=True)
    if not image_paths:
        print(f"ERRO: Nenhuma imagem com extensão '{IMAGE_EXTENSION}' encontrada em '{SOURCE_DIR}'.")
        return
        
    label_paths = [get_label_path_from_image_path(p, IMAGE_EXTENSION) for p in image_paths]

    # 1. Obter estatísticas das classes para saber a raridade
    print("1/5 - Analisando a distribuição das classes...")
    class_rarity = get_class_stats(label_paths)
    if not class_rarity:
        print("Aviso: Nenhuma classe encontrada nos arquivos de label. A divisão será aleatória.")
    else:
        print(f"Distribuição de classes encontrada: {dict(class_rarity)}")


    # 2. Criar a lista de chaves para estratificação
    print("2/5 - Criando chaves de estratificação para cada imagem...")
    stratify_keys = [get_image_stratify_key(lp, class_rarity) for lp in label_paths]

    # 3. Primeira divisão: Treino+Validação vs. Teste
    print("3/5 - Dividindo em conjuntos de treino e teste...")
    
    # Usamos os caminhos das imagens como a lista principal a ser dividida
    # As stratify_keys garantem que a divisão seja equilibrada
    train_val_paths, test_paths, _, _ = train_test_split(
        image_paths, 
        stratify_keys, # A lista de chaves para estratificar
        test_size=TEST_SPLIT_RATIO,
        random_state=42 # Para resultados reproduzíveis
    )

    # 4. Segunda divisão (opcional): Treino vs. Validação
    if VALIDATION_SPLIT_RATIO > 0:
        print("4/5 - Dividindo o conjunto de treino em treino e validação...")
        # Recalcular as chaves de estratificação apenas para o conjunto de treino+validação
        train_val_labels = [get_label_path_from_image_path(p, IMAGE_EXTENSION) for p in train_val_paths]
        train_val_stratify_keys = [get_image_stratify_key(lp, class_rarity) for lp in train_val_labels]
        
        # Calcula a proporção de validação em relação ao novo conjunto (train_val)
        val_ratio_of_train_set = VALIDATION_SPLIT_RATIO / (1 - TEST_SPLIT_RATIO)

        train_paths, val_paths, _, _ = train_test_split(
            train_val_paths,
            train_val_stratify_keys,
            test_size=val_ratio_of_train_set,
            random_state=42
        )
    else:
        print("4/5 - Divisão de validação ignorada (ratio = 0).")
        train_paths = train_val_paths
        val_paths = []

    print("\n--- Resumo da Divisão ---")
    print(f"Imagens de Treino: {len(train_paths)}")
    if val_paths:
        print(f"Imagens de Validação: {len(val_paths)}")
    print(f"Imagens de Teste: {len(test_paths)}")
    print("-------------------------\n")


    # 5. Criar pastas e copiar os arquivos
    print("5/5 - Criando pastas e copiando arquivos...")
    sets = {'train': train_paths, 'val': val_paths, 'test': test_paths}

    for set_name, image_paths_in_set in sets.items():
        if not image_paths_in_set: 
            continue

        # Cria as pastas 'images' e 'labels' dentro de 'train', 'val', 'test'
        image_dest_dir = os.path.join(OUTPUT_DIR, set_name, 'images')
        label_dest_dir = os.path.join(OUTPUT_DIR, set_name, 'labels')
        os.makedirs(image_dest_dir, exist_ok=True)
        os.makedirs(label_dest_dir, exist_ok=True)

        # Copia os arquivos
        for img_path in image_paths_in_set:
            label_path = get_label_path_from_image_path(img_path, IMAGE_EXTENSION)
            
            # Copia a imagem
            shutil.copy(img_path, os.path.join(image_dest_dir, os.path.basename(img_path)))
            
            # Copia o label, se ele existir
            if os.path.exists(label_path):
                shutil.copy(label_path, os.path.join(label_dest_dir, os.path.basename(label_path)))
    
    print("\nDivisão concluída com sucesso!")
    print(f"O dataset dividido está em: '{OUTPUT_DIR}'")


if __name__ == '__main__':
    main()