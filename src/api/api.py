"""

"""
import os
from functools import wraps

import toml
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import Flask
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec.extension import FlaskApiSpec
from flask_apispec.views import MethodResource
from flask_restful import Api
from flask_restplus import abort
from flask_restplus import Resource
from managers import InfluxDB
from managers import SQLiteDB
from managers import USBManager
from packet import off_to_add
from packet import Packet
from station import Station
from webargs.flaskparser import parser
from webargs.flaskparser import use_args

from .schemas import DeviceReadRequestSchema
from .schemas import DevicesResponseSchema
from .schemas import DeviceWriteRequestSchema
from .schemas import ErrorResponseSchema
from .schemas import StationStatusSchema
from .schemas import StatusMessageSchema

toml_config = toml.load(os.environ["TOML_STATION"])

# Initialize and configure the api
app = Flask(toml_config["station"]["name"])
app.url_map.strict_slashes = False
app.config["SECRET_KEY"] = toml_config["station"]["secret_key"]
app.config.update(
    {
        "APISPEC_SPEC": APISpec(
            title="SRAM Acquisition Platform",
            version="1.0",
            description="Control the SRAM Acquisition Station",
            plugins=[MarshmallowPlugin()],
            openapi_version="3.0.0",
        ),
        "APISPEC_SWAGGER_URL": "/api_swagger",
        "APISPEC_SWAGGER_UI_URL": "/api_documentation",
    }
)
api = Api(app)
docs = FlaskApiSpec(app)

# Initialize and configure the station
sqlite = SQLiteDB(toml_config["databases"]["sqlite"])
influxdb = InfluxDB(toml_config["loggers"]["influx"])
usb_manager = USBManager(toml_config["station"])
station = Station(toml_config["station"], usb_manager, sqlite, influxdb)


def reg_and_doc(route, document=True):
    """
    Registers the given route and add it to the swagger documentation.

    If document is True, add the route to the swagger documentation
    """

    def inner(cls):
        @wraps(cls)
        def wrapper(*args):
            global api, docs
            api.add_resource(cls, args[0])
            if args[1]:
                docs.register(cls)

        return wrapper(route, document)

    return inner


@reg_and_doc("/api/status")
class StatusAPI(MethodResource, Resource):
    """Current status of the station"""

    @doc(description="Returns the current status of the station", tags=["Station"])
    @marshal_with(StationStatusSchema, code=200, description="OK")
    @marshal_with(StatusMessageSchema, code=500, description="Station not working")
    def get(self):
        return station.status()


@reg_and_doc("/api/devices")
class DevicesList(MethodResource):
    @doc(
        description="List all devices registered into the the station", tags=["Devices"]
    )
    @marshal_with(DevicesResponseSchema, code=200, description="OK")
    def get(self):
        devices = station.devices
        devices = [d.__dict__ for d in devices]
        return {
            "status": "success",
            "message": "Devices registered in the station",
            "data": devices,
        }


@reg_and_doc("/api/devices/register/<string:device>")
class DeviceRegister(MethodResource, Resource):
    @doc(description="Register a device connected to the station", tags=["Devices"])
    @marshal_with(DevicesResponseSchema, code=200, description="OK")
    @marshal_with(
        StatusMessageSchema, code=422, description="Device not registered or not found"
    )
    @marshal_with(StatusMessageSchema, code=500, description="Station not working")
    def get(self, device):
        is_reg = bool([d for d in station.devices if d.uid == device])
        if not is_reg:
            abort(422, f"Device {device} not found in the list of registered devices")

        packets = station.cmd_ping({"device": device})
        if not packets:
            return {
                "status": "fail",
                "message": f"Device {device} not registered or not found",
            }, 406
        else:
            return {
                "status": "success",
                "message": f"Device {device} found",
                "data": packets,
            }


