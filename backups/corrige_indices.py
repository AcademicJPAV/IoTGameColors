import os

DIRETORIO_IMAGENS = "datasetFinalComElectro"
DIRETORIO_TXTS = "datasetFinalComElectro"

count = 1
MODO_ESCOLHIDO = 1  # Escolha o modo de renomeação: 0 ou 1,
# 0 para renomear pastas organizadas por tipo de elemento.
# 1 para renomear fotos e labels separadamente separadas nas pastas images e labels,
match MODO_ESCOLHIDO:
    case 0:
        for directory in os.listdir(DIRETORIO_IMAGENS):
            images_base = os.path.join(DIRETORIO_IMAGENS, directory)
            if os.path.isdir(images_base):
                for file in os.listdir(images_base):
                    if file.endswith(".png"):
                        old_base = os.path.splitext(file)[0]
                        new_base = f"imagem_{count}"
                        dir_path = images_base

                        # Renomeia o arquivo .png
                        os.rename(
                            os.path.join(dir_path, file),
                            os.path.join(dir_path, f"{new_base}.png"),
                        )

                        # Renomeia o arquivo .txt correspondente, se existir
                        txt_file = f"{old_base}.txt"
                        if os.path.exists(os.path.join(dir_path, txt_file)):
                            os.rename(
                                os.path.join(dir_path, txt_file),
                                os.path.join(dir_path, f"{new_base}.txt"),
                            )

                        count += 1
    case 1:
        images_base = os.path.join(DIRETORIO_IMAGENS, "images")
        txts_base = os.path.join(DIRETORIO_TXTS, "labels")
        fotos = os.listdir(images_base)
        txts = os.listdir(txts_base)
        for foto in fotos:
            new_name = f"imagem_{count}.png"
            old_name = os.path.join(images_base, foto)
            new_name_full = os.path.join(images_base, new_name)

            new_txt_name = f"imagem_{count}.txt"
            old_txt_name = os.path.join(txts_base, foto.replace(".png", ".txt"))
            new_txt_name_full = os.path.join(txts_base, new_txt_name)
            os.rename(old_name, new_name_full)
            os.rename(old_txt_name, new_txt_name_full)
            count += 1
