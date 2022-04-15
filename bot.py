"""
Telegram Bot to return the rating of a movie or game using the title
Source: https://github.com/YuuKwn/SuperNota_bot/blob/main/bot.py
"""

from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
import re
import requests, json
import logging
import os
from bs4 import BeautifulSoup
from howlongtobeatpy import HowLongToBeat




PORT = int(os.environ.get('PORT', 8443))
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

key = 'd87fbf5f'
movieExists = False
TOKEN = '5205421916:AAEBcTQYdpYt6HKmW6VieNrSnibr-5GS6vg'

headers = {
	'Accept' : '*/*',
	'Accept-Language': 'en-US,en;q=0.5',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82',
}

def get_op_page(game_name):
    url = 'https://www.google.com/search?q="open+critic"+' + game_name
    content = requests.get(url, headers = headers).text
    soup = BeautifulSoup(content, 'html.parser')
    hasOP = soup.find('h3', text = re.compile('OpenCritic'))
    if hasOP is not None:
        firstrating = soup.find('h3', text = re.compile('for'))
        print(firstrating)
        if firstrating is None:
            return 'https://opencritic.com/game/3698/score/reviews'
        else:
            first_link = firstrating.find_previous('a')
            return first_link['href']
    else: 
        return 'https://opencritic.com/game/3698/score/reviews'

def get_op_info(url):
    op_content = requests.get(url, headers = headers).text
    url = BeautifulSoup(op_content, 'html.parser')

    wrong = url.find('strong', text= re.compile('percentile'))
    if wrong is not None:    
        return 'Jogo não encontrado no banco de dados do OpenCritic', '', '', 'https://i.imgur.com/2lFiGXm.png', '', '', '', ''

    elif wrong is None:

        rating_text = url.find_all('div', class_ = 'inner-orb')
        if len(rating_text) > 0:
            rating = rating_text[0].text
            recommendation = rating_text[1].text
            game_title = url.find('h1').text
            game_image_element = url.find('img', {'alt' : game_title + ' header image'})
            if game_image_element is not None:
                game_image = game_image_element.get('src')
            else:
                game_image = 'https://i.imgur.com/RgTqosu.jpg'
            
            platforms = url.find_all('strong')
            available_platforms = ''
            for i in range(len(platforms)):
                available_platforms += platforms[i].text + ', '

            available_platforms = available_platforms[:-2]

            results_list = HowLongToBeat().search(game_title)
            if results_list is not None and len(results_list) > 0:
                best_element = max(results_list, key=lambda element: element.similarity)
                hltb_main = (best_element.gameplay_main + " " +best_element.gameplay_main_unit)
                hltb_main = hltb_main.replace('Hours', 'Horas')
                hltb_main = hltb_main.replace('Mins', 'Minutos')
                hltb_extras = (best_element.gameplay_main_extra + " " +best_element.gameplay_main_extra_unit)
                hltb_extras = hltb_extras.replace('Hours', 'Horas')
                hltb_extras = hltb_extras.replace('Mins', 'Minutos')
                hltb_completionist = (best_element.gameplay_completionist + " " +best_element.gameplay_completionist_unit)  
                hltb_completionist = hltb_completionist.replace('Hours', 'Horas')
                hltb_completionist = hltb_completionist.replace('Mins', 'Minutos')

            return rating, recommendation, game_title, game_image, available_platforms, hltb_main, hltb_extras, hltb_completionist
        else :
            return 'Jogo não encontrado no banco de dados do OpenCritic', '', '', 'https://i.imgur.com/2lFiGXm.png', '', '', '', ''


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
    elif data['Response'] == 'True' and data['Poster'] == 'N/A':
        return 'https://i.imgur.com/7wlZlWi.jpg'
    else: 
        return 'https://i.imgur.com/tss8ZcO.png'


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
    txt = get_rotten_tomatoes_rating(movie_name, movie_year)
    update.message.reply_photo(get_rotten_tomatoes_movie_posters(movie_name, movie_year), caption= str(txt))

def print_op_rating(update: Update, context: CallbackContext):
    game_name = " ".join(context.args)
    rating, recommendation, game_title, game_image, available_platforms, hltb_main, hltb_extras, hltb_complete = get_op_info(get_op_page(game_name))
    if rating == 'Jogo não encontrado no banco de dados do OpenCritic':
        update.message.reply_photo(game_image, caption= str(rating))
    else:
        available_platforms = available_platforms.replace(', Critic Consensus', '')
        txt = ('Jogo: ' + game_title + '\n' + 'Média do OpenCritic: ' + rating + '\n' + 'Porcentagem de recomendação da crítica: ' + recommendation + '\n' + 'Plataformas Disponiveis: ' + available_platforms + '\n' + 'Tempo de jogo para completar o jogo: ' + hltb_main + '\n' + 'Tempo de jogo para completar o jogo com extras: ' + hltb_extras + '\n' + 'Tempo de jogo para terminar tudo do jogo: ' + hltb_complete)
        update.message.reply_photo(game_image, caption= str(txt))

def main():
    updater = Updater(TOKEN,
                  use_context=True)
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('nota', print_rotten_tomatoes_rating))
    updater.dispatcher.add_handler(CommandHandler('game', print_op_rating))
    ##updater.dispatcher.add_handler(MessageHandler(Filters.text, echo))
    updater.dispatcher.add_error_handler(error)



    updater.start_webhook(listen="0.0.0.0",
                            port=int(PORT),
                            url_path=TOKEN,
                            webhook_url='https://supernota-bot.herokuapp.com/' + TOKEN)

    updater.idle()
    
if __name__ == '__main__':
    main()