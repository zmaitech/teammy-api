# Plugin Implementation Example

## Overview
Full guide for plugin implementation using Teammy API can be found [here](how-to-guides.md).
<!-- we should double link to the guide as these go hand in hand -->
Let's walk through a practical example of how to implement the `LLMActionPlugin` in a meeting scenario. We will outline the steps required to integrate the plugin, how it interacts with the transcription data, and how actions are detected using the LLM (Large Language Model). This example will cover the plugin's lifecycle, configuration, and data processing methods.

The whole implementation of this plugin can be found here [llm-action-plugin](https://bitbucket.org/zmaitech/llm-action-plugin/src/main/).

## Step-by-Step Implementation

### 1. Project configuration

Add required dependencies using Poetry, including pulling teammy-stub.

```toml
[tool.poetry]
name = "plugin"  # IMPORTANT! Has to be named plugin
version = "0.1.0"
description = ""
authors = [""]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.12"
openai = "^1.51.2"


[tool.poetry.group.dev.dependencies]
black = "^24.10.0"
pytest = "^8.3.3"
isort = "^5.13.2"
pytest-asyncio = "^0.24.0"
teammy = { git = "https://bitbucket.org/zmaitech/teammy-stub.git", branch = "main" }


[tool.pytest.ini_options]
pythonpath = ["src"]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### 2. Define Plugin Metadata

The `LLMActionPlugin` requires a configuration that specifies the possible actions it can handle. This configuration is represented by the `LLMActionPluginConfig` class.

```py
@dataclass(frozen=True)
class LLMActionPluginConfig(PluginConfig):
    possible_actions: list[str]
```

In your main application, you would specify the possible actions when initializing the plugin:

```py
POSSIBLE_ACTIONS = [
    {
        "action": "google-search",
        "description": "Looks up the asked for term on google. Takes in search parameter",
    }
]

plugin_config = LLMActionPluginConfig(possible_actions=possible_actions)
```

Implement the [`get_metadata`](../reference/plugin/in-call-plugin.md/#teammy.api.plugin.InCallPlugin.get_metadata) method to return the metadata defined earlier.

```py
@classmethod
async def get_metadata(cls) -> InCallPluginMetadata:
    return InCallPluginMetadata(
        name="llm-action",
        version="0.0.1",  # fetch from pyproject.toml
        sources=["transcription"],
        config=LLMActionPluginConfig(possible_actions=POSSIBLE_ACTIONS),
    )
```

### 3. Handle Plugin Lifecycle Events

Implement methods for handling the lifecycle events of the plugin if necessary.
In this particular example, no additional tasks are necessary for these events, so they simply log informational messages.

```py
@classmethod
async def on_install(cls):
    logging.info("Installed plugin")

@classmethod
async def on_startup(cls, config: PluginConfig):
    logging.info("Startup plugin")
    
@classmethod
async def on_shutdown(cls, engine: MeetingEngine):
    logging.info("Plugin shutdown")
```

### 4. Define Data Receive Hooks

Implement the [`get_data_receive_hooks`](../reference/plugin/in-call-plugin.md/#teammy.api.plugin.InCallPlugin.get_data_receive_hooks) method to return a dictionary mapping declared data types the plugin consumes to handler functions.

Each handler function should be an async that accepts [`DataPacket`](../reference/data/data-packet.md) and [`MeetingEngine`](../reference/engine/meeting-engine.md).

```py
@classmethod
async def get_data_receive_hooks(cls) -> dict[str, InCallPlugin.HookFunction]:
    return {"transcription": transcription_handler}
```

The result of a hook, if it does not return `None`, will be exposed as a consumable type to the rest of the system. For example, if a plugin named `llm-action` (as defined in the config) processes data, it will produce a JSON result of a `llm-action`. This result is then pushed to the data stream for other components or plugins to consume.

### 5. Manage Meeting Events

Implement the [`on_meeting_start`](../reference/plugin/in-call-plugin.md/#teammy.api.plugin.InCallPlugin.on_meeting_start) and [`on_meeting_end`](../reference/plugin/in-call-plugin.md/#teammy.api.plugin.InCallPlugin.on_meeting_end) methods to handle required tasks when the meeting begins and ends.
In this example, no additional tasks are necessary for these events, so they simply log informational messages.

```py
@classmethod
async def on_meeting_start(
    cls, meeting_info: MeetingMetadata, engine: MeetingEngine
):
    logging.info(f"Meeting started: {meeting_info}")

@classmethod
async def on_meeting_end(cls, meeting_info: MeetingMetadata, engine: MeetingEngine):
    logging.info(f"Meeting ended: {meeting_info}")
```

### 6. Utilize Meeting Engine

The [`MeetingEngine`](../reference/engine/meeting-engine.md) provides a singleton instance that serves as the primary interaction point with the core system. It manages LLM access and data persistence, acting as the bridge between your plugin and the rest of the system.

**Note:** The only point of access to the rest of the VPC (Virtual Private Cloud) is through the [`MeetingEngine`](../reference/engine/meeting-engine.md). The [`MeetingEngine`](../reference/engine/meeting-engine.md) is used for persistence and LLM (Large Language Model) access. In the future, more features will be available.

#### Using LLMProvider

[`MeetingEngine`](../reference/engine/meeting-engine.md) provides LLM access through [`LLMProvider`](../reference/engine/llm-provider.md) class.
`LLMActionPlugin` uses LLM to interpret and respond to meeting transcriptions by detecting specific actions mentioned in the dialogue.

#### Using PersistenceProvider

[`MeetingEngine`](../reference/engine/meeting-engine.md) provides LLM access through [`PersistenceProvider`](../reference/engine/persistence-provider.md) class. In this example, the PersistenceProvider plays a crucial role in managing and storing the state of the plugin and the associated meeting data, ensuring that actions and transcripts are maintained throughout the lifecycle of the meeting.

Example of using [`LLMProvider`](../reference/engine/llm-provider.md) and [`PersistenceProvider`](../reference/engine/persistence-provider.md) from [`MeetingEngine`](../reference/engine/meeting-engine.md) in a hook method:

```py
async def transcription_handler(
    packet: DataPacket, engine: MeetingEngine
) -> Awaitable[str]:
    # Expected data schema is a serialized json
    transcription_packet = TranscriptionPacket.model_validate_json(packet.data)

    running_transcription: str = (
        await engine.datastore().get(packet.meeting_metadata, "running_transcription")
        or ""
    )
    # Get last 1000 characters of the transcript naively
    running_transcription: str = running_transcription[-1000:]
    transcription = running_transcription + transcription_packet.transcription

    try:
        used_actions_data: list[dict] = (
            await engine.datastore().get(packet.meeting_metadata, "used_actions") or []
        )

        used_actions: list[TranscriptionAction] = [
            TranscriptionAction(**action) for action in used_actions_data
        ]
    except ValidationError as e:
        logging.error(e)
        return "Validation error occurred."

    used_actions_formatted = json.dumps(
        [action.model_dump() for action in used_actions], indent=4
    )

    user_prompt = USER_PROMPT_TEMPLATE.format_map(
        {
            "DETECTED_ACTIONS": used_actions_formatted,
            "TRANSCRIPT_SEGMENT": transcription,
        }
    )

    res = await engine.llm().prompt(
        messages=[
            {"role": "user", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
    )

    new_actions_data = find_and_parse_last_json(res, "[", "]")

    try:
        new_actions = [TranscriptionAction(**action) for action in new_actions_data]
        new_actions_json = [action.model_dump() for action in new_actions]
        await engine.datastore().set(
            packet.meeting_metadata, "used_actions", new_actions_json
        )
    except ValidationError as e:
        logging.error(e)
        return "Validation error occurred."

    await engine.datastore().set(
        packet.meeting_metadata, "running_transcription", transcription
    )

    return res
```
