# rupert-audio-player

`rupert-audio-player` is a Kafka-driven audio playback service for Rupert.
It consumes JSON control events, manages playback through VLC, and supports single track, playlist, shuffle, repeat, directory-based playlists, and transport controls.

## Service Notes

- Service entrypoint class: `RupertAudioProsumer` in `rupert_audio_player.py`.
- Player engine class: `RupertAudioPlayer` in `rupert_audio_player.py`.
- Event handling:
  - `event_type == "control"`: applies playback changes via `RupertAudioPlayer.set(...)`.
  - `event_type == "status"`: currently reserved (no status publish implementation yet).
- Supported controls in the event payload:
  - `play`: `"play" | "pause" | "stop"`
  - `play_track`: single track path
  - `play_tracks`: list of track paths
  - `play_directory`: directory containing audio files (auto-filtered)
  - `shuffle`: `true | false`
  - `loop`: `"single" | "repeat" | "loop"`
  - `navigate`: `"next" | "previous"`
  - `volume`: integer 0-100 (VLC scale)

## Example JSON Events

### 1) Play a Single Track

```json
{
  "event_type": "control",
  "play_tracks": ["/data/audio/sine-test1.mp3"],
  "play": "play"
}
```

### 2) Play a Playlist with Shuffle

```json
{
  "event_type": "control",
  "play_tracks": [
    "/data/audio/track-a.mp3",
    "/data/audio/track-b.mp3",
    "/data/audio/track-c.mp3"
  ],
  "shuffle": true,
  "play": "play"
}
```

### 3) Add a Directory as Playlist

```json
{
  "event_type": "control",
  "play_directory": "/data/audio",
  "play": "play"
}
```

### 4) Playback Navigation and Repeat

```json
{
  "event_type": "control",
  "navigate": "next",
  "loop": "loop"
}
```

### 5) Pause / Resume / Stop / Volume

```json
{
  "event_type": "control",
  "play": "pause",
  "volume": 25
}
```

## Configuration Example

This service extends `RupertProsumer`, so it expects the same Kafka and logging configuration structure used by `rupert-prosumer`.

```json
{
  "kafka": {
    "connection": {
      "bootstrap.servers": "localhost:9092"
    },
    "consumer": {
      "group.id": "rupert-audio-player-group",
      "auto.offset.reset": "earliest"
    },
    "topics": {
      "audio_control": "rupert.audio.control"
    }
  },
  "logging": {
    "rotation": "10 MB",
    "retention": "7 days",
    "level": "INFO"
  }
}
```

## Python Module Requirements

No lockfile is currently committed in this repository, so the versions below are minimum recommendations for local/dev consistency.

- Python: `~=3.12`
- `python-vlc`: `~=3.0.0`
- `beartype`: `~=0.19.0`
- `loguru`: `~=0.7.0`
- `confluent-kafka`: `~=2.3.0` (required through `rupert-prosumer`)
- `behave`: `~=1.2.0` (for BDD tests)

Example install:

```bash
pip install "python-vlc~=3.0.0" "beartype~=0.19.0" "loguru~=0.7.0" "confluent-kafka~=2.3.0" "behave~=1.2.6"
```

## VLC Software Requirement

`python-vlc` is only a Python binding. You must also install the VLC application/runtime on the host.

- macOS (Homebrew):

```bash
brew install --cask vlc
```

- Ubuntu/Debian:

```bash
sudo apt-get update && sudo apt-get install -y vlc
```

After installation, verify VLC is available to the runtime environment and that audio output is configured on the host/container.

## Running BDD Tests

```bash
PYTHONPATH=../rupert-prosumer python -m behave features/playlist.feature
```
