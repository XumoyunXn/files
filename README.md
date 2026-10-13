# 🎬 Image → Video Telegram Bot

Rasm yuborasiz → Prompt yozasiz → Video olasiz!

## O'rnatish

### 1. Kerakli narsalar

- Python 3.10+
- Telegram Bot Token (@BotFather dan)
- Runway ML API Key (https://app.runwayml.com/account/api-keys)
- VPS yoki lokal server

### 2. Paketlarni o'rnatish

```bash
pip install -r requirements.txt
```

### 3. Token va API Key sozlash

**Linux/Mac:**
```bash
export TELEGRAM_BOT_TOKEN="7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export RUNWAY_API_KEY="rw_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

**Windows:**
```cmd
set TELEGRAM_BOT_TOKEN=7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
set RUNWAY_API_KEY=rw_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Yoki `bot.py` faylida to'g'ridan-to'g'ri o'zgartiring:
```python
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"
RUNWAY_API_KEY = "YOUR_RUNWAY_KEY_HERE"
```

### 4. Botni ishga tushirish

```bash
python bot.py
```

---

## Ishlatish

1. Telegram da botni toping
2. `/start` bosing
3. Rasm yuboring
4. Prompt yozing (inglizcha yaxshi ishlaydi):
   - `"A woman walking slowly in the rain, cinematic"`
   - `"Camera slowly zooms out, dramatic lighting"`
   - `"Leaves falling from trees, slow motion"`
5. 30-90 soniya kuting → Video keladi!

---

## Runway ML Narxlari

- 5 soniyalik video: ~$0.05
- 10 soniyalik video: ~$0.10
- Bepul trial: ro'yxatdan o'tganda 125 ta kredit

---

## VPS ga joylashtirish (ixtiyoriy)

```bash
# systemd service yaratish
sudo nano /etc/systemd/system/videobot.service

[Unit]
Description=Image to Video Telegram Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/image-to-video-bot
Environment=TELEGRAM_BOT_TOKEN=your_token
Environment=RUNWAY_API_KEY=your_key
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target

sudo systemctl enable videobot
sudo systemctl start videobot
```
