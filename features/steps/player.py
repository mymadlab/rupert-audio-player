# pylint: disable=missing-module-docstring,missing-function-docstring

from pathlib import Path

from behave import given, then, when
import vlc

from rupert_audio_player import RupertAudioPlayer


TRACKS_DIR = Path(__file__).resolve().parent / "tracks"


def _track_path(filename):
	return str((TRACKS_DIR / filename).resolve())


def _setup_audio_player(context):
	context.audio_player = RupertAudioPlayer(options="--no-video")


def _cleanup(context):
	if hasattr(context, "audio_player") and context.audio_player.media_list_player:
		context.audio_player.set({"play": "stop"})


def _start_playing_track(context, filename):
	context.current_track_name = filename
	context.current_track_path = _track_path(filename)
	context.audio_player.set(
		{
			"play_tracks": [context.current_track_path],
			"play_track": context.current_track_path,
			"play": "play",
		}
	)


def _media_mrl_contains(context, name):
	return context.audio_player.media and name in context.audio_player.media.get_mrl()


@given("an audio player is set up")
def an_audio_player_is_set_up(context):
	_setup_audio_player(context)


@when("we play an audio file")
def we_play_an_audio_file(context):
	_start_playing_track(context, "sine-test1.mp3")


@then("the audio should start playing")
def the_audio_should_start_playing(context):
	assert context.audio_player.media_list_player is not None
	assert context.audio_player.media_list_player.get_state() == vlc.State.Playing
	assert _media_mrl_contains(context, context.current_track_name)
	_cleanup(context)


@when("we enable loop mode for a file")
def we_enable_loop_mode_for_a_file(context):
	_start_playing_track(context, "whitenoise-test2.mp3")
	context.audio_player.set({"loop": "loop"})


@then("the audio should play that file continuously until loop mode is disabled")
def the_audio_should_play_that_file_continuously_until_loop_mode_is_disabled(context):
	assert context.audio_player.media_list_player is not None
	assert context.audio_player.media_list_player.get_state() == vlc.State.Playing
	assert _media_mrl_contains(context, context.current_track_name)
	_cleanup(context)


@given("an audio player is playing a file")
def an_audio_player_is_playing_a_file(context):
	_setup_audio_player(context)
	_start_playing_track(context, "silence-test3.mp3")


@when("we pause the playback")
def we_pause_the_playback(context):
	context.audio_player.set({"play": "pause"})


@then("the audio should pause")
def the_audio_should_pause(context):
	assert context.audio_player.media_list_player is not None
	assert context.audio_player.media_list_player.get_state() == vlc.State.Paused


@when("we resume the playback")
def we_resume_the_playback(context):
	context.audio_player.set({"play": "play"})


@then("the audio should continue playing")
def the_audio_should_continue_playing(context):
	assert context.audio_player.media_list_player is not None
	assert context.audio_player.media_list_player.get_state() == vlc.State.Playing
	_cleanup(context)


@when("we stop the playback")
def we_stop_the_playback(context):
	context.audio_player.set({"play": "stop"})


@then("the audio should stop and reset to the beginning")
def the_audio_should_stop_and_reset_to_the_beginning(context):
	assert context.audio_player.media_list_player is not None
	assert context.audio_player.media_list_player.get_state() == vlc.State.Stopped
	assert _media_mrl_contains(context, context.current_track_name)
	_cleanup(context)


@when("we adjust the volume to a specific level")
def we_adjust_the_volume_to_a_specific_level(context):
	context.target_volume = 25
	context.current_track_name = "sine-test1.mp3"
	context.current_track_path = _track_path(context.current_track_name)
	context.audio_player.set(
		{
			"play_tracks": [context.current_track_path],
			"play_track": context.current_track_path,
			"volume": context.target_volume,
		}
	)


@then("the audio player should set the volume to that level")
def the_audio_player_should_set_the_volume_to_that_level(context):
	assert context.audio_player.media_list_player is not None
	volume = context.audio_player.media_list_player.get_media_player().audio_get_volume()
	assert volume == context.target_volume
	_cleanup(context)


@when("we try to play a non-existent audio file")
def we_try_to_play_a_non_existent_audio_file(context):
	context.missing_track = "missing-track.mp3"
	context.missing_track_path = _track_path(context.missing_track)
	context.play_error = None
	try:
		context.audio_player.set(
			{
				"play_tracks": [context.missing_track_path],
				"play_track": context.missing_track_path,
				"play": "play",
			}
		)
	except Exception as exc:  # pragma: no cover
		context.play_error = exc


@then("the audio player should log an error message indicating the file was not found")
def the_audio_player_should_log_an_error_message_indicating_the_file_was_not_found(context):
	assert context.audio_player.media_list_player is not None
	assert context.audio_player.media_list_player.get_state() != vlc.State.Playing
	assert _media_mrl_contains(context, context.missing_track)
	_cleanup(context)
