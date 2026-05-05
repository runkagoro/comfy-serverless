import runpod
import os
import requests
import time
import subprocess
import json
import base64

# Настройки путей
COMFYUI_PATH = "/comfyui"
OUTPUT_PATH = os.environ.get("COMFYUI_OUTPUT_PATH", "/comfyui/output")

def start_comfyui():
    """Запуск процесса ComfyUI в фоне"""
    print("--- Запуск ComfyUI ---")
    # Запускаем ComfyUI как отдельный процесс
    subprocess.Popen(["python3", "main.py", "--listen", "127.0.0.1", "--port", "8188"], cwd=COMFYUI_PATH)
    
    # Ждем, пока API станет доступно
    while True:
        try:
            requests.get("http://127.0.0.1:8188/history")
            print("--- ComfyUI готов к работе ---")
            break
        except requests.exceptions.ConnectionError:
            print("Ожидание запуска API ComfyUI...")
            time.sleep(1)

def handler(job):
    """Основной обработчик запросов от RunPod"""
    job_input = job["input"]
    workflow = job_input.get("workflow") # Твой JSON-воркфлоу

    if not workflow:
        return {"error": "JSON воркфлоу не найден в запросе"}

    # Отправляем промпт в локальное API ComfyUI
    prompt_id = requests.post("http://127.0.0.1:8188/prompt", json={"prompt": workflow}).json()["prompt_id"]

    # Ждем завершения генерации
    while True:
        history = requests.get(f"http://127.0.0.1:8188/history/{prompt_id}").json()
        if prompt_id in history:
            break
        time.sleep(0.5)

    # Ищем последнюю созданную картинку в папке output
    files = os.listdir(OUTPUT_PATH)
    if not files:
        return {"error": "Картинка не была сгенерирована"}
    
    latest_file = max([os.path.join(OUTPUT_PATH, f) for f in files], key=os.path.getctime)
    
    # Читаем картинку и кодируем в base64 для отправки обратно
    with open(latest_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    return {"image": encoded_string}

if __name__ == "__main__":
    # 1. Сначала запускаем сам ComfyUI
    start_comfyui()
    # 2. Затем запускаем воркер RunPod
    runpod.serverless.start({"handler": handler})
