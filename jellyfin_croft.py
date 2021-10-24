import logging
import subprocess
from enum import Enum
from collections import defaultdict
from mycroft.util.parse import match_one
import json
import re

try:
    # this import works when installing/running the skill
    # note the relative '.'
    from .jellyfin_client import JellyfinClient, MediaItemType, JellyfinMediaItem, PublicJellyfinClient
except (ImportError, SystemError):
    # when running unit tests the '.' from above fails so we exclude it
    from jellyfin_client import JellyfinClient, MediaItemType, JellyfinMediaItem, PublicJellyfinClient

class IntentType(Enum):
    MEDIA = "media"
    ARTIST = "artist"
    ALBUM = "album"
    SONG = "song"
    PLAYLIST = "playlist"
    GENRE = "genre"

    @staticmethod
    def from_string(enum_string):
        assert enum_string is not None
        for item_type in IntentType:
            if item_type.value == enum_string.lower():
                return item_type


class JellyfinCroft(object):

    def __init__(self, host, username, password, client_id='12345', diagnostic=False):
        self.host = JellyfinCroft.normalize_host(host)
        self.log = logging.getLogger(__name__)
        self.version = "UNKNOWN"
        self.meta = []
        self.set_version()
        if not diagnostic:
            self.client = JellyfinClient(
                self.host, username, password,
                device="Mycroft", client="Jellyfin Skill", client_id=client_id, version=self.version)
        else:
            self.client = PublicJellyfinClient(self.host, client_id=client_id)


    @staticmethod
    def determine_intent(intent: dict):
        """
        Determine the intent!

        :param self:
        :param intent:
        :return:
        """
        if 'media' in intent:
            return intent['media'], IntentType.from_string('media')
        elif 'artist' in intent:
            return intent['artist'], IntentType.from_string('artist')
        elif 'album' in intent:
            return intent['album'], IntentType.from_string('album')
        elif 'playlist' in intent:
            return intent['playlist'], IntentType.from_string('playlist')
        elif 'genre' in intent:
            return intent['genre'], IntentType.from_string('genre')
        else:
            return None

    def handle_intent(self, intent: str, intent_type: IntentType):
        """
        Returns songs for given intent if songs are found; none if not
        :param intent_type:
        :param intent:
        :return:
        """

        songs = []
        if intent_type == IntentType.MEDIA:
            # default to instant mix
            songs = self.find_songs(intent)
        elif intent_type == IntentType.ARTIST:
            # return songs by artist
            artist_items = self.search_artist(intent)
            if len(artist_items) > 0:
                songs = self.get_songs_by_artist(artist_items[0].id)
        elif intent_type == IntentType.ALBUM:
            # return songs by album
            album_items = self.search_album(intent)
            if len(album_items) > 0:
                songs = self.get_songs_by_album(album_items[0].id)
        elif intent_type == IntentType.PLAYLIST:
            # return songs in playlist
            playlist_items = self.search_playlist(intent)
            songs = self.get_songs_by_playlist(playlist_items[0].id)
        elif intent_type == IntentType.GENRE:
            genre_items = get_songs_by_genre(intent)
            songs = self.get_songs_by_genre(genre_items[0].id)
        return songs

    def find_songs(self, media_name, media_type=None)->[]:
        """
        This is the expected entry point for determining what songs to play

        :param media_name:
        :param media_type:
        :return:
        """

        songs = []
        songs = self.instant_mix_for_media(media_name)
        return songs

    def set_meta(self, meta_data):
        if meta_data != []:
            self.meta = meta_data

    def get_meta(self, track_id):
        # stream?static=true&DeviceId=none&song_id=e67feaa1a1fac274d87e2442a9b5d1e5
        track_id = self.track_id_from_url(track_id)
        for item in self.meta:
            if item['Id'] == track_id:
                return item
        return False

    def get_all_meta(self):
        return self.meta

    def get_track_list(self):
        track_list = []
        for item in self.meta:
            track = {
                'artist' : item["Artists"],
                'album' : item["Album"],
                'track' : item['Name']
            }
            track_list.append(track)
            self.log.info(track)
        return track_list

    def track_id_from_url(self, url):
         # stream?static=true&DeviceId=none&song_id=e67feaa1a1fac274d87e2442a9b5d1e5
        track_id = re.search(".*song_id=(.*)", url).group(1)
        return track_id

    def add_to_playlist(self, track_id, playlist):
        playlist = self.search_playlist(playlist)
        if len(playlist) > 0:
            song_id = self.track_id_from_url(track_id)
            self.log.info("playlist id:")
            self.log.info(playlist[0].id)
            add_to = self.client.add_to_playlist(song_id, playlist[0].id)
            return add_to
        else:
            return False
            
    def search_artist(self, artist):
        """
        Helper method to just search Jellyfin for an artist
        :param artist:
        :return:
        """
        return self.search(artist, [MediaItemType.ARTIST.value])

    def search_album(self, artist):
        """
        Helper method to just search Jellyfin for an album
        :param album:
        :return:
        """
        return self.search(artist, [MediaItemType.ALBUM.value])

    def search_genre(self, artist):
        """
        Helper method to just search Jellyfin for an album
        :param album:
        :return:
        """
        return self.search(artist, [MediaItemType.GENRE.value])

    def search_song(self, song):
        """
        Helper method to just search Jellyfin for songs
        :param song:
        :return:
        """
        return self.search(song, [MediaItemType.SONG.value])

    def search_playlist(self, playlist):
        """
        Helper method to search Jellyfin for a named playlist

        :param playlist:
        :return:
        """
        return self.search(playlist, [MediaItemType.PLAYLIST.value])

    def search(self, query, include_media_types=[]):
        """
        Searches Jellyfin from a given query
        :param query:
        :param include_media_types:
        :return:
        """
        response = self.client.search(query, include_media_types)
        search_items = JellyfinCroft.parse_search_hints_from_response(response)
        return JellyfinMediaItem.from_list(search_items)

    def get_instant_mix_songs(self, item_id):
        """
        Requests an instant mix from an Jellyfin item id
        and returns song uris to be played by the Audio Service
        :param item_id:
        :return:
        """
        response = self.client.instant_mix(item_id)
        queue_items = JellyfinMediaItem.from_list(
            JellyfinCroft.parse_response(response))
        self.set_meta(
            JellyfinCroft.parse_response(response))
        song_uris = []
        for item in queue_items:
            song_uris.append(self.client.get_song_file(item.id))
        return song_uris

    def instant_mix_for_media(self, media_name):
        """
        Method that takes in a media name (artist/song/album) and
        returns an instant mix of song uris to be played

        :param media_name:
        :return:
        """

        items = self.search(media_name)
        if items is None:
            items = []

        songs = []
        for item in items:
            self.log.info('Instant Mix potential match: ' + item.name)
            if len(songs) == 0:
                songs = self.get_instant_mix_songs(item.id)
            else:
                break

        return songs

    def get_albums_by_artist(self, artist_id):
        return self.client.get_albums_by_artist(artist_id)

    def get_songs_by_album(self, album_id):
        response = self.client.get_songs_by_album(album_id)
        return self.convert_response_to_playable_songs(response)

    def get_songs_by_artist(self, artist_id):
        response = self.client.get_songs_by_artist(artist_id)
        return self.convert_response_to_playable_songs(response)

    def get_songs_by_genre(self, genre_id):
        response = self.client.get_songs_by_genre(genre_id)
        return self.convert_response_to_playable_songs(response)

    def get_all_artists(self):
        return self.client.get_all_artists()

    def get_songs_by_playlist(self, playlist_id):
        response = self.client.get_songs_by_playlist(playlist_id)
        return self.convert_response_to_playable_songs(response)


    def get_server_info_public(self):
        return self.client.get_server_info_public()

    def get_server_info(self):
        return self.client.get_server_info()

    def convert_response_to_playable_songs(self, item_query_response):
        queue_items = JellyfinMediaItem.from_list(
            JellyfinCroft.parse_response(item_query_response))
        self.set_meta(
            JellyfinCroft.parse_response(item_query_response))
        for i in JellyfinCroft.parse_response(item_query_response):
            for x, y in i.items():
                self.log.debug(x + ":" + str(y))
        return self.convert_to_playable_songs(queue_items)

    def convert_to_playable_songs(self, songs):
        song_uris = []
        for item in songs:
            song_uris.append(self.client.get_song_file(item.id))
        return song_uris


    @staticmethod
    def parse_search_hints_from_response(response):
        if response.text:
            response_json = response.json()
            return response_json["SearchHints"]

    @staticmethod
    def parse_response(response):
        if response.text:
            response_json = response.json()
            return response_json["Items"]

    def smart_parse_common_phrase(self, phrase: str):
        """
        Attempt to get keywords in phrase such as
        {artist/album/song} and determine a users
        intent
        :param phrase:
        :return:
        """

        removals = ['emby', 'mb']
        media_types = {'artist': MediaItemType.ARTIST,
                       'album': MediaItemType.ALBUM,
                       'song': MediaItemType.SONG,
                       'playlist': MediaItemType.PLAYLIST,
                       'genre' : MediaItemType.GENRE}

        phrase = phrase.lower()

        for removal in removals:
            phrase = phrase.replace(removal, "")

        # determine intent if exists
        # does not handle play album by artist
        intent = None
        for media_type in media_types.keys():
            if media_type in phrase:
                intent = media_types.get(media_type)
                logging.log(20, "Found intent in common phrase: " + media_type)
                phrase = phrase.replace(media_type, "")
                break

        return phrase, intent

    def parse_common_phrase(self, phrase: str):
        """
        Attempts to match jellyfin items with phrase
        :param phrase:
        :return:
        """

        logging.log(20, "phrase: " + phrase)

        phrase, intent = self.smart_parse_common_phrase(phrase)

        include_media_types = []
        if intent is not None:
            include_media_types.append(intent.value)

        results = self.search(phrase, include_media_types)

        if results is None or len(results) is 0:
            return None, None
        else:
            logging.log(20, "Found: " + str(len(results)) + " to parse")
            # the idea here is
            # if an artist is found, return songs from this artist
            # elif an album is found, return songs from this album
            # elif a song is found, return song
            artists = []
            albums = []
            songs = []
            playlists = []
            genre = []
            for result in results:
                if result.type == MediaItemType.ARTIST:
                    artists.append(result)
                elif result.type == MediaItemType.ALBUM:
                    albums.append(result)
                elif result.type == MediaItemType.PLAYLIST:
                    playlists.append(result)
                elif result.type == MediaItemType.GENRE:
                    genre.append(result)
                elif result.type == MediaItemType.SONG:
                    songs.append(result)
                else:
                    logging.log(20, "Item is not an Artist/Album/Song: " + result.type.value)
            if artists:
                artist_songs = self.get_songs_by_artist(artists[0].id)
                return 'artist', artist_songs
            elif albums:
                album_songs = self.get_songs_by_album(albums[0].id)
                return 'album', album_songs
            elif genre:
                genre_songs = self.get_songs_by_genre(genre[0].id)
                return 'genre', genre_songs
            elif songs:
                # if a song(s) matches pick the 1st
                song_songs = self.convert_to_playable_songs(songs)
                return 'song', song_songs
            elif playlists:
                playlist_songs = self.get_songs_by_playlist(playlists[0].id)
                return 'playlist', playlist_songs
            else:
                return None, None

    def set_version(self):
        """
        Attempts to get version based on the git hash
        :return:
        """
        try:
            self.version = subprocess.check_output(["git", "describe", "--always"]).strip().decode()
        except Exception as e:
            self.log.info("Failed to determine version with error: {}".format(str(e)))

    @staticmethod
    def normalize_host(host: str):
        """
        Attempts to add http if http is not present in the host name

        :param host:
        :return:
        """

        if host is not None and 'http' not in host.lower():
            host = "http://" + host

        return host

    def diag_public_server_info(self):
        # test the public server info endpoint
        connection_success = False
        server_info = {}

        response = None
        try:
            response = self.get_server_info_public()
        except Exception as e:
            details = 'Error occurred when attempting to connect to the Jellyfin server. Error: ' + str(e)
            self.log.info(details)
            server_info['Error'] = details
            return connection_success, server_info

        if response.status_code != 200:
            logging.log(20, 'Non 200 status code returned when fetching public server info: ' + str(response.status_code))
        else:
            connection_success = True
        try:
            server_info = json.loads(response.text)
        except Exception as e:
            details = 'Failed to parse server details, error: ' + str(e)
            logging.log(20, details)
            server_info['Error'] = details

        return connection_success, server_info
