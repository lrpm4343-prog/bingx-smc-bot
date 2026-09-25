import os
import time
import ccxt
import requests

# Configuración de credenciales desde las variables de entorno de Railway
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Inicializar el exchange BingX
exchange = ccxt.bingx({
    'enableRateLimit': True,
})

def send_telegram_message(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Error: Credenciales de Telegram no configuradas.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error al enviar mensaje a Telegram: {e}")

def analyze_market():
    print("Iniciando escaneo en BingX...")
    try:
        markets = exchange.load_markets()
        # Filtrar pares USDT de futuros o spot según prefieras
        symbols = [symbol for symbol in markets if symbol.endswith('/USDT:USDT') or symbol.endswith('/USDT')]
        
        # Temporalidades a escanear (ej. '1h', '4h')
        timeframes = ['1h', '4h']

        for symbol in symbols[:30]: # Limitamos para optimizar velocidad de escaneo
            for tf in timeframes:
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=50)
                    if len(ohlcv) < 20:
                        continue
                    
                    # Calcular rango de compresión en las últimas velas
                    highs = [candle[2] for candle in ohlcv[-20:]]
                    lows = [candle[3] for candle in ohlcv[-20:]]
                    max_high = max(highs)
                    min_low = min(lows)
                    current_price = ohlcv[-1][4]
                    
                    range_pct = ((max_high - min_low) / min_low) * 100

                    # Condición de compresión estricta (< 3%)
                    if range_pct < 3.0:
                        # Estimar sesgo simple basado en la posición del precio actual dentro del rango
                        bias = "Alcista 🟢 (Cerca del límite superior / Acumulación institucional)" if current_price > ((max_high + min_low) / 2) else "Bajista 🔴 (Cerca del soporte / Posible barrido de liquidez)"
                        
                        message = (
                            f"📊 *Alerta de Compresión / Acumulación*\n"
                            f"🪙 *Activo:* `{symbol}`\n"
                            f"⏱️ *Temporalidad:* `{tf}`\n"
                            f"📉 *Rango:* `{range_pct:.2f}%`\n"
                            f"🧭 *Sesgo Probable:* {bias}\n"
                            f"💡 *Patrón estilo SMC detectado.*"
                        )
                        send_telegram_message(message)
                        time.sleep(1) # Pausa breve para evitar saturar la API de Telegram
                except Exception as e:
                    continue
    except Exception as e:
        print(f"Error en el ciclo de mercado: {e}")

if __name__ == "__main__":
    print("Bot iniciado correctamente. Monitoreando mercados...")
    send_telegram_message("🚀 *Bot SMC BingX reiniciado y actualizado.* Monitoreando compresiones con temporalidad y sesgo...")
    while True:
        analyze_market()
        time.sleep(900) # Espera 15 minutos antes del próximo escaneo completo
