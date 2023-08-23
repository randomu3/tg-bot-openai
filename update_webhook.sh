#!/bin/bash

# Получить URL из ngrok
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')

# Обновить config.py с новым URL
sed -i "s|WEBHOOK_URL = .*|WEBHOOK_URL = \"$NGROK_URL\" + WEBHOOK_PATH|" config.py

# Перезапустить telegram_bot через pm2
pm2 restart telegram_bot

