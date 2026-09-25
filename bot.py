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
    print("Iniciando escaneo del top de futuros en BingX...")
    try:
        exchange.options['defaultType'] = 'swap'
        markets = exchange.load_markets()
        
        # Obtener tickers para evaluar volumen y filtrar solo futuros perpetuos USDT válidos
        tickers = exchange.fetch_tickers()
        
        valid_symbols = []
        for symbol, market in markets.items():
            if market.get('linear') == True and market.get('swap') == True and symbol.endswith('/USDT:USDT'):
                # Evitar tokens extraños o de prueba
                base_currency = symbol.split('/')[0]
                if any(bad in base_currency for bad in ['TEST', 'USD', '2USD', 'NCSK', 'UP', 'DOWN']):
                    continue
                
                # Obtener el volumen de 24h para ordenar por liquidez
                ticker = tickers.get(symbol, {})
                quote_volume = ticker.get('quoteVolume', 0) or 0
                valid_symbols.append((symbol, quote_volume))
        
        # Ordenar de mayor a menor volumen y seleccionar los más líquidos (ej. los 40 principales del mercado de futuros)
        valid_symbols.sort(key=lambda x: x[1], reverse=True)
        top_symbols = [item[0] for item in valid_symbols[:40]]
        
        # Temporalidades a escanear
        timeframes = ['1h', '4h']

        for symbol in top_symbols: 
            for tf in timeframes:
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=50)
                    if len(ohlcv) < 30:
                        continue
                    
                    # Calcular rango de compresión en las últimas 20 velas
                    highs = [candle[2] for candle in ohlcv[-20:]]
                    lows = [candle[3] for candle in ohlcv[-20:]]
                    max_high = max(highs)
                    min_low = min(lows)
                    
                    range_pct = ((max_high - min_low) / min_low) * 100

                    # Condición de compresión estricta (< 3%)
                    if range_pct < 3.0:
                        # Sesgo estructural basado en el impulso previo antes del rango
                        previous_close = ohlcv[-25][4]
                        current_close = ohlcv[-1][4]
                        
                        if current_close > previous_close:
                            bias = "🟢 Alta probabilidad de Ruptura Alcista (Continuación institucional)"
                        else:
                            bias = "🔴 Alta probabilidad de Ruptura Bajista (Continuación o barrido)"
                        
                        message = (
                            f"📊 *Alerta Top Compresión (Futuros)*\n"
                            f"🪙 *Activo:* `{symbol}`\n"
                            f"⏱️ *Temporalidad:* `{tf}`\n"
                            f"📉 *Rango:* `{range_pct:.2f}%`\n"
                            f"🧭 *Sesgo Estructural:* {bias}\n"
                            f"💡 *Zona de alta liquidez lista para expansión.*"
                        )
                        send_telegram_message(message)
                        time.sleep(1) 
                except Exception as e:
                    continue
    except Exception as e:
        print(f"Error en el ciclo de mercado: {e}")

if __name__ == "__main__":
    print("Bot con filtro de volumen superior iniciado...")
    send_telegram_message("🚀 *Bot BingX optimizado.* Escaneando únicamente el *Top de futuros por volumen*...")
    while True:
        analyze_market()
        time.sleep(900)
