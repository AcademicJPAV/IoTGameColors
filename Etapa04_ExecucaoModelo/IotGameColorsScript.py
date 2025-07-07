import os
import sys
import getpass
import requests
import cv2
import numpy as np
from ultralytics import YOLO
import mss
import pygetwindow as gw
from dotenv import load_dotenv
import time

# --- CONFIGURAÇÕES GLOBAIS ---
MODEL_PATH = "C:/Users/juand/git/pessoal/IoTGameColors/PoC_ExecucaoModelo/modeloIoTColorsCorrigidoFinal.pt"
DATA_YAML_PATH = "C:/Users/juand/git/pessoal/IoTGameColors/PoC_TreinamentoDoModelo/datasetFinal/iot_colors_dataset.yaml"


# --- CLASSE DA MÁQUINA DE ESTADOS ---
class DebuffStateMachine:
    """
    Gerencia os estados de debuff com base em detecções confirmadas e controla
    dispositivos do Home Assistant via API.
    """

    STATE_NEUTRO, STATE_PYRO, STATE_HYDRO, STATE_ELECTRO, STATE_CRYO, STATE_DENDRO = (
        "NEUTRO",
        "PYRO",
        "HYDRO",
        "ELECTRO",
        "CRYO",
        "DENDRO",
    )

    CONFIRMATION_THRESHOLD = 2

    def __init__(
        self,
        ha_url: str,
        ha_token: str,
        target_id,
        target_type: str,
        neutral_action: dict,
    ):
        self.ha_url = ha_url
        self.target_id = target_id
        self.target_type = target_type
        self.headers = {
            "Authorization": f"Bearer {ha_token}",
            "Content-Type": "application/json",
        }

        self.current_state = self.STATE_NEUTRO
        self.candidate_state = self.STATE_NEUTRO
        self.detection_counter = 0

        self.states_config = {
            self.STATE_ELECTRO: {
                "priority": 0,
                "detection_name": "Electro",
                "action": {
                    "service": "turn_on",
                    "rgb_color": [200, 0, 255],
                    "brightness_pct": 100,
                },
            },
            self.STATE_CRYO: {
                "priority": 1,
                "detection_name": "Cryo",
                "action": {
                    "service": "turn_on",
                    "rgb_color": [200, 255, 255],
                    "brightness_pct": 100,
                },
            },
            self.STATE_DENDRO: {
                "priority": 2,
                "detection_name": "Dendro",
                "action": {
                    "service": "turn_on",
                    "rgb_color": [200, 255, 0],
                    "brightness_pct": 100,
                },
            },
            self.STATE_HYDRO: {
                "priority": 3,
                "detection_name": "Hydro",
                "action": {
                    "service": "turn_on",
                    "rgb_color": [0, 100, 255],
                    "brightness_pct": 100,
                },
            },
            self.STATE_PYRO: {
                "priority": 4,
                "detection_name": "Pyro",
                "action": {
                    "service": "turn_on",
                    "rgb_color": [255, 100, 0],
                    "brightness_pct": 100,
                },
            },
            self.STATE_NEUTRO: {
                "priority": 99,
                "detection_name": None,
                "action": neutral_action,
            },
        }

        self.detection_to_state_map = {
            conf["detection_name"]: state
            for state, conf in self.states_config.items()
            if conf["detection_name"]
        }

        print("\n[Máquina de Estados Otimizada] Pronta para operar.")
        self._make_api_call(self.STATE_NEUTRO)

    def _make_api_call(self, state: str):
        action = self.states_config[state]["action"]
        if not action:
            return

        service = action.get("service")
        if not service:
            return

        url = f"{self.ha_url}/api/services/light/{service}"

        body = {}
        if self.target_type in ["floor", "area"]:
            body["area_id"] = self.target_id
        elif self.target_type == "entity":
            body["entity_id"] = self.target_id
        else:
            return

        if service == "turn_on":
            for key in [
                "rgb_color",
                "hs_color",
                "color_temp",
                "brightness",
                "brightness_pct",
            ]:
                if key in action:
                    body[key] = action[key]
        try:
            requests.post(
                url, headers=self.headers, json=body, timeout=5
            ).raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[API] ERRO: Falha na comunicação com o Home Assistant: {e}")

    def _determine_potential_state(self, detected_classes: set) -> str:
        if not detected_classes:
            return self.STATE_NEUTRO

        if found_states := {
            self.detection_to_state_map[name]
            for name in detected_classes
            if name in self.detection_to_state_map
        }:
            return min(
                found_states, key=lambda state: self.states_config[state]["priority"]
            )
        else:
            return self.STATE_NEUTRO

    def process_detections(self, detected_classes: set):
        potential_state = self._determine_potential_state(detected_classes)

        if potential_state == self.candidate_state:
            self.detection_counter += 1
        else:
            print(
                f"[Estado] Novo estado potencial detectado: '{potential_state}'. Resetando contagem."
            )
            self.candidate_state = potential_state
            self.detection_counter = 1

        if (
            self.detection_counter >= self.CONFIRMATION_THRESHOLD
            and self.candidate_state != self.current_state
        ):
            print(
                f"[Estado] MUDANÇA CONFIRMADA: De '{self.current_state}' para '{self.candidate_state}'"
            )
            self.current_state = self.candidate_state
            self._make_api_call(self.current_state)
            self.detection_counter = 0


