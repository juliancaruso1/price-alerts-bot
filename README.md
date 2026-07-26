# Price Alerts Bot

Bot de Telegram que te avisa cuando el dólar (oficial, blue, bolsa, etc.) o una
criptomoneda (bitcoin, ethereum) cruza un valor que vos definís.

Ejemplo de uso: `/alerta blue < 1200` → el bot te escribe apenas el dólar blue baje de $1200.

---

## 1. Instalar Visual Studio Code

Si no lo tenés: descargalo de https://code.visualstudio.com/ (gratis).

Al abrirlo por primera vez, instalá la extensión **Python** (de Microsoft) desde
la pestaña de Extensiones (ícono de cuadraditos en la barra izquierda, o `Ctrl+Shift+X`).

## 2. Requisitos previos

- **Python 3.10 o superior** instalado. Verificalo en una terminal con:
  ```bash
  python --version
  ```
  Si no lo tenés, bajalo de https://www.python.org/downloads/ (marcá la opción
  "Add Python to PATH" durante la instalación en Windows).

- **Un token de bot de Telegram** (gratis, se consigue en 2 minutos):
  1. Abrí Telegram y buscá el bot `@BotFather`.
  2. Enviale `/newbot` y seguí las instrucciones (nombre y username del bot).
  3. Te va a dar un token con este formato: `123456789:ABCdefGHIjklMNOpqrSTUvwxYZ`.
     Guardalo, lo vas a necesitar en el paso 4.

## 3. Abrir el proyecto en VS Code

1. Descomprimí la carpeta `price-alerts-bot` en tu computadora.
2. Abrí VS Code → `File > Open Folder...` → seleccioná la carpeta `price-alerts-bot`.
3. Abrí una terminal integrada: `Terminal > New Terminal` (o `` Ctrl+` ``).

## 4. Crear un entorno virtual e instalar dependencias

En la terminal de VS Code (parado dentro de la carpeta del proyecto):

```bash
# Crear entorno virtual
python -m venv venv

# Activarlo
# En Windows:
venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

Cuando el entorno esté activado vas a ver `(venv)` al principio de la línea de la terminal.

## 5. Configurar el token del bot

Definí la variable de entorno con el token que te dio BotFather:

```bash
# En Windows (PowerShell):
$env:TELEGRAM_BOT_TOKEN="tu_token_aca"

# En Mac/Linux:
export TELEGRAM_BOT_TOKEN="tu_token_aca"
```

> Nota: esta variable se pierde al cerrar la terminal. Para no tener que repetirlo
> cada vez, podés instalar `python-dotenv` y crear un archivo `.env` — si querés,
> te ayudo a agregar eso después.

## 6. Correr el bot

```bash
python bot.py
```

Si ves `Bot iniciado. Esperando mensajes...` en la terminal, andá a Telegram,
buscá tu bot (por el username que le pusiste) y mandale `/start`.

## 7. Correr los tests

```bash
pytest tests/ -v
```

Esto corre automáticamente los tests de `price_fetcher.py` y `alerts.py` sin
necesidad de conexión a internet real (usan mocks).

## 8. Subir a GitHub (opcional pero recomendado)

1. Creá un repositorio nuevo en https://github.com/new
2. En la terminal:
   ```bash
   git init
   git add .
   git commit -m "Primera versión del bot de alertas"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/price-alerts-bot.git
   git push -u origin main
   ```
3. El workflow en `.github/workflows/tests.yml` va a correr los tests
   automáticamente en cada push, sin configuración adicional.

---

## Próximos pasos sugeridos

- **Agregar más criptos**: sumá ids de CoinGecko al set `CRYPTO_ASSETS` en `bot.py`.
- **Deploy 24/7**: hoy el bot corre mientras tu notebook esté prendida y conectada.
  Para que funcione todo el tiempo sin depender de tu compu, se puede desplegar
  gratis o muy barato en Railway, Render, o un VPS chico.
- **Monetización**: limitar a los usuarios free a 2 alertas activas, y ofrecer
  alertas ilimitadas + chequeo más frecuente vía suscripción con Mercado Pago.
