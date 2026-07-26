"""
price_fetcher.py
Consulta cotizaciones de dólar (Argentina) y criptomonedas usando APIs públicas gratuitas.
No requieren API key.
"""
import requests

DOLAR_API_URL = "https://dolarapi.com/v1/dolares"
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"


def get_dolar_prices() -> dict:
    """
    Devuelve un diccionario con las cotizaciones de dólar en Argentina.
    Ejemplo de salida:
    {
        "oficial": 1050.0,
        "blue": 1230.0,
        "bolsa": 1210.0,
        "contadoconliqui": 1215.0,
        ...
    }
    """
    response = requests.get(DOLAR_API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()

    prices = {}
    for item in data:
        # cada item tiene "casa" (nombre) y "venta" (precio de venta)
        casa = item.get("casa", "").lower().replace(" ", "")
        venta = item.get("venta")
        if casa and venta is not None:
            prices[casa] = float(venta)
    return prices


def get_crypto_prices(coins: list[str], vs_currency: str = "usd") -> dict:
    """
    Devuelve precios de criptomonedas usando CoinGecko.
    coins: lista de ids de CoinGecko, ej ["bitcoin", "ethereum"]
    vs_currency: moneda de referencia, ej "usd" o "ars"

    Ejemplo de salida:
    {"bitcoin": 65000.0, "ethereum": 3400.0}
    """
    params = {
        "ids": ",".join(coins),
        "vs_currencies": vs_currency,
    }
    response = requests.get(COINGECKO_API_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    prices = {}
    for coin in coins:
        if coin in data and vs_currency in data[coin]:
            prices[coin] = float(data[coin][vs_currency])
    return prices


if __name__ == "__main__":
    # Prueba rápida manual
    print("Dólar:", get_dolar_prices())
    print("Cripto:", get_crypto_prices(["bitcoin", "ethereum"], "usd"))
