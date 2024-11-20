from __future__ import annotations
from datetime import timedelta
from typing import Awaitable

import openai

from teammy.api.data import DataPacket, MeetingMetadata


class LLMProvider:
    """Main entry point for interacting with the LLM.

    All plugins requiring the access to LLM should use this interface in order to:

    1. make sure it has access to LLM even though communicating outside network is prohibited;
    2. make sure it reuses existing resources.
    3. it talks to the latest (or correct) version of the model.
    """

    client: openai.AsyncOpenAI | None = None

    async def _init_client(self):
        if self.client is None:
            self.client = openai.AsyncOpenAI()

    async def fast_prompt(
        self,
        messages: list[dict],
        temperature: float,
    ):
        """Sends a prompt to the LLM and returns the generated response.

        Args:
            messages: A list of messages to send to the model
            temperature: Sampling temperature to use for the response
        """
        await self._init_client()
        res = await self.client.chat.completions.create(
            messages=messages, temperature=temperature, model="gpt-4o-mini"
        )
        return res.choices[0].message.content

    async def prompt(
        self,
        messages: list[dict],
        temperature: float,
    ):
        """Sends a prompt to the LLM and returns the generated response.

        Args:
            messages: A list of messages to send to the model
            temperature: Sampling temperature to use for the response
        """
        await self._init_client()
        res = await self.client.chat.completions.create(
            messages=messages, temperature=temperature, model="gpt-4o"
        )
        return res.choices[0].message.content


class PersistenceProvider:
    """Main entry point for maintaining and persisting the state of the plugin execution.

    Main logic behind each InCallPlugin is triggered on each new data packet arriving,
    there is no guarantee that the same instance will be triggered on next packet.
    Therefore, using PersistenceProvider should be the preferred (an only guaranteed way) to maintain state.

    There are two main ways of state maintenance:

    1. Manually save and restore state (to and from local key/value cache).
    2. Recollect all outputs this plugin (or it's dependencies) made so far.
    """

    _store: dict[str, object] = {}
    _history: dict = {}

    async def set(self, info: MeetingMetadata, key: str, data: object) -> Awaitable:
        """Persist state for the given <plugin_id, meeting_id, user_id> combination.

        Args:
            info: Meeting metadata
            key: some key
            data: some data

        Returns:
            Awaitable
        """
        self._store[f"{info.plugin_name}+{info.meeting_id}+{key}"] = data

    async def get(self, info: MeetingMetadata, key: str) -> Awaitable[object]:
        """Get current state for the given <plugin_id, meeting_id, user_id> combination.

        Args:
            info: Meeting metadata
            key: some key

        Returns:
            Awaitable
        """
        return self._store.get(f"{info.plugin_name}+{info.meeting_id}+{key}")

    async def get_stream_history(
        self,
        info: MeetingMetadata,
        num_packets: int = 0,
        not_before: timedelta = None,
    ) -> list[DataPacket]:
        """Get outputs for plugin made so far.

        Args:
            info: Meeting metadata
            num_packets: some key
            not_before: timedelta

        Returns:
            List of data packets
        """
        # FIXME limit to one of num_packets or timestamp.
        # Get this from the core app directly in prod
        pass


class MeetingEngine:
    """Main entry point for all interactions with the core system.

    Each plugin is provided with the singleton instance implementing the MeetingEngine.
    """

    _instance: MeetingEngine = None

    _datastore = PersistenceProvider()
    _llm = LLMProvider()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def llm(self) -> LLMProvider:
        """Get the instance of LLMProvider.

        Returns:
            Instance of LLMProvider
        """
        return self._llm

    def datastore(self) -> PersistenceProvider:
        """Get the instance of PersistenceProvider.

        Returns:
            Instance of PersistenceProvider
        """
        return self._datastore
