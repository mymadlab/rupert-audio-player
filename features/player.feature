Feature: Basic Audio Player

	Scenario: Play a file
		Given an audio player is set up
		When we play an audio file
		Then the audio should start playing
	
	Scenario: Loop a file
		Given an audio player is set up
		When we enable loop mode for a file
		Then the audio should play that file continuously until loop mode is disabled

	Scenario: Pause and resume playback
		Given an audio player is playing a file
		When we pause the playback
		Then the audio should pause
		When we resume the playback
		Then the audio should continue playing

	Scenario: Stop playback
		Given an audio player is playing a file
		When we stop the playback
		Then the audio should stop and reset to the beginning

	Scenario: Adjust volume
		Given an audio player is set up
		When we adjust the volume to a specific level
		Then the audio player should set the volume to that level

	Scenario: Handle file not found error
		Given an audio player is set up
		When we try to play a non-existent audio file
		Then the audio player should log an error message indicating the file was not found
