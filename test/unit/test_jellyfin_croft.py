import pytest, json
from collections import defaultdict
from unittest import TestCase, mock
from jellyfin_croft import JellyfinCroft, IntentType
from jellyfin_client import MediaItemType, JellyfinMediaItem

HOST = "http://jellyfin:8096"
USERNAME = "ricky"
PASSWORD = ""

"""
This test file is expected to have tests using mock's and using a real jellyfin server
The expectation is that there will be 2 tests that are exactly the same.
1 that will utilize mocks for the calls to the jellyfin server and another that
will actually call the Jellyfin server and handle real responses. There is probably
a better way to do this but I'm lazy :)

"""


class TestJellyfinCroft(object):

    # load mocked responses
    mocked_responses = None
    with open("test/unit/test_responses.json") as f:
        mocked_responses = json.load(f)
    common_phrases = None
    with open("test/unit/common_phrases.json") as f:
        common_phrases = json.load(f)

    @pytest.mark.mocked
    def test_auth_mock(self):
        with mock.patch('requests.post') as MockRequestsPost:
            auth_server_response = TestJellyfinCroft.mocked_responses["jellyfin"]["3.5.2.0"]["auth_server_response"]
            response = MockResponse(200, auth_server_response)
            MockRequestsPost.return_value = response
            jellyfin_croft = JellyfinCroft(HOST, USERNAME, PASSWORD)

            assert jellyfin_croft.client.auth.token is auth_server_response["AccessToken"]
            assert jellyfin_croft.client.auth.user_id is auth_server_response["User"]["Id"]

    @pytest.mark.mocked
    def test_instant_mix_mock(self):
        with mock.patch('requests.post') as MockRequestsPost:
            auth_server_response = TestJellyfinCroft.mocked_responses["jellyfin"]["3.5.2.0"]["auth_server_response"]
            search_response = TestJellyfinCroft.mocked_responses["jellyfin"]["3.5.2.0"]["search_response"]
            get_songs_response = TestJellyfinCroft.mocked_responses["jellyfin"]["3.5.2.0"]["get_songs_response"]

            album = "This is how the wind shifts"
            response = MockResponse(200, auth_server_response)
            MockRequestsPost.return_value = response
            jellyfin_croft = JellyfinCroft(HOST, USERNAME, PASSWORD)

            with mock.patch('requests.get') as MockRequestsGet:
                responses = [MockResponse(200, search_response), MockResponse(200, get_songs_response)]
                MockRequestsGet.side_effect = responses

                songs = jellyfin_croft.handle_intent(album, IntentType.MEDIA)
                assert songs is not None
                assert len(songs) is 1

    @pytest.mark.mocked
    def test_parsing_common_phrase_mock(self):
        with mock.patch('requests.post') as MockRequestsPost:
            auth_server_response = TestJellyfinCroft.mocked_responses["jellyfin"]["3.5.2.0"]["auth_server_response"]
            response = MockResponse(200, auth_server_response)
            MockRequestsPost.return_value = response
            jellyfin_croft = JellyfinCroft(HOST, USERNAME, PASSWORD)

            for phrase in TestJellyfinCroft.common_phrases:
                match_type = TestJellyfinCroft.common_phrases[phrase]["match_type"]

                search_response = TestJellyfinCroft.mocked_responses["jellyfin"]["3.5.2.0"]["common_play"][match_type][
                    "search_response"]
                get_songs_response = TestJellyfinCroft.mocked_responses["jellyfin"]["3.5.2.0"]["common_play"][match_type][
                    "songs_response"]
                with mock.patch('requests.get') as MockRequestsGet:
                    responses = [MockResponse(200, search_response), MockResponse(200, get_songs_response)]
                    MockRequestsGet.side_effect = responses

                    match_type, songs = jellyfin_croft.parse_common_phrase(phrase)

                    assert match_type == TestJellyfinCroft.common_phrases[phrase]["match_type"]
                    assert songs

    @pytest.mark.mocked
    def test_determine_intent(self):
        #@ToDo use pytest.parameterize
        dict_test_args = {
            IntentType.ARTIST: 'artistHere',
            IntentType.MEDIA: 'media_here'
        }

        for intent_type, intent in dict_test_args.items():
            message = defaultdict(dict)
            message['data'] = {intent_type.value: intent}

            intent, intent_type = JellyfinCroft.determine_intent(message['data'])
            assert intent_type == intent_type
            assert intent == intent

    @pytest.mark.mocked
    def test_find_songs_by_artist_mock(self):
        with mock.patch('requests.post') as MockRequestsPost:
            auth_server_response = TestJellyfinCroft.mocked_responses["jellyfin"]["3.5.2.0"]["auth_server_response"]
            response = MockResponse(200, auth_server_response)
            MockRequestsPost.return_value = response
            jellyfin_croft = JellyfinCroft(HOST, USERNAME, PASSWORD)

            search_response = TestJellyfinCroft.mocked_responses["jellyfin"]["3.5.2.0"]["artist_search"][
                "search_response"]
            get_songs_response = TestJellyfinCroft.mocked_responses["jellyfin"]["3.5.2.0"]["artist_search"][
                "songs_response"]
            with mock.patch('requests.get') as MockRequestsGet:
                responses = [MockResponse(200, search_response), MockResponse(200, get_songs_response)]
                MockRequestsGet.side_effect = responses

                songs = jellyfin_croft.handle_intent("dance gavin dance", IntentType.ARTIST)

                assert songs
                assert len(songs) == 4

    @pytest.mark.mocked
    def test_find_songs_by_album_mock(self):
        with mock.patch('requests.post') as MockRequestsPost:
            auth_server_response = TestJellyfinCroft.mocked_responses["jellyfin"]["3.5.2.0"]["auth_server_response"]
            response = MockResponse(200, auth_server_response)
            MockRequestsPost.return_value = response
            jellyfin_croft = JellyfinCroft(HOST, USERNAME, PASSWORD)

            search_response = TestJellyfinCroft.mocked_responses["jellyfin"]["3.5.2.0"]["album_search"][
                "search_response"]
            get_songs_response = TestJellyfinCroft.mocked_responses["jellyfin"]["3.5.2.0"]["album_search"][
                "songs_response"]
            with mock.patch('requests.get') as MockRequestsGet:
                responses = [MockResponse(200, search_response), MockResponse(200, get_songs_response)]
                MockRequestsGet.side_effect = responses

                songs = jellyfin_croft.handle_intent("deadweight", IntentType.ARTIST)

                assert songs
                assert len(songs) == 1

    @pytest.mark.mocked
    def test_handle_intent_by_playlist(self):
        with mock.patch('requests.post') as MockRequestsPost:
            auth_server_response = TestJellyfinCroft.mocked_responses["jellyfin"]["3.5.2.0"]["auth_server_response"]
            response = MockResponse(200, auth_server_response)
            MockRequestsPost.return_value = response
            jellyfin_croft = JellyfinCroft(HOST, USERNAME, PASSWORD)

            search_response = TestJellyfinCroft.mocked_responses["jellyfin"]["4.2.1.0"]["playlist_search"][
                "search_response"]
            get_songs_response = TestJellyfinCroft.mocked_responses["jellyfin"]["4.2.1.0"]["playlist_search"][
                "songs_response"]
            with mock.patch('requests.get') as MockRequestsGet:
                responses = [MockResponse(200, search_response), MockResponse(200, get_songs_response)]
                MockRequestsGet.side_effect = responses

                songs = jellyfin_croft.handle_intent("xmas music", IntentType.PLAYLIST)

                assert songs
                assert len(songs) == 1

    @pytest.mark.mocked
    def test_diag_public_server_info_happy_path_mock(self):

        jellyfin_croft = JellyfinCroft(HOST, USERNAME, PASSWORD, diagnostic=True)

        with mock.patch('requests.get') as MockRequestsGet:
            public_info_response = TestJellyfinCroft.mocked_responses["jellyfin"]["4.1.1.0"]["public_info"]
            response = MockResponse(200, public_info_response)
            MockRequestsGet.return_value = response
            connection_success, info = jellyfin_croft.diag_public_server_info()

            assert connection_success
            assert info is not None

    @pytest.mark.mocked
    def test_diag_public_server_info_bad_host_mock(self):

        jellyfin_croft = JellyfinCroft('badhostHere', USERNAME, PASSWORD, diagnostic=True)

        with mock.patch('requests.get') as MockRequestsGet:
            MockRequestsGet.side_effect = Exception('Fail')
            connection_success, info = jellyfin_croft.diag_public_server_info()

            assert not connection_success
            assert info is not None

    @pytest.mark.live
    @pytest.mark.mocked
    def test_host_normalize(self):

        hostname = "noProtocol"
        normaized_host = JellyfinCroft.normalize_host(hostname)
        assert "http://" + hostname == normaized_host

        # assert that if http exists then no change
        hostname = "hTtps://hasProtocol"
        assert hostname == JellyfinCroft.normalize_host(hostname)

    @pytest.mark.live
    def test_auth(self):
        jellyfin_client = JellyfinCroft(HOST, USERNAME, PASSWORD)
        assert jellyfin_client.client.auth is not None

    @pytest.mark.live
    def test_instant_mix_live(self):
        album = "This is how the wind shifts"
        jellyfin_croft = JellyfinCroft(HOST, USERNAME, PASSWORD)

        songs = jellyfin_croft.instant_mix_for_media(album)
        assert songs is not None

    @pytest.mark.live
    def test_handle_intent_by_artist(self):
        artist = "dance gavin dance"

        jellyfin_croft = JellyfinCroft(HOST, USERNAME, PASSWORD)
        songs = jellyfin_croft.handle_intent(artist, IntentType.ARTIST)
        assert songs is not None

    @pytest.mark.live
    def test_handle_intent_by_album(self):
        album = "deadweight"

        jellyfin_croft = JellyfinCroft(HOST, USERNAME, PASSWORD)
        songs = jellyfin_croft.handle_intent(album, IntentType.ALBUM)
        assert songs is not None

    @pytest.mark.live
    def test_handle_intent_by_playlist(self):
        playlist = "xmas music"

        jellyfin_croft = JellyfinCroft(HOST, USERNAME, PASSWORD)
        songs = jellyfin_croft.handle_intent(playlist, IntentType.PLAYLIST)
        assert songs is not None

    @pytest.mark.live
    def test_search_for_song(self):
        song = "And I Told Them I Invented Times New Roman"

        jellyfin_croft = JellyfinCroft(HOST, USERNAME, PASSWORD)
        songs = jellyfin_croft.search_song(song)
        assert len(songs) == 3
        for song_item in songs:
            assert song in song_item.name
            assert song_item.id is not None
            assert song_item.type == MediaItemType.SONG

    @pytest.mark.live
    def test_parsing_common_phrase(self):

        jellyfin_croft = JellyfinCroft(HOST, USERNAME, PASSWORD)

        for phrase in TestJellyfinCroft.common_phrases:
            match_type, songs = jellyfin_croft.parse_common_phrase(phrase)

            assert match_type == TestJellyfinCroft.common_phrases[phrase]['match_type']
            assert songs

    @pytest.mark.live
    def test_diag_public_server_info_happy_path(self):

        jellyfin_croft = JellyfinCroft(HOST, USERNAME, PASSWORD, diagnostic=True)
        connection_success, info = jellyfin_croft.diag_public_server_info()

        assert connection_success
        assert info is not None

    @pytest.mark.live
    def test_diag_public_server_info_bad_host(self):

        jellyfin_croft = JellyfinCroft('badhostHere', USERNAME, PASSWORD, diagnostic=True)
        connection_success, info = jellyfin_croft.diag_public_server_info()

        assert not connection_success
        assert info is not None


class MockResponse:
    def __init__(self, status_code, json_data):
        self.json_data = json_data
        self.text = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data