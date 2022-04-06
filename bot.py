
"""
Ver. 1.0
Telegram Bot to return the rating of a movie using the movie title
Source: https://github.com/YuuKwn/SuperNota_bot/blob/main/bot.py
"""

from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
import requests, json
import logging
import os


PORT = int(os.environ.get('PORT', 8443))
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

key = 'd87fbf5f'
movieExists = False
TOKEN = '5205421916:AAEBcTQYdpYt6HKmW6VieNrSnibr-5GS6vg'



def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def start(update: Update, context: CallbackContext):
    update.message.reply_text('fala fi')

def get_rotten_tomatoes_movie_posters(movie_name, movie_year):
    url = 'http://www.omdbapi.com/?t=' + movie_name + '&y='+ movie_year + '&apikey=' + key
    response = requests.get(url)
    data = json.loads(response.text)
    if data['Response'] == 'True' and data['Poster'] != 'N/A':
        return  data['Poster']
    else:
        return 'https://i.imgur.com/jfkRgwB.png'

def get_rotten_tomatoes_rating(movie_name, movie_year):
    url = 'http://www.omdbapi.com/?t=' + movie_name + '&y='+ movie_year + '&apikey=' + key
    response = requests.get(url)
    data = json.loads(response.text)

    if data['Response'] == 'True':
        for i in range(len(data['Ratings'])):
            if data['Ratings'][i]['Source'] == 'Rotten Tomatoes':
                txt = ('A nota do Rotten Tomatoes para ' + data['Title'] + ' é ' + data['Ratings'][i]['Value'])
                return txt
        for i in range(len(data['Ratings'])):
            if data['Ratings'][i]['Source'] == 'Internet Movie Database':
                txt = ('A nota do IMDb para ' + data['Title'] + ' é ' + data['Ratings'][i]['Value'])
                return txt
        for i in range(len(data['Ratings'])):
            if data['Ratings'][i]['Source'] == 'Metacritic':
                txt = ('A nota do Metacritic para ' + data['Title'] + ' é ' + data['Ratings'][i]['Value'])
                return txt
        else:
            txt = ('Não encontrei nenhuma nota para ' + data['Title'])
            return txt
    else:
        txt = ('Não encontrei ' + movie_name)
        return txt



def print_rotten_tomatoes_rating(update: Update, context: CallbackContext):
    separate = " ".join(context.args).split(",")
    movie_name = separate[0]
    movie_year = ""
    if len(separate) > 1:
        movie_year = separate[1]
    print('text:', movie_name)   # /start something
    print('args:', movie_year)          # ['something']
    txt = get_rotten_tomatoes_rating(movie_name, movie_year)
    update.message.reply_photo(get_rotten_tomatoes_movie_posters(movie_name, movie_year), caption= str(txt))


def get_open_critic_game_rating(game_name):
    url = 'https://www.opencritic.com/api/v1/games/' + game_name
    response = requests.get(url)
    data = json.loads(response.text)
    if data['status'] == 'success':
        return data['data']['rating']
    else:
        return 'Não encontrei nenhuma nota para ' + game_name


def print_open_critic_game_rating(update: Update, context: CallbackContext):
    game_name = " ".join(context.args)
    print('text:', game_name)   # /start something
    txt = get_open_critic_game_rating(game_name)
    update.message.reply_text(txt)


def main():
    updater = Updater(TOKEN,
                  use_context=True)
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('nota', print_rotten_tomatoes_rating))
    updater.dispatcher.add_handler(CommandHandler('game', print_open_critic_game_rating))

    ##updater.dispatcher.add_handler(MessageHandler(Filters.text, echo))
    updater.dispatcher.add_error_handler(error)



    updater.start_webhook(listen="0.0.0.0",
                            port=int(PORT),
                            url_path=TOKEN,
                            webhook_url='https://supernota-bot.herokuapp.com/' + TOKEN)

    updater.idle()
    
if __name__ == '__main__':
    main()