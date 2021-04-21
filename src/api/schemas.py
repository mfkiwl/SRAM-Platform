#!/usr/bin/env python3
from marshmallow import fields
from marshmallow import post_load
from marshmallow import Schema
from marshmallow import validate

from packet import Packet


class StatusMessageSchema(Schema):
    status = fields.String(
        description="Execution status. Can be either success or fail"
    )
    message = fields.String(
        description="Informative message about the process carried out"
    )


class DeviceReadRequestSchema(Schema):
    device = fields.String(
        required=True,
        description="Hex string representation of the device",
        validate=validate.Length(max=24),
    )
    offset = fields.Integer(
        required=True,
        description="Offset to read from memory",
        validate=validate.Range(min=-1, max=9999),
    )

    @post_load
    def make_config(self, args, **kwargs):
        return args


class DeviceWriteRequestSchema(DeviceReadRequestSchema):
    data = fields.List(
        fields.Int(),
        required=True,
        description="List of bytes to write",
        validate=validate.Length(equal=Packet.DATA_SIZE),
    )


class PortInfo(Schema):
    port = fields.String(description="Path to the port in use")
    state = fields.String(description="State of the port. Can be either ON or OFF")


class DeviceInfo(Schema):
    device = fields.String(
        description="Hex string representation of the device internal ID"
    )
    pic = fields.Integer(description="Position In the Chain of the device")
    state = fields.String(description="Whether the device is ON or OFF")
    sram_size = fields.Integer(description="Size in bytes of the device internal SRAM")


class ErrorResponseSchema(Schema):
    status = fields.String(
        description="Execution status. Can be either success or fail"
    )
    messages = fields.List(fields.String(description="Error message"))


class DevicesResponseSchema(StatusMessageSchema):
    data = fields.List(fields.Nested(DeviceInfo()))


class StationStatusSchema(Schema):
    uptime = fields.DateTime(description="UTC time when the station was created")
    ports = fields.List(fields.Nested(PortInfo()))
    devices = fields.List(fields.Nested(DeviceInfo()))
