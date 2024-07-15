import hashlib
import hmac
import json
import logging
from logging import getLogger
from typing import Callable, Optional, cast, Dict
import asyncio
from datetime import datetime, timedelta

from linkkit.linkkit import LinkKit
from paho.mqtt.client import Client, MQTTMessage, MQTTv311, connack_string

from pyluba.data.model.enums import RTKStatus
from pyluba.utility.constant.device_constant import WorkMode, device_mode

from pyluba.data.model import RapidState
from pyluba.data.mqtt.event import ThingEventMessage
from pyluba.data.mqtt.properties import ThingPropertiesMessage
from pyluba.data.mqtt.status import ThingStatusMessage
from pyluba.luba.base import BaseLuba
from pyluba.mammotion.commands.mammotion_command import MammotionCommand
from pyluba.proto import luba_msg_pb2
from pyluba.proto.luba_msg import LubaMsg
import betterproto
from utils.cloud_gateway import CloudIOTGateway
from base64 import b64decode

logger = getLogger(__name__)


# with sqlite3.connect("messages.db") as conn:
#     conn.execute("CREATE TABLE IF NOT EXISTS messages (topic TEXT, timestamp INTEGER, payload TEXT)")


class LubaMQTT(BaseLuba):

    _cloud_client = None
    _mammotionCommand = None

    _isMQTTConnected = False

    _last_status_update = 0

    _statusList : dict[str, LubaMsg]  = {}

    _iotIdsList : dict[str, datetime] = {}

    _tmpIotIdsList = []

    def __init__(self, region_id: str, product_key: str, device_name: str, device_secret: str, iot_token: str,
                 client_id: Optional[str] = None, iotIds = []):
        super().__init__()

        self.on_connected: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_disconnected: Optional[Callable[[], None]] = None


        self._tmpIotIdsList = iotIds
        self._product_key = product_key
        self._device_name = device_name
        self._device_secret = device_secret
        self._iot_token = iot_token
        self._mqtt_username = f"{device_name}&{product_key}"
        # linkkit provides the correct MQTT service for all of this and uses paho under the hood
        if client_id is None:
            client_id = f"python-{device_name}"
        self._mqtt_client_id = f"{client_id}|securemode=2,signmethod=hmacsha1|"
        sign_content = f"clientId{client_id}deviceName{device_name}productKey{product_key}"
        self._mqtt_password = hmac.new(
            device_secret.encode("utf-8"), sign_content.encode("utf-8"),
            hashlib.sha1
        ).hexdigest()

        self._client_id = client_id

        self._linkkit_client = LinkKit(region_id, product_key, device_name, device_secret, auth_type="",
                                       client_id=client_id, password=self._mqtt_password, username=self._mqtt_username)

        self._linkkit_client.enable_logger(level=logging.DEBUG)
        self._linkkit_client.on_connect = self._thing_on_connect
        self._linkkit_client.on_disconnect = self._on_disconnect
        self._linkkit_client.on_thing_enable = self._thing_on_thing_enable
        self._linkkit_client.on_topic_message = self._thing_on_topic_message
        #        self._mqtt_host = "public.itls.eu-central-1.aliyuncs.com"
        self._mqtt_host = f"{self._product_key}.iot-as-mqtt.{region_id}.aliyuncs.com"

        self._client = Client(
            client_id=self._mqtt_client_id,
            protocol=MQTTv311,
        )
        self._client.on_message = self._on_message
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.username_pw_set(self._mqtt_username, self._mqtt_password)
        self._client.enable_logger(logger.getChild("paho"))

    # region Connection handling
    def connect(self):
        logger.info("Connecting...")
        self._client.connect(host=self._mqtt_host)
        self._client.loop_forever()

    def connect_async(self):
        logger.info("Connecting...")
        self._linkkit_client.thing_setup()
        self._linkkit_client.connect_async()
        # self._client.connect_async(host=self._mqtt_host)
        # self._client.loop_start()
        self._linkkit_client.start_worker_loop()

    def disconnect(self):
        logger.info("Disconnecting...")
        self._linkkit_client.disconnect()
        self._client.disconnect()
        self._client.loop_stop()

    def _thing_on_thing_enable(self, user_data):
        print("on_thing_enable")
        # print('subscribe_topic, topic:%s' % echo_topic)
        # self._linkkit_client.subscribe_topic(echo_topic, 0)
        self._linkkit_client.subscribe_topic(f"/sys/{self._product_key}/{self._device_name}/app/down/account/bind_reply")
        self._linkkit_client.subscribe_topic(f"/sys/{self._product_key}/{self._device_name}/app/down/thing/event/property/post_reply")
        self._linkkit_client.subscribe_topic(f"/sys/{self._product_key}/{self._device_name}/app/down/thing/events")
        self._linkkit_client.subscribe_topic(f"/sys/{self._product_key}/{self._device_name}/app/down/thing/status")
        self._linkkit_client.subscribe_topic(f"/sys/{self._product_key}/{self._device_name}/app/down/thing/properties")
        self._linkkit_client.subscribe_topic(f"/sys/{self._product_key}/{self._device_name}/app/down/thing/model/down_raw")

        self._linkkit_client.publish_topic(f"/sys/{self._product_key}/{self._device_name}/app/up/account/bind",
                                           json.dumps({
                                               "id": "msgid1",
                                               "version": "1.0",
                                               "request": {
                                                   "clientId": self._mqtt_username
                                               },
                                               "params": {
                                                   "iotToken": self._iot_token
                                               }
                                           })
                                           )

        # self._linkkit_client.query_ota_firmware()
        self._isMQTTConnected = True
        

    def _thing_on_topic_message(self, topic, payload, qos, user_data):
        print("on_topic_message, receive message, topic:%s, payload:%s, qos:%d" % (topic, payload, qos))
        payload = json.loads(payload)
        logger.debug(f"Payload: {payload}")
        if topic.endswith("/app/down/thing/events"):
            if(payload['method'] == "thing.events"):
                if(payload['params']['identifier'] == "device_protobuf_msg_event" and payload["params"]["deviceName"].startswith(("Luba-", "Yuka-"))):
                    self.parse_luba_message(payload['params']['iotId'], payload['params']['value']['content'])

    def _thing_on_connect(self, session_flag, rc, user_data):
        print("on_connect, session_flag:%d, rc:%d" % (session_flag, rc))

        # self._linkkit_client.subscribe_topic(f"/sys/{self._product_key}/{self._device_name}/#")

    def send_cloud_command(self, iotId: str, command) -> str:
        if (self._isMQTTConnected is False):
            return "Not logged in"
        command = MammotionCommand(device_name="Luba")
        self._cloud_client.send_cloud_command(iotId, command.get_report_cfg())
        return "OK"

    async def send_update_data_periodic(self, interval: int):
        for key in self._tmpIotIdsList:
            self._iotIdsList[key] = datetime.min # imposto last send a 0
        while True:
            logger.debug("TASK aggiornamento dati: numero devices " + str(len(self._iotIdsList)))
            for iot_id, lastUpdate in self._iotIdsList.items():
                if self._cloud_client is not None and self._isMQTTConnected:
                    logger.debug(f"Try send update for {iot_id}")
                    now = datetime.now()
                    if(lastUpdate + timedelta(seconds=10) < now):
                        self._iotIdsList[iot_id] = now + timedelta(seconds=10)
                        command = MammotionCommand(device_name="Luba")
                        self._cloud_client.send_cloud_command(iot_id, command.get_report_cfg())
            await asyncio.sleep(interval)


    def _on_connect(self, _client, _userdata, _flags: dict, rc: int):
        if rc == 0:
            logger.info("Connected")
            self._client.subscribe(f"/sys/{self._product_key}/{self._device_name}/#")
            self._client.subscribe(f"/sys/{self._product_key}/{self._device_name}/app/down/account/bind_reply")

            self._client.publish(f"/sys/{self._product_key}/{self._device_name}/app/up/account/bind",
                                 json.dumps({
                                     "id": "msgid1",
                                     "version": "1.0",
                                     "request": {
                                         "clientId": self._mqtt_username
                                     },
                                     "params": {
                                         "iotToken": self._iot_token
                                     }
                                 })
                                 )

            if self.on_connected:
                self.on_connected()
        else:
            logger.error("Could not connect %s", connack_string(rc))
            if self.on_error:
                self.on_error(connack_string(rc))

    def _on_disconnect(self, _client, _userdata, rc: int):
        logger.info("Disconnected")
        logger.debug(rc)
        if self.on_disconnected:
            self.on_disconnected()

    # endregion

    def _on_message(self, _client, _userdata, message: MQTTMessage):
        logger.info("Message on topic %s", message.topic)
        # with sqlite3.connect("messages.db") as conn:
        #     conn.execute("INSERT INTO messages (topic, timestamp, payload) VALUES (?, ?, ?)",
        #                  (message.topic, int(message.timestamp), message.payload.decode("utf-8")))

        payload = json.loads(message.payload)
        if message.topic.endswith("/app/down/thing/events"):
            event = ThingEventMessage(**payload)
            params = event.params
            if params.identifier == "device_protobuf_msg_event":
                content = cast(luba_msg_pb2, params.value.content)
                if content.WhichOneof("subMsg") == "sys" and content.sys.WhichOneof("subSysMsg") == "systemRapidState":
                    state = RapidState.from_raw(content.sys.systemRapidState.data)
                    self._set_rapid_state(state)
                else:
                    logger.info("Unhandled protobuf event: %s", content.WhichOneof("subMsg"))
            elif params.identifier == "device_warning_event":
                if self.on_warning:
                    self.on_warning(params.value.code)
            else:
                logger.info("Unhandled event: %s", params.identifier)
        elif message.topic.endswith("/app/down/thing/status"):
            status = ThingStatusMessage(**payload)
            self._set_status(status.params.status.value)
        elif message.topic.endswith("/app/down/thing/properties"):
            properties = ThingPropertiesMessage(**payload)
        else:
            logger.info("Unhandled topic: %s", message.topic)
            logger.debug(payload)


    def parse_luba_message(self, iotId: str, contentEncoded: str) -> None:
        raw_data = LubaMsg().to_dict(casing=betterproto.Casing.SNAKE)
        binary = b64decode(contentEncoded, validate=True)
        tmp_msg = LubaMsg.FromString(binary)
        res = betterproto.which_one_of(tmp_msg, "LubaSubMsg")

        match res[0]:
            case "nav":
                nav_sub_msg = betterproto.which_one_of(tmp_msg.nav, "SubNavMsg")
                nav = raw_data.get("nav")
                if nav is None:
                    raw_data["nav"] = {}
                if isinstance(nav_sub_msg[1], int):
                    raw_data["net"][nav_sub_msg[0]] = nav_sub_msg[1]
                else:
                    raw_data["nav"][nav_sub_msg[0]] = nav_sub_msg[1].to_dict(
                        casing=betterproto.Casing.SNAKE
                    )
            case "sys":
                sys_sub_msg = betterproto.which_one_of(tmp_msg.sys, "SubSysMsg")
                sys = raw_data.get("sys")
                if sys is None:
                    raw_data["sys"] = {}
                raw_data["sys"][sys_sub_msg[0]] = sys_sub_msg[1].to_dict(
                    casing=betterproto.Casing.SNAKE
                )
            case "driver":
                drv_sub_msg = betterproto.which_one_of(tmp_msg.driver, "SubDrvMsg")
                drv = raw_data.get("driver")
                if drv is None:
                    raw_data["driver"] = {}
                raw_data["driver"][drv_sub_msg[0]] = drv_sub_msg[1].to_dict(
                    casing=betterproto.Casing.SNAKE
                )
            case "net":
                net_sub_msg = betterproto.which_one_of(tmp_msg.net, "NetSubType")
                net = raw_data.get("net")
                if net is None:
                    raw_data["net"] = {}
                if isinstance(net_sub_msg[1], int):
                    raw_data["net"][net_sub_msg[0]] = net_sub_msg[1]
                else:
                    raw_data["net"][net_sub_msg[0]] = net_sub_msg[1].to_dict(
                        casing=betterproto.Casing.SNAKE
                    )
            case "mul":
                mul_sub_msg = betterproto.which_one_of(tmp_msg.mul, "SubMul")
                mul = raw_data.get("mul")
                if mul is None:
                    raw_data["mul"] = {}
                raw_data["mul"][mul_sub_msg[0]] = mul_sub_msg[1].to_dict(
                    casing=betterproto.Casing.SNAKE
                )
            case "ota":
                ota_sub_msg = betterproto.which_one_of(tmp_msg.ota, "SubOtaMsg")
                ota = raw_data.get("ota")
                if ota is None:
                    raw_data["ota"] = {}
                raw_data["ota"][ota_sub_msg[0]] = ota_sub_msg[1].to_dict(
                    casing=betterproto.Casing.SNAKE
                )
        logger.debug("Parsing ok")
        self._statusList[iotId] = LubaMsg().from_dict(raw_data)
    
    def get_device_status_by_iotId(self, iotId: str, format:str = None) -> str:
        if(iotId in self._statusList):
            if format is not None:
                data = self._statusList[iotId]
                if format == "human":
                    device = {
                        "battery_status": f"{str(data.sys.toapp_report_data.dev.battery_val)}%" + (" (Charging)" if data.sys.toapp_report_data.dev.charge_state == 1 else ""),
                        "wifiRSSI": f"{str(data.sys.toapp_report_data.connect.wifi_rssi)}dBm",
                        "bleRSSI": f"{str(data.sys.toapp_report_data.connect.ble_rssi)}dBm",
                        "robot_status": device_mode(data.sys.toapp_report_data.dev.sys_status)
                    }
                    rtk = {
                        "pos_status": str(RTKStatus.from_value(data.sys.toapp_report_data.rtk.status)),
                        "robot_sat": str(data.sys.toapp_report_data.rtk.gps_stars),
                        "ref_station_sat": str(int(data.sys.toapp_report_data.rtk.dis_status) >> 16 & 255) + "L1 " + str(int(data.sys.toapp_report_data.rtk.dis_status) >> 24 & 255) + "L2",
                        "co_view_sat" : str(int(data.sys.toapp_report_data.rtk.co_view_stars) >> 0 & 255) + "L1 " + str(int(data.sys.toapp_report_data.rtk.co_view_stars) >> 8 & 255) + "L2",
                        "signal_quality_robot": "", #toDo
                        "signal_quality_ref_station": "", #toDo
                        "lora_status": "Connected" if data.sys.toapp_report_data.rtk.lora_info.lora_connection_status == 1 else "Disconnected",
                        "lora_number": str(data.sys.toapp_report_data.rtk.lora_info.pair_code_scan) + "." + str(data.sys.toapp_report_data.rtk.lora_info.pair_code_channel) + "." + str(data.sys.toapp_report_data.rtk.lora_info.pair_code_locid) + "." + str(data.sys.toapp_report_data.rtk.lora_info.pair_code_netid),
                    }
                    location = {}

                    if len(data.sys.toapp_report_data.locations) > 0:
                        loc = data.sys.toapp_report_data.locations[0]
                        loc.real_pos_x
                        location = {
                            "lat": str(self.get_parse_double_data(loc.real_pos_x, 4)),
                            "lon": str(self.get_parse_double_data(loc.real_pos_y, 4)),
                        }
                    work = {}

                    if(data.sys.toapp_report_data.dev.sys_status >= 13 and data.sys.toapp_report_data.dev.sys_status <= 19):
                        work = {
                            "total_area": str(data.sys.toapp_report_data.work.area & 65535) + "m²",
                            "mowing_speed": str(data.sys.toapp_report_data.work.man_run_speed / 100) + "m/s",
                            "progress": str(data.sys.toapp_report_data.work.area >> 16) + "%",
                            "total_time": str(data.sys.toapp_report_data.work.progress & 65535) + "min",
                            "elapsed_time": str((data.sys.toapp_report_data.work.progress & 65535) - (data.sys.toapp_report_data.work.progress >> 16)) + "min",
                            "left_time": str(data.sys.toapp_report_data.work.progress >> 16)+ "min",
                            "blade_height": str(data.sys.toapp_report_data.work.knife_height)+ "mm"
                        }

                    content = {
                        "device": device,
                        "rtk": rtk,
                        "location": location,
                        "work": work,
                    }

                    return json.dumps(content)
            return self._statusList[iotId].to_json()
        else:
            return "{}"

    def get_parse_double_data(self, value, digits):
        """Converte un intero in un float con un numero specifico di cifre decimali."""
        format_string = f"{{:.{digits}f}}"
        return float(format_string.format(value))