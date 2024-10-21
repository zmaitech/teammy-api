
# Implement Plugin Using Teammy API

## Introduction

This guide provides step-by-step instructions on how to implement plugins using the Teammy API. It covers everything from setting up your environment to integrating and testing your plugins.

## Overview of the API

For a comprehensive overview of Teammy API, visit the [Overview](../reference/reference.md) page.

## Step-by-Step Instructions

Teammy plugins are built as packages that are injected into the Teammy runtime. The plugin itself can use available VPC resources through the Teammy API, which is dependency injected at runtime. The available Teammy API package is used as a stub for local development.

### Step 1: Setting Up the Environment

Initialize the repository using a Python package manager. We recommend `poetry`.

```bash
poetry init
```

The package should be named `plugin` so it can be properly runtime injected.

```toml
[tool.poetry]
name = "plugin"
```

Add Teammy API dependency to `pyproject.toml` as a development dependency:

```toml
[tool.poetry.group.dev.dependencies]
teammy = { git = "https://bitbucket.org/zmaitech/teammy-stub.git", branch = "main" }
```

This is a stub dependency and will be replaced during runtime. It allows developers to test the plugin locally.

### Step 2: Define Plugin Metadata

Each plugin must define its metadata, such as the name, version, and data sources it will consume. This is done by implementing the [`InCallPluginMetadata`](../reference/plugin/in-call-plugin-metadata.md) class.

Define a class for your plugin metadata that includes:

- **Plugin name**: A unique name to identify the plugin.
- **Version**: The version string for your plugin.
- **Data sources**: A list of data sources that your plugin will consume.
- **Plugin config**: A configuration object specific to your plugin.

### Step 3: Implement Plugin Class

The main plugin functionality is implemented in a class that inherits from [`InCallPlugin`](../reference/plugin/in-call-plugin.md). This class will manage various lifecycle events and data handling.
Each plugin package should implement only one [`InCallPlugin`](../reference/plugin/in-call-plugin.md) class.

**Important:** The [`InCallPlugin`](../reference/plugin/in-call-plugin.md) class must be stateless, and all state management is done through the [`MeetingEngine`](../reference/engine/meeting-engine.md). This ensures that the runtime itself keeps the state shared with other instances of the same plugin, facilitating horizontal scaling.

#### 3.1 Retrieve Plugin Metadata

