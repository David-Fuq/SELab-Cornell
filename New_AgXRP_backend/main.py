# File helpers
from controller import Controller

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


def is_connected():
    return (time.time() - last_ping_time) < connection_timeout


# This is a task that waits for writes from the client
# and updates the sensor location.
async def sensor_location_task(controller, data):
    
    print("EN SENSOR LOCATION")
    data_list = data.split(",")
    cmd = data_list[0]
    ##connection, data = await sensor_desired_location_characteristic.written()
    #print("Received desired position data: ", data)
    if data is not None:
        # Action types (2 bytes uint16)
        # 0 = Stop
        # 1 = Move to absolute position
        # 2 = probe at current position
        # 3 = Move to home position
        # 4 = Turn on pump of a certain amount
        # 5 = run mission by id
        #    - 2 bytes for mission id uint16
        # 6 = re-calibrate gantry size
        # 7 = change mission details by id
        # 8 = delete mission by id
        #    - 2 bytes for mission id uint16
        # 9 = delete plant by id
        #    - 2 bytes for plant id uint16
        # Grab the fisrt byte of the data to determine the action
        #action = struct.unpack("<H", data[:2])[0]
        #print("Mission action:", action)
        if cmd == "ping":
            print("pong")
        action = int(cmd)
        if action == 0:
            controller.agbot.stop()
        elif action == 1:
            #_, x, y, _, _ = struct.unpack("<HHHHH", data)
            #print("Moving to: ", x, y)
            x = data_list[1]
            y = data_list[2]
            await controller.agbot.move_to(int(x), int(y))
        elif action == 2:
            print("Probing...")
            moisture_reading = await controller.agbot.read()
            print("J")
            print("Moisture reading: ", moisture_reading)
            print("X")

        elif action == 3:
            await controller.agbot.home()
        elif action == 5:
            mission_id = struct.unpack("<H", data[2:4])[0]
            print("Running mission: ", mission_id)
            await controller.run_mission(mission_id=mission_id)
        elif action == 6:
            print("Recalibrating gantry size")
            await controller.setup_xy_max(force=True)
            # move to 20, 20
            await controller.agbot.move_to(20, 20)
        elif action == 8:
            mission_id = struct.unpack("<H", data[2:4])[0]
            print("Deleting mission: ", mission_id)
            controller.memory.delete_mission(mission_id)
        elif action == 9:
            plant_id = struct.unpack("<H", data[2:4])[0]    
            print("Deleting plant: ", plant_id)
            controller.memory.delete_plant(plant_id)
        elif action == 10:
            # add / remove plant from mission
            # 2 bytes for mission id uint16
            # 2 bytes for plant id uint16
            # 1 byte for add / remove
            #     0 = add
            #     1 = remove
            data = struct.unpack("<HHH", data[2:])
            if data[2]:
                print("Adding plant to mission", data)
                controller.memory.add_plant_to_mission(data[0], data[1])
            else:
                print("Removing plant from mission")
                controller.memory.remove_plant_from_mission(data[0], data[1])
        elif action == 11:
            print("Getting gantry size from argot_data.json")
            await controller.setup_xy_max(force=False)
            # move to 20, 20
            await controller.agbot.move_to(20, 20)
        else:
            print("Invalid action")
        
        
    await asyncio.sleep_ms(100) 

async def not_connected_task(controller):
    controller.agbot.home()

async def master_task(controller):
    print("Holiwis!")
    global task_movement_ref, task_not_connected_ref, last_ping_time
    buffer = ""
    is_connect = is_connected()
    while True:
        #Automatic mode
        is_connect = is_connected()
        if not is_connect:
            print("Start automatic mode")
            print("Cancelling movement task if necessary")
            if task_movement_ref and not task_movement_ref.done():
                task_movement_ref.cancel()
                controller.agbot.stop()
                await asyncio.sleep(0.1)
                print("Movement cancelled")
            else:
                print("No movement atm")            
            task_not_connected_ref = asyncio.create_task(not_connected_task(controller))
            
        #Manual mode
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            #Keepalive
            # Read character by character without blocking the loop
            # This allows the loop to continue running while waiting for input
            # and also allows the loop to process other tasks.

            # Stop manual mode if the controller is connected
            if is_connect:
                if task_not_connected_ref and not task_not_connected_ref.done():
                    print("Stopping not connected task (Auto mode)...")
                    task_not_connected_ref.cancel()
                    await asyncio.sleep(0.1)
                #else: 
                    #print("Auto mode off atm")
                           

            char = sys.stdin.read(1)
            if char in ("\n", "\r"):
                user_input = buffer.strip()
                buffer = ""
                if user_input not in ("", " ", "  "):
                    last_ping_time = time.time()
                    is_connect = is_connected()
                    if user_input == "ping":
                        print("pong")
                    elif user_input == "STAP":
                        print("Stopping movement task...")
                        print(task_movement_ref)
                        print(task_movement_ref.done())
                        if task_movement_ref and not task_movement_ref.done():
                            task_movement_ref.cancel()
                            controller.agbot.stop()
                            await asyncio.sleep(0)
                            print("movement task stopped")
                        else:
                            print("Movement task is not running.")
                    else: 
                        print("Received command: ", user_input)
                        if task_movement_ref is None or task_movement_ref.done():
                            print("Starting movement task...")
                            task_movement_ref = asyncio.create_task(sensor_location_task(controller, user_input))
                            print("After callind sensor_location")
                        else:
                            print("Movement task already running.")
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
        print("Error: ", e)
        controller.agbot.stop()
        Utils.append_error_to_log(str(e))
        machine.reset()
        
# Run the main function
if __name__ == "__main__":
    asyncio.run(main())

