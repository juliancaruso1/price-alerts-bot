"""
bot.py
Bot de Telegram para alertas de precio (dólar y cripto).

Comandos:
  /start                          -> mensaje de bienvenida
  /alerta <activo> <op> <valor>   -> crea una alerta. Ej: /alerta blue < 1200
  /misalertas                     -> lista tus alertas activas
  /cancelar <id>                  -> desactiva una alerta

Activos soportados hoy:
  Dólar: oficial, blue, bolsa, contadoconliqui, tarjeta, mayorista
  Cripto: bitcoin, ethereum (fácil de agregar más en CRYPTO_ASSETS)

Requiere variable de entorno TELEGRAM_BOT_TOKEN (ver README.md).
"""
import asyncio
import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from alerts import init_db, add_alert, list_alerts, deactivate_alert, get_all_active_alerts, alert_is_triggered
from price_fetcher import get_dolar_prices, get_crypto_prices

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CRYPTO_ASSETS = {"bitcoin", "ethereum"}
CHECK_INTERVAL_SECONDS = 300  # cada 5 minutos


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "¡Hola! Soy tu bot de alertas de precio.\n\n"
        "Comandos disponibles:\n"
        "/alerta <activo> <op> <valor> - Crea una alerta. Ej: /alerta blue < 1200\n"
        "/misalertas - Lista tus alertas activas\n"
        "/cancelar <id> - Cancela una alerta\n\n"
        "Activos disponibles: oficial, blue, bolsa, contadoconliqui, tarjeta, mayorista, bitcoin, ethereum"
    )


async def crear_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    args = context.args

    if len(args) != 3:
        await update.message.reply_text(
            "Uso correcto: /alerta <activo> <op> <valor>\nEjemplo: /alerta blue < 1200"
        )
        return

    asset, operator, value_str = args[0].lower(), args[1], args[2]

    if operator not in ("<", ">"):
        await update.message.reply_text("El operador debe ser '<' o '>'")
        return

    try:
        target_value = float(value_str)
    except ValueError:
        await update.message.reply_text("El valor debe ser un número, ej: 1200")
        return

    alert_id = add_alert(chat_id, asset, operator, target_value)
    await update.message.reply_text(
        f"✅ Alerta #{alert_id} creada: avisaré cuando {asset} sea {operator} {target_value}"
    )


async def mis_alertas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    alertas = list_alerts(chat_id)

    if not alertas:
        await update.message.reply_text("No tenés alertas activas. Creá una con /alerta")
        return

    lines = [f"#{a.id}: {a.asset} {a.operator} {a.target_value}" for a in alertas]
    await update.message.reply_text("Tus alertas activas:\n" + "\n".join(lines))


async def cancelar_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) != 1 or not args[0].isdigit():
        await update.message.reply_text("Uso correcto: /cancelar <id>")
        return

    alert_id = int(args[0])
    deactivate_alert(alert_id)
    await update.message.reply_text(f"Alerta #{alert_id} cancelada.")


async def check_alerts_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job periódico: consulta precios actuales y avisa a los usuarios cuyas alertas se cumplan."""
    active_alerts = get_all_active_alerts()
    if not active_alerts:
        return

    # Traer precios una sola vez por ciclo (evita golpear las APIs de más)
    try:
        dolar_prices = get_dolar_prices()
    except Exception as e:
        logger.warning(f"Error consultando dólar: {e}")
        dolar_prices = {}

    needed_cryptos = {a.asset for a in active_alerts if a.asset in CRYPTO_ASSETS}
    crypto_prices = {}
    if needed_cryptos:
        try:
            crypto_prices = get_crypto_prices(list(needed_cryptos), "usd")
        except Exception as e:
            logger.warning(f"Error consultando cripto: {e}")

    all_prices = {**dolar_prices, **crypto_prices}

    for alert in active_alerts:
        current_price = all_prices.get(alert.asset)
        if current_price is None:
            continue

        if alert_is_triggered(alert, current_price):
            try:
                await context.bot.send_message(
                    chat_id=alert.chat_id,
                    text=(
                        f"🔔 ¡Alerta cumplida! {alert.asset} está en {current_price} "
                        f"({alert.operator} {alert.target_value})"
                    ),
                )
            except Exception as e:
                logger.warning(f"Error enviando mensaje a {alert.chat_id}: {e}")
            deactivate_alert(alert.id)


def main() -> None:
    # Fix de compatibilidad: en Python 3.14+ ya no se crea automáticamente
    # un event loop en el hilo principal, así que lo creamos a mano.
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    init_db()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "Falta la variable de entorno TELEGRAM_BOT_TOKEN. Ver README.md para configurarla."
        )

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("alerta", crear_alerta))
    application.add_handler(CommandHandler("misalertas", mis_alertas))
    application.add_handler(CommandHandler("cancelar", cancelar_alerta))

    # Chequeo periódico de alertas
    application.job_queue.run_repeating(check_alerts_job, interval=CHECK_INTERVAL_SECONDS, first=10)

    logger.info("Bot iniciado. Esperando mensajes...")
    application.run_polling()


if __name__ == "__main__":
    main()
