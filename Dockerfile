FROM runpod/worker-comfyui:latest-base

USER root

# 1. Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    git \
    wget \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. Библиотека GGUF для работы загрузчика моделей (обязательно!)
RUN pip install --no-cache-dir --upgrade gguf

# 3. Установка кастомных нод
WORKDIR /comfyui/custom_nodes
RUN rm -rf ComfyUI-Manager ComfyUI-Image-Saver ComfyUI-KJNodes RES4LYF rgthree-comfy ComfyUI-GGUF && \
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git && \
    git clone https://github.com/alexopus/ComfyUI-Image-Saver.git && \
    git clone https://github.com/kijai/ComfyUI-KJNodes.git && \
    git clone https://github.com/ClownsharkBatwing/RES4LYF.git && \
    git clone https://github.com/rgthree/rgthree-comfy.git && \
    git clone https://github.com/city96/ComfyUI-GGUF.git

# 4. Установка зависимостей для всех склонированных нод
RUN for dir in /comfyui/custom_nodes/*/; do \
      if [ -f "$dir/requirements.txt" ]; then \
        pip install --no-cache-dir -r "$dir/requirements.txt"; \
      fi; \
    done

# 5. Создаем папки для моделей и внутреннюю папку для сохранения картинок
RUN mkdir -p /comfyui/models/unet /comfyui/models/text_encoders /comfyui/models/vae /comfyui/output

# 6. Скачиваем модели (используем кэширование RunPod)
# Основная модель GGUF Q5_K (15.1 ГБ)
RUN wget -L -O /comfyui/models/unet/Qwen-v19-Q5.gguf \
    "https://huggingface.co/Novice25/Qwen-Image-Edit-Rapid-AIO-GGUF/resolve/main/v19/Qwen-Rapid-AIO-NSFW-v19_Q5_K.gguf?download=true"

# Текстовый Энкодер (CLIP)
RUN wget -L -O /comfyui/models/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors \
    "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors"

# VAE
RUN wget -L -O /comfyui/models/vae/qwen_image_vae.safetensors \
    "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors"

# --- НАСТРОЙКИ ЗАПУСКА И КОПИРОВАНИЕ ФАЙЛОВ ---
WORKDIR /comfyui
ENV RUNPOD_SERVERLESS=1

# Используем внутреннюю папку контейнера (т.к. Network Volume отключен)
ENV COMFYUI_OUTPUT_PATH=/comfyui/output

# 7. ВАЖНО: Копируем файлы из GitHub в САМОМ КОНЦЕ
# Теперь изменения в коде не заставят перекачивать 25 ГБ моделей!
COPY . .

# Команда запуска файла-обработчика
CMD ["python", "-u", "worker_main.py"]
