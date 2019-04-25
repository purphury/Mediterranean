# -*- coding: utf-8 -*-

# City Guide: A sample Alexa Skill Lambda function
# This function shows how you can manage data in objects and arrays,
# choose a random recommendation,
# call an external API and speak the result,
# handle YES/NO intents with session attributes,
# and return text data on a card.

import logging
import gettext
import random
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractRequestInterceptor)
from ask_sdk_core.utils import is_intent_name, is_request_type
import requests
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard

from alexa import util

# Skill Builder object
sb = SkillBuilder()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def name_from_id(track_id):
    url = 'http://us-qa.api.iheart.com/api/v1/catalog/getTrackByTrackId'
    headers = {'Accept': 'application/json'}
    params = (
        ('trackId', track_id),
    )
    return requests.get(url, headers=headers, params=params).json()['track']['title']

def get_rand_pop_podcasts():
    url = 'https://leads.radioedit.iheart.com/api/cards?collection=collections/popular-podcasts&country=US'
    headers = {'Accept': 'application/json'}
    podcasts = requests.get(url, headers=headers, params=None).json()
    final_podcasts = []

    for x in range(3):
        final_podcasts.append(podcasts['cards'][ random.randint(0, len(podcasts['cards']) - 1) ])
    
    return final_podcasts


def log_in_user():
    url = 'http://us-qa.api.iheart.com/api/v3/locationConfig'
    headers = {'Accept': 'application/json'}
    params = (
        ('email', 'dannynewman@yahoo.com'),
        ('hostname', 'webapp'),
        ('version', '8-prod'),

    )
    return requests.get(url, headers=headers, params=params).json()

def fetch_user_playlist():
    url = 'http://us-qa.api.iheart.com/api/v2/playlists/1050508256/ARTIST/9288'
    headers = {'Accept': 'application/json'}
    params = (
        ('X-Session-Id', 'dannynewman@yahoo.com'),
        ('X-User-Id', 'webapp'),
    )
    return requests.get(url, headers=headers, params=params).json()


def user_collection():
    url = 'http://us-qa.api.iheart.com/api/v3/collection/user/1050508256/collection'
    headers = {'Accept': 'application/json'}
    params = (
        ()

    )
    return requests.get(url, headers=headers, params=params).json()


def genre_from_album(album_id):
    url = 'http://us-qa.api.iheart.com/api/v1/catalog/getAlbumsByAlbumIds'
    headers = {'Accept': 'application/json'}
    params = (
        ('albumId', album_id),
    )
    return requests.get(url, headers=headers, params=params).json()['trackBundles'][0]['genre']


def get_genre_id(genre_name):
    url = 'http://us-qa.api.iheart.com/api/v2/content/genre'
    headers = {'Accept': 'application/json'}
    params = (
        ('offset', '0'),
    )
    genres = requests.get(url, headers=headers, params=params).json()

    finID = None

    for ids in range(len(genres['hits'])):
        if genre_name == genres['hits'][ids]:
            finID = genres['hits'][ids]
    
    return finID

def get_genre_stream(genre_id):
    url = 'http://us-qa.api.iheart.com/api/v2/content/liveStations'
    headers = {'Accept': 'application/json'}
    params = (
        ('genreId', genre_id),
        ('limit', '50'),
        ('useIP', 'false')
    )
    station_list = requests.get(url, headers=headers, params=params).json()
    station_url = None

    for stations in range(len(station_list['hits'])):
        if 'secure_hls_stream' in station_list['hits'][stations]['streams']:
            station_url = station_list['hits'][stations]['streams']['secure_hls_stream']
    
    return station_url

def get_working_station(station_list):
    
    for stations in range(len(station_list['hits'])):
        if 'secure_hls_stream' in station_list['hits'][stations]['streams']:
            working_station = station_list['hits'][stations]
            break

    return working_station