Plugin must implement the [`get_metadata`](../reference/plugin/in-call-plugin.md/#teammy.api.plugin.InCallPlugin.get_metadata) method to return an instance of [`InCallPluginMetadata`](../reference/plugin/in-call-plugin-metadata.md).

This method is called once during the installation of the plugin.

#### 3.2 Handle Lifecycle Events

Plugins must manage key lifecycle events. These lifecycle events represent different phases in a plugin's operation, such as installation, startup, and shutdown. Handling these events properly ensures that plugins are correctly initialized, execute their tasks efficiently, and release resources when no longer needed.

1. **Installation Phase**<br>
During the installation phase, the plugin is prepared for deployment. This phase typically occurs when the plugin is being built, such as during the docker build process. Any setup that needs to happen before the plugin is deployed should be handled here.
To define what happens during installation, implement the [`on_install`](../reference/plugin/in-call-plugin.md/#teammy.api.plugin.InCallPlugin.on_install) method.
2. **Startup Phase**<br>
Once the plugin is deployed, the startup phase occurs. During this phase, the plugin initializes itself and prepares to handle its tasks. This is the time to set up connections, prepare resources, and ensure the plugin is ready to start processing data.
To manage the initialization tasks, implement the [`on_startup`](../reference/plugin/in-call-plugin.md/#teammy.api.plugin.InCallPlugin.on_startup) method.
3. **Shutdown Phase**<br>
When the plugin is no longer needed or the container is gracefully stopped, the shutdown phase is triggered. In this phase, the plugin should release resources, disconnect from any external services, and perform cleanup tasks to ensure a smooth shutdown.
To handle resource cleanup, implement the [`on_shutdown`](../reference/plugin/in-call-plugin.md/#teammy.api.plugin.InCallPlugin.on_shutdown) method.

#### 3.3 Define Data Receive Hooks

The plugin must define hooks for specific data sources it consumes, such as audio or transcription. These hooks are responsible for processing incoming [`DataPacket`](../reference/data/data-packet.md) objects.
The data inside the packet may be any object that should be parsed.

- Implement the [`get_data_receive_hooks`](../reference/plugin/in-call-plugin.md/#teammy.api.plugin.InCallPlugin.get_data_receive_hooks) method to return a dictionary that maps the data types your plugin consumes to their respective handler functions.
- Each handler function should be an asynchronous method that accepts a [`DataPacket`](../reference/data/data-packet.md) and [`MeetingEngine`](../reference/engine/meeting-engine.md) as parameters.
- The result of a hook, if it does not return `None`, will be exposed as a consumable type to the rest of the system. For example, if a plugin named `llm-action` (as defined in the config) processes data, it will produce a JSON result of a `llm-action`. This result is then pushed to the data stream for other components or plugins to consume.

- The result can be any serializable object, such as:
    - bytearray
    - string
    - JSON-serializable object
    - Pydantic object (which can be serialized using model_dump(type=json))

**Important**: Each plugin may consume multiple data sources, but it only produces one output. This output is distinguished by the plugin name, as defined in the configuration.

#### 3.4 Manage Meeting Events

When a plugin is assigned to a meeting, it must respond to specific meeting events, such as when the meeting starts or ends. These events trigger the [`on_meeting_start`](../reference/plugin/in-call-plugin.md/#teammy.api.plugin.InCallPlugin.on_meeting_start) and [`on_meeting_end`](../reference/plugin/in-call-plugin.md/#teammy.api.plugin.InCallPlugin.on_meeting_end) methods.

- At the start of the meeting, the hook is subscribed to the data stream, and incoming data will be processed as [`DataPacket`](../reference/data/data-packet.md) objects. Implement the [`on_meeting_start`](../reference/plugin/in-call-plugin.md/#teammy.api.plugin.InCallPlugin.on_meeting_start) method to handle any initialization tasks when the meeting starts.
- At the end of the meeting, the hook is unsubscribed from the data stream. Implement the [`on_meeting_end`](../reference/plugin/in-call-plugin.md/#teammy.api.plugin.InCallPlugin.on_meeting_end) method to handle cleanup tasks when the meeting ends.

### Step 4: Utilize Meeting Engine

The [`MeetingEngine`](../reference/engine/meeting-engine.md) provides a singleton instance that serves as the primary interaction point with the core system. It manages LLM access and data persistence, acting as the bridge between your plugin and the rest of the system.

**Note:** The only point of access to the rest of the VPC (Virtual Private Cloud) is through the [`MeetingEngine`](../reference/engine/meeting-engine.md). The [`MeetingEngine`](../reference/engine/meeting-engine.md) is used for persistence and LLM (Large Language Model) access. In the future, more features will be available.

#### Using LLMProvider

The [`LLMProvider`](../reference/engine/llm-provider.md) class is your entry point for interacting with the LLM (Large Language Model). You can use it to send prompts and retrieve responses.

For example, if your plugin involves analyzing conversation data, you can send parts of the conversation to the LLM for summarization or analysis.

See the reference for [LLMProvider](../reference/engine/llm-provider.md).

#### Using PersistenceProvider

The [`PersistenceProvider`](../reference/engine/persistence-provider.md) class allows your plugin to maintain state across executions. You can use it to store and retrieve data related to the meeting, such as chat history or meeting artifacts.

It is particularly useful for long-running sessions where you need to preserve data between different phases of the plugin lifecycle.

See the reference for [PersistenceProvider](../reference/engine/persistence-provider.md).