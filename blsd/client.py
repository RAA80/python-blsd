#! /usr/bin/env python3

"""Реализация класса клиента для управления контроллером BLSD."""

from __future__ import annotations

import logging
from functools import reduce

from serial import Serial

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())


class BlsdError(Exception):
    pass


class Client:
    """Класс клиента для управления контроллером BLSD."""

    def __init__(self, port: str, unit: int, timeout: float = 1.0) -> None:
        """Инициализация класса клиента с указанными параметрами."""

        self.socket = Serial(port=port, timeout=timeout)
        self.port = port
        self.unit = unit

    def __repr__(self) -> str:
        """Строковое представление объекта."""

        return f"{type(self).__name__}(port={self.port}, unit={self.unit})"

    def __del__(self) -> None:
        """Закрытие соединения с устройством при удалении объекта."""

        if self.socket:
            self.socket.close()

    @staticmethod
    def _fast_calc(byte: int, crc: int) -> int:
        """Вычисление значения полинома."""

        return reduce(lambda crc, i: (crc ^ 0x18) >> 1 | 0x80
                      if (crc ^ byte >> i) & 1 else crc >> 1, range(8), crc)

    def _blsd_crc(self, data: tuple[int, ...]) -> int:
        """Алгоритм вычисления контрольной суммы."""

        return reduce(lambda crc, val: self._fast_calc(val, crc), data, 0)

    def _make_packet(self, command: int, value: int | None = None) -> bytes:
        """Формирование пакета для записи."""

        data = () if value is None else (value,)
        msg = (self.unit, command, *data)
        crc = self._blsd_crc(msg)
        return bytes((0xE6, *msg, crc))

    def _bus_exchange(self, packet: bytes) -> bytes:
        """Обмен по интерфейсу."""

        self.socket.reset_input_buffer()
        self.socket.reset_output_buffer()

        self.socket.write(packet)
        return self.socket.read(5)

    def _send_massage(self, command: int, value: int | None = None) -> bytes:
        """Послать команду в устройство."""

        packet = self._make_packet(command, value)
        _logger.debug("Send frame = %r", list(packet))

        answer = self._bus_exchange(packet)
        _logger.debug("Recv frame = %r", list(answer))

        return answer

    def set_address(self, value: int) -> bool:
        """Установка нового адреса блока."""

        if value not in range(255):
            msg = "Value must be in range from 0 to 254"
            raise BlsdError(msg)
        return bool(self._send_massage(command=0xA0, value=value))

    def release_address(self) -> None:
        """Отбой установки нового адреса блока."""

        self._send_massage(command=0xA1, value=0)

    def set_pulse_per_turn(self, value: int) -> bool:
        """Установка числа импульсов Холла на оборот."""

        if value not in range(256):
            msg = "Value must be in range from 0 to 255"
            raise BlsdError(msg)
        return bool(self._send_massage(command=0xA2, value=value))

    def set_speed(self, value: int) -> bool:
        """Установка скорости движения (об/сек)."""

        if value not in range(251):
            msg = "Value must be in range from 0 to 250"
            raise BlsdError(msg)
        return bool(self._send_massage(command=0xA3, value=value))

    def set_max_speed(self, value: int) -> bool:
        """Установка максимальной скорости движения (об/сек)."""

        if value not in range(251):
            msg = "Value must be in range from 0 to 250"
            raise BlsdError(msg)
        return bool(self._send_massage(command=0xA4, value=value))

    def set_acceleration(self, value: int) -> bool:
        """Установка ускорения движения."""

        if value not in range(1, 25):
            msg = "Value must be in range from 1 to 24"
            raise BlsdError(msg)
        return bool(self._send_massage(command=0xA5, value=value))

    def set_slowdown(self, value: int) -> bool:
        """Установка торможения движения."""

        if value not in range(1, 25):
            msg = "Value must be in range from 1 to 24"
            raise BlsdError(msg)
        return bool(self._send_massage(command=0xA6, value=value))

    def set_direction(self, value: int) -> bool:
        """Установка направления движения."""

        if value not in range(2):
            msg = "Value must be in range from 0 to 1"
            raise BlsdError(msg)
        return bool(self._send_massage(command=0xA7, value=value))

    def get_state(self) -> dict[str, int]:
        """Опрос состояния."""

        state = self._send_massage(command=0x50, value=None)
        return {"synchro": state[1] >> 7 & 1,
                "overflow": state[1] >> 6 & 1,
                "default": state[1] >> 5 & 1,
                "direction": state[1] >> 4 & 1,
                "turn": ((state[1] & 0xF) << 8) + state[2],
                "speed": state[3],
               }

    def start_move(self) -> bool:
        """Запуск двигателя."""

        return bool(self._send_massage(command=0x51, value=0))

    def stop_move(self) -> bool:
        """Остановка двигателя."""

        return bool(self._send_massage(command=0x52, value=0))
