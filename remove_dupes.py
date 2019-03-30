#!/usr/bin/env python3

import math
from itertools import groupby
from operator import itemgetter

from gmusicapi import Mobileclient


def group_by_keys(iterable, keys):
    key_func = itemgetter(*keys)

    # For groupby() to do what we want, the iterable needs to be sorted
    # by the same key function that we're grouping by.
    sorted_iterable = sorted(iterable, key=key_func)

    return [list(group) for key, group in groupby(sorted_iterable, key_func)]


api = Mobileclient()
api.oauth_login(Mobileclient.FROM_MAC_ADDRESS)
songs = api.get_all_songs()
songs = [song for song in songs if song["album"] != "" or song["album"] != ""]
albums = group_by_keys(songs, ("artist", "album"))

for album in albums:
    tracks_without_size = [track for track in album if "estimatedSize" not in track]
    if len(tracks_without_size) > 0:
        for track in tracks_without_size:
            print("size not found: {}".format(track))
        album_with_sizes = [track for track in album if not any(track["id"] == x["id"] for x in tracks_without_size)]
    else:
        album_with_sizes = album

    album_with_bitrates = [
        dict(
            item, **{"bitrate": math.floor((int(item["estimatedSize"]) * 0.008) / (int(item["durationMillis"]) / 1000))}
        )
        for item in album_with_sizes
    ]
    dupes = []
    for song in album_with_bitrates:

        matches = [
            track
            for track in album_with_bitrates
            if track["trackNumber"] == song["trackNumber"] and track["title"] == song["title"]
        ]
        if len(matches) > 1:
            min_bitrate_song = min(matches, key=lambda x: x["bitrate"])
            if not any(d["id"] == min_bitrate_song["id"] for d in dupes):
                dupes.append(min_bitrate_song)
    if len(dupes) > 0:
        print("=================\ndeleting:")
        for dupe in dupes:
            print("{} - {} - {}".format(dupe["artist"], dupe["trackNumber"], dupe["title"]))
        api.delete_songs([dupe["id"] for dupe in dupes])