def get_recent_station_track(streamId):

    url = f'http://us-qa.api.iheart.com/api/v3/live-meta/stream/{streamId}/trackHistory'
    headers = {'Accept': 'application/json'}
    params = ()

    track_id = requests.get(url, headers=headers, params=params).json()['data'][0]['trackId']

    return name_from_id(track_id) 

def get_all_stations():
    url = 'http://us-qa.api.iheart.com/api/v2/content/liveStations'
    headers = {'Accept': 'application/json'}
    params = (
        ('allMarkets', 'true'),
        ('limit', '-1'),
        ('offset', '0'),
    )
    return requests.get(url, headers=headers, params=params).json()


def get_market_id(city):
    url='http://us-qa.api.iheart.com/api/v2/content/markets'
    headers = {'Accept': 'application/json'}
    params = (
        ('city', city),
        ('limit', '1'),
        ('offset', '0'),
        ('useIP', 'false')
    )
    marketJSON = requests.get(url, headers=headers, params=params).json()
    marketId = marketJSON['hits'][0]['marketId']
    logger.info(f'{marketId}')
    return marketId


def get_locational_stations(city):
    url = 'http://us-qa.api.iheart.com/api/v2/content/liveStations'
    headers = {'Accept': 'application/json'}
    params = (
        ('allMarkets', 'false'),
        ('limit', '-1'),
        ('offset', '0'),
        ('marketId', get_market_id(city))
    )
    return requests.get(url, headers=headers, params=params).json()


def get_local_stations():
    url = 'http://us-qa.api.iheart.com/api/v2/content/liveStations'
    headers = {'Accept': 'application/json'}
    params = (
        ('allMarkets', 'false'),
        ('limit', '20'),
        ('offset', '0'),
        ('useIP', 'true'),
        ('sort', 'cume'),
    )
    return requests.get(url, headers=headers, params=params).json()


def load_station_dicts(a):
    station_urls = {}
    station_names = {}
    station_descs = {}

    # read values into dicts
    i = 0
    for x in range(a['total']):
        try:
            hls_url = a['hits'][x]['streams']['hls_stream']
            if hls_url != '':
                station_urls[i] = hls_url
                station_names[i] = a['hits'][i]['name']
                station_descs[i] = a['hits'][i]['description']
                i += 1
        except:
            continue

    return station_urls, station_names, station_descs, i


profile_id = '1050508256'
session_id = '5HZkQn3a4aEUZG4ST69ahk'

# Debug Calls Start
# test = get_rand_pop_podcasts()
# Debug Calls End


history = requests.get(
    'https://us.api.iheart.com/api/v1/history/' + profile_id +
    '/getAll?campaignId=foryou_favorites&numResults=100&profileId=' +
    profile_id + '&sessionId=' + session_id
    ).json()['events']
try:
    recent = history[0]['events'][0]['title']
except:
    recent = 'No recent songs'

y = [x['events'] for x in history]
favorites = [item for sublist in y for item in sublist]

def recentSong():
    history = regenHistory()
    try:
        recent = history[0]['events'][0]['title']
    except:
        recent = 'No recent songs'

    return recent
def favGenre():
    genres = [f['albumId'] for f in favorites]
    return genre_from_album(max(set(genres), key=genres.count))

def favSong():
    songs = [f['songId'] for f in favorites]
    return name_from_id(max(set(songs), key=songs.count))

def favArtist():
    artists = [f['artistName'] for f in favorites]
    return max(set(artists), key=artists.count)

def favAlbum():
    albums = [f['album'] for f in favorites]
    return max(set(albums), key=albums.count)

def regenHistory():
    history = requests.get(
    'https://us.api.iheart.com/api/v1/history/' + profile_id +
    '/getAll?campaignId=foryou_favorites&numResults=100&profileId=' +
    profile_id + '&sessionId=' + session_id
    ).json()['events']
    logger.info(history)
    return history