# --- FUNÇÕES DE SETUP, AVALIAÇÃO E OPERAÇÃO ---
def setup_interactive():  # sourcery skip: low-code-quality
    """Guia o usuário pela configuração completa, com fallback para .env."""
    print("--- Configuração do Home Assistant ---")
    load_dotenv()
    ha_url = os.getenv("HOME_ASSISTANT_URL")
    ha_token = os.getenv("HOME_ASSISTANT_TOKEN")

    if ha_url and ha_token:
        print("[Configuração] Arquivo .env encontrado. Usando credenciais salvas.")
    else:
        print("[Configuração] Arquivo .env não encontrado. Iniciando modo interativo.")
        ha_url = input(
            "Digite o URL do seu Home Assistant (ex: http://homeassistant.local:8123): "
        )
        ha_token = getpass.getpass("Digite seu Token de Acesso de Longa Duração: ")

    if not ha_url or not ha_token:
        print("URL e Token são obrigatórios.")
        return None

    headers = {
        "Authorization": f"Bearer {ha_token}",
        "Content-Type": "application/json",
    }
    template_body = {
        "template": '{ "areas": [ {% set comma = namespace(needed=false) %}{% for area in areas() %}{% set lights = area_entities(area) | select(\'search\', \'^light\\.\') | list %}{% if lights %}{% if comma.needed %},{% endif %}{ "area_name": "{{ area_name(area) }}", "area_id": "{{ area }}", "lights": [ {% for light in lights %}{ "entity_id": "{{ light }}"}{% if not loop.last %},{% endif %}{% endfor %} ] }{% set comma.needed = true %}{% endif %}{% endfor %} ] }'
    }

    try:
        print("\nBuscando dispositivos no Home Assistant...")
        response_areas = requests.post(
            f"{ha_url}/api/template", headers=headers, json=template_body, timeout=10
        )
        response_areas.raise_for_status()
        areas_data = response_areas.json().get("areas", [])

        response_states = requests.get(
            f"{ha_url}/api/states", headers=headers, timeout=10
        )
        response_states.raise_for_status()
        all_entities = response_states.json()

        selectable_targets, lights_in_areas = [], set()
        for area in areas_data:
            if area["lights"]:
                selectable_targets.append(
                    {
                        "display": f"Área: {area['area_name']}",
                        "id": area["area_id"],
                        "type": "area",
                        "ref_light": area["lights"][0]["entity_id"],
                    }
                )
                for light in area["lights"]:
                    lights_in_areas.add(light["entity_id"])

        standalone_lights = [
            e
            for e in all_entities
            if e["entity_id"].startswith("light.")
            and e["entity_id"] not in lights_in_areas
        ]
        selectable_targets.extend(
            {
                "display": f"Luz: {light['attributes'].get('friendly_name', light['entity_id'])}",
                "id": light["entity_id"],
                "type": "entity",
                "ref_light": light["entity_id"],
            }
            for light in standalone_lights
        )
        if not selectable_targets:
            print("Nenhum alvo de luz encontrado.")
            return None

        print("\n--- Alvos Encontrados (Áreas e Luzes Individuais) ---")
        for i, target in enumerate(selectable_targets, 1):
            print(f"{i}: {target['display']}")

        selected_target = None
        while not selected_target:
            try:
                choice = int(
                    input("Escolha o NÚMERO do alvo que você quer controlar: ")
                )
                if 1 <= choice <= len(selectable_targets):
                    selected_target = selectable_targets[choice - 1]
                else:
                    print("Escolha inválida.")
            except ValueError:
                print("Entrada inválida. Digite um número.")

        print("\n--- Definir Ação para o Estado Neutro ---")
        print(
            "1. Voltar ao estado atual da lâmpada (Recomendado)\n2. Desligar a lâmpada"
        )

        neutral_action = None
        while not neutral_action:
            choice_neutral = input("Escolha a ação para o estado Neutro (1-2): ")
            if choice_neutral == "2":
                neutral_action = {"service": "turn_off"}
            elif choice_neutral == "1":
                ref_light_id = selected_target["ref_light"]
                print(
                    f"Buscando estado atual da lâmpada de referência ({ref_light_id})..."
                )
                response_light = requests.get(
                    f"{ha_url}/api/states/{ref_light_id}", headers=headers, timeout=10
                )
                response_light.raise_for_status()
                light_state = response_light.json()

                if light_state["state"] == "off":
                    neutral_action = {"service": "turn_off"}
                else:
                    attrs = light_state["attributes"]
                    neutral_action = {"service": "turn_on"}
                    if attrs.get("color_mode") == "hs" and "hs_color" in attrs:
                        neutral_action["hs_color"] = attrs["hs_color"]
                    elif (
                        attrs.get("color_mode") == "color_temp"
                        and "color_temp" in attrs
                    ):
                        neutral_action["color_temp"] = attrs["color_temp"]
                    else:
                        neutral_action["rgb_color"] = [255, 251, 230]  # type: ignore
                    if "brightness" in attrs:
                        neutral_action["brightness"] = attrs["brightness"]
            else:
                print("Opção inválida.")

        print(f"Estado Neutro definido como: {neutral_action}")
        return {
            "url": ha_url,
            "token": ha_token,
            "target_id": selected_target["id"],
            "target_type": selected_target["type"],
            "neutral_action": neutral_action,
        }
    except requests.exceptions.RequestException as e:
        print(
            f"ERRO: Não foi possível conectar ao Home Assistant. Verifique o URL e o Token.\nDetalhe: {e}"
        )
        return None


