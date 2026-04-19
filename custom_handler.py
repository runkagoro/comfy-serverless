import runpod
import urllib.request
import json
import time
import os
import base64

COMFYUI_ADDRESS = "127.0.0.1:8188"

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"http://{COMFYUI_ADDRESS}/prompt", data=data)
    response = urllib.request.urlopen(req)
    return json.loads(response.read())

def get_history(prompt_id):
    try:
        with urllib.request.urlopen(f"http://{COMFYUI_ADDRESS}/history/{prompt_id}") as response:
            return json.loads(response.read())
    except:
        return {}

def handler(job):
    job_input = job['input']
    # Скрипт поймет и 'workflow', и 'prompt' — бот больше не сломается
    workflow = job_input.get('workflow') or job_input.get('prompt')
    
    if not workflow:
        return {"error": "Нет данных workflow для генерации"}

    try:
        print("🚀 Отправка задачи в ComfyUI...")
        queued_data = queue_prompt(workflow)
        prompt_id = queued_data['prompt_id']
        
        print(f"⏳ Ожидание генерации (ID: {prompt_id})...")
        while True:
            history = get_history(prompt_id)
            if prompt_id in history:
                break
            time.sleep(1.5)
        
        outputs = history[prompt_id]['outputs']
        image_filename = None
        for node_id, node_output in outputs.items():
            if 'images' in node_output:
                image_filename = node_output['images'][0]['filename']
                break
        
        if not image_filename:
            return {"error": "ComfyUI закончил работу, но файл картинки не найден"}
        
        # Проверяем оба пути, чтобы точно найти файл (на диске SHARKY или в памяти)
        paths_to_check = [
            os.path.join("/runpod-volume/ComfyUI/output", image_filename),
            os.path.join("/comfyui/output", image_filename)
        ]
        
        img_base64 = None
        for path in paths_to_check:
            if os.path.exists(path):
                with open(path, "rb") as f:
                    img_base64 = base64.b64encode(f.read()).decode('utf-8')
                print(f"✅ Файл {image_filename} найден и закодирован!")
                break
        
        if not img_base64:
            return {"error": f"Файл {image_filename} не найден ни в одной из папок вывода"}
        
        # Отдаем боту ровно то, что он ждет!
        return {"message": img_base64}

    except Exception as e:
        return {"error": str(e)}

runpod.serverless.start({"handler": handler})
