import logging
import os
import re
from abc import ABC, abstractmethod
from typing import List, NamedTuple, Optional

import requests
from bs4 import BeautifulSoup
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

from tools.consts import SPOTIFY_CREDS
from tools.utils import read_json_file

APP_NAME = os.path.basename(__file__).replace(".py", "")
logger = logging.getLogger(APP_NAME)


class SpotifyCred(NamedTuple):
    client_id: str
    client_secret: str
    redirect_uri: str


class Song(NamedTuple):
    """ Holds parsed song information, used to search for tracks
    """

    name: str
    artist: str
    album: str


class Track(NamedTuple):
    """ Holds track searched returned from spotify
    """

    id: str
    name: str
    artists: List[str]
    album: str


class SpotfiyPlaylistMaker(ABC):
    """
    Scrapes website for tracks and make a playlist with them, although not very extensible...

    Details on Spotify web API: https://developer.spotify.com/documentation/web-api/reference-beta/#category-library
    """

    PUB_PLAYLIST_MOD_SCOPE = "playlist-modify-public"
    LIB_READ_SCOPE = "user-library-read"

    CREDS = SPOTIFY_CREDS

    def __init__(self, spotify_creds: SpotifyCred):
        self.sp: Spotify = Spotify(auth_manager=SpotifyOAuth(**spotify_creds._asdict()))
        self._user_id = None

    @classmethod
    def from_json(cls, json_loc=CREDS):
        return cls(SpotifyCred(**read_json_file(json_loc)))

    def _update_scope(self, scope: str):
        self.sp.auth_manager.scope = scope

    @property
    def user_id(self):
        if not self._user_id:
            self._update_scope(self.PUB_PLAYLIST_MOD_SCOPE)
            me = self.sp.current_user()
            user_id = me["id"]
            self._user_id = user_id
        return self._user_id

    def read_user_tracks(self, limit: int = 20, offset: int = 0):
        """ test method from spotipy: https://spotipy.readthedocs.io/en/2.16.1/#getting-started
        """
        self._update_scope(self.LIB_READ_SCOPE)
        results = self.sp.current_user_saved_tracks(limit, offset)
        for idx, item in enumerate(results["items"]):
            track = item["track"]
            logger.info(
                f"{idx} - {track['artists'][0]['name']} - {track['popularity']}"
            )

    def search_track(
        self, name: str, artist: Optional[str] = None, album: Optional[str] = None
    ) -> Track:
        query_string = f'"{name}" '
        query_string += f"artist:{artist} " if artist else ""
        query_string += f"album:{album} " if album else ""
        results = self.sp.search(q=query_string, type="track")
        tracks = results["tracks"]["items"]
        if not tracks:
            logger.error(f"no tracks found for {name}")
            return
        track = tracks[0]
        strack = Track(
            track["id"],
            track["name"],
            [a["name"] for a in track["artists"]],
            track["album"]["name"],
        )
        logger.info(f"spotify track found: {strack}")
        return strack

    @abstractmethod
    def get_songs_list(self) -> List[Song]:
        raise NotImplementedError

    def make_playlist(self, playlist_name: str, description: str = ""):
        self._update_scope(self.PUB_PLAYLIST_MOD_SCOPE)
        results = self.sp.user_playlist_create(
            self.user_id, playlist_name, description=description
        )
        playlist_id = results["id"]
        logger.info(f"playlist {playlist_name} created with ID: '{playlist_id}'")
        return playlist_id

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]):
        self.sp.user_playlist_add_tracks(self.user_id, playlist_id, track_ids)
        logger.info(
            f"successfully added {len(track_ids)} tracks to playlist '{playlist_id}'"
        )

    def run(self, playlist_name: str, description: str = ""):
        playlist_id = self.make_playlist(playlist_name, description)
        songs = self.get_songs_list()
        track_ids = []
        for song in songs:
            track = self.search_track(**song._asdict())
            if track:
                track_ids.append(track.id)
        self.add_tracks_to_playlist(playlist_id, track_ids)


class JazzPlaylistMaker(SpotfiyPlaylistMaker):
    JAZZ_SITE = "https://www.jazz24.org/the-jazz-100/"

    def get_songs_list(self):
        response = requests.get(self.JAZZ_SITE)
        soup = BeautifulSoup(response.text, "html.parser")
        songs = []
        logger.info("scraping jazz website for 100 jazz songs..")
        for idx, row in enumerate(soup.find_all("tr")):
            row_text = [i.text for i in row.find_all("td")]
            logger.debug(f"raw data: {idx} {row_text}")
            if idx == 0:
                continue
            _, song, artist = row_text
            # clean parsed info
            song = re.sub(r"[\(\)\n\&]", " ", song).strip()
            artist = re.sub(r"[\(\)\n\&]", " ", artist).strip()
            songs.append(Song(song, artist, None))
            logger.debug(f"Song parsed: {songs[-1]}")
        return songs


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format=f"{APP_NAME}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    jpm = JazzPlaylistMaker.from_json()
    jpm.run("Top 100 Jazz")
