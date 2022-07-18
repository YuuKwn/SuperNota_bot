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
from translate import Translator
from datetime import datetime

t = Translator(to_lang="pt-BR")


PORT = int(os.environ.get('PORT', 8443))
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

omdb_api_key = 'd87fbf5f'
movieExists = False
BOT_TOKEN = '5205421916:AAEBcTQYdpYt6HKmW6VieNrSnibr-5GS6vg'



igdb_client_id = 'rb28wttfszwg5kki1baracnzlki67z'
igdb_secret = 'wicf4p0pq1p76nexptfpxdopvp9tx2'

#Get Game info from IGDB
def get_igdb_game_info(game_name):
    
    response = requests.post("https://id.twitch.tv/oauth2/token?client_id="+igdb_client_id+"&client_secret="+igdb_secret+"&grant_type=client_credentials")

    access_token = response.json()['access_token']
    headers = {
        'Client-ID': igdb_client_id,
        'Authorization': 'Bearer ' + access_token
        }

    game_info = requests.post("https://api.igdb.com/v4/games/?fields=name,aggregated_rating,rating,first_release_date,genres.name,platforms.name,cover.url&limit=1&search="+game_name+"&where=parent_game=null", headers=headers)
    game_info = game_info.json()
    if game_info == []:
        return 'Game not found', 'https://i.imgur.com/2lFiGXm.png', '', '', '', '', '', '', '', ''
    elif game_info != []:    
        try:
            game_title = game_info[0]['name']

            try:
                game_image = game_info[0]['cover']['url']
                game_image = game_image.replace('t_thumb', 't_cover_big')
                game_image = game_image.replace('//', 'https://')
                
            except:
                game_image = 'https://i.imgur.com/RgTqosu.jpg'
            try:
                game_critic_rating = str(round(game_info[0]['aggregated_rating'], 0))[:-2]
            except:
                game_critic_rating = 'N/A'
            try:
                game_user_rating = str(round(game_info[0]['rating'], 0))[:-2]
            except:
                game_user_rating = 'N/A'
            try:
                game_release_date = datetime.utcfromtimestamp(game_info[0]['first_release_date']).strftime('%d/%m/%Y')
            except:
                game_release_date = 'N/A'
            game_genres = game_info[0]['genres']
            game_platforms = game_info[0]['platforms']
            game_platforms_names = ''
            game_genres_names = ''
            for i in range(len(game_genres)):
                game_genres_names += game_genres[i]['name'] + ', '  
                
            for i in range(len(game_platforms)):
                game_platforms_names += game_platforms[i]['name'] + ', '

            game_genres_names = game_genres_names[:-2]
            game_platforms_names = game_platforms_names[:-2]

            #Based on the game name, get HowLongToBeat's information]
            results_list = HowLongToBeat().search(game_title)
            if results_list is not None and len(results_list) > 0:
                best_element = results_list[0]
                if best_element.gameplay_main_unit is not None:       
                    hltb_main = (str(best_element.gameplay_main) + " " +best_element.gameplay_main_unit)

                    hltb_main = hltb_main.replace('-1', 'N/A')
                else: 
                    hltb_main = 'N/A'

                if best_element.gameplay_main_extra_unit is not None:
                    hltb_extras = (str(best_element.gameplay_main_extra) + " " +best_element.gameplay_main_extra_unit)

                    hltb_extras = hltb_extras.replace('-1', 'N/A')
                else: 
                    hltb_extras = 'N/A'

                if best_element.gameplay_completionist_unit is not None:
                    hltb_completionist = (str(best_element.gameplay_completionist) + " " +best_element.gameplay_completionist_unit)  

                    hltb_completionist = hltb_completionist.replace('-1', 'N/A')
                else: 
                    hltb_completionist = 'N/A'
                
                return game_title, game_image, game_critic_rating, game_user_rating, game_release_date, game_genres_names, game_platforms_names, hltb_main, hltb_extras, hltb_completionist
            else:

                return game_title, game_image, game_critic_rating, game_user_rating, game_release_date, game_genres_names, game_platforms_names, 'N/A', 'N/A', 'N/A'
        except:
            return 'Deu um ruim inesperado', 'https://c.tenor.com/14hr1KPxcCoAAAAC/community-donald-glover.gif', '', '', '', '', '', '', '', ''

