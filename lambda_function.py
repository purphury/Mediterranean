# -*- coding: utf-8 -*-

# City Guide: A sample Alexa Skill Lambda function
# This function shows how you can manage data in objects and arrays,
# choose a random recommendation,
# call an external API and speak the result,
# handle YES/NO intents with session attributes,
# and return text data on a card.

import gettext
import logging

import requests
from alexa import util
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractRequestInterceptor)
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_intent_name, is_request_type
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard

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


def genre_from_album(album_id):
    url = 'http://us-qa.api.iheart.com/api/v1/catalog/getAlbumsByAlbumIds'
    headers = {'Accept': 'application/json'}
    params = (
        ('albumId', album_id),
    )
    return requests.get(url, headers=headers, params=params).json()['trackBundles'][0]['genre']


def get_all_stations():
    url = 'http://us-qa.api.iheart.com/api/v2/content/liveStations'
    headers = {'Accept': 'application/json'}
    params = (
        ('allMarkets', 'true'),
        ('limit', '-1'),
        ('offset', '0'),
    )
    return requests.get(url, headers=headers, params=params).json()


def get_locational_stations(city):
    url = 'http://us-qa.api.iheart.com/api/v2/content/liveStations'
    headers = {'Accept': 'application/json'}
    params = (
        ('allMarkets', 'false'),
        ('limit', '-1'),
        ('offset', '0'),
        ('city', city),
    )
    return requests.get(url, headers=headers, params=params).json()


def get_local_stations():
    url = 'http://us-qa.api.iheart.com/api/v2/content/liveStations'
    headers = {'Accept': 'application/json'}
    params = (
        ('allMarkets', 'false'),
        ('limit', '-1'),
        ('offset', '0'),
        ('useIP', 'true'),
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
session_id = '2QEdWamz1a7gLQ6cXMftBk'

history = requests.get(
    'https://us.api.iheart.com/api/v1/history/' + profile_id +
    '/getAll?campaignId=foryou_favorites&numResults=100&profileId=' +
    profile_id + '&sessionId=' + session_id).json()['events']
recent = history[0]['events'][0]['title']
y = [x['events'] for x in history]
favorites = [item for sublist in y for item in sublist]


def recentSong():
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


# Request Handler classes

class PlayHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("Play")(handler_input))

    def handle(self, handler_input):
        stream = 'https://c2.prod.playlists.ihrhls.com/6639/playlist.m3u8'
        return util.play(stream)


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

        speech = _("Welcome to iheartradio! What can iheart do for you?")
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
        for station in stations[:min(3, len(stations) + 1)]:
            speech += stations['hits'][0]['pronouncements'][0]['utterance']

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
        speech = f"Here are {min(3, len(stations))} stations in {city}: "
        for station in stations[:min(3, len(stations) + 1)]:
            speech += stations['hits'][0]['pronouncements'][0]['utterance']

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
    """Handler for handling fallback intent or Yes/No without
    restaurant info intent.

     2018-May-01: AMAZON.FallackIntent is only currently available in
     en-US locale. This handler will not be triggered except in that
     locale, so it can be safely deployed for any locale."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        session_attr = handler_input.attributes_manager.session_attributes
        return (is_intent_name("AMAZON.FallbackIntent")(handler_input) or
                ("restaurant" not in session_attr and (
                        is_intent_name("AMAZON.YesIntent")(handler_input) or
                        is_intent_name("AMAZON.NoIntent")(handler_input))
                 ))

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
# sb.skill_id = "amzn1.ask.skill.630a7f58-595f-4083-9393-3b20117e1647"

# Add all request handlers to the skill.
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GetListOfLocalStations())
sb.add_request_handler(GetFavoriteGenre())
sb.add_request_handler(GetFavoriteSong())
sb.add_request_handler(GetFavoriteArtist())
sb.add_request_handler(GetFavoriteAlbum())
sb.add_request_handler(GetLocalStationsByCity())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(ExitIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Add exception handler to the skill.
sb.add_exception_handler(CatchAllExceptionHandler())

# Add locale interceptor to the skill.
sb.add_global_request_interceptor(LocalizationInterceptor())

# Expose the lambda handler to register in AWS Lambda.
lambda_handler = sb.lambda_handler()