def avaliar_modelo(model: YOLO):
    """Calcula as métricas de performance no conjunto de teste."""
    print("\n--- Modo de Avaliação de Métricas ---")
    try:
        if not os.path.exists(DATA_YAML_PATH):
            print(f"ERRO: Arquivo de dados '{DATA_YAML_PATH}' não encontrado.")
            return
        metrics = model.val(data=DATA_YAML_PATH, split="test", verbose=False)
        print("\n--- Métricas de Performance no Conjunto de Teste ---")
        print(
            f"  - mAP50-95 (principal): {metrics.box.map:.4f}, mAP50 (popular): {metrics.box.map50:.4f}"
        )
        print(
            f"  - Precisão (Precision): {metrics.box.p[0]:.4f}, Recall (Recall): {metrics.box.r[0]:.4f}"
        )
    except Exception as e:
        print(f"ERRO: Falha ao avaliar o modelo.\nDetalhe: {e}")


def select_monitor():
    """Lista e permite a seleção de um monitor físico."""
    with mss.mss() as sct:
        monitores = sct.monitors[1:]
        if not monitores:
            print("ERRO: Nenhum monitor físico detectado.")
            return None
        print("\n--- Monitores Físicos Detectados ---")
        for i, m in enumerate(monitores, 1):
            print(f"{i}: Tela {i} - {m['width']}x{m['height']}")
        while True:
            try:
                choice = int(input("Escolha o número do monitor: "))
                if 1 <= choice <= len(monitores):
                    return monitores[choice - 1]
                else:
                    print("Escolha inválida.")
            except ValueError:
                print("Entrada inválida.")


