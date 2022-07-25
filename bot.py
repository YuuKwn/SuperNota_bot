"""
Telegram Bot to return the rating of a movie or game using the title
Source: https://github.com/YuuKwn/SuperNota_bot/blob/main/bot.py
"""

from telegram.ext.updater import Updater
from telegram import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, ReplyMarkup
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
import re, requests, json, logging, os
from bs4 import BeautifulSoup
from howlongtobeatpy import HowLongToBeat
from translate import Translator
from datetime import datetime
from igdb.wrapper import IGDBWrapper

PORT = int(os.environ.get('PORT', 8443))
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

IGDB_CLIENT_ID = os.getenv('IGDB_CLIENT_ID')
IGDB_SECRET = os.getenv('IGDB_SECRET')
BOT_TOKEN = os.getenv('BOT_TOKEN')
OMDB_API_KEY = os.getenv('OMDB_API_KEY')
movieExists = False
game_0, game_1, game_2, game_3, option_0, option_1, option_2, option_3 = '', '', '', '', '', '', '', ''
globals = globals()
d={}
g={}
game_not_found= 'https://i.imgur.com/2lFiGXm.png'
wrong_game='https://c.tenor.com/14hr1KPxcCoAAAAC/community-donald-glover.gif'

#Get Game info from IGDB
def get_igdb_game_info(game_id):
    
    response = requests.post("https://id.twitch.tv/oauth2/token?client_id="+IGDB_CLIENT_ID+"&client_secret="+IGDB_SECRET+"&grant_type=client_credentials")
    access_token = response.json()['access_token']
    wrapper = IGDBWrapper(IGDB_CLIENT_ID, access_token)
    game_info = wrapper.api_request(
        'games',
        'fields name,aggregated_rating,rating,first_release_date,genres.name,platforms.name,cover.url; where id='+game_id+';'
        )
    game_info = json.loads(game_info.decode('utf-8'))
   
    try:
        game_title = game_info[0]['name']

        try:
            game_image = game_info[0]['cover']['url']
            game_image = game_image.replace('t_thumb', 't_cover_big_2x')
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
            
            txt = ('Game: ' + game_title + '\n' + 'Critic Rating: ' + game_critic_rating + '\n' + 'User Rating: ' + game_user_rating + '\n' + 'Platforms: ' + game_platforms_names + '\n' + 'Release Date: ' + game_release_date + '\n' + 'Genres: ' + game_genres_names+ '\n' + 'Time to beat: ' + hltb_main + '\n' + 'Time to beat + extras: ' + hltb_extras + '\n' + 'Time to beat everything: ' + hltb_completionist)

            return game_image, txt
        else:
            txt = ('Game: ' + game_title + '\n' + 'Critic Rating: ' + game_critic_rating + '\n' + 'User Rating: ' + game_user_rating + '\n' + 'Platforms: ' + game_platforms_names + '\n' + 'Release Date: ' + game_release_date + '\n' + 'Genres: ' + game_genres_names+ '\n' + 'Time to beat: ' + '?' + '\n' + 'Time to beat + extras: ' + '?' + '\n' + 'Time to beat everything: ' + '?')
            return game_image, txt
    except:
        return wrong_game, 'Something went wrong'

