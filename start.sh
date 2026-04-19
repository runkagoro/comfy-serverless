#!/bin/bash
echo "🚀 Запуск ComfyUI в фоновом режиме..."
python main.py --listen 127.0.0.1 --port 8188 &

echo "⏳ Даем ComfyUI 10 секунд на загрузку нод..."
sleep 10

echo "🤖 Запуск кастомного обработчика API..."
python custom_handler.py
