import os
import time
import ccxt
import requests

# Configuración del Bot de Telegram (puedes usar variables de entorno o ponerlos directos)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', 'TU_TOKEN_DE_TELEGRAM')
CHAT_ID = os.getenv('CHAT_ID', 'TU_CHAT_ID')

def enviar_alerta(mensaje):
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == 'TU_TOKEN_DE_TELEGRAM':
        print("Telegram no configurado:", mensaje)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error al enviar mensaje a Telegram: {e}")

def escanear_mercado():
    print("Iniciando escaneo en BingX...")
    try:
        exchange = ccxt.bingx({
            'enableRateLimit': True,
        })
        
        # Cargar mercados de futuros / swap
        markets = exchange.load_markets()
        # Filtrar pares USDT de futuros
        symbols = [s for s in markets if '/USDT' in s and markets[s]['swap']]

        for symbol in symbols[:20]: # Escaneando una muestra para evitar límites de velocidad
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=24)
                if len(ohlcv) < 24:
                    continue
                
                # Análisis básico de rango (Compresión / Acumulación)
                precios_altos = [x[2] for x in ohlcv]
                precios_bajos = [x[3] for x in ohlcv]
                
                max_precio = max(precios_altos)
                min_precio = min(precios_bajos)
                rango_porcentual = ((max_precio - min_precio) / min_precio) * 100
                
                # Si el rango en 24 horas es estrecho (ej. menor al 3%), detectamos compresión
                if rango_porcentual < 3.0:
                    mensaje = (
                        f"📊 *Alerta de Compresión / Acumulación*\n"
                        f"🪙 *Activo:* `{symbol}`\n"
                        f"📉 *Rango 24h:* `{rango_porcentual:.2f}%`\n"
                        f"💡 Posible acumulación estilo SMC detectada."
                    )
                    enviar_alerta(mensaje)
                    time.sleep(1)
            except Exception as e:
                print(f"Error analizando {symbol}: {e}")
                
    except Exception as e:
        print(f"Error general en el exchange: {e}")

if __name__ == "__main__":
    print("Bot iniciado correctamente. Monitoreando mercados...")
    enviar_alerta("🤖 *Bot de BingX SMC iniciado y operativo.*")
    
    while True:
        escanear_mercado()
        # Espera 1 hora antes del siguiente escaneo
        time.sleep(3600)
