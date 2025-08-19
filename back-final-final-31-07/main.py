# File helpers
from controller import Controller
from clock import Clock
from file_transfer import FileTransfer
from agbot_file_util import Utils

import time
from agbot_file_util import Utils
import sys

sys.path.append("")

from micropython import const

import uasyncio as asyncio

import select
import machine

import struct

# device info

#Global variables
last_ping_time = time.time()
connection_timeout = 10

task_movement_ref = None
nected_ref = None
task_file_transfer_ref = None
task_send_file_transfer_ref = None
task_not_connected_ref = None
#(year, month, day, weekday, hours, minutes, seconds, subseconds)
datetime_from_pc : tuple = (2002, 6, 1, 5, 13, 11, 54, 0)

# File transfer manager
file_transfer = FileTransfer()

def is_connected():
    """
    Input: None
    Output: Boolean - True if connected, False if not
    Description: Checks if the connection with the client is active by comparing the time since the last ping against the timeout threshold
    """
    global connection_timeout
    if time.time() - last_ping_time < 0:
        pass
    return (time.time() - last_ping_time) < connection_timeout



async def sensor_location_task(controller, data):
    """
    Input: controller - Controller object to manage the AgBot
           data - String containing command and parameters from client
    Output: None
    Description: Processes incoming commands from the client and executes the corresponding actions on the AgBot
                 Commands include movement, moisture reading, homing, plant management, and more
    """
    global datetime_from_pc
    print("EN SENSOR LOCATION")
    data_list = data.split(",")
    cmd = data_list[0]
    
    if data is not None:
            
        action = int(cmd)
        if action == 0:
            # Stop the AgBot's movement
            controller.agbot.stop()
        elif action == 1:
            # Move the AgBot to specific X,Y coordinates
            x = data_list[1]
            y = data_list[2]
            await controller.agbot.move_to(int(x), int(y))
        elif action == 2:
            # Take a moisture reading at the current position and return the value
            print("Probing...")
            moisture_reading = await controller.agbot.read()
            print(f"2,{moisture_reading}")  # Send back moisture reading

        elif action == 3:
            # Return the AgBot to its home position
            await controller.agbot.home()
        #4,Plantain,100,100,110,110,3,50
        elif action == 4:
            # Add a new plant to the system with specified parameters
            plant_name = data_list[1]
            x_sense = int(data_list[2])
            y_sense = int(data_list[3])
            x_plant = int(data_list[4])
            y_plant = int(data_list[5])
            moisture_threshhold = int(data_list[6])
            ml_response = int(data_list[7])
            plant_id = int(data_list[8])
            controller.memory.add_plant(plant_name, x_sense, y_sense, x_plant, y_plant, moisture_threshhold, ml_response, plant_id)
        elif action == 5:
            # Run a specific mission with the given ID
            mission_id = int(data_list[1])
            await controller.run_mission(mission_id=mission_id, date_from_pc = datetime_from_pc)
        elif action == 6:
            # Force recalibration of XY limits and move to a safe position
            await controller.setup_xy_max(force=True)
            await controller.agbot.move_to(20, 20)
        elif action == 8:
            # Delete a mission with the specified ID
            mission_id = int(data_list[1])
            controller.memory.delete_mission(mission_id)
        elif action == 9:
            # Delete a plant with the specified ID
            plant_id = int(data_list[1])
            controller.memory.delete_plant(plant_id)
        elif action == 10:
            # Add or remove a plant from a mission
            plant_id = int(data_list[1])
            mission_id = int(data_list[2])
            add_remove = int(data_list[3])  # 0=add, 1=remove
            if add_remove == 0:
                # Add the plant to the mission
                controller.memory.add_plant_to_mission(plant_id, mission_id)
            else:
                # Remove the plant from the mission
                controller.memory.remove_plant_from_mission(plant_id, mission_id)
        elif action == 11:
            # Load gantry size from configuration without recalibration
            print("Getting gantry size from agbot_data.json")
            await controller.setup_xy_max(force=False)
            await controller.agbot.move_to(20, 20)
        elif action == 12:
            # Manually dispense a specific amount of water
            water_amount = float(data_list[1])
            print("En el condicional 12")
            await controller.water_manually(water_amount)
        # File transfer commands
        elif action == 20:
            # Request file transfer with specified file ID
            # Format: 20,file_id
            file_id = int(data_list[1])
            await file_transfer_request_task(controller, file_id)
        elif action == 21:
            # Prepare to receive a file with the given ID and optional name
            # Format: 21,file_id,file_name
            file_id = int(data_list[1])
            file_name = data_list[2] if len(data_list) > 2 else None
            print(f"Ready to receive file: ID={file_id}, name={file_name}")
        else:
            # Handle unrecognized action
            print(f"Invalid action: {action}")
        
    await asyncio.sleep_ms(100)

async def not_connected_task(controller):
    """
    Input: controller - Controller object to manage the AgBot
    Output: None
    Description: Executes the controller's automatic run function when the client is disconnected
                 to allow the AgBot to operate autonomously
    """
    await controller.run()