@reg_and_doc("/api/devices/register")
class DevicesRegister(MethodResource, Resource):
    @doc(description="Register all devices connected to the station", tags=["Devices"])
    @marshal_with(DevicesResponseSchema, code=200, description="OK")
    @marshal_with(
        StatusMessageSchema,
        code=406,
        description="Devices not connected or not registered",
    )
    @marshal_with(StatusMessageSchema, code=500, description="Station not working")
    def get(self):
        packets = station.cmd_ping({})
        if not packets:
            return {
                "status": "fail",
                "message": "Devices not connected or not registered",
            }, 406
        else:
            if not isinstance(packets, list):
                packets = [packets]
            return {
                "status": "success",
                "message": "Devices registered",
                "data": packets,
            }


@reg_and_doc("/api/devices/read")
class DevicesRead(MethodResource, Resource):
    @doc(description="Read a region of memory from a device", tags=["Devices"])
    @use_args(DeviceReadRequestSchema)
    @marshal_with(StatusMessageSchema, code=200)
    def get(self, data):
        config = DeviceReadRequestSchema().load(data)

        device = [d for d in station.devices if d.uid == config["device"]]
        if len(device) < 1:
            return {
                "status": "fail",
                "message": f"Device {config['device']} not found in the list of registered devices",
            }, 400

        res = station.cmd_read(config)
        if not res:
            return {
                "status": "fail",
                "message": "Could not read memory from device",
            }, 400

        address = off_to_add(config["offset"])
        metrics = {
            "measurement": "commands",
            "fields": {"command": "READ"},
            "tags": {
                "user": config.get("token", "TIMA"),
                "device": config["device"],
                "address": address,
            },
        }
        station.insert_sample(res, config)
        station.metrics_log(metrics)
        message = f"Values read from device {config['device']} at {address}"
        return {"status": "success", "message": message}


