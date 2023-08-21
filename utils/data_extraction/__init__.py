import numpy as np
import os
import pandas as pd
import spotipy

from itertools import compress

def get_playlist_track_features(
    spotipy_client: spotipy.Spotify,
    playlist_uri: str,
    out_path: str
) -> pd.DataFrame:
    """
    A function which returns the audio features for every track in a Spotify playlist
    
    Arguments:
        spotipy_client (spotipy.Spotify): the spotipy client being used for the session
        playlist_uri (str): the uri for a particular Spotify playlist
        out_path (str): the file location where the output dataframe should be saved
        
    Returns:
        pd.DataFrame: a dataframe containing the audio features for every track in the playlist
    """

    # if dataframe has already been saved at the specified path, we read it in rather than calling the data using spotipy
    # as it is time-consuming
    if os.path.exists(out_path):
        df_output = pd.read_csv(out_path)
        return df_output
    
    
    # get all tracks in a particular playlist
    playlist_tracks_dict = spotipy_client.playlist_tracks(playlist_uri)
    
    # store audio features of each track in a list, so that we end up with a list of dictionaries, which can be used to create a dataframe
    # we can only extract 100 tracks from the `playlist_tracks_dict` dictionary at any one time, therefore we have to get the next 'page' by calling
    # the `next` function until we have looped through every 'page'.
    # using this, we assemble a list of track IDs and we then get the audio features for those 100 tracks (note: we cannot get audio features)
    # for more than 100 tracks at a time
    track_audio_features_list = []
    track_name_list = []
    label_list = []
    if playlist_tracks_dict.get('next'):
        counter = 1
        while playlist_tracks_dict.get('next'):
            if counter > 1:
                playlist_tracks_dict = spotipy_client.next(playlist_tracks_dict)

            track_id_list = []
            for track_dict in playlist_tracks_dict.get('items'):
                if track_dict is not None:
                    track_id_list += [track_dict.get('track').get('id')]

            # we cannot access the information for every track at once due to request constraints, therefore
            # we will do this in `num_chunks` smaller chunks
            num_chunks = 10
            for ii in range(num_chunks):
                track_id_sublist = track_id_list[
                    int(ii * len(track_id_list) / num_chunks): 
                    int((ii + 1) * len(track_id_list) / num_chunks)
                ]
                
                # store track names to check later 
                # track_name_list += [track_dict.get('name') for track_dict in spotipy_client.tracks(track_id_sublist).get('tracks')]
                album_id_list = [track_dict.get('album').get('id') for track_dict in spotipy_client.tracks([track_id for track_id in track_id_sublist if isinstance(track_id, str)]).get('tracks')]
                label_list += [album_dict.get('label') if album_dict is not None else None for album_dict in spotipy_client.albums(album_id_list).get('albums')]    
 
            track_audio_features_list += spotipy_client.audio_features([track_id for track_id in track_id_list if isinstance(track_id, str)])
    
            counter += 1
    else:
        track_id_list = []
        for track_dict in playlist_tracks_dict.get('items'):
            if track_dict is not None:
                track_id_list += [track_dict.get('track').get('id')]

        # we cannot access the information for every track at once due to request constraints, therefore
        # we will do this in 4 smaller chunks
        num_chunks = 10
        for ii in range(num_chunks):
            track_id_sublist = track_id_list[
                int(ii * len(track_id_list) / num_chunks): 
                int((ii + 1) * len(track_id_list) / num_chunks)
            ]
            
            # store track names to check later 
            # track_name_list += [track_dict.get('name') for track_dict in spotipy_client.tracks(track_id_sublist).get('tracks')]
            album_id_list = [album_dict.get('album').get('id') for album_dict in spotipy_client.tracks(track_id_sublist).get('tracks')]
            label_list += [album_dict.get('label') for album_dict in spotipy_client.albums(album_id_list).get('albums') if album_dict is not None]    
            
        track_audio_features_list += spotipy_client.audio_features([track_id for track_id in track_id_list if isinstance(track_id, str)])
    
    # the dictionaries for some tracks come through as `None`, so we remove them here to prevent errors when trying to
    # convert to a dataframe
    mask = np.where(np.array(track_audio_features_list) != None, True, False)
    track_audio_features_list = list(compress(track_audio_features_list, mask))
    label_list = list(compress(label_list, mask))
    
    df_output = pd.DataFrame(track_audio_features_list)
    df_output['label'] = label_list
    
    df_output.to_csv(out_path)
    
    return df_output