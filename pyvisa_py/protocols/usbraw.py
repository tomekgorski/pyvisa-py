# -*- coding: utf-8 -*-
"""Implements Session to control USB Raw devices

Loosely based on PyUSBTMC:python module to handle
USB-TMC(Test and Measurement class) devices. by Noboru Yamamot, Accl. Lab, KEK, JAPAN

This file is an offspring of the Lantz Project.

:copyright: 2014-2020 by PyVISA-py Authors, see AUTHORS for more details.
:license: MIT, see LICENSE for more details.

"""
from .usbtmc import USBRaw as USBRaw
from .usbutil import find_devices, find_interfaces


def find_raw_devices(
    vendor=None, product=None, serial_number=None, custom_match=None, **kwargs
):
    """Find connected USB RAW devices. See usbutil.find_devices for more info."""

    def is_usbraw(dev):
        if custom_match and not custom_match(dev):
            return False
        return bool(find_interfaces(dev, bInterfaceClass=0xFF, bInterfaceSubClass=0x00))

    return find_devices(vendor, product, serial_number, is_usbraw, **kwargs)


class USBRawDevice(USBRaw):

    RECV_CHUNK = 1024**2

    find_devices = staticmethod(find_raw_devices)

    def __init__(self, vendor=None, product=None, serial_number=None, **kwargs):
        super(USBRawDevice, self).__init__(vendor, product, serial_number, **kwargs)

        if not (self.usb_recv_ep and self.usb_send_ep):
            raise ValueError(
                "USBRAW device must have both Bulk-In and Bulk-out endpoints."
            )

    def write(self, data):
        """Send raw bytes to the instrument.

        :param data: bytes to be sent to the instrument
        :type data: bytes
        """

        begin, end, size = 0, 0, len(data)
        bytes_sent = 0

        raw_write = super(USBRawDevice, self).write

        while not end > size:
            begin = end
            end = begin + self.RECV_CHUNK
            bytes_sent += raw_write(data[begin:end])

        return bytes_sent

    def read(self, size):
        """Read raw bytes from the instrument.

        :param size: amount of bytes to be sent to the instrument
        :type size: integer
        :return: received bytes
        :return type: bytes
        """

        raw_read = super(USBRawDevice, self).read

        received = bytearray()

        while not len(received) >= size:
            resp = raw_read(self.RECV_CHUNK)

            received.extend(resp)

        return bytes(received)

    def control_transfer(self, request_type_bitmap_field, request_id, request_value=0, index=0, data_or_wlength=None):
        """Performs a USB control pipe transfer from the device.
        :param request_type_bitmap_field: bmRequestType parameter of the setup stage of a USB control transfer.
        :param request_id: bRequest parameter of the setup stage of a USB control transfer.
        :param request_value: wValue parameter of the setup stage of a USB control transfer.
        :param index: wIndex parameter of the setup stage of a USB control transfer.
                      This is usually the index of the interface or endpoint.
        :param data_or_wlength: wLength parameter of the setup stage of a USB control transfer.
                       This value also specifies the size of the data buffer to receive the data from the
                       optional data stage of the control transfer.
        :return: - The data buffer that receives the data from the optional data stage of the control transfer
                 - return value of the library call.
        :rtype: - bytes
                - :class:`pyvisa.constants.StatusCode`
        """

        return self.usb_dev.ctrl_transfer(request_type_bitmap_field, request_id, request_value, index, data_or_wlength)
