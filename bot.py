from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
import requests, json
key = 'd87fbf5f'

updater = Updater("5205421916:AAEBcTQYdpYt6HKmW6VieNrSnibr-5GS6vg",
                  use_context=True)

def start(update: Update, context: CallbackContext):
    update.message.reply_text('Hi!')

def get_rotten_tomatoes_movie_posters(movie_name):
    url = 'http://www.omdbapi.com/?t=' + movie_name + '&apikey=' + key
    response = requests.get(url)
    data = json.loads(response.text)
    if data['Response'] == 'True':
        return  data['Poster']
    else:
        return 'N/A'

def get_rotten_tomatoes_rating(movie_name):
    url = 'http://www.omdbapi.com/?t=' + movie_name + '&apikey=' + key
    response = requests.get(url)
    data = json.loads(response.text)
    if data['Response'] == 'True':
        return data['Ratings'][1]['Value']
    else:
        return 'N/A'

def print_rotten_tomatoes_rating(update: Update, context: CallbackContext):
    movie_name = " ".join(context.args)
    
    txt = ('A nota do IMDB para ' + movie_name + ' é ' + get_rotten_tomatoes_rating(movie_name))
    update.message.reply_photo(get_rotten_tomatoes_movie_posters(movie_name), caption= str(txt))

    



updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('nota', print_rotten_tomatoes_rating))
updater.start_polling()