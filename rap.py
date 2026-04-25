#!/usr/bin/env python3
"""
Rupert Audio Player (RAP)
"""
import os
import sys
from rupert_audio_player import RupertAudioProsumer

if __name__ == '__main__': # Required to support multiprocessing in the prosumer
	config_path = os.environ.get('RUPERT_CONFIG_PATH')
	if not config_path:
		print("Error: RUPERT_CONFIG_PATH environment variable not set.")
		sys.exit(1)
	if len(sys.argv) < 2:
		print("Error: Missing listen argument.")
		sys.exit(1)
	topic = sys.argv[1]
	audio_consumer = RupertAudioProsumer(config_path)
	audio_consumer.listen(topic)