def select_window():
    """Lista e permite a seleção de uma janela de aplicativo aberta."""
    windows = [w for w in gw.getAllTitles() if w]
    if not windows:
        print("ERRO: Nenhuma janela de aplicativo encontrada.")
        return None
    print("\n--- Janelas de Aplicativo Detectadas ---")
    for i, title in enumerate(windows, 1):
        print(f"{i}: {title}")
    while True:
        try:
            choice = int(input("Escolha o número da janela: "))
            if 1 <= choice <= len(windows):
                window = gw.getWindowsWithTitle(windows[choice - 1])[0]
                return {
                    "left": window.left,
                    "top": window.top,
                    "width": window.width,
                    "height": window.height,
                }
            else:
                print("Escolha inválida.")
        except ValueError:
            print("Entrada inválida.")
        except IndexError:
            print(
                "ERRO: A janela selecionada não foi encontrada. Pode ter sido fechada."
            )
            return None


def select_capture_mode(base_region):
    """Permite escolher o modo de captura para a região base (monitor ou janela)."""
    print("\n--- Modo de Captura ---")
    print("1. Desenhar uma área de recorte (ROI) manualmente")
    print("2. Usar uma ROI automática baseada em quadrantes")
    choice = input("Escolha uma opção (1-2): ")

    if choice == "1":
        with mss.mss() as sct:
            print(
                "Na janela que aparecer, clique e arraste. Pressione ENTER para confirmar ou ESC para cancelar."
            )
            img_bgr = cv2.cvtColor(np.array(sct.grab(base_region)), cv2.COLOR_BGRA2BGR)
            roi = cv2.selectROI(
                "Desenhe a area e pressione ENTER",
                img_bgr,
                fromCenter=False,
                showCrosshair=True,
            )
            cv2.destroyAllWindows()
            if roi[2] == 0 or roi[3] == 0:
                print("Seleção cancelada.")
                return None
            return {
                "left": base_region["left"] + roi[0],
                "top": base_region["top"] + roi[1],
                "width": roi[2],
                "height": roi[3],
            }
    elif choice == "2":
        w, h = base_region["width"], base_region["height"]
        roi_x, roi_w = int(w * 0.4), int(w * 0.2)
        roi_y, roi_h = int(h * 0.85), int(h * 0.1)
        return {
            "left": base_region["left"] + roi_x,
            "top": base_region["top"] + roi_y,
            "width": roi_w,
            "height": roi_h,
        }
    else:
        print("Opção inválida.")
        return None