#Generate variable with Game info
def print_igdb_info(update: Update, context: CallbackContext):
    game_name = " ".join(context.args)
    game_title, game_image, game_critic_rating, game_user_rating, game_release_date, game_genres_names, game_platforms_names, hltb_main, hltb_extras, hltb_completionist = get_igdb_game_info(game_name)
    if game_title == 'Game not found' or game_title == 'Deu um ruim inesperado':
        update.message.reply_photo(game_image, caption= str(game_title))

    else:
        txt = ('Game: ' + game_title + '\n' + 'Critic Rating: ' + game_critic_rating + '\n' + 'User Rating: ' + game_user_rating + '\n' + 'Platforms: ' + game_platforms_names + '\n' + 'Release Date: ' + game_release_date + '\n' + 'Genres: ' + game_genres_names+ '\n' + 'Time to beat: ' + hltb_main + '\n' + 'Time to beat + extras: ' + hltb_extras + '\n' + 'Time to beat everything: ' + hltb_completionist)
        update.message.reply_photo(game_image, caption= str(txt))

#Get Movie Info
def get_rotten_tomatoes_movie_posters(movie_name, movie_year):
    #Get the movie posters from omdb if the movie is found in the database
    url = 'http://www.omdbapi.com/?t=' + movie_name + '&y='+ movie_year + '&apikey=' + omdb_api_key
    response = requests.get(url)
    data = json.loads(response.text)
    if data['Response'] == 'True' and data['Poster'] != 'N/A':
        return  data['Poster']
    elif data['Response'] == 'True' and data['Poster'] == 'N/A':
        return 'https://i.imgur.com/7wlZlWi.jpg'
    else: 
        return 'https://i.imgur.com/tss8ZcO.png'


def get_rotten_tomatoes_rating(movie_name, movie_year):
    url = 'http://www.omdbapi.com/?t=' + movie_name + '&y='+ movie_year + '&apikey=' + omdb_api_key
    response = requests.get(url)
    data = json.loads(response.text)
    rotten_rating, imdb_rating, meta_rating = 'Not Found'

    try:
        released = data['Released']
        country = data['Country']
        plot = data['Plot']
        try:
            box_office = data['boxOffice']
        except KeyError:
            box_office = 'N/A'

        for i in range(len(data['Ratings'])):
            if data['Ratings'][i]['Source'] == 'Rotten Tomatoes':
                rotten_rating = data['Ratings'][i]['Value']
            if data['Ratings'][i]['Source'] == 'Internet Movie Database':
                imdb_rating = data['Ratings'][i]['Value']
            if data['Ratings'][i]['Source'] == 'Metacritic':
                meta_rating = data['Ratings'][i]['Value']

        txt =  ('**Title:** ' + data['Title'] + '\n' + '**Rotten Tomatoes Recommendation %:** ' + rotten_rating + '\n' '**IMDB User Rating Avg.:** ' + imdb_rating + '\n' '**Metacritic Avg.:** ' + meta_rating + '\n' + '**Released:** ' + released + '\n' + '**Director:** ' + data['Director'] + '\n' +  '**Country:** ' + country + '\n' + '**Box Office:** ' + box_office + '\n' +'**Plot:** ||' + plot + '||')
        txt_escaped = re.escape(txt)
        txt_escaped = txt_escaped.replace('\*\*\\', '**')
        txt_escaped = txt_escaped.replace('\*\*', '**')
        txt_escaped = txt_escaped.replace('\|\|', '||')
        return txt_escaped

    except:
        txt = (movie_name + 'not found')
        txt_escaped = re.escape(txt)
        return txt_escaped.replace('\|\|', '||')


def print_rotten_tomatoes_rating(update: Update, context: CallbackContext):
    separate = " ".join(context.args).split(",")
    movie_name = separate[0]
    movie_year = ""
    if len(separate) > 1:
        movie_year = separate[1]
    txt = get_rotten_tomatoes_rating(movie_name, movie_year)
    update.message.reply_photo(get_rotten_tomatoes_movie_posters(movie_name, movie_year), caption= str(txt), parse_mode="MARKDOWNV2")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    updater = Updater(BOT_TOKEN,
                  use_context=True)
    updater.dispatcher.add_handler(CommandHandler('nota', print_rotten_tomatoes_rating))
    updater.dispatcher.add_handler(CommandHandler('game', print_igdb_info))
    updater.dispatcher.add_error_handler(error)



    updater.start_webhook(listen="0.0.0.0",
                            port=int(PORT),
                            url_path=BOT_TOKEN,
                            webhook_url='https://supernota-bot.herokuapp.com/' + BOT_TOKEN)

    updater.idle()
    
if __name__ == '__main__':
    main()