@reg_and_doc("/api/devices/write")
class DevicesWrite(MethodResource, Resource):
    @doc(description="Write a region of memory to a device", tags=["Devices"])
    @use_args(DeviceWriteRequestSchema)
    @marshal_with(StatusMessageSchema, code=200)
    def post(self, data):
        config = DeviceWriteRequestSchema().load(data)
        device = [d for d in station.devices if d.uid == config["device"]]
        if len(device) < 1:
            return {
                "status": "fail",
                "message": f"Device {config['device']} not found in the list of registered devices",
            }, 400

        max_offset = (device[0].sram_size // Packet.DATA_SIZE) - 1
        if config["offset"] < 6 or config["offset"] > (max_offset - 6):
            return {
                "status": "fail",
                "message": f"Offset should be between 6 and {max_offset - 6}",
            }, 400

        res = station.cmd_write(config)
        address = off_to_add(config["offset"])

        metrics = {
            "measurement": "commands",
            "fields": {"command": "WRITE"},
            "tags": {
                "user": config.get("token", "TIMA"),
                "device": config["device"],
                "address": address,
            },
        }
        station.metrics_log(metrics)
        message = f"Values written to device {config['device']} at {address}"
        return {"status": "success", "message": message}, 200


@reg_and_doc("/api/devices/write/invert")
class DevicesWriteInvert(MethodResource, Resource):
    @doc(
        description="Write the inverted values of the reference sample from a device",
        tags=["Devices"],
    )
    @use_args(DeviceReadRequestSchema)
    @marshal_with(StatusMessageSchema, code=200)
    def get(self, data):
        config = DeviceReadRequestSchema().load(data)
        device = [d for d in station.devices if d.uid == config["device"]]
        if len(device) < 1:
            return {
                "status": "fail",
                "message": f"Device {config['device']} not found in the list of registered devices",
            }, 400

        max_offset = (device[0].sram_size // Packet.DATA_SIZE) - 1
        if config["offset"] < 6 or config["offset"] > (max_offset - 6):
            return {
                "status": "fail",
                "message": f"Offset should be between 6 and {max_offset - 6}",
            }, 400

        config["address"] = off_to_add(config["offset"])
        query = station.query_reference(config)
        if not query:
            message = "Board or offset not found. Read the address of the specified device first"
            return {"status": "fail", "message": message}, 400

        config["data"] = query["data"]
        config["data"] = list(~config["data"])
        res = station.cmd_write(config)

        metrics = {
            "measurement": "commands",
            "fields": {"command": "WRITE_INV"},
            "tags": {
                "user": config.get("token", "TIMA"),
                "device": config["device"],
                "address": config["address"],
            },
        }
        station.metrics_log(metrics)
        message = (
            f'Inverse values written to device {config["device"]}'
            f' at address {config["address"]}'
        )
        return {"status": "success", "message": message}, 200


@reg_and_doc("/api/devices/sensors/<string:device>")
class DevicesSensors(MethodResource, Resource):
    @doc(
        description="Extract the sensor information from the devices", tags=["Devices"]
    )
    def get(self, device):
        dev = [d for d in station.devices if d.uid == device]
        if len(dev) < 1:
            return {
                "status": "fail",
                "message": f"Device {device} not found in the list of registered devices",
            }, 400

        packet = station.cmd_sensors({"device": device})
        if not packet:
            return {
                "status": "fail",
                "message": f"Could not read sensors from device {device}",
            }, 400

        metrics = {
            "measurement": "sensors",
            "fields": {
                "temperature": packet["temperature"],
                "voltage": packet["voltage"],
            },
            "tags": {
                "device": device,
            },
        }
        station.metrics_log(metrics)
        message = "Sensor information extracted from devices"
        return {"status": "success", "message": message, "data": packet}


@reg_and_doc("/api/ports")
class PortsList(MethodResource, Resource):
    @doc(description="List all ports connected into the station", tags=["Ports"])
    def get(self):
        return {"status": "success", "data": station.ports}


@reg_and_doc("/api/ports/register")
class PortsRegister(MethodResource, Resource):
    @doc(description="Register all ports connected into the station", tags=["Ports"])
    def get(self):
        station.initialize()
        return {"status": "success", "message": "Ports registered"}


@reg_and_doc("/api/ports/power_on")
class PortsPowerOn(MethodResource, Resource):
    @doc(description="Power on the selected ports", tags=["Ports"])
    @marshal_with(StatusMessageSchema, code=200, description="OK")
    @marshal_with(
        StatusMessageSchema, code=406, description="Port specified does not exist"
    )
    @marshal_with(StatusMessageSchema, code=500, description="Station not working")
    def get(self):
        station.ports_power_on({})
        return {"status": "success", "message": "Ports powered on"}


@reg_and_doc("/api/ports/power_off")
class PortsPowerOff(MethodResource, Resource):
    @doc(description="Power off the selected ports", tags=["Ports"])
    @marshal_with(StatusMessageSchema, code=200, description="OK")
    @marshal_with(
        StatusMessageSchema, code=406, description="Port specified does not exist"
    )
    @marshal_with(StatusMessageSchema, code=500, description="Station not working")
    def get(self):
        station.ports_power_off({})
        return {"status": "success", "message": "Ports powered off"}


@parser.error_handler
@marshal_with(ErrorResponseSchema)
def handle_request_parsing_error(
    err, req, schema, *args, error_status_code, error_headers
):
    """
    General request parsing error handler.

    When a request cannot be validated, this handler is called with the error information
    """
    abort(400, messages=err.messages["json"], status="fail")


@app.errorhandler(404)
@marshal_with(StatusMessageSchema)
def not_found(arg):
    """
    Handler for a not found request
    """
    return (
        {"status": "fail", "message": "The requested URL was not found on the server"},
        404,
    )


@app.errorhandler(405)
@marshal_with(StatusMessageSchema)
def method_not_valid(arg):
    """
    Handler for a method not valid request
    """
    return (
        {
            "status": "fail",
            "message": "The method is not allowed for the requested URL",
        },
        405,
    )


@app.errorhandler(500)
@marshal_with(StatusMessageSchema)
def server_error(arg):
    """
    Handler for server error request
    """
    return (
        {
            "status": "fail",
            "message": "The is a problem with the server",
        },
        405,
    )