#Get rating and other infos
def get_rotten_tomatoes_rating(movie_name):
    url = 'http://www.omdbapi.com/?i=' + movie_name+ '&apikey=' + OMDB_API_KEY
    response = requests.get(url)
    data = json.loads(response.text)
    rotten_rating = 'Not Found'
    imdb_rating = 'Not Found'
    meta_rating = 'Not Found'

    try:
        if data['Poster'] != 'N/A':
            poster = data['Poster']
        else:
            poster = 'https://i.imgur.com/7wlZlWi.jpg'
        title = data['Title']
        released = data['Released']
        country = data['Country']
        plot = data['Plot']
        director = data['Director']
        try:
            box_office = data['BoxOffice']
        except KeyError:
            box_office = 'N/A'

        for i in range(len(data['Ratings'])):
            if data['Ratings'][i]['Source'] == 'Rotten Tomatoes':
                rotten_rating = data['Ratings'][i]['Value']
            if data['Ratings'][i]['Source'] == 'Internet Movie Database':
                imdb_rating = data['Ratings'][i]['Value']
            if data['Ratings'][i]['Source'] == 'Metacritic':
                meta_rating = data['Ratings'][i]['Value']


        txt =  ('**Title:** ' + title + '\n' + '**RT Recommendation %:** ' + rotten_rating + '\n' '**IMDB User Rating Avg.:** ' + imdb_rating + '\n' '**Metacritic Avg.:** ' + meta_rating + '\n' + '**Released:** ' + released + '\n' + '**Director:** ' + director + '\n' +  '**Country:** ' + country + '\n' + '**Box Office:** ' + box_office + '\n' + '**Plot:** ' + '||' + plot + '||')
        txt_escaped = re.escape(txt)
        txt_escaped = txt_escaped.replace('\*\*\\', '**')
        txt_escaped = txt_escaped.replace('\*\*', '**')
        txt_escaped = txt_escaped.replace('\|\|', '||')
        return txt_escaped, poster

    except:
        txt = (movie_name + 'not found')
        txt_escaped = re.escape(txt)
        poster = 'https://i.imgur.com/tss8ZcO.png'
        return txt_escaped.replace('\|\|', '||'), poster

def get_game_results(update: Update, context: CallbackContext):
    game_name = " ".join(context.args)
    response = requests.post("https://id.twitch.tv/oauth2/token?client_id="+IGDB_CLIENT_ID+"&client_secret="+IGDB_SECRET+"&grant_type=client_credentials")
    access_token = response.json()['access_token']
    wrapper = IGDBWrapper(IGDB_CLIENT_ID, access_token)
    game_info = wrapper.api_request(
        'games',
        'search \"'+game_name+'\";fields id,name,aggregated_rating,rating,first_release_date,genres.name,platforms.name,cover.url; limit 4; where genres >= 1; where first_release_date >= 17705387;'
        )

    game_info = json.loads(game_info.decode('utf-8'))
    if game_info == []:
        update.message.reply_photo(game_not_found, caption= str('Game not found'), parse_mode="MARKDOWNV2")
    if game_info != []:

        if len(game_info) == 4:
            for i in range(4):
                g["game_{0}".format(i)] = game_info[i]['name'], datetime.utcfromtimestamp(game_info[i]['first_release_date']).strftime('%Y'), str(game_info[i]['id'])
            globals['game_0'] = ('1.' +g['game_0'][0]+', '+g['game_0'][1])
            globals['game_1'] = ('2.' +g['game_1'][0]+', '+g['game_1'][1])
            globals['game_2'] = ('3.' +g['game_2'][0]+', '+g['game_2'][1])
            globals['game_3'] = ('4.' +g['game_3'][0]+', '+g['game_3'][1])    
            buttons = [[KeyboardButton(game_0)], [KeyboardButton(game_1)], [KeyboardButton(game_2)], [KeyboardButton(game_3)]]
            pick = update.message.reply_text(text='Pick one',reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, selective=True))

        if len(game_info) == 3:
            for i in range(3):
                g["game_{0}".format(i)] = game_info[i]['name'], datetime.utcfromtimestamp(game_info[i]['first_release_date']).strftime('%Y'), str(game_info[i]['id'])
            globals['game_0'] = ('1.' +g['game_0'][0]+', '+g['game_0'][1])
            globals['game_1'] = ('2.' +g['game_1'][0]+', '+g['game_1'][1])
            globals['game_2'] = ('3.' +g['game_2'][0]+', '+g['game_2'][1])
            buttons = [[KeyboardButton(game_0)], [KeyboardButton(game_1)], [KeyboardButton(game_2)]]
            pick = update.message.reply_text(text='Pick one',reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, selective=True))

        if len(game_info) == 2:
            for i in range(2):
                g["game_{0}".format(i)] = game_info[i]['name'], datetime.utcfromtimestamp(game_info[i]['first_release_date']).strftime('%Y'), str(game_info[i]['id'])
            globals['game_0'] = ('1.' +g['game_0'][0]+', '+g['game_0'][1])
            globals['game_1'] = ('2.' +g['game_1'][0]+', '+g['game_1'][1])
            buttons = [[KeyboardButton(game_0)], [KeyboardButton(game_1)]]
            pick = update.message.reply_text(text='Pick one',reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, selective=True))

        if len(game_info) == 1:
            game_image, txt= get_igdb_game_info(str(game_info[0]['id']))
            update.message.reply_photo(game_image, caption= str(txt), parse_mode="HTML")

        

