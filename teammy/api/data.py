import datetime

from pydantic import BaseModel


class MeetingMetadata(BaseModel):
    """Represents meeting metadata, including the meeting's unique identifier and the associated plugin name.

    Attributes:
        meeting_id: Meeting ID
        plugin_name: Plugin name
    """

    meeting_id: str
    plugin_name: str


class ExecutionMetadata(BaseModel):
    """Represents execution metadata, including the meeting's unique identifier and the source plugin name.

    Attributes:
        meeting_id: Meeting ID
        source_name: Source plugin name
    """

    meeting_id: str
    source_name: str


class DataPacket(BaseModel):
    """Represents a data packet containing a timestamp, execution metadata, and the associated data.

    Attributes:
        timestamp: Data packet timestamp
        execution_metadata: ExecutionMetadata object
    """

    timestamp: datetime.datetime | None = None
    execution_metadata: ExecutionMetadata | None = None


class PluginState(BaseModel):
    """Represents a plugin state containing a timestamp and the associated data.

    Attributes:
        timestamp: Plugin state timestamp
    """

    timestamp: datetime.datetime | None = None
