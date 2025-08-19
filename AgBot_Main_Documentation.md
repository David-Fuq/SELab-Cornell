# AgBot Control System Documentation

## Overview

The AgBot control system is designed to manage an agricultural robot that performs automated plant care tasks such as moisture sensing and watering. The system operates in two primary modes:

1. **Connected mode**: When a client is connected via USB, the AgBot receives and executes commands in real-time.
2. **Autonomous mode**: When no client is connected, the AgBot operates independently according to pre-configured missions.

The control system is built on an asynchronous architecture using MicroPython's `uasyncio` library, allowing for concurrent execution of multiple tasks such as movement, sensor reading, and file transfers.

## System Structure

The main control system in `main.py` consists of several key components:

### 1. Global State Management

The system maintains global variables to track:
- Connection status (via ping timestamps)
- Active task references
- DateTime synchronization with the client
- File transfer management

### 2. Core Functions

The system is organized around these primary functions:

#### `main()`
Entry point that initializes the system and starts the master task. It:
- Creates the controller and clock instances
- Sets up the system boundaries
- Handles exceptions and system resets

#### `master_task(controller, clock)`
The central orchestrator that runs continuously to:
- Monitor connection status
- Switch between connected and autonomous modes
- Process incoming serial commands
- Manage task lifecycles

#### `process_incoming_command(controller, user_input)`
Parses and routes commands from the client to the appropriate handlers:
- Synchronizes time via ping messages
- Manages movement tasks
- Handles file transfer requests and data
- Prevents concurrent operations on the same resources

#### `sensor_location_task(controller, data)`
Executes movement and sensing commands:
- Controls AgBot positioning (move, home, stop)
- Takes moisture readings
- Manages plant and mission configurations
- Triggers watering actions
- Initiates file transfers

#### `file_transfer_request_task(controller, data_list)` and `file_transfer_receive_task(data_list)`
Handle file operations between the AgBot and client:
- Send system data (configuration, logs, readings)
- Receive updates to plant/mission configurations
- Process file chunks during transfer

#### `not_connected_task(controller)`
Executes autonomous operations when no client is connected.

## Process Management

### Connection Management

The system continuously monitors the connection status using ping messages:

```python
def is_connected():
    return (time.time() - last_ping_time) < connection_timeout
```

When a ping message is received, the system updates the `last_ping_time` and synchronizes the internal clock with the client's timestamp.

### Mode Switching

The `master_task` function implements the core logic for switching between connected and autonomous modes:

#### Disconnected → Autonomous Mode

When the client disconnects (no ping received within the timeout period):

1. Any active movement task is cancelled for safety
2. The `not_connected_task` is started to run pre-configured missions automatically
3. The system continues to monitor for client reconnection

```python
if not is_connect:
    # Cancel any ongoing movement if the client disconnects
    if task_movement_ref and not task_movement_ref.done():
        task_movement_ref.cancel()
        controller.agbot.stop()
        
    # Start the autonomous operation task if not already running
    if task_not_connected_ref is None or task_not_connected_ref.done():
        task_not_connected_ref = asyncio.create_task(not_connected_task(controller))
```

#### Autonomous → Connected Mode

When a client reconnects:

1. The autonomous task is cancelled
2. The system returns to client-controlled operation
3. The client can then send commands for movement, sensing, or file transfers

```python
elif task_not_connected_ref and not task_not_connected_ref.done():
    # When client reconnects, stop autonomous mode
    task_not_connected_ref.cancel()
```

### Concurrent Task Management

The system is designed to handle multiple operations concurrently while preventing resource conflicts:

#### Movement and Control Tasks

Movement commands are executed through the `sensor_location_task`:

- Only one movement task can run at a time
- If a movement task is already running, new movement commands are rejected
- The STAP command can emergency stop any movement

```python
if task_movement_ref is None or task_movement_ref.done():
    task_movement_ref = asyncio.create_task(sensor_location_task(controller, user_input))
else:
    print("Movement task already running.")
```

#### File Transfer Tasks

File transfers operate independently of movement tasks, allowing simultaneous operations:

- File transfers use separate task references (`task_file_transfer_ref` and `task_send_file_transfer_ref`)
- Transfers prevent concurrent operations of the same type (send or receive)
- The system can be moving while sending or receiving files

```python
if task_file_transfer_ref is None or task_file_transfer_ref.done():
    task_file_transfer_ref = asyncio.create_task(file_transfer_receive_task(data_list))
else:
    print("File transfer task already running, please wait.")
```

### Command Processing Pipeline

1. Serial input is buffered until a complete command (terminated by newline) is received
2. `process_incoming_command` identifies the command type and routes it appropriately
3. Commands are executed asynchronously as tasks
4. Results/responses are sent back to the client when needed

## Data Management

The system handles several types of data:

1. **Configuration Data**: Plant and mission settings stored in JSON format
2. **Operation Logs**: Records of missions, moisture readings, and watering events in CSV format
3. **Real-time Commands**: Immediate control commands for movement and sensing
4. **File Transfers**: Bidirectional transfer of configuration and log files

Files can be requested by the client using file IDs:
- ID 0: System configuration (agbot_data.json)
- ID 1: Mission history (mission_history.csv)
- ID 2: Moisture readings (moisture_readings.csv)
- ID 3: Water log (water_log.csv)

## Command Protocol

The system uses a simple comma-separated value protocol for commands:

- Movement: `1,x,y` to move to coordinates (x,y)
- Sensing: `2` to take a moisture reading
- Homing: `3` to return to home position
- Plant Management: `4,name,x_sense,y_sense,x_plant,y_plant,threshold,ml_response,id`
- Mission Execution: `5,mission_id`
- Emergency Stop: `STAP`
- File Requests: `20,file_id`
- File Data: `FT,type,data...`
- System Changes: `CHA,action_code,...`

## Conclusion

The AgBot control system demonstrates a sophisticated asynchronous architecture that effectively manages concurrent operations while providing both manual and autonomous control modes. The system's ability to handle multiple tasks simultaneously (movement, sensing, and file transfers) while maintaining safety through proper task cancellation and resource management makes it a robust solution for agricultural automation.

The clear separation between connected and autonomous modes ensures that the AgBot can operate effectively regardless of client connection status, providing reliability in field conditions where connectivity might be intermittent.
