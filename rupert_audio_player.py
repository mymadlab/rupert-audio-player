"""
Description: Controls rupert audio
"""
import json
import random
import time
from loguru import logger
from beartype import beartype
import vlc
from rupert_prosumer import RupertProsumer

class RupertAudioProsumer(RupertProsumer):
	"""
		Description: Audio Synapse class.
		Responsible for:
			1. Basic constructor for connecting/starting
			2. Initiates Kafka cosumer
	"""
	@beartype
	def __init__(self, config_file: str) -> None:
		super().__init__(config_file=config_file)
		self.rap = RupertAudioPlayer(options="", log=logger)

	@beartype
	def process_event(self, consumer_message: object) -> None:
		"""
			Description: Initiates events for the requested audio control
			Responsible for:
				1. Converts the messages value to dictionary
				2. Runs the audio control event as a daemon thread
			Requires:
				consumer_message
		"""
		control_dict = json.loads(consumer_message.value().decode("utf-8"))
		if control_dict['event_type'] == 'control':
			self.logger.info(f"Received control event")
			self.logger.debug(f"Event: {control_dict}")
			self.rap.set(control_dict)
		elif control_dict['event_type'] == 'status':
			pass
		else :
			pass

class RupertAudioPlayer():
	"""
		Description: Handles playing audio
		Responsible for:
			1. Initiating the VLC Player
			2. Controlling playback
	"""
	@beartype
	def __init__(self, options: str='', log: object = logger) -> None:
		self.player = vlc.Instance(options)
		self.logger = log
		self.media_list = None
		self.media_list_player = None
		self.media = None
		self.control_dict = None
		self.eos = None

	@beartype
	def status(self) -> dict[str, str | int | bool]:
		"""
			Description: Gets the current status of the player
			Responsible for:
				1. Returning a dictionary with the current status of the player
		"""
		status_dict = {
			"state": self.media_list_player.get_state().name if self.media_list_player else "stopped",
			"volume": (
				self.media_list_player.get_media_player().audio_get_volume()
				if self.media_list_player
				else 0
			),
			"loop": self.media_list_player.get_playback_mode().name if self.media_list_player else "single",
			"track": self.media.get_mrl() if self.media else None
		}
		logger.debug(f"Current player status: {status_dict}")
		return status_dict

	@beartype
	def bye(self) -> None:
		"""Cleans up the the current player"""
		try:
			self.stop()
			self.media_list_player.get_media_player().release()
			del self.media
			del self.media_list_player
			self.player.release()
			del self.player
		except AttributeError:
			# do nothing we know this may blow up if something has not already started to play
			print("Stopping crash bypassed")

	def set(self, control_dict: dict[str, set[str, int]]) -> None:
		"""
		Control the audio player. Requires:
			control_dict = Dictionary detailing what controls to execute
		"""
		self.control_dict = control_dict
		if 'play_tracks' in self.control_dict:
			self.__set_media()

		if 'play' in self.control_dict:
			self.__play_stop_pause()
			time.sleep(1) # Required in the event we are also updating loop
		elif 'volume' in self.control_dict:
			self.__set_volume()

		if 'loop' in self.control_dict:
			self.__set_loop()

## Private methods

	@beartype
	def __play_stop_pause(self) -> None:
		"""
			Starts or stops the player
		"""
		logger.info(f"Setting play status to {self.control_dict['play']}")
		if self.control_dict['play'] == 'stop':
			try:
				self.media_list_player.get_media_player().stop()
			except vlc.VLCException as e:
				print("VLCException during stop:", e)
			except AttributeError as e:
				print("AttributeError during stop:", e)
		elif self.control_dict['play'] == 'play':
			self.media_list_player.play()
		elif self.control_dict['play'] == 'pause':
			try:
				self.media_list_player.pause()
			except vlc.VLCException as e:
				print("VLCException during pause:", e)
			except AttributeError as e:
				print("AttributeError during pause:", e)
		else:
			raise ValueError(f"Unknown play status: {self.control_dict['play']}")

	@beartype
	def __set_loop(self) -> None:
		"""
			Manipulates looping
		"""
		logger.info(f"Setting loop status to {self.control_dict['loop']}")
		# current
		if self.control_dict['loop'] == 'repeat':
			self.media_list_player.set_playback_mode(vlc.PlaybackMode.repeat)
		# play list
		elif self.control_dict['loop'] == 'loop':
			self.media_list_player.set_playback_mode(vlc.PlaybackMode.loop)
		# end loop
		elif self.control_dict['loop'] == "single":
			self.media_list_player.set_playback_mode(vlc.PlaybackMode.default)
		else:
			raise ValueError(f"Unknown loop type requested: {self.control_dict['loop']}")

	@beartype
	def __set_media(self) -> None:
		"""
			Sets the playing media
		"""
		# creating a new media list
		self.media_list = self.player.media_list_new()
		# creating a media player object
		self.media_list_player = self.player.media_list_player_new()
		if 'volume' in self.control_dict:
			self.__set_volume()
		self.media = self.player.media_new(self.control_dict['play_track'])
		self.logger.info(f"Setting media to {self.control_dict['play_track']}")
		# adding media to media list
		self.media_list.add_media(self.media)

		# setting media list to the mediaplayer
		self.media_list_player.set_media_list(self.media_list)

	@beartype
	def __set_volume(self) -> None:
		"""
			Adjusts the volume
		"""
		logger.info(f"Setting volume to {self.control_dict['volume']}")
		self.media_list_player.get_media_player().audio_set_volume(int(self.control_dict['volume']))