# Request Handler classes
class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for skill launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In LaunchRequestHandler")
        _ = handler_input.attributes_manager.request_attributes["_"]

        # logger.info(_("This is an untranslated message"))

        speech = _("What can iheart do for you?")
        handler_input.response_builder.speak(speech)
        handler_input.response_builder.ask(_(
            "What can iheart do for you?"))
        return handler_input.response_builder.response


# Gets some local stations
class GetListOfLocalStations(AbstractRequestHandler):
    """Handler for Skill Launch and GetNewFact Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("GetLocalStation")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In GetListOfLocalStations")

        stations = get_local_stations()

        speech = f"Here are {min(3, len(stations))} of the local stations around you: "
        logger.info(type(stations))
        logger.info(stations['hits'][0]['pronouncements'][0])
        
        for hitList in range(min(len(stations['hits']), 3)):
            try:
                speech += stations['hits'][hitList]['pronouncements'][0]['utterance'] + ', '
            except:
                speech += stations['hits'][hitList]['name'] + ', '

        handler_input.response_builder.speak(speech).set_card(
            SimpleCard("Local Station", speech))
        return handler_input.response_builder.response

class GetRecentSong(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("GetRecentSong")(handler_input))

    def handle(self, handler_input):
        speech = "Here is your recent song: "
        handler_input.response_builder.speak(speech + recentSong())

        return handler_input.response_builder.response

class GetFavoriteGenre(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("GetFavoriteGenre")(handler_input))

    def handle(self, handler_input):
        speech = "Here is your favorite genre: "
        handler_input.response_builder.speak(speech + favGenre())
        
        return handler_input.response_builder.response

class PlayFavoriteGenre(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("PlayFavoriteGenre")(handler_input)

    def handle(self, handler_input):
        genreID = get_genre_id(favGenre())
        stream = get_genre_stream(genreID)

        return util.play(stream, 0, "Playing...", util.data.en['card'], handler_input.response_builder)


class PlayHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("Play")(handler_input)

    def handle(self, handler_input):
        stream = get_working_station(get_local_stations())
        logger.info(stream)
        if stream == None:
            handler_input.response_builder.speak("Could not find a live station")
            logger.info("STREAM IS NONE")
            return handler_input.response_builder.response

        stream_url = stream['streams']['secure_hls_stream']
        try:
            currently_playing = get_recent_station_track(stream['id'])
            logger.info(f"{currently_playing} | {stream['id']}")
            echo_response = f"Now playing {currently_playing} on {stream['pronouncements'][0]['utterance']}"
        except:
            echo_response = f"Now playing {stream['pronouncements'][0]['utterance']}"
            logger.info(f"In exception | {stream['id']}")

        return util.play(stream_url, 0, echo_response, util.data.en['card'], handler_input.response_builder)


class StopHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input) or
                is_intent_name("AMAZON.PauseIntent")(handler_input))

    def handle(self, handler_input):
        
        return util.stop('Stoping audio...', handler_input.response_builder)


class GetFavoriteAlbum(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("GetFavoriteAlbum")(handler_input))

    def handle(self, handler_input):
        speech = "Here is your favorite album: "
        handler_input.response_builder.speak(speech + favAlbum())
        
        return handler_input.response_builder.response

class GetFavoriteSong(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("GetFavoriteSong")(handler_input))

    def handle(self, handler_input):
        speech = "Here is your favorite song: "
        handler_input.response_builder.speak(speech + favSong())
        
        return handler_input.response_builder.response

class GetFavoriteArtist(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("GetFavoriteArtist")(handler_input))

    def handle(self, handler_input):
        speech = "Here is your favorite artist: "
        handler_input.response_builder.speak(speech + favArtist())
        
        return handler_input.response_builder.response

class GetLocalStationsByCity(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("GetLocalStationsByCity")(handler_input))

    def handle(self, handler_input):
        city = util.get_resolved_value(
            handler_input.request_envelope.request, "city")
        
        stations = get_locational_stations(city)
        logger.info(stations)
        speech = f"Here are {min(3, len(stations))} stations in {city}: "
        
        logger.info(min(len(stations['hits']), 3))

        for hitList in range(min(len(stations['hits']), 3)):
            try:
                speech += stations['hits'][hitList]['pronouncements'][0]['utterance'] + ', '
            except:
                speech += stations['hits'][hitList]['name'] + ', '

        handler_input.response_builder.speak(speech)
        return handler_input.response_builder.response

class NewPodcast(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("NewPodcast")(handler_input))

    def handle(self, handler_input):
        logger.info("In NewPodcast")
        podcasts = get_rand_pop_podcasts()
        speech = "Search for " + podcasts[0]['title'] + " on I heart media. " + podcasts[0]['subtitle']
        handler_input.response_builder.speak(speech)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for skill session end."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In SessionEndedRequestHandler")
        logger.info("Session ended with reason: {}".format(
            handler_input.request_envelope.request.reason))
        return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for help intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In HelpIntentHandler")
        _ = handler_input.attributes_manager.request_attributes["_"]

        handler_input.response_builder.speak(_(
            "Say local radio stations")).ask(_("Say local radio stations"))
        return handler_input.response_builder.response


class ExitIntentHandler(AbstractRequestHandler):
    """Single Handler for Cancel, Stop intents."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In ExitIntentHandler")
        _ = handler_input.attributes_manager.request_attributes["_"]

        handler_input.response_builder.speak(_(
            "Okay, see you later!")).set_should_end_session(True)
        return handler_input.response_builder.response


