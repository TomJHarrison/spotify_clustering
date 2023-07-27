import pandas as pd
import spotipy


def get_playlist_track_features(
    spotipy_client: spotipy.Spotify,
    playlist_uri: str
) -> pd.DataFrame:
    """
    A function which returns the audio features for every track in a Spotify playlist
    
    Arguments:
        spotipy_client (spotipy.Spotify): the spotipy client being used for the session
        playlist_uri (str): the uri for a particular Spotify playlist
        
    Returns:
        pd.DataFrame: a dataframe containing the audio features for every track in the playlist
    """

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
                album_id_list = [track_dict.get('album').get('id') for track_dict in spotipy_client.tracks(track_id_sublist).get('tracks')]
                label_list += [album_dict.get('label') for album_dict in spotipy_client.albums(album_id_list).get('albums')]    
            
            track_audio_features_list += spotipy_client.audio_features([track_id for track_id in track_id_list if isinstance(track_id, str)])

            counter += 1
    else:
        track_id_list = []
        for track_dict in playlist_tracks_dict.get('items'):
            track_id_list += [track_dict.get('track').get('id')]

        # we cannot access the information for every track at once due to request constraints, therefore
        # we will do this in 4 smaller chunks
        num_chunks = 10
        for ii in range(num_chunks = 10):
            track_id_sublist = track_id_list[
                int(ii * len(track_id_list) / num_chunks): 
                int((ii + 1) * len(track_id_list) / num_chunks)
            ]
            
            # store track names to check later 
            # track_name_list += [track_dict.get('name') for track_dict in spotipy_client.tracks(track_id_sublist).get('tracks')]
            album_id_list = [album_dict.get('album').get('id') for album_dict in spotipy_client.tracks(track_id_sublist).get('tracks')]
            label_list += [album_dict.get('label') for album_dict in spotipy_client.albums(album_id_list).get('albums')]    
            
        track_audio_features_list += spotipy_client.audio_features([track_id for track_id in track_id_list if isinstance(track_id, str)])
    
    # the dictionaries for some tracks come through as `None`, so we remove them here to prevent errors when trying to
    # convert to a dataframe
    track_audio_features_list = [track_audio_features for track_audio_features in track_audio_features_list if track_audio_features is not None]
    
    df_output = pd.DataFrame(track_audio_features_list)
    df_output['track_name'] = track_name_list
    df_output['label'] = label_list
    
    return df_output