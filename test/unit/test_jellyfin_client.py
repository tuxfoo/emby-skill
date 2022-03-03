import pytest

from jellyfin_client import JellyfinClient, PublicJellyfinClient, MediaItemType, JellyfinMediaItem
from jellyfin_croft import JellyfinCroft

HOST = "http://jellyfin:8096"
USERNAME = "ricky"
PASSWORD = ""


class TestJellyfinClient(object):

    @pytest.mark.client
    @pytest.mark.live
    def test_songs_by_artist(self):
        artist = 'slaves'
        client = JellyfinClient(HOST, USERNAME, PASSWORD)
        response = client.search(artist, [MediaItemType.ARTIST.value])
        search_items = JellyfinCroft.parse_search_hints_from_response(response)
        artists = JellyfinMediaItem.from_list(search_items)
        assert len(artists) == 1
        artist_id = artists[0].id
        songs = client.get_songs_by_artist(artist_id)
        assert songs is not None
        for song in songs.json()['Items']:
            assert artist in [a.lower() for a in song['Artists']]

    @pytest.mark.client
    @pytest.mark.live
    def test_songs_by_album(self):
        album = 'deadweight'
        client = JellyfinClient(HOST, USERNAME, PASSWORD)
        response = client.search(album, [MediaItemType.ALBUM.value])
        search_items = JellyfinCroft.parse_search_hints_from_response(response)
        albums = JellyfinMediaItem.from_list(search_items)
        assert len(albums) == 1
        album_id = albums[0].id
        songs = client.get_songs_by_album(album_id)
        assert songs is not None
        for song in songs.json()['Items']:
            assert album == song['Album'].lower()

    @pytest.mark.client
    @pytest.mark.live
    def test_songs_by_playlist(self):
        playlist = 'Xmas Music'
        client = JellyfinClient(HOST, USERNAME, PASSWORD)
        response = client.search(playlist, [MediaItemType.PLAYLIST.value])
        search_items = JellyfinCroft.parse_search_hints_from_response(response)
        playlists = JellyfinMediaItem.from_list(search_items)
        assert len(playlists) == 1
        playlist_id = playlists[0].id
        songs = client.get_songs_by_playlist(playlist_id)
        assert songs is not None

    @pytest.mark.client
    @pytest.mark.live
    def test_server_info_public(self):
        client = PublicJellyfinClient(HOST)
        response = client.get_server_info_public()
        assert response.status_code == 200
        server_info = response.json()
        TestJellyfinClient._assert_server_info(server_info)

    @pytest.mark.client
    @pytest.mark.live
    def test_server_info(self):
        client = JellyfinClient(HOST, USERNAME, PASSWORD)
        response = client.get_server_info()
        assert response.status_code == 200
        server_info = response.json()
        TestJellyfinClient._assert_server_info(server_info)

    def _assert_server_info(server_info):
        assert server_info['LocalAddress'] is not None
        assert server_info['WanAddress'] is not None
        assert server_info['ServerName'] is not None
        assert server_info['Version'] is not None
        assert server_info['Id'] is not None
