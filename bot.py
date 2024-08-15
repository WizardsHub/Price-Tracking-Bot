import sys
import time
import threading
import logging
import requests

from telegram.ext import CommandHandler, MessageHandler, Filters, Updater
from pricepolicebot.myproduct import MyProduct
from details.mytoken import TOKEN

LOGGER = logging.getLogger(__name__)

MAX_ITEMS = 10
MONITOR_INTERVAL = 1 * 30
ITEM_INTERVAL  = 1

def monitor_items(update, context):
    while True:
        with context.user_data["lock"]:
            matched = [False] * len(context.user_data["products"])

            for i in range(len(context.user_data["products"])):
                info_old = context.user_data["products"][i].get_product_info()
                info = {}

                try:
                    info = context.user_data["products"][i].update_product_info()

                except Exception as exc:
                    LOGGER.error("Error updating product: %s", exc)
                    continue

                LOGGER.info("Old info: %s; New info: %s", info_old, info)

                if not info_old["available"] and info["available"]:
                    message = f"The product {info['name']} is back in stock, "\
                              f"costing ₹ {format(info['price'], '.2f')}. "\
                              f"{info['url']}"
                    update.message.reply_text(message)

                if info["available"] and info["price"] <= context.user_data["products"][i].max_price:
                    message = (
                        f"Hey! The item {info['name']} is now costing "
                        f"₹ {format(info['price'], '.2f')}! Buy it now! "
                        f"{info['url']} I will stop monitoring it now!"
                    )

                    update.message.reply_text(message)
                    matched[i] = True

                time.sleep(ITEM_INTERVAL)

            context.user_data["products"] = [
                elem for i, elem in enumerate(context.user_data["products"]) if not matched[i]
            ]

        time.sleep(MONITOR_INTERVAL)

def start(update, context):
    greeting = "Hi! I am your price monitoring bot. \n\nTip: if link contains spaces, replace them for %20, so "\
                "bot can successfully retreive the information.\n\n"
    update.message.reply_text(greeting)
    show_help(update, context)

    context.user_data["products"] = []
    context.user_data["lock"] = threading.RLock()
    context.user_data["thread"] = threading.Thread(target = monitor_items, args=(update, context))
    context.user_data["thread"].start()
    LOGGER.info("Started thread %s", context.user_data["thread"])

def show_help(update, context):
    response = "Available commands:\n"\
               "  - Start monitoring a product: /add <link> <desired price>\n"\
               "  - Stop monitoring a product: /remove <product ID>\n"\
               "  - List products and prices: /status\n"\
               "  - List commands and stores: /help\n\n"\
               "Available stores for monitoring:\n" +\
               '\n'.join([f"  - {s}" for s in MyProduct.stores])
    update.message.reply_text(response)

def add_item(update, context):
    """Add item to monitor."""
    arguments_str = update.message.text.partition(' ')[1]
    arguments = arguments_str.split(' ')
    # /add url price 
    # argument = [url, price] // len = 2
    LOGGER.info("Recieved arguments: %s", arguments)

    # Validating the arguments passed
    try:
        assert len(arguments) == 2
        url = arguments[0]

        # concept of type conversion 
        price = float(arguments[1])
    except (AssertionError, ValueError):
        response = "Command usage: /add <link> <desired price>\n"\
                   "Tip: write the price as XXXXXX.XX, with no"\
                   " currency symbols."
        update.message.reply_text(response)
        return

    # Try to instantiate a new Product object
    try:
        new_prod = MyProduct(url, price)
    except (ValueError, requests.RequestException):
        response = "There was a problem retrieving the product. Please "\
                   "check if the store is accepted by the bot and if the "\
                   "link is not broken."
        update.message.reply_text(response)
        return

    # We need to acquire the lock add a new product to the list
    with context.user_data["lock"]:
        if len(context.user_data["products"]) > MAX_ITEMS:
            response = "You're monitoring too many items! Remove some."
            update.message.reply_text(response)
            return

    context.user_data["products"].append(new_prod)

    response = f"Ok, I am now monitoring the product {new_prod.name} at the "\
               f"store {new_prod.store}. I'll warn you when the price drops "\
               f"to ₹ {format(new_prod.max_price, '.2f')} or less."
    update.message.reply_text(response)

def remove_item(update,context):
    index_str = update.message.text.partition(' ')[2]
    item_removed = None

    status(update, context)

    with context.user_data["lock"]:
        try:
            index = int(index_str) -1
            item_removed = context.user_data["products"].pop(index)
        except (ValueError, IndexError):
            response =  "There was a problem removing the product. Did you "\
                       "pass the right product ID?"
            update.message.reply_text(response)
            return

    if item_removed:
        response = f"The product {item_removed.name} from the store "\
                   f"{item_removed.store} was successfully removed."
        update.message.reply_text(response)

def status(update, context):
    response = "I'm currently monitoring the following items:\n"
    update.message.reply_text(response)

    with context.user_data["lock"]:
        if not context.user_data["products"]:
            response = "Nothing!"
            update.message.reply_text(response)
    
    #product list:
        # 0. tshirt - 90
        # 1. phone - 78
        # 2. lollipop - 89
        for i, prod in enumerate(context.user_data["products"]):
            msg_price = (
                f"Current price: ₹ {format(prod.price, '.2f')}\n\n"
                if prod.available else "Currently unavailable\n\n"
            )

            response = f"[ID {i + 1}] {prod.name} at {prod.store}\n{msg_price}"
            update.message.reply_text(response)

def ping(update, context):
    response = "Ping!"
    update.message.reply_text(response)

def unknown(update, context):
    response = "I don't know what you mean"
    update.message.reply_text(response)

def main():
    updater = Updater(token = TOKEN, use_context = True)
    disp = updater.dispatcher

    disp.add_handler(CommandHandler('start', start))
    disp.add_handler(CommandHandler('ping', ping))
    disp.add_handler(CommandHandler('help', show_help))
    disp.add_handler(CommandHandler('add', add_item))
    disp.add_handler(CommandHandler('remove', remove_item))
    disp.add_handler(CommandHandler('status', status))
    disp.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    file_handler = logging.FileHandler("pricepolice.log")
    stdout_handler = logging.StreamHandler(sys.stdout)

    logging.basicConfig(format = "%(asctime)s %(levelname)s   %(message)s",
                        handlers = (file_handler, stdout_handler),
                        level = logging.INFO
                        )

    print("Press Ctrl-C to stop the bot.")
    main()