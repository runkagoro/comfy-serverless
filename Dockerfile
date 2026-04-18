FROM runpod/worker-comfyui:latest-base

USER root
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /comfyui/custom_nodes

RUN rm -rf ComfyUI-Manager ComfyUI-Image-Saver ComfyUI-KJNodes RES4LYF rgthree-comfy && \
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git && \
    git clone https://github.com/alexopus/ComfyUI-Image-Saver.git && \
    git clone https://github.com/kijai/ComfyUI-KJNodes.git && \
    git clone https://github.com/ClownsharkBatwing/RES4LYF.git && \
    git clone https://github.com/rgthree/rgthree-comfy.git

RUN for dir in /comfyui/custom_nodes/*/; do \
      if [ -f "$dir/requirements.txt" ]; then \
        pip install --no-cache-dir -r "$dir/requirements.txt"; \
      fi; \
    done

WORKDIR /comfyui
ENV RUNPOD_SERVERLESS=1

ENV COMFYUI_OUTPUT_GATHERING=1
ENV COMFYUI_OUTPUT_PATH=/runpod-volume/ComfyUI/output
