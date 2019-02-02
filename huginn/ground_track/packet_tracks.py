"""
Ground track class for packet operations.

__authors__ = ['Quinn Kupec', 'Zachary Burnett']
"""

from huginn.ground_track import data_structures
from huginn.telemetry import packets


class LocationPacketTrack:
    def __init__(self, packets=None):
        """
        Location packet track.

        :param packets: iterable of packets
        """

        self.packets = data_structures.DoublyLinkedList(packets)

    def append(self, packet: packets.LocationPacket):
        self.packets.append(packet)

    def altitude(self) -> float:
        """
        Return altitude of most recent packet.

        :return: altitude in meters
        """

        return self.packets[-1].altitude

    def coordinates(self, z: bool = False) -> tuple:
        """
        Return coordinates of most recent packet.

        :param z: whether to include altitude as third entry in tuple
        :return: tuple of coordinates (lon, lat[, alt])
        """

        return self.packets[-1].coordinates(z)

    def ascent_rate(self) -> float:
        """
        Calculate ascent rate.

        :return: ascent rate in meters per second
        """

        if len(self.packets) > 1:
            # TODO implement filtering
            return (self.packets[-1] - self.packets[-2]).ascent_rate
        else:
            return 0.0

    def ground_speed(self) -> float:
        """
        Calculate ground speed.

        :return: ground speed in meters per second
        """

        if len(self.packets) > 1:
            # TODO implement filtering
            return (self.packets[-1] - self.packets[-2]).ground_speed
        else:
            return 0.0

    def seconds_to_impact(self) -> float:
        """
        Calculate seconds to reach the ground.

        :return: seconds to impact
        """

        current_ascent_rate = self.ascent_rate()

        if current_ascent_rate < 0:
            # TODO implement landing location as the intersection of the predicted descent track with a local DEM
            # TODO implement a time to impact calc based off of standard atmo
            return self.packets[-1].altitude / current_ascent_rate
        else:
            return -1

    def downrange_distance(self, longitude, latitude) -> float:
        """
        Calculate overground distance from the most recent packet to a given point.

        :return: distance to point in meters
        """

        if len(self.packets) > 0:
            return self.packets[-1].distance_to_point(longitude, latitude)
        else:
            return 0.0

    def __getitem__(self, index: int):
        """
        Indexing function (for integer indexing of packets).

        :param index: index
        :return: packet at index
        """

        return self.packets[index]

    def __iter__(self):
        return iter(self.packets)

    def __reversed__(self):
        return reversed(self.packets)

    def __len__(self) -> int:
        return len(self.packets)

    def __eq__(self, other):
        return self.packets == other.packets

    def __str__(self):
        return str(list(self))


class APRSTrack(LocationPacketTrack):
    def __init__(self, callsign: str, packets=None):
        """
        APRS packet track.

        :param callsign: callsign of APRS packets
        :param packets: iterable of packets
        """

        self.callsign = callsign
        super().__init__(packets)

    def append(self, packet: packets.APRSPacket):
        packet_callsign = packet['callsign']

        if packet_callsign == self.callsign:
            # TODO check if packet is a duplicate
            super().append(packet)
        else:
            print(f'Packet callsign {packet_callsign} does not match ground track callsign {self.callsign}.')

    def __eq__(self, other):
        return self.callsign == other.callsign and super().__eq__(other)

    def __str__(self):
        return f'{self.callsign}: {super().__str__()}'