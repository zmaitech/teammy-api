import datetime
from dataclasses import dataclass

# TODO: rename to execution metadata
@dataclass
class MeetingMetadata:
    """Represents meeting metadata, including the meeting's unique identifier and the associated plugin name.

    Attributes:
        meeting_id: Meeting ID
        plugin_name: Plugin name
    """
    meeting_id: str
    plugin_name: str


@dataclass
class DataPacket:
    """Represents a data packet containing a timestamp, meeting metadata, and the associated data.

    Attributes:
        timestamp: Data packet timestamp
        meeting_metadata: Meeting metadata object
        data: Data object
    """
    timestamp: datetime.datetime
    meeting_metadata: MeetingMetadata
    data: object
