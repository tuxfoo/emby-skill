import hashlib
from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel
from mycroft import intent_file_handler
from mycroft.util.parse import match_one
from mycroft.skills.audioservice import AudioService
from mycroft.api import DeviceApi
from random import shuffle

from .jellyfin_croft import JellyfinCroft


class Jellyfin(CommonPlaySkill):

    def __init__(self):
        super().__init__()
        self._setup = False
        self.audio_service = None
        self.jellyfin_croft = None
        self.device_id = hashlib.md5(
            ('Jellyfin'+DeviceApi().identity.uuid).encode())\
            .hexdigest()

    def CPS_match_query_phrase(self, phrase):
        """ This method responds whether the skill can play the input phrase.

            The method is invoked by the PlayBackControlSkill.

            Returns: tuple (matched phrase(str),
                            match level(CPSMatchLevel),
                            optional data(dict))
                     or None if no match was found.
        """

        # first thing is connect to jellyfin or bail
        if not self.connect_to_jellyfin():
            return None

        self.log.debug("CPS Phrase:")
        self.log.debug(phrase)
        match_type, songs = self.jellyfin_croft.parse_common_phrase(phrase)

        if match_type and songs:
            match_level = None
            if match_type != None:
                self.log.info('Found match of type: ' + match_type)

                if match_type == 'song' or match_type == 'album':
                    match_level = CPSMatchLevel.TITLE
                elif match_type == 'artist':
                    match_level = CPSMatchLevel.ARTIST
                    #shuffle(songs)
                self.log.info('match level :' + str(match_level))
    
            song_data = dict()
            song_data[phrase] = songs
            
            self.log.info("First 3 item urls returned")
            max_songs_to_log = 3
            songs_logged = 0

            for song in songs:
                self.log.debug(song)
                songs_logged = songs_logged + 1
                if songs_logged >= max_songs_to_log:
                    break
            return phrase, CPSMatchLevel.TITLE, song_data
        else:
            return None

    def CPS_start(self, phrase, data):
        """ Starts playback.

            Called by the playback control skill to start playback if the
            skill is selected (has the best match level)
        """
        # setup audio service
        self.audio_service = AudioService(self.bus)
        self.speak_playing(phrase)
        self.audio_service.play(data[phrase])

    def connect_to_jellyfin(self, diagnostic=False):
        """
        Attempts to connect to the server based on the config
        if diagnostic is False an attempt to auth is also made
        returns true/false on success/failure respectively

        :return:
        """
        auth_success = False
        self.log.debug("Testing connection to: " + self.settings["hostname"])
        try:
            self.jellyfin_croft = JellyfinCroft(
                self.settings["hostname"] + ":" + str(self.settings["port"]),
                self.settings["username"], self.settings["password"],
                self.device_id, diagnostic)
            auth_success = True
        except Exception as e:
            self.log.info("failed to connect to jellyfin, error: {0}".format(str(e)))

        return auth_success

    def initialize(self):
        pass

    @intent_file_handler('jellyfin.intent')
    def handle_jellyfin(self, message):

        self.log.info(message.data)

        # first thing is connect to jellyfin or bail
        if not self.connect_to_jellyfin():
            self.speak_dialog('configuration_fail')
            return

        # determine intent
        intent, intent_type = JellyfinCroft.determine_intent(message.data)

        songs = []
        try:
            songs = self.jellyfin_croft.handle_intent(intent, intent_type)
        except Exception as e:
            self.log.info(e)
            self.speak_dialog('play_fail', {"media": intent})

        if not songs or len(songs) < 1:
            self.log.info('No songs Returned')
            self.speak_dialog('play_fail', {"media": intent})
        else:
            # setup audio service and play
            self.audio_service = AudioService(self.bus)
            self.speak_playing(intent)
            self.audio_service.play(songs, message.data['utterance'])


    def speak_playing(self, media):
        data = dict()
        data['media'] = media
        self.speak_dialog('jellyfin', data)

    @intent_file_handler('playingsong.intent')
    def handle_playing(self, message):
        track = "Unknown"
        artist = "Unknown"
        if self.audio_service.is_playing:
            track = self.audio_service.track_info()['name']
            artist = self.audio_service.track_info()['artists']
            if artist != [None]:
                self.speak_dialog('whatsplaying', {'track' : track, 'artist': artist})
            else:
                self.speak_dialog('notrackinfo')
        else:
            self.speak_dialog('notplaying')


    @intent_file_handler('diagnostic.intent')
    def handle_diagnostic(self, message):

        self.log.info(message.data)
        self.speak_dialog('diag_start')

        # connec to jellyfin for diagnostics
        self.connect_to_jellyfin(diagnostic=True)
        connection_success, info = self.jellyfin_croft.diag_public_server_info()

        if connection_success:
            self.speak_dialog('diag_public_info_success', info)
        else:
            self.speak_dialog('diag_public_info_fail', {'host': self.settings['hostname']})
            self.speak_dialog('general_check_settings_logs')
            self.speak_dialog('diag_stop')
            return

        if not self.connect_to_jellyfin():
            self.speak_dialog('diag_auth_fail')
            self.speak_dialog('diag_stop')
            return
        else:
            self.speak_dialog('diag_auth_success')

        self.speak_dialog('diagnostic')

    def stop(self):
        pass


def create_skill():
    return Jellyfin()
