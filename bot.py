"""
bot.py
Bot de Telegram para alertas de precio (dólar y cripto).

Comandos:
  /start                          -> mensaje de bienvenida
  /alerta <activo> <op> <valor>   -> crea una alerta. Ej: /alerta blue < 1200
  /misalertas                     -> lista tus alertas activas
  /cancelar <id>                  -> desactiva una alerta
  /premium                        -> muestra tu estado y cómo pasar a premium
  /miid                           -> muestra tu chat_id (útil para soporte/activación)
  /activar_premium <chat_id> <dias>  -> (solo admin) activa premium a un usuario

Activos soportados hoy:
  Dólar: oficial, blue, bolsa, contadoconliqui, tarjeta, mayorista
  Cripto: bitcoin, ethereum (fácil de agregar más en CRYPTO_ASSETS)

Requiere variables de entorno (ver README.md):
  TELEGRAM_BOT_TOKEN  -> token del bot
  ADMIN_CHAT_ID        -> tu chat_id, para poder usar /activar_premium
  PAYMENT_LINK          -> (opcional) link de pago de Mercado Pago
"""
import asyncio
import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from alerts import (
    init_db,
    add_alert,
    list_alerts,
    deactivate_alert,
    get_all_active_alerts,
    alert_is_triggered,
    count_active_alerts,
    is_premium,
    set_premium,
)
from price_fetcher import get_dolar_prices, get_crypto_prices

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CRYPTO_ASSETS = {"bitcoin", "ethereum"}
CHECK_INTERVAL_SECONDS = 300  # cada 5 minutos
FREE_ALERT_LIMIT = 2
PAYMENT_LINK = os.environ.get("PAYMENT_LINK", "(todavía no configuraste tu link de pago)")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "¡Hola! Soy tu bot de alertas de precio.\n\n"
        "Comandos disponibles:\n"
        "/alerta <activo> <op> <valor> - Crea una alerta. Ej: /alerta blue < 1200\n"
        "/misalertas - Lista tus alertas activas\n"
        "/cancelar <id> - Cancela una alerta\n"
        "/premium - Ver tu estado y cómo tener alertas ilimitadas\n\n"
        f"Activos disponibles: oficial, blue, bolsa, contadoconliqui, tarjeta, mayorista, bitcoin, ethereum\n\n"
        f"Plan gratis: hasta {FREE_ALERT_LIMIT} alertas activas."
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

    # Aplicar límite de alertas gratis (si el usuario no es premium)
    if not is_premium(chat_id):
        current_count = count_active_alerts(chat_id)
        if current_count >= FREE_ALERT_LIMIT:
            await update.message.reply_text(
                f"⚠️ Llegaste al límite de {FREE_ALERT_LIMIT} alertas del plan gratis.\n\n"
                "Para tener alertas ilimitadas, pasate a premium:\n"
                f"{PAYMENT_LINK}\n\n"
                "Una vez que pagues, escribime para activar tu cuenta. Usá /premium para más info."
            )
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


async def premium_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    if is_premium(chat_id):
        await update.message.reply_text("✅ Ya sos usuario premium. Tenés alertas ilimitadas.")
        return

    current_count = count_active_alerts(chat_id)
    await update.message.reply_text(
        f"Estás en el plan gratis: {current_count}/{FREE_ALERT_LIMIT} alertas usadas.\n\n"
        "Para tener alertas ilimitadas, pasate a premium acá:\n"
        f"{PAYMENT_LINK}\n\n"
        "Una vez que pagues, avisá para activar tu cuenta (mandá /miid y compartí ese número)."
    )


async def mi_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"Tu chat_id es: {chat_id}\n\nCompartilo si necesitás soporte o activar premium."
    )


async def activar_premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando de administrador: activa premium a un usuario por su chat_id."""
    sender_chat_id = str(update.effective_chat.id)
    admin_chat_id = os.environ.get("ADMIN_CHAT_ID")

    if not admin_chat_id or sender_chat_id != admin_chat_id:
        await update.message.reply_text("No tenés permiso para usar este comando.")
        return

    args = context.args
    if len(args) != 1 or not args[0].lstrip("-").isdigit():
        await update.message.reply_text("Uso correcto: /activar_premium <chat_id>")
        return

    target_chat_id = int(args[0])
    set_premium(target_chat_id, True)
    await update.message.reply_text(f"✅ Usuario {target_chat_id} activado como premium.")

    try:
        await context.bot.send_message(
            chat_id=target_chat_id,
            text="🎉 ¡Tu cuenta premium fue activada! Ya tenés alertas ilimitadas.",
        )
    except Exception as e:
        logger.warning(f"No se pudo avisar al usuario {target_chat_id}: {e}")


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
    application.add_handler(CommandHandler("premium", premium_info))
    application.add_handler(CommandHandler("miid", mi_id))
    application.add_handler(CommandHandler("activar_premium", activar_premium))

    # Chequeo periódico de alertas
    application.job_queue.run_repeating(check_alerts_job, interval=CHECK_INTERVAL_SECONDS, first=10)

    logger.info("Bot iniciado. Esperando mensajes...")
    application.run_polling()


if __name__ == "__main__":
    main()
