import uasyncio as asyncio
import sys

task_2_ref = None
task_3_ref = None

async def task_2():
    try:
        while True:
            print("hello from task 2")
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("task 2 stopped")

async def task_3():
    try:
        while True:
            print("hello from task 3")
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("task 3 stopped")

async def task_1():
    global task_2_ref
    global task_3_ref
    buffer = ""

    while True:
        # Leer carácter por carácter sin bloquear el loop
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            char = sys.stdin.read(1)
            if char in ("\n", "\r"):
                user_input = buffer.strip()
                buffer = ""

                if user_input == "A":
                    if task_2_ref is None or task_2_ref.done():
                        print("Starting task 2...")
                        task_2_ref = asyncio.create_task(task_2())
                    else:
                        print("task 2 already running.")
                elif user_input == "B":
                    if task_2_ref and not task_2_ref.done():
                        print("Stopping task 2...")
                        task_2_ref.cancel()
                        await asyncio.sleep(0)
                    else:
                        print("task 2 is not running.")
                elif user_input == "C":
                    if task_3_ref is None or task_3_ref.done():
                        print("Starting task 3...")
                        task_3_ref = asyncio.create_task(task_3())
                    else:
                        print("task 3 already running.")
                elif user_input == "D":
                    if task_3_ref and not task_3_ref.done():
                        print("Stopping task 3...")
                        task_3_ref.cancel()
                        await asyncio.sleep(0)
                    else:
                        print("task 3 is not running.")
                else:
                    print("Unknown command: ", user_input)
            else:
                buffer += char
        await asyncio.sleep(0.1)  # Cede tiempo al event loop

async def main():
    await task_1()

import select
asyncio.run(main())
