import os
import sys
import cv2
import numpy as np
from ultralytics import YOLO
import mss

# --- CONFIGURAÇÕES GLOBAIS ---
MODEL_PATH = "./modelo_final_384px_300_epocas.pt"
DATA_YAML_PATH = "./iot_colors_dataset.yaml"
# --- FIM DAS CONFIGURAÇÕES ---


def avaliar_modelo():
    """
    Função para carregar o modelo e calcular as métricas de performance
    no conjunto de dados de teste definido no arquivo .yaml.
    """
    print("\n--- Modo de Avaliação de Métricas ---")
    try:
        model = YOLO(MODEL_PATH)
        print(f"Modelo '{MODEL_PATH}' carregado com sucesso.")
    except Exception as e:
        print(f"ERRO: Não foi possível carregar o modelo em '{MODEL_PATH}'.")
        print(f"Detalhes do erro: {e}")
        return
    print("\nIniciando avaliação no conjunto de teste...")
    try:
        metrics = model.val(data=DATA_YAML_PATH, split="test", verbose=False)
        print("\n--- Métricas de Performance no Conjunto de Teste ---")
        print("\n  Métricas de Previsão (quanto maior, melhor):")
        print(f"  - mAP50-95 (principal): {metrics.box.map:.4f}")
        print(f"  - mAP50 (popular):      {metrics.box.map50:.4f}")
        print(f"  - Precisão (Precision): {metrics.box.p[0]:.4f}")
        print(f"  - Recall (Recall):      {metrics.box.r[0]:.4f}")
    except Exception as e:
        print(f"ERRO: Falha ao avaliar o modelo. Verifique o caminho do dataset em '{DATA_YAML_PATH}'.")
        print(f"Detalhes do erro: {e}")


def iniciar_deteccao_tela():
    """
    Workflow aprimorado: primeiro seleciona um monitor, depois define
    se a captura será da tela inteira ou de uma região desenhada (ROI).
    """
    print("\n--- Modo de Detecção em Tempo Real ---")
    regiao_de_captura = None

    with mss.mss() as sct:
        # --- ETAPA 1: SELEÇÃO OBRIGATÓRIA DE MONITOR ---
        monitores = sct.monitors[1:]  # Ignora o monitor 0 (tela virtual combinada)
        if not monitores:
            print("ERRO: Nenhum monitor físico detectado.")
            return

        print("\n--- Monitores Físicos Detectados ---")
        for i, monitor in enumerate(monitores, 1):
            print(f"{i}: Tela {i} - {monitor['width']}x{monitor['height']} (Posição: {monitor['left']}, {monitor['top']})")

        monitor_selecionado = None
        while not monitor_selecionado:
            try:
                escolha_monitor = int(input("Primeiro, escolha o número do monitor para trabalhar: "))
                if 1 <= escolha_monitor <= len(monitores):
                    monitor_selecionado = monitores[escolha_monitor - 1]
                else:
                    print("Escolha inválida. Por favor, selecione um número da lista.")
            except ValueError:
                print("Entrada inválida. Por favor, digite um número.")
        
        # --- ETAPA 2: ESCOLHA ENTRE TELA INTEIRA OU ROI ---
        print(f"\nVocê selecionou a Tela {escolha_monitor}. O que deseja fazer?") # type: ignore
        print("1. Capturar esta tela inteira")
        print("2. Desenhar uma área de recorte (ROI) nesta tela")
        
        escolha_modo = input("Escolha uma opção (1-2): ")

        if escolha_modo == '1':
            regiao_de_captura = monitor_selecionado
        elif escolha_modo == '2':
            print("\nPreparando para selecionar a região...")
            print("Na janela que aparecer, clique e arraste para desenhar a área.")
            print("Pressione ENTER ou ESPAÇO para confirmar, ou ESC para cancelar.")
            
            # Captura uma imagem apenas do monitor selecionado para o usuário desenhar
            screenshot = sct.grab(monitor_selecionado)
            img_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGRA2BGR)
            
            # Usuário desenha a ROI na imagem daquele monitor
            roi = cv2.selectROI(f"Desenhe a area na Tela {escolha_monitor} e pressione ENTER", img_bgr, fromCenter=False) # type: ignore
            cv2.destroyAllWindows()

            if roi[2] == 0 or roi[3] == 0:
                print("Seleção de região cancelada.")
                return
            
            # CRÍTICO: Converte as coordenadas da ROI (que são relativas à janela) 
            # para coordenadas absolutas da tela, somando o deslocamento do monitor.
            regiao_de_captura = {
                'left': monitor_selecionado['left'] + roi[0],
                'top': monitor_selecionado['top'] + roi[1],
                'width': roi[2],
                'height': roi[3]
            }
        else:
            print("Opção inválida.")
            return
            
    # --- ETAPA 3: INICIAR DETECÇÃO ---
    if not regiao_de_captura:
        print("Nenhuma região de captura definida. Retornando ao menu.")
        return

    print(f"\nIniciando detecção na região: {regiao_de_captura}")
    print("Pressione a tecla 'q' na janela de visualização para sair.")

    try:
        model = YOLO(MODEL_PATH)
        print(f"Modelo '{MODEL_PATH}' carregado com sucesso.")
    except Exception as e:
        print(f"ERRO: Não foi possível carregar o modelo em '{MODEL_PATH}'.")
        print(f"Detalhes do erro: {e}")
        return

    try:
        with mss.mss() as sct:
            while True:
                img_mss = sct.grab(regiao_de_captura)
                frame_bgr = cv2.cvtColor(np.array(img_mss), cv2.COLOR_BGRA2BGR)
                results = model.predict(frame_bgr, verbose=False)
                annotated_frame = results[0].plot()
                cv2.imshow("Deteccao em Tempo Real | Pressione 'q' para sair", annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        print("Encerrando detecção em tempo real...")
        cv2.destroyAllWindows()


def main_menu():
    # Esta função continua a mesma.
    if not os.path.exists(MODEL_PATH):
        print(f"AVISO: O arquivo do modelo '{MODEL_PATH}' não foi encontrado.")
    if not os.path.exists(DATA_YAML_PATH):
        print(f"AVISO: O arquivo de dados '{DATA_YAML_PATH}' não foi encontrado.")

    while True:
        print("\n=============== MENU PRINCIPAL ================")
        print("1. Avaliar Métricas do Modelo no Conjunto de Teste")
        print("2. Iniciar Detecção em Tempo Real na Tela")
        print("3. Sair")
        print("=============================================")
        escolha = input("Escolha uma opção (1-3): ")
        if escolha == "1":
            avaliar_modelo()
        elif escolha == "2":
            iniciar_deteccao_tela()
        elif escolha == "3":
            print("Saindo do programa...")
            sys.exit(0)
        else:
            print("Opção inválida. Por favor, tente novamente.")
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    main_menu()