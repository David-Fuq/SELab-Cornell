# File helpers
from controller import Controller
from file_transfer import FileTransfer

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
task_not_connected_ref = None
task_file_transfer_ref = None
task_send_file_transfer_ref = None

# File transfer manager
file_transfer = FileTransfer()

def is_connected():
    return (time.time() - last_ping_time) < connection_timeout


# This is a task that waits for writes from the client
# and updates the sensor location.
async def sensor_location_task(controller, data):
    print("EN SENSOR LOCATION")
    data_list = data.split(",")
    cmd = data_list[0]
    
    if data is not None:
        if cmd == "ping":
            print("pong")
            return
            
        action = int(cmd)
        if action == 0:
            controller.agbot.stop()
        elif action == 1:
            x = data_list[1]
            y = data_list[2]
            await controller.agbot.move_to(int(x), int(y))
        elif action == 2:
            print("Probing...")
            moisture_reading = await controller.agbot.read()
            print(f"2,{moisture_reading}")  # Send back moisture reading

        elif action == 3:
            await controller.agbot.home()
        elif action == 5:
            mission_id = int(data_list[1])
            await controller.run_mission(mission_id=mission_id)
        elif action == 6:
            await controller.setup_xy_max(force=True)
            await controller.agbot.move_to(20, 20)
        elif action == 8:
            mission_id = int(data_list[1])
            controller.memory.delete_mission(mission_id)
        elif action == 9:
            plant_id = int(data_list[1])
            controller.memory.delete_plant(plant_id)
        elif action == 10:
            # Add/remove plant from mission
            plant_id = int(data_list[1])
            mission_id = int(data_list[2])
            add_remove = int(data_list[3])  # 0=add, 1=remove
            if add_remove == 0:
                controller.memory.add_plant_to_mission(plant_id, mission_id)
            else:
                controller.memory.remove_plant_from_mission(plant_id, mission_id)
        elif action == 11:
            print("Getting gantry size from agbot_data.json")
            await controller.setup_xy_max(force=False)
            await controller.agbot.move_to(20, 20)
        # File transfer commands
        elif action == 20:
            # Request file
            # Format: 20,file_id
            file_id = int(data_list[1])
            await file_transfer_request_task(controller, file_id)
        elif action == 21:
            # Start file receive 
            # Format: 21,file_id,file_name
            file_id = int(data_list[1])
            file_name = data_list[2] if len(data_list) > 2 else None
            print(f"Ready to receive file: ID={file_id}, name={file_name}")
        else:
            print(f"Invalid action: {action}")
        
    await asyncio.sleep_ms(100)

async def not_connected_task(controller):
    await controller.agbot.home()

async def file_transfer_request_task(controller, file_id):
    """Handle file transfer requests"""
    try:
        if file_id == 0:
            # Send memory data (JSON)
            await file_transfer.send_file(controller.memory.data, "JSON", "agbot_data.json")
        elif file_id == 1:
            # Send mission history (CSV)
            data = Utils.get_file_data("mission_history.csv")
            if data:
                await file_transfer.send_file(data, "CSV", "mission_history.csv")
            else:
                print("FT,ERR,File mission_history.csv not found")
        elif file_id == 2:
            # Send moisture readings (CSV)
            data = Utils.get_file_data("moisture_readings.csv")
            if data:
                await file_transfer.send_file(data, "CSV", "moisture_readings.csv")
            else:
                print("FT,ERR,File moisture_readings.csv not found")
        elif file_id == 5:
            # Send water log (CSV)
            data = Utils.get_file_data("water_log.csv")
            if data:
                await file_transfer.send_file(data, "CSV", "water_log.csv")
            else:
                print("FT,ERR,File water_log.csv not found")
        else:
            print(f"FT,ERR,Unknown file ID: {file_id}")
    except Exception as e:
        print(f"FT,ERR,{e}")

async def file_transfer_receive_task(data_list):
    """Handle file transfer reception"""
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
    """Process incoming command from stdin"""
    global last_ping_time, task_movement_ref, task_file_transfer_ref
    
    # Update the last ping time for connection status
    last_ping_time = time.time()
    
    # Parse the command
    if user_input == "ping":
        print("pong")
    elif user_input == "STAP":
        # Stop movement task
        if task_movement_ref and not task_movement_ref.done():
            task_movement_ref.cancel()
            controller.agbot.stop()
            await asyncio.sleep(0)
            print("movement task stopped")
        else:
            print("Movement task is not running.")
    elif user_input.startswith("FT,"):
        # File transfer command
        data_list = user_input.split(",")
        if task_file_transfer_ref is None or task_file_transfer_ref.done():
            task_file_transfer_ref = asyncio.create_task(file_transfer_receive_task(data_list))
        else:
            print("File transfer task already running, please wait.")
    #elif user_input.startswith("20,") or user_input.startswith("21,"):
     #   pass
    #TODO Create a task for file transfer requests
    else: 
        # Standard command
        print(f"Received command: {user_input}")
        if task_movement_ref is None or task_movement_ref.done():
            task_movement_ref = asyncio.create_task(sensor_location_task(controller, user_input))
        else:
            print("Movement task already running.")

async def master_task(controller):
    """Main loop that handles input and manages tasks"""
    print("AgBot serial controller started!")
    global task_movement_ref, task_not_connected_ref, last_ping_time
    buffer = ""
    
    while True:
        # Check connection status
        is_connect = is_connected()
        if not is_connect:
            # Switch to automatic mode when not connected
            if task_movement_ref and not task_movement_ref.done():
                task_movement_ref.cancel()
                controller.agbot.stop()
                await asyncio.sleep(0.1)
                print("Movement cancelled - disconnected")
            
            # Start automatic mode if not already running
            if task_not_connected_ref is None or task_not_connected_ref.done():
                task_not_connected_ref = asyncio.create_task(not_connected_task(controller))
        elif task_not_connected_ref and not task_not_connected_ref.done():
            # Stop automatic mode when connected
            task_not_connected_ref.cancel()
            await asyncio.sleep(0.1)
                
        # Check for serial input
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            char = sys.stdin.read(1)
            if char in ("\n", "\r"):
                user_input = buffer.strip()
                buffer = ""
                if user_input not in ("", " ", "  "):
                    await process_incoming_command(controller, user_input)
            else:
                buffer += char
                
        await asyncio.sleep_ms(10)

async def main():
    try:
        controller = Controller.get_default_controller()
        await master_task(controller)
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
