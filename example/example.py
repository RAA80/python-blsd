#! /usr/bin/env python3

"""Пример использования библиотеки."""

import logging
from time import sleep

from blsd.client import Client

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    client = Client(port="COM5", unit=0)
    print(client)

    print(f"set_pulse_per_turn = {client.set_pulse_per_turn(value=255)}")
    print(f"set_speed = {client.set_speed(value=100)}")
    print(f"set_max_speed = {client.set_max_speed(value=250)}")
    print(f"set_acceleration = {client.set_acceleration(value=10)}")
    print(f"set_slowdown = {client.set_slowdown(value=10)}")
    print(f"set_direction = {client.set_direction(value=1)}")

    print(f"start_move = {client.start_move()}")
    sleep(5)
    print(f"stop_move = {client.stop_move()}")