class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        session_attr = handler_input.attributes_manager.session_attributes
        return (is_intent_name("AMAZON.FallbackIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        _ = handler_input.attributes_manager.request_attributes["_"]

        handler_input.response_builder.speak(_(
            "I can't help you with that.").format("iheart")).ask(_(
            "I can't help you with that.").format("iheart"))

        return handler_input.response_builder.response


# Exception Handler classes
class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch All Exception handler.

    This handler catches all kinds of exceptions and prints
    the stack trace on AWS Cloudwatch with the request envelope."""
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)
        logger.info("Original request was {}".format(
            handler_input.request_envelope.request))

        speech = "Sorry, there was some problem. Please try again!!"
        handler_input.response_builder.speak(speech).ask(speech)

        return handler_input.response_builder.response


class LocalizationInterceptor(AbstractRequestInterceptor):
    """Add function to request attributes, that can load locale specific data."""
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        locale = handler_input.request_envelope.request.locale
        logger.info("Locale is {}".format(locale))
        i18n = gettext.translation(
            'base', localedir='locales', languages=[locale], fallback=True)
        handler_input.attributes_manager.request_attributes[
            "_"] = i18n.gettext


# Set the skill id [Not needed (maybe)]
#sb.skill_id = "amzn1.ask.skill.630a7f58-595f-4083-9393-3b20117e1647"

# Add all request handlers to the skill.
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GetListOfLocalStations())
sb.add_request_handler(GetFavoriteGenre())
sb.add_request_handler(GetFavoriteSong())
sb.add_request_handler(GetFavoriteArtist())
sb.add_request_handler(GetFavoriteAlbum())
sb.add_request_handler(GetRecentSong())
sb.add_request_handler(NewPodcast())
sb.add_request_handler(GetLocalStationsByCity())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(ExitIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(PlayHandler())
sb.add_request_handler(StopHandler())
sb.add_request_handler(PlayFavoriteGenre())


# Add exception handler to the skill.
sb.add_exception_handler(CatchAllExceptionHandler())

# Add locale interceptor to the skill.
sb.add_global_request_interceptor(LocalizationInterceptor())

# Expose the lambda handler to register in AWS Lambda.
lambda_handler = sb.lambda_handler()