def run_detection_loop(
    model: YOLO,
    state_machine: DebuffStateMachine,
    capture_region: dict,
    debug_mode: bool,
    frame_delay: float,
    confidence_threshold: float,
):
    """
    Executa o loop de captura e detecção com controle de FPS e confiança.
    """
    if debug_mode:
        print(f"\nIniciando detecção em MODO DEBUG na região: {capture_region}.")
        print("Pressione 'q' na janela de visualização para sair.")
    else:
        fps_target = f"{1 / frame_delay:.0f} FPS" if frame_delay > 0 else "ILIMITADO"
        print(
            f"\nIniciando detecção em MODO PRODUÇÃO ({fps_target}) na região: {capture_region}."
        )
        print(f"Limiar de confiança definido em: {confidence_threshold * 100:.0f}%")
        print("Pressione Ctrl+C no terminal para sair.")

    try:
        with mss.mss() as sct:
            while True:
                img_mss = sct.grab(capture_region)
                frame_bgr = cv2.cvtColor(np.array(img_mss), cv2.COLOR_BGRA2BGR)

                results = model.predict(
                    frame_bgr,
                    conf=confidence_threshold,
                    verbose=False,
                    half=False,
                    imgsz=768,
                )

                detected_classes = {
                    model.names[int(box.cls[0].item())]
                    for box in results[0].boxes  # type: ignore
                }
                state_machine.process_detections(detected_classes)

                if debug_mode:
                    annotated_frame = results[0].plot()
                    cv2.imshow("Modo Debug | Pressione 'q' para sair", annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        state_machine.process_detections(set())
                        break
                elif frame_delay > 0:
                    time.sleep(frame_delay)

    except KeyboardInterrupt:
        print("\nInterrupção pelo usuário (Ctrl+C). Encerrando...")
        state_machine.process_detections(set())
    finally:
        print("Limpando recursos...")
        cv2.destroyAllWindows()


def iniciar_deteccao_com_luz(model: YOLO, state_machine: DebuffStateMachine):
    """Orquestra a seleção de alvo, modo de captura, modo de execução e FPS."""
    print("""
--- Configurar Área de Captura ---
1. Capturar um Monitor
2. Capturar uma Janela de Aplicativo""")
    target_choice = input("Escolha o tipo de alvo (1-2): ")

    base_region = None
    if target_choice == "1":
        base_region = select_monitor()
    elif target_choice == "2":
        base_region = select_window()

    if not base_region:
        print("Seleção de alvo inválida ou cancelada.")
        return

    regiao_de_captura = select_capture_mode(base_region)
    if not regiao_de_captura:
        print("Nenhuma região de captura definida.")
        return

    # --- Menu Modo de Execução (Debug/Produção) ---
    print("""\n--- Modo de Execução ---
1. Modo Debug (visualização em tempo real, FPS ilimitado)
2. Modo Produção (eficiente, sem janela de visualização)""")

    debug_mode = True
    while True:
        mode_choice = input("Escolha o modo de execução (1-2) [Padrão: 1]: ")
        if mode_choice in ["1", ""]:
            debug_mode = True
            break
        elif mode_choice == "2":
            debug_mode = False
            break
        else:
            print("Opção inválida. Digite 1 ou 2.")

    # --- Lógica de seleção de FPS (apenas para o modo Produção) ---
    frame_delay = 0.0
    if not debug_mode:
        print("""\n--- Controle de FPS (Modo Produção) ---
1. 30 FPS (Recomendado para a maioria dos jogos)
2. 60 FPS (Para jogos de alta velocidade)
3. 90 FPS (Competitivo/Monitores de alta frequência)
4. Ilimitado (Uso máximo da CPU, menor latência)""")

        fps_map = {
            "1": 1 / 30,
            "2": 1 / 60,
            "3": 1 / 90,
            "4": 0.0,
        }

        while True:
            fps_choice = input("Escolha a taxa de FPS (1-4) [Padrão: 1]: ")
            if fps_choice in ["", "1"]:
                frame_delay = fps_map["1"]
                break
            elif fps_choice in fps_map:
                frame_delay = fps_map[fps_choice]
                break
            else:
                print("Opção inválida. Digite um número de 1 a 4.")

    confidence_threshold = 0.9

    # Chama a função de loop com todas as configurações
    run_detection_loop(
        model,
        state_machine,
        regiao_de_captura,
        debug_mode,
        frame_delay,
        confidence_threshold,
    )


def main_menu(model, state_machine):
    """Exibe o menu principal e gerencia a escolha do usuário."""
    while True:
        print("""\n=============== MENU PRINCIPAL ================
1. Avaliar Métricas do Modelo
2. Iniciar Detecção com Controle de Luz
3. Sair
===============================================""")
        escolha = input("Escolha uma opção (1-3): ")
        if escolha == "1":
            avaliar_modelo(model)
        elif escolha == "2":
            iniciar_deteccao_com_luz(model, state_machine)
        elif escolha == "3":
            print("Desligando/Restaurando a lâmpada e saindo...")
            state_machine.process_detections(set())
            sys.exit(0)
        else:
            print("Opção inválida.")
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    print("Iniciando Ferramenta de Detecção e Automação YOLO...")
    if not os.path.exists(MODEL_PATH):
        print(
            f"ERRO CRÍTICO: Arquivo do modelo não encontrado em '{MODEL_PATH}'. Verifique o caminho."
        )
        sys.exit(1)

    if config := setup_interactive():
        print("\nConfiguração concluída com sucesso. Carregando recursos...")
        try:
            yolo_model = YOLO(MODEL_PATH)
            print(f"Modelo YOLO '{MODEL_PATH}' carregado.")
            fsm = DebuffStateMachine(
                ha_url=config["url"],
                ha_token=config["token"],
                target_id=config["target_id"],
                target_type=config["target_type"],
                neutral_action=config["neutral_action"],
            )
            main_menu(yolo_model, fsm)
        except Exception as e:
            print(f"\nERRO FATAL ao inicializar o programa: {e}")
            input("Pressione Enter para sair.")
    else:
        print("\nSetup não foi concluído. Saindo do programa.")

    sys.exit(0)
