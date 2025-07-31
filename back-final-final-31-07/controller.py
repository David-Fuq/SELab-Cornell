from agbot import AgBot
from agbot_memory import AgBotMemory
import time
import machine
from agbot_file_util import Utils

import uasyncio as asyncio
#from clock import Clock

class Controller():
    @classmethod
    def get_default_controller(cls):
        memory = AgBotMemory.get_default_agbotmemory()
        agBot = AgBot.get_default_agbot()
        rtc = machine.RTC()
        #(year, month, day, weekday, hours, minutes, seconds, subseconds)
        #rtc.datetime((2025, 7, 16, 0, 13, 8, 33, 36))
        #rtc.datetime((2025, 6, 1, 14, 20, 30, 0, 0))
        #clock = Clock.get_default_clock()
        return Controller(memory, agBot, rtc) 
    
    def __init__(self,
                 memory: AgBotMemory,
                 agbot: AgBot,
                 rtc):
        self.rtc = rtc
        self.memory = memory
        self.agbot = agbot
        
        self.agbot.stop()
        
    async def setup_xy_max(self, force=False):
        ## sets gantry endstops
        
        x_stored, y_stored = self.memory.get_gantry_size()
        
        ## if the endstops are not stored yet, find them and store them
        if (x_stored == 0 and y_stored == 0) or force:
            print("XY gantry size not stored yet. Finding it now")
            await self.agbot.home()
            x_max, y_max = await self.agbot.find_size()
            self.memory.set_gantry_size(x_max, y_max)
        x_stored, y_stored = self.memory.get_gantry_size()
        
        ## tell the gantry object what the endstops are
        self.agbot.xy.x_max = x_stored
        self.agbot.xy.y_max = y_stored
         
    async def routine(self, entry_time):
        plant_names = self.memory.get_plant_names()
        readings = {}
        for plant in plant_names:
            ### move to moisture sensing spot
            probe_site = self.memory.get_plant_sense_spot(plant)
            self.agbot.move_to(probe_site[0], probe_site[1])
            
            # read moisture level
            moisture_reading = self.agbot.read()
            moisure_threshold = self.memory.get_moisture_threshold(plant)
            water_amount = 0
            if moisture_reading < moisure_threshold:

                # if moisutre is below threshold, water the plant
                # move there
                water_site = self.memory.get_plant_water_spot(plant)
                self.agbot.move_to(water_site[0], water_site[1])
                # water
                water_amount = self.memory.get_plant_ml_response(plant)
                self.agbot.water(water_amount)
                Utils.log_watering(plant, water_amount)
                
            # log plant reading and water amount
            readings[plant] = [moisture_reading, water_amount]
        # log readings & save
        if entry_time is not None:
            self.memory.data["readings"][entry_time] = readings
        self.memory.save()
        
        # go back home
        self.agbot.home()
    
    def log_string_from_reading(self, date, x, y, reading):
        return date + "," + str(int(x)) + "," + str(int(y)) + "," + str(reading)

    async def run_mission(self, date=None, mission_id=0, date_from_pc=None):
        # Step 1: Move to each location
        # Step 2: Sense the moisture
        # Repeat for all locations in mission
        #`Step 3: Move back home
        mission = self.memory.get_mission(mission_id)

        if date is None and date_from_pc is None:
            time_local = self.rtc.datetime()
            if time_local is not None:
                year, month, day, weekday, hour, minute, second, microsecond = self.rtc.datetime()
                print(second, minute, hour, weekday, month, day, year)
                date = Utils.reading_name_from_time(month, day, year, hour, minute, second)
            else:
                print("Error: Could not get time")
                return
        elif date_from_pc is not None:
            year, month, day, weekday, hours, minutes, seconds, subseconds = date_from_pc
            self.rtc.datetime((year, month, day, weekday, hours, minutes, seconds, subseconds))
            time_local = self.rtc.datetime()
            if time_local is not None:
                year, month, day, weekday, hour, minute, second, microsecond = self.rtc.datetime()
                print(second, minute, hour, weekday, month, day, year)
                date = Utils.reading_name_from_time(month, day, year, hour, minute, second)
            else:
                print("Error: Could not get time")
                return
            
            
            
        if mission is not None:
            for location in mission.get("locations", []):
                print("Sensing moisture at: ", location)
                cordiantes = self.memory.get_plant_sense_spot(location)
                if cordiantes is None:
                    print("Plant not found in memory")
                    continue
                
                print("Cordinates: ", cordiantes)
                await self.agbot.move_to(cordiantes[0], cordiantes[1])
                moisture_reading = await self.agbot.read()
                reading_string = self.log_string_from_reading(date,
                                                              cordiantes[0],
                                                              cordiantes[1],
                                                              moisture_reading)

                moisure_threshold = self.memory.get_moisture_threshold(location)
                water_amount = 0
                print("Moisture reading: ", moisture_reading)
                print("Moisture threshold: ", moisure_threshold)
                if moisture_reading < moisure_threshold:
                    print("Watering plant: ", location)
                    # if moisutre is below threshold, water the plant
                    # move there
                    water_site = self.memory.get_plant_water_spot(location)
                    await self.agbot.move_to(water_site[0], water_site[1])

                    # water
                    water_amount = self.memory.get_plant_ml_response(location)
                    await self.agbot.water(water_amount)
                    water_reading_string = self.log_string_from_reading(date,
                                                                        water_site[0],
                                                                        water_site[1],
                                                                        water_amount)
                    print("Watering: ", water_reading_string)
                    Utils.append_reading_to_csv("water_log.csv", water_reading_string)	


                print("String to log: ", reading_string)
                Utils.append_reading_to_csv("moisture_readings.csv", reading_string)

            # Step 3: Move back home
            await self.agbot.move_to(10, 10)

    async def run(self, datetime_from_pc=None):
        """
        Run the scheduled routine
        This function will run the routine at scheduled times
        """
        print("Hello from controller.run")
        missions = self.memory.get_missions()
        mission_history = Utils.get_mission_history()
        for m in mission_history:
            print("Mission history: ", m)

        print("Mission times: ")
        for mission in missions:                
            print("\t", mission["type"], "at", mission["time"][0], mission["time"][1])

        await self.agbot.home()
        print("Despues de homing")
        await asyncio.sleep(1)
        await self.setup_xy_max()
        print("Despues de xymax")
        await asyncio.sleep(1)
        await self.agbot.move_to(20, 20)
        print("Antes del while")
        
        if datetime_from_pc is not None:
            year, month, day, weekday, hours, minutes, seconds, subseconds = datetime_from_pc
            self.rtc.datetime((year, month, day, weekday, hours, minutes, seconds, subseconds))
        while True:
            # get the time
            print("Despues de agbot.move_to(20,20)")
            time_local = self.rtc.datetime()
            print(time_local)
            if time_local is None:
                print("Error: Could not get time")
                await asyncio.sleep(30)
                continue
            print("Antes de tupla")
            year, month, day, weekday, hour, minute, second, microsecond = self.rtc.datetime()
            fecha_string = str(year)+str(month)+str(day)+str(hour)+str(minute)+str(second)
            print("Despues de tupla")
            fecha_log = f"{year}/{month}/{day} {hour}:{minute}:{second}"
            Utils.append_reading_to_csv("hora_procesos.csv", fecha_log)
            print("Fecha evaluada", fecha_log)
            print(second, minute, hour, weekday, month, day, year)
            date = Utils.reading_name_from_time(month, day, year, hour, minute, second)
            print(date)
            
            i = 0
            for mission in missions:
                i += 1
                print("Lectura de mision", i)
                mission_compeleted = False
                for past_mission in mission_history:
                    print("For past_mission in mission_history")
                    if past_mission[0] == mission["mission_id"]:
                        # Mission has already been run today
                        if past_mission[1] == day and past_mission[2] == month and past_mission[3] == year-2000:
                            mission_compeleted = True
                            break
                
                # If its is past mission time, run the mission
                if (mission_compeleted == False) and (mission["time"][0] == int(hour) and mission["time"][1] <= int(minute) or \
                    mission["time"][0] < int(hour)):
                    # we run the mission if it is within 5 minutes of the scheduled time
                    # if the mission has not been completed
                    print("Running mission: ", mission["type"])
                    if mission["type"] == "sense_moisture":
                        await self.run_mission(date, mission["mission_id"])
                        mission_history.append([mission["mission_id"], day, month, year-2000, hour, minute])
                        Utils.append_mission_to_history(mission["mission_id"], day, month, year, hour, minute)
            print("Antes del await")
            await asyncio.sleep(30)
            print("Despues del await")
            
    async def water_manually(self, water_amount):
        print("En water manually")
        await self.agbot.water(water_amount)
        
          
    def manual(self):
        while True:
            print()
            print("1. Agbot Controls")
            print("2. Memory Controls")
            print("3. Clock Controls")
            print("4. Run Scheduled")
            print("5. Run Routine")
            print("6. Water 10 ml")
            print("7. Exit")
            choice = int(input("Enter choice: "))
            if choice == 1:
                self.agbot.manual()
            elif choice == 2:
                self.memory.manual()
            #elif choice == 3:
                #self.clock.manual()
            elif choice == 4:
                self.run()
            elif choice == 5:
                self.routine(None)
            elif choice == 6:
                await self.water_manually(10)
            elif choice == 7:
                break
            else:
                print("Invalid choice")