def messageHandler(update:Update, context: CallbackContext):
    #verification for movies/series

        if update.message.text == option_0:
            reply = context.bot.send_message(chat_id = update.effective_chat.id, text='Here it is', reply_markup=ReplyKeyboardRemove())
            reply.delete()
            txt, poster = get_rotten_tomatoes_rating(d['option_0'][1])
            update.message.reply_photo(poster, caption= str(txt), parse_mode="MARKDOWNV2")

        if update.message.text == option_1:
            reply = context.bot.send_message(chat_id = update.effective_chat.id, text='Here it is', reply_markup=ReplyKeyboardRemove())
            reply.delete()
            txt, poster = get_rotten_tomatoes_rating(d['option_1'][1])
            update.message.reply_photo(poster, caption= str(txt), parse_mode="MARKDOWNV2")

        if update.message.text == option_2:
            reply = context.bot.send_message(chat_id = update.effective_chat.id, text='Here it is', reply_markup=ReplyKeyboardRemove())
            reply.delete()
            txt, poster = get_rotten_tomatoes_rating(d['option_2'][1])
            update.message.reply_photo(poster, caption= str(txt), parse_mode="MARKDOWNV2")

        if update.message.text == option_3:
            reply = context.bot.send_message(chat_id = update.effective_chat.id, text='Here it is', reply_markup=ReplyKeyboardRemove())
            reply.delete()
            txt, poster = get_rotten_tomatoes_rating(d['option_3'][1])
            update.message.reply_photo(poster, caption= str(txt), parse_mode="MARKDOWNV2")

        if update.message.text == game_0:
            reply = context.bot.send_message(chat_id = update.effective_chat.id, text='Here it is', reply_markup=ReplyKeyboardRemove())
            reply.delete()
            game_image, txt= get_igdb_game_info(g['game_0'][2])
            update.message.reply_photo(game_image, caption= str(txt), parse_mode="HTML")

        if update.message.text == game_1:
            reply = context.bot.send_message(chat_id = update.effective_chat.id, text='Here it is', reply_markup=ReplyKeyboardRemove())
            reply.delete()
            game_image, txt= get_igdb_game_info(g['game_1'][2])
            update.message.reply_photo(game_image, caption= str(txt), parse_mode="HTML")

        if update.message.text == game_2:
            reply = context.bot.send_message(chat_id = update.effective_chat.id, text='Here it is', reply_markup=ReplyKeyboardRemove())
            reply.delete()
            game_image, txt= get_igdb_game_info(g['game_2'][2])
            update.message.reply_photo(game_image, caption= str(txt), parse_mode="HTML")

        if update.message.text == game_3:
            reply = context.bot.send_message(chat_id = update.effective_chat.id, text='Here it is', reply_markup=ReplyKeyboardRemove())
            reply.delete()
            game_image, txt= get_igdb_game_info(g['game_3'][2])
            update.message.reply_photo(game_image, caption= str(txt), parse_mode="HTML")

     #verification for games