async def file_transfer_request_task(controller, data_list):
    """
    Input: controller - Controller object to manage the AgBot
           data_list - List containing file transfer request parameters
    Output: None
    Description: Handles file transfer requests from the client, sending various data files 
                 (JSON configuration, mission history, moisture readings, water logs)
                 or processing changes to plants and missions
    """
    try:
        if data_list[0] == '20':
            # Handle file download requests based on file ID
            file_id = int(data_list[1])
            if file_id == 0:
                # Send memory data (JSON) - system configuration
                await file_transfer.send_file(controller.memory.data, "JSON", "agbot_data.json")
            elif file_id == 1:
                # Send mission history (CSV) - log of executed missions
                data = Utils.get_file_data("mission_history.csv")
                if data:
                    await file_transfer.send_file(data, "CSV", "mission_history.csv")
                else:
                    print("FT,ERR,File mission_history.csv not found")
            elif file_id == 2:
                # Send moisture readings (CSV) - historical sensor data
                data = Utils.get_file_data("moisture_readings.csv")
                if data:
                    await file_transfer.send_file(data, "CSV", "moisture_readings.csv")
                else:
                    print("FT,ERR,File moisture_readings.csv not found")
            elif file_id == 3:
                # Send water log (CSV) - record of water dispensing events
                data = Utils.get_file_data("water_log.csv")
                if data:
                    await file_transfer.send_file(data, "CSV", "water_log.csv")
                else:
                    print("FT,ERR,File water_log.csv not found")
            else:
                # Unknown file ID requested
                print(f"FT,ERR,Unknown file ID: {file_id}")
        elif data_list[0] == 'CHA':
            # Handle system configuration changes
            print("Modifying plants or missions")
            if int(data_list[1]) == 4:
                # Add a new plant to the system
                plant_name = data_list[2]
                x_sense = int(data_list[3])
                y_sense = int(data_list[4])
                x_plant = int(data_list[5])
                y_plant = int(data_list[6])
                moisture_threshhold = int(data_list[7])
                ml_response = int(data_list[8])
                plant_id = int(data_list[9])
                controller.memory.add_plant(plant_name, x_sense, y_sense, x_plant, y_plant, moisture_threshhold, ml_response, plant_id)
            elif int(data_list[1]) == 9:
                # Delete a plant from the system
                plant_id = int(data_list[2])
                controller.memory.delete_plant(plant_id)
            elif int(data_list[1]) == 8:
                # Delete a mission from the system
                mission_id = int(data_list[2])
                controller.memory.delete_mission(mission_id)
            elif int(data_list[1]) == 12:
                # Add a new mission to the system
                mission_name = data_list[2]
                hour = int(data_list[3])
                minute = int(data_list[4])
                action = int(data_list[5])
                mission_id = int(data_list[6])
                controller.memory.add_mission(mission_name, hour, minute, action, mission_id)
            elif int(data_list[1]) == 10:
                # Modify mission-plant associations
                plant_id = int(data_list[2])
                mission_id = int(data_list[3])
                add_remove = int(data_list[4])  # 0=add, 1=remove
                if add_remove == 0:
                    # Add the plant to the mission
                    controller.memory.add_plant_to_mission(plant_id, mission_id)
                else:
                    # Remove the plant from the mission
                    controller.memory.remove_plant_from_mission(plant_id, mission_id)
    except Exception as e:
        # Log any errors that occur during file transfer operations
        print(f"FT,ERR,{e}")

async def file_transfer_receive_task(data_list):
    """
    Input: data_list - List containing file transfer data
    Output: None
    Description: Handles incoming file transfer data from the client, processes different 
                 transfer phases (header, chunks, finalization) and manages file reception
    """
    try:
        # Format: FT,type,data
        ft_type = data_list[1]
        
        if ft_type == "H":  # Header
            # Format: FT,H,header_data_hex
            await file_transfer.receive_file(data_list[2])
        elif ft_type == "P":  # Payload/chunk
            # Format: FT,P,chunk_index,total_chunks,chunk_data_hex
            chunk_index = int(data_list[2])
            total_chunks = int(data_list[3])
            await file_transfer.process_chunk(chunk_index, total_chunks, data_list[4])
        elif ft_type == "L":  # Last/end
            # Format: FT,L,last_data_hex,file_name
            file_name = data_list[3] if len(data_list) > 3 else None
            await file_transfer.finalize_file(data_list[2], file_name)
    except Exception as e:
        print(f"FT,ERR,{e}")

