[![Build Status](https://travis-ci.com/tuxfoo/jellyfin-skill.svg?branch=master)](https://github.com/tuxfoo/jellyfin-skill)
# Jellyfin
This skill is a fork of the emby skill and allows audio playback from a Jellyfin server

## About
Stream music from your Jellyfin server using Mycroft! Play all songs by an artist or an instant mix of any artist/album/song in your Jellyfin library.

## Common Play Framework
This skill supports the common play framework! This means you don't have to specify "Jellyfin" in your intent. For Example
* "Play The Beatles"
* "Play artist The Beatles"

## Set up
As this is a very new fork of the emby skill made to work with Jellyfin, you might not be able to have both installed at the same time.
Replace the random api key with your own in emby_client.py
You can generate and revoke API keys in your jellyfin dashboard
The API key requirement might be removed in a future version

## Credits
rickyphewitt
tuxfoo

## Category
**Music**

## Tags
#Emby,#Music

## Contributing
Always looking for bug fixes, features, translation, and feedback that make the Jellyfin for Mycroft experience better!

## Troubleshooting
### Setup Connection Info
* Ensure your host, port, username, and password are set at https://account.mycroft.ai/skills
### Check Server Connection
* "Check Jellyfin/Emby"
    * This will attempt to connect then authenticate to your Jellyfin server using the connection info provided above
