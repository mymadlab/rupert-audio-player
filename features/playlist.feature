Feature: Playlists
	As a user of the Rupert Audio Player
	I want to be able to play a playlist of tracks
	So that I can enjoy my music without having to manually select each track

	Scenario: Play a playlist
		Given a playlist of tracks
		When I play the playlist
		Then the tracks in the playlist should start playing in order
	
	Scenario: Shuffle a playlist
		Given a playlist of tracks
		When I enable shuffle mode for the playlist
		Then the tracks in the playlist should play in a random order
	
	Scenario: Repeat a playlist
		Given a playlist of tracks
		When I enable repeat mode for the playlist
		Then the tracks in the playlist should play continuously until repeat mode is disabled

	Scenario: Move to next track in playlist
		Given a playlist of tracks is playing
		When I skip to the next track
		Then the next track in the playlist should start playing
	
	Scenario: Move to previous track in playlist
		Given a playlist of tracks is playing
		When I skip to the previous track
		Then the previous track in the playlist should start playing

	Scenario: Directory as a playlist
		Given a directory containing audio files
		When I add the directory to the playlist
		Then all audio files in the directory should be added to the playlist and start playing in order
