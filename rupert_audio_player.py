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
			self.logger.info("Received control event")
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
	def status(self) -> dict[str, str | int | bool | list[str] | None]:
		"""
			Description: Gets the current status of the player
			Responsible for:
				1. Returning a dictionary with the current status of the player
		"""
		current_media = None
		current_track_mrl = None
		track_index = -1
		media_list_mrls: list[str] = []

		if self.media_list_player:
			media_player = self.media_list_player.get_media_player()
			if media_player:
				current_media = media_player.get_media()
				if current_media:
					current_track_mrl = current_media.get_mrl()

		if self.media_list and current_media:
			track_index = self.media_list.index_of_item(current_media)

		if self.media_list:
			for index in range(self.media_list.count()):
				media_item = self.media_list.item_at_index(index)
				if media_item:
					media_list_mrls.append(media_item.get_mrl())

		if self.media_list_player:
			state = str(self.media_list_player.get_state())
			try:
				loop_mode = str(self.media_list_player.get_playback_mode())
			except AttributeError:
				loop_mode = "single"
			volume = self.media_list_player.get_media_player().audio_get_volume()
		else:
			state = "stopped"
			loop_mode = "single"
			volume = 0

		status_dict = {
			"state": state,
			"volume": volume,
			"loop": loop_mode,
			"track": current_track_mrl,
			"track_index": track_index,
			"instance_index": track_index,
			"media_list": media_list_mrls,
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
		elif 'volume' in self.control_dict: # If media is being volume will be set as well
			self.__set_volume()

		if 'loop' in self.control_dict:
			self.__set_loop()

		if 'navigate' in self.control_dict:
			self.__navigate()

## Private methods

	@beartype
	def __navigate(self) -> None:
		media_list_count = self.media_list.count()
		media_index = self.media_list.index_of_item(
			self.media_list_player.get_media_player().get_media()
		)
		self.logger.debug(f"Media list count: {media_list_count} media index: {media_index}")
		if self.control_dict['navigate'] == 'next':
			if media_index + 1 < media_list_count: # If not on the last track go to the next one
				self.logger.info("Next track")
				self.media_list_player.next()
			else: # Else reset to the initial track
				self.logger.info("Initial Track")
				self.media_list_player.play_item_at_index(0)
		elif self.control_dict['navigate'] == 'previous':
			media_index = self.media_list.index_of_item(
				self.media_list_player.get_media_player().get_media()
			)
			if media_index - 1 >= 0: # If not on the first track go to the previous one
				self.logger.info("Previous track")
				self.media_list_player.previous()
			else: # Else reset to the initial track
				self.logger.info("Initial Track")
				self.media_list_player.play_item_at_index(0)

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

		if 'volume' in self.control_dict: # Set volume if it was part the request
			self.__set_volume()

		if isinstance(self.control_dict['play_tracks'], list):
			if self.control_dict.setdefault('shuffle', False):
				random.shuffle(self.control_dict['play_tracks'])

			for media in self.control_dict['play_tracks']:
				self.logger.info(f"Adding media: {media}")
				self.media = self.player.media_new(media)
				self.media_list.add_media(self.media)
		else:
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
