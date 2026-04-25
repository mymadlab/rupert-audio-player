# pylint: disable=missing-module-docstring,missing-function-docstring

from pathlib import Path
import time

from behave import given, then, when
from rupert_audio_player import RupertAudioPlayer


TRACKS_DIR = Path(__file__).resolve().parent / "tracks"


def _track_paths() -> list[str]:
	paths = sorted(path.resolve() for path in TRACKS_DIR.glob("*.mp3"))
	assert paths, "No .mp3 files found under features/steps/tracks"
	return [str(path) for path in paths]


def _setup_player(context):
	context.audio_player = RupertAudioPlayer(options="--no-video")
	context.playlist_paths = _track_paths()


def _cleanup(context):
	if hasattr(context, "audio_player") and context.audio_player.media_list_player:
		context.audio_player.set({"play": "stop"})


def _play_playlist(context, shuffle=False):
	context.audio_player.set(
		{
			"play_tracks": list(context.playlist_paths),
			"shuffle": shuffle,
			"play": "play",
		}
	)


def _wait_for_track_index(context, expected_index, timeout_seconds=4.0):
	deadline = time.monotonic() + timeout_seconds
	while time.monotonic() < deadline:
		status = context.audio_player.status()
		if status["track_index"] == expected_index and "playing" in str(status["state"]).lower():
			return status
		time.sleep(0.1)
	return context.audio_player.status()


def _track_names_from_mrls(mrls: list[str]) -> list[str]:
	return [Path(mrl.replace("file://", "")).name for mrl in mrls]


@given("a playlist of tracks")
def step_given_playlist_of_tracks(context):
	_setup_player(context)


@when("I play the playlist")
def step_when_i_play_the_playlist(context):
	_play_playlist(context, shuffle=False)


@then("the tracks in the playlist should start playing in order")
def step_then_playlist_should_play_in_order(context):
	status = _wait_for_track_index(context, 0)
	assert status["track"] is not None
	assert status["track_index"] == 0
	assert _track_names_from_mrls(status["media_list"]) == [Path(p).name for p in context.playlist_paths]
	_cleanup(context)


@when("I enable shuffle mode for the playlist")
def step_when_i_enable_shuffle_mode(context):
	context.shuffle_orders = []
	for _ in range(4):
		_play_playlist(context, shuffle=True)
		status = _wait_for_track_index(context, 0)
		context.shuffle_orders.append(_track_names_from_mrls(status["media_list"]))


@then("the tracks in the playlist should play in a random order")
def step_then_playlist_should_play_random_order(context):
	original = [Path(p).name for p in sorted(context.playlist_paths)]
	assert context.shuffle_orders
	assert all(set(order) == set(original) for order in context.shuffle_orders)
	assert any(order != original for order in context.shuffle_orders)
	_cleanup(context)


@when("I enable repeat mode for the playlist")
def step_when_i_enable_repeat_mode(context):
	_play_playlist(context, shuffle=False)
	context.audio_player.set({"loop": "loop"})


@then("the tracks in the playlist should play continuously until repeat mode is disabled")
def step_then_playlist_should_play_continuously(context):
	status = _wait_for_track_index(context, 0)
	assert status["track"] is not None
	assert status["track_index"] >= 0
	assert len(status["media_list"]) == len(context.playlist_paths)
	_cleanup(context)


@given("a playlist of tracks is playing")
def step_given_playlist_is_playing(context):
	_setup_player(context)
	_play_playlist(context, shuffle=False)
	_ = _wait_for_track_index(context, 0)


@when("I skip to the next track")
def step_when_i_skip_to_next_track(context):
	before = context.audio_player.status()["track_index"]
	context.expected_track_index = before + 1
	context.audio_player.set({"navigate": "next"})


@then("the next track in the playlist should start playing")
def step_then_next_track_should_play(context):
	status = _wait_for_track_index(context, context.expected_track_index)
	assert status["track_index"] == context.expected_track_index
	_cleanup(context)


@when("I skip to the previous track")
def step_when_i_skip_to_previous_track(context):
	context.audio_player.set({"navigate": "next"})
	_ = _wait_for_track_index(context, 1)
	context.expected_track_index = 0
	context.audio_player.set({"navigate": "previous"})


@then("the previous track in the playlist should start playing")
def step_then_previous_track_should_play(context):
	status = _wait_for_track_index(context, context.expected_track_index)
	assert status["track_index"] == context.expected_track_index
	_cleanup(context)


@given("a directory containing audio files")
def step_given_directory_containing_audio_files(context):
	_setup_player(context)
	context.play_directory = str(TRACKS_DIR.resolve())


@when("I add the directory to the playlist")
def step_when_i_add_directory_to_playlist(context):
	context.audio_player.set(
		{
			"play_directory": context.play_directory,
			"play": "play",
		}
	)


@then("all audio files in the directory should be added to the playlist and start playing in order")
def step_then_directory_audio_files_added_and_playing(context):
	status = _wait_for_track_index(context, 0)
	assert status["track"] is not None
	assert status["track_index"] == 0
	assert _track_names_from_mrls(status["media_list"]) == [Path(p).name for p in context.playlist_paths]
	_cleanup(context)