def get_results(update: Update, context: CallbackContext):
    separate = " ".join(context.args).split(",")
    movie_name = separate[0]
    movie_year = ""
    if len(separate) > 1:
        movie_year = separate[1]
    url = 'http://www.omdbapi.com/?s=' + movie_name + '&y='+ movie_year+'&apikey=' + OMDB_API_KEY
    response = requests.get(url)
    data = json.loads(response.text)
    if data['Response'] == 'False':
        txt, poster = get_rotten_tomatoes_rating('on your majesty secret service')
        update.message.reply_photo(poster, caption= str(txt), parse_mode="MARKDOWNV2")
    else:
        if len(data['Search']) >= 4:
            for i in range(4):
                d["option_{0}".format(i)] = [data['Search'][i]['Title'], data['Search'][i]['imdbID'], data['Search'][i]['Year']]
            globals['option_0'] = '1.'+str(d['option_0'][0]) +', '+ str(d['option_0'][2])
            globals['option_1'] = '2.'+str(d['option_1'][0]) + ', ' + str(d['option_1'][2])
            globals['option_2'] = '3.'+str(d['option_2'][0]) +', ' +  str(d['option_2'][2])
            globals['option_3'] = '4.'+str(d['option_3'][0]) + ', '+ str(d['option_3'][2])
            buttons = [[KeyboardButton(option_0)], [KeyboardButton(option_1)], [KeyboardButton(option_2)], [KeyboardButton(option_3)]]
            pick = update.message.reply_text(text='Pick one', reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, selective=True))

        elif len(data['Search']) == 3:
            for i in range(3):
                d["option_{0}".format(i)] = [data['Search'][i]['Title'], data['Search'][i]['imdbID'], data['Search'][i]['Year']]
            globals['option_0'] = '1.'+str(d['option_0'][0]) +', '+ str(d['option_0'][2])
            globals['option_1'] = '2.'+str(d['option_1'][0]) + ', ' + str(d['option_1'][2])
            globals['option_2'] = '3.'+str(d['option_2'][0]) +', ' +  str(d['option_2'][2])
            buttons = [[KeyboardButton(option_0)], [KeyboardButton(option_1)], [KeyboardButton(option_2)]]
            pick = update.message.reply_text(text='Pick one',reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, selective=True))

        elif len(data['Search']) == 2:
            for i in range(2):
                d["option_{0}".format(i)] = [data['Search'][i]['Title'], data['Search'][i]['imdbID'], data['Search'][i]['Year']]
            globals['option_0'] = '1.'+str(d['option_0'][0]) +', '+ str(d['option_0'][2])
            globals['option_1'] = '2.'+str(d['option_1'][0]) + ', ' + str(d['option_1'][2])
            buttons = [[KeyboardButton(option_0)], [KeyboardButton(option_1)]]
            pick = update.message.reply_text(text='Pick one', reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, selective=True))


        elif len(data['Search']) == 1:
            for i in range(1):
                d["option_{0}".format(i)] = [data['Search'][i]['Title'], data['Search'][i]['imdbID']]
            txt, poster = get_rotten_tomatoes_rating(d['option_0'][1])
            update.message.reply_photo(poster, caption= str(txt), parse_mode="MARKDOWNV2")
        
    
def remove_keyboard(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id = update.effective_chat.id, text='Here it is',reply_markup=ReplyKeyboardRemove(selective=True))

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    updater = Updater(BOT_TOKEN,
                  use_context=True)
    updater.dispatcher.add_handler(CommandHandler('nota', get_results))
    updater.dispatcher.add_handler(CommandHandler('game', get_game_results))
    updater.dispatcher.add_handler(CommandHandler('keyboard', remove_keyboard()))


    updater.dispatcher.add_error_handler(error)
    updater.dispatcher.add_handler(MessageHandler(Filters.text, messageHandler))


    updater.start_webhook(listen="0.0.0.0",
                            port=int(PORT),
                            url_path=BOT_TOKEN,
                            webhook_url='https://supernota-bot.herokuapp.com/' + BOT_TOKEN)

    updater.idle()
    
if __name__ == '__main__':
    main()