async def process_incoming_command(controller, user_input):
    """
    Input: controller - Controller object to manage the AgBot
           user_input - String containing the command from the client
    Output: None
    Description: Processes all incoming commands from the client, updates connection status,
                 handles ping messages with time synchronization, manages file transfers,
                 and starts appropriate tasks for movement and other operations
    """
    global last_ping_time, task_movement_ref, task_file_transfer_ref, task_send_file_transfer_ref, datetime_from_pc
    
    # Update the last ping time for connection status
    last_ping_time = time.time()
    
    # Parse the command
    if user_input.startswith("ping"):
        # Handle ping messages with timestamp sync
        # Format: ping,year,month,day,weekday,hours,minutes,seconds,subseconds
        datetime_tuple = user_input.split(",")
        ping, year, month, day, weekday, hours, minutes, seconds, subseconds = datetime_tuple
        datetime_from_pc = (int(year), int(month), int(day), int(weekday), int(hours), int(minutes), int(seconds), int(subseconds))
        #print("tiempo del input", datetime_from_pc)
        # Synchronize the AgBot's RTC with the client's timestamp
        machine.RTC().datetime(datetime_from_pc)
        last_ping_time = time.time()
        #print(last_ping_time)
    elif user_input == "STAP":
        # Stop all movement - emergency stop command
        if task_movement_ref and not task_movement_ref.done():
            # Cancel the current movement task
            task_movement_ref.cancel()
            # Stop the physical motors
            controller.agbot.stop()
            await asyncio.sleep(0)
            print("movement task stopped")
        else:
            print("Movement task is not running.")
    elif user_input.startswith("FT,"):
        # Handle incoming file transfer chunks and commands
        data_list = user_input.split(",")
        if task_file_transfer_ref is None or task_file_transfer_ref.done():
            # Start a new file transfer receive task
            task_file_transfer_ref = asyncio.create_task(file_transfer_receive_task(data_list))
        else:
            print("File transfer task already running, please wait.")
    elif user_input.startswith("20,") or user_input.startswith("CHA,"):
        # Handle file transfer requests or system configuration changes
        data_list = user_input.split(",")
        if task_send_file_transfer_ref is None or task_send_file_transfer_ref.done():
            # Start a new file transfer send task
            task_send_file_transfer_ref = asyncio.create_task(file_transfer_request_task(controller, data_list))
        else:
            print("File send request task already running, please wait.")
     #   pass
    #TODO Create a task for file transfer requests
    else: 
        # Handle standard AgBot control commands (movement, sensing, etc.)
        print(f"Received command: {user_input}")
        if task_movement_ref is None or task_movement_ref.done():
            # Start a new movement/control task
            task_movement_ref = asyncio.create_task(sensor_location_task(controller, user_input))
        else:
            print("Movement task already running.")

async def master_task(controller, clock):
    """
    Input: controller - Controller object to manage the AgBot
           clock - Clock object for time management
    Output: None
    Description: Main control loop that handles input from the client, manages connection status,
                 switches between manual and autonomous modes, and processes incoming commands.
                 This is the central task orchestrator for the AgBot system.
    """
    print("AgBot serial controller started!")
    global task_movement_ref, task_not_connected_ref, last_ping_time, datetime_from_pc
    buffer = ""
    
    while True:
        # Check connection status
        is_connect = is_connected()
        if not is_connect:
            # When client is disconnected, switch to autonomous mode
            
            # Cancel any ongoing movement if the client disconnects
            if task_movement_ref and not task_movement_ref.done():
                task_movement_ref.cancel()
                controller.agbot.stop()
                await asyncio.sleep(0.1)
                print("Movement cancelled - disconnected")
            
            # Start the autonomous operation task if not already running
            if task_not_connected_ref is None or task_not_connected_ref.done():
                print("INICIANDO AUTO TASK")
                task_not_connected_ref = asyncio.create_task(not_connected_task(controller))
        elif task_not_connected_ref and not task_not_connected_ref.done():
            # When client reconnects, stop autonomous mode
            print("Cancelando task automatico")
            task_not_connected_ref.cancel()
            print("Despues de cancelar")
            await asyncio.sleep(0.1)
                
        # Check for incoming serial data from client
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            #print(clock.get_time())
            # Read one character at a time
            char = sys.stdin.read(1)
            if char in ("\n", "\r"):
                # End of command reached, process the complete command
                user_input = buffer.strip()
                buffer = ""
                if user_input not in ("", " ", "  "):
                    # Process non-empty commands
                    await process_incoming_command(controller, user_input)
            else:
                # Accumulate characters until a complete command is received
                buffer += char
                
        # Short delay to prevent CPU hogging
        await asyncio.sleep_ms(10)

async def main():
    """
    Input: None
    Output: None
    Description: Entry point for the AgBot control system. Initializes the controller and clock,
                 sets up the system, and starts the master task. Includes error handling for
                 keyboard interrupts and unexpected exceptions with system reset capability.
    """
    try:
        controller = Controller.get_default_controller()
        await controller.setup_xy_max(force=False)
        clock = Clock.get_default_clock()
        machine.RTC().datetime(datetime_from_pc)
        await master_task(controller, clock)
    except KeyboardInterrupt:
        print("Keyboard interrupt")
        controller.agbot.stop()
    except Exception as e:
        print(f"Error: {e}")
        controller.agbot.stop()
        Utils.append_error_to_log(str(e))
        machine.reset()
        
# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
