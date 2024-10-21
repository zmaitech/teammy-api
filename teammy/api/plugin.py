from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Awaitable

from teammy.api.data import DataPacket, MeetingMetadata
from teammy.api.engine import MeetingEngine


class PluginConfig(ABC):
    """Plugin specific configuration for the metadata used in PluginMetadata."""

    pass


@dataclass(frozen=True)
class InCallPluginMetadata:
    """Metadata for in-meeting plugins.

    This class provides metadata about the plugin, such as name, version, and data sources.
    Each plugin implementation must provide exactly one instance of this class.

    Attributes:
        name: Plugin name
        version: Plugin version
        sources: List of data sources
        config: PluginConfig object
    """

    name: str
    version: str
    sources: list[str]
    config: PluginConfig


class InCallPlugin(ABC):
    """Base class for in-meeting plugins.

    Since this plugin has no internal state and is driven by external state passed in through the
    meeting engine, all methods are class methods. Users of this class should not create
    instances of it. Lifecycle events are handled at the class level.
    """

    @classmethod
    @abstractmethod
    async def get_metadata(cls) -> InCallPluginMetadata:
        """Retrieves the plugin metadata. Metadata is gathered once during installation.

        This method should return the required metadata for the plugin, such as:

        - Plugin name (used for identification)
        - Semantic version string
        - List of data sources the plugin consumes
        - Plugin specific config

        Returns:
            Plugin metadata object
        """
        pass

    @classmethod
    @abstractmethod
    async def on_install(cls):
        """Post-install callback.

        This is called when the plugin is installed into the system (e.g., service container).
        By default, it does nothing but can be overridden.
        """
        pass

    @classmethod
    @abstractmethod
    async def on_startup(cls, config: PluginConfig):
        """Post-startup callback.

        Called when the service container running this plugin is started. Can be triggered multiple times
        if the service or container restarts during a meeting.

        Args:
            config: Plugin configuration object
        """
        pass

    HookFunction = Callable[[DataPacket, MeetingEngine], Awaitable[object]]

    @classmethod
    @abstractmethod
    async def get_data_receive_hooks(cls) -> dict[str, HookFunction]:
        """Define hooks for receiving data types.

        This is called once per meeting to fetch handlers for the declared data types the plugin consumes.
        The handlers should be defined as async functions that accept a DataPacket and the MeetingEngine.

        Returns:
            Dictionary containing data types and respective handler functions.
        """
        pass

    @classmethod
    @abstractmethod
    async def on_meeting_start(
        cls, meeting_info: MeetingMetadata, engine: MeetingEngine
    ):
        """Triggered when the plugin is assigned to a meeting.

        Once assigned, the plugin will start receiving data from the declared sources for this meeting.
        This method must be implemented to handle meeting initialization.

        Args:
            meeting_info: Meeting metadata
            engine: Instance of meeting engine
        """
        pass

    @classmethod
    @abstractmethod
    async def on_meeting_end(cls, meeting_info: MeetingMetadata, engine: MeetingEngine):
        """Post-meeting cleanup callback.

        This is called when the meeting has ended. The default implementation does nothing,
        but plugins can override it to handle cleanup of meeting specific resources.

        Args:
            meeting_info: Meeting metadata
            engine: Instance of meeting engine
        """
        pass

    @classmethod
    @abstractmethod
    async def on_shutdown(cls, engine: MeetingEngine):
        """Clean-up callback when the service container is gracefully stopped.

        This method is called when the container running the plugin is shut down.
        Default implementation does nothing.

        Args:
            engine: Instance of meeting engine
        """
        pass
