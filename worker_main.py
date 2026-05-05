import runpod
import os
import requests
import time
import subprocess
import base64
import json

# Папка для входящих картинок
INPUT_DIR = "/comfyui/input"

def start_comfyui():
    print("--- Запуск ComfyUI ---")
    subprocess.Popen(["python3", "main.py", "--listen", "127.0.0.1", "--port", "8188"], cwd="/comfyui")
    while True:
        try:
            requests.get("http://127.0.0.1:8188/history")
            print("--- ComfyUI готов! ---")
            break
        except:
            time.sleep(1)

def handler(job):
    job_input = job["input"]
    workflow = job_input.get("workflow")
    
    # 1. СОХРАНЯЕМ ВХОДЯЩУЮ КАРТИНКУ
    input_image_base64 = job_input.get("input_image")
    image_name = job_input.get("image_name", "input.jpg") 
    
    if input_image_base64:
        os.makedirs(INPUT_DIR, exist_ok=True)
        with open(os.path.join(INPUT_DIR, image_name), "wb") as f:
            f.write(base64.b64decode(input_image_base64))
        print(f"Картинка {image_name} успешно сохранена!")

    if not workflow: 
        return {"error": "Нет параметра workflow"}
    
    if isinstance(workflow, str):
        workflow = json.loads(workflow)

    # 2. ОТПРАВЛЯЕМ ЗАПРОС
    response = requests.post("http://127.0.0.1:8188/prompt", json={"prompt": workflow}).json()
    
    # Защита от ошибок
    if "prompt_id" not in response:
        return {"error": f"Ошибка ComfyUI: {response}"}

    prompt_id = response["prompt_id"]

    # 3. ЖДЕМ И ВОЗВРАЩАЕМ РЕЗУЛЬТАТ
    while True:
        history = requests.get(f"http://127.0.0.1:8188/history/{prompt_id}").json()
        if prompt_id in history: 
            break
        time.sleep(0.5)

    out_path = os.environ.get("COMFYUI_OUTPUT_PATH", "/comfyui/output")
    files = os.listdir(out_path)
    if not files: 
        return {"error": "Картинка не создана"}
    
    latest_file = max([os.path.join(out_path, f) for f in files], key=os.path.getctime)
    with open(latest_file, "rb") as f:
        return {"image": base64.b64encode(f.read()).decode('utf-8')}

if __name__ == "__main__":
    start_comfyui()
    runpod.serverless.start({"handler": handler})
