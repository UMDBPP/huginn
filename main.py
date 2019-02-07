"""
Balloon telemetry parsing, display, and logging.

__authors__ = ['Quinn Kupec', 'Zachary Burnett']
"""

import datetime
import os
import sys

import logbook

from huginn import tracks, parsing, serial, packets

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        port_name = sys.argv[1]
    else:
        port_name = '/dev/ttyUSB0'

    if len(sys.argv) > 2:
        callsigns = sys.argv[2].split(',')
    else:
        callsigns = ['W3EAX-13']

    if len(sys.argv) > 3:
        log_directory = sys.argv[3]
    else:
        log_directory = '/home/bpp/Desktop/log/'

    if not os.path.exists(log_directory):
        os.mkdir(log_directory)

    log_filename = os.path.join(log_directory, f'{datetime.datetime.now().strftime("%Y%m%dT%H%M%S")}_huginn_log.txt')

    logbook.StreamHandler(sys.stdout).push_application()
    logbook.FileHandler(log_filename).push_application()
    log = logbook.Logger('Huginn')

    ground_tracks = {callsign: tracks.APRSTrack(callsign) for callsign in callsigns}

    while True:
        raw_packets = serial.serial_packet_candidates(port_name)
        for raw_packet in raw_packets:
            callsign_present = False

            for callsign in callsigns:
                if callsign in raw_packet:
                    callsign_present = True

            if callsign_present:
                try:
                    parsed_packet = packets.APRSPacket(raw_packet)
                except parsing.PartialPacketError as error:
                    parsed_packet = None
                    log.debug(f'PartialPacketError: {error} ("{raw_packet}")')

                if parsed_packet is not None:
                    callsign = parsed_packet['callsign']

                    if callsign in ground_tracks:
                        ground_tracks[callsign].append(parsed_packet)

                    ascent_rate = ground_tracks[callsign].ascent_rate()
                    ground_speed = ground_tracks[callsign].ground_speed()

                    message = f'{parsed_packet} ascent_rate={ascent_rate} ground_speed={ground_speed}'

                    if ascent_rate < 0:
                        seconds_to_impact = ground_tracks[callsign].seconds_to_impact()
                        message += f' seconds_to_impact={seconds_to_impact}'

                    log.notice(message)
                    print(message)
