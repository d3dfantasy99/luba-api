import asyncio
import logging
import os
import traceback
import json

from aiohttp import ClientSession
from typing import List

from pymammotion import MammotionHTTP
from pymammotion.http.http import connect_http
from pymammotion.mammotion.devices.mammotion import MammotionMixedDeviceManager
from pymammotion.aliyun.cloud_gateway import CloudIOTGateway
from pymammotion.const import MAMMOTION_DOMAIN
from pymammotion.mammotion.commands.mammotion_command import MammotionCommand
from pymammotion.mqtt.mammotion_mqtt import MammotionMQTT, logger

from pymammotion.http.http import Response as MammotionLoginResponse
from pymammotion.mammotion.devices.mammotion import MammotionBaseCloudDevice

from pymammotion.data.model.enums import RTKStatus
from pymammotion.utility.constant.device_constant import WorkMode, device_mode
from pymammotion.data.model.device import MowingDevice
from pymammotion.proto.mctrl_sys import RptAct, RptInfoType
from pymammotion.mammotion.devices.mammotion import create_devices, ConnectionPreference, Mammotion
from pymammotion.data.model.account import Credentials

class AccountUtils:
    _instance = None
    _devices_list: List[MammotionBaseCloudDevice] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AccountUtils, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):  # Prevent reinitialization
            self._mammotionMQTT : MammotionMQTT = None
            self._devices_list: List[MammotionBaseCloudDevice] = None
            self._mammotion : Mammotion =  None
            self._initialized = True
    
    def is_login(self) -> bool:
        if self._mammotion is not None:
                if self._mammotion.mqtt.is_ready:
                    return True
        return False
        
    def iotId_exist(self, iotId: str):
        for device_name , device  in self._mammotion.devices.devices.items():
            if device.cloud().iot_id == iotId:
                return True
        return False
    
    def get_device_list(self):
        # Esempio di dati di dispositivi ottenuti dinamicamente
        device_list = []
        
        # Esempio di aggiunta dinamica di dati di dispositivi
        for device in self._mammotion.cloud_client.get_devices_by_account_response().data.data:
            if(device.deviceName.startswith(("Luba-", "Yuka-"))):
                device_name = f"{device.deviceName}"
                nick_name = f"{device.nickName}"
                iot_id = f"{device.iotId}"
                status = "Online" if int(device.status) == 1 else "Offline"
                device_list.append({
                    "deviceName": device_name,
                    "nick_name": nick_name,
                    "iotID": iot_id,
                    "status": status,
                    "online": True if int(device.status) == 1 else False
                })
        
        return device_list
    
    def get_mammotion_cloud_device_by_iotId(self, iotId: str): 
        for device_name , device  in self._mammotion.devices.devices.items():
                if device.cloud().iot_id == iotId:
                    return device_name, device
        return None, None
    
    def get_device_by_iotId(self, iotId: str):
        # Esempio di dati di dispositivi ottenuti dinamicamente
        device = None
        
        # Esempio di aggiunta dinamica di dati di dispositivi
        for device in self._mammotion.cloud_client.get_devices_by_account_response().data.data:
            if(device.iotId == iotId):
                device_name = f"{device.deviceName}"
                nick_name = f"{device.nickName}"
                product_model = f"{device.productModel}"
                product_key = f"{device.productKey}"
                iot_id = f"{device.iotId}"
                status = "Online" if int(device.status) == 1 else "Offline"
                device = {
                    "deviceName": device_name,
                    "nick_name": nick_name,
                    "productModel": product_model,
                    "productKey": product_key,
                    "iotID": iot_id,
                    "status": status
                }
                return device
        
        return device
    
    def get_device_list_init(self, listing_dev_by_account_response):
        # Esempio di dati di dispositivi ottenuti dinamicamente
        device_list = []
        
        # Esempio di aggiunta dinamica di dati di dispositivi
        for device in listing_dev_by_account_response.data.data:
            if(device.deviceName.startswith(("Luba-", "Yuka-"))):
                device_name = f"{device.deviceName}"
                nick_name = f"{device.nickName}"
                iot_id = f"{device.iotId}"
                status = "Online" if int(device.status) == 1 else "Offline"
                device_list.append({
                    "deviceName": device_name,
                    "nick_name": nick_name,
                    "iotID": iot_id,
                    "status": status
                })
        logger.debug(device_list)
        return device_list
    
    def get_device_status_by_iotId(self, iotId: str, format:str = None) -> str:
        mammotionDevice: MammotionMixedDeviceManager = None
        deviceName: str = None
        for device_name , device  in self._mammotion.devices.devices.items():
            if device.cloud().iot_id == iotId:
                mammotionDevice = device
                deviceName = device_name
                break
        if mammotionDevice:
            if format is not None:
                if format == "human":
                    device = {
                        "battery_status": f"{str(mammotionDevice.mower_state().report_data.dev.battery_val)}%" + (" (Charging)" if mammotionDevice.mower_state().report_data.dev.charge_state == 1 else ""),
                        "wifiRSSI": f"{str(mammotionDevice.mower_state().report_data.connect.wifi_rssi)}dBm",
                        "bleRSSI": f"{str(mammotionDevice.mower_state().report_data.connect.ble_rssi)}dBm",
                        "robot_status": device_mode(mammotionDevice.mower_state().report_data.dev.sys_status)
                    }
                    rtk = {
                        "pos_status": str(RTKStatus.from_value(mammotionDevice.mower_state().report_data.rtk.status)),
                        "robot_sat": str(mammotionDevice.mower_state().report_data.rtk.gps_stars),
                        "ref_station_sat": "", #str(int(mammotionDevice.mower_state().report_data.rtk.dis_status) >> 16 & 255) + "L1 " + str(int(mammotionDevice.mower_state().report_data.rtk.dis_status) >> 24 & 255) + "L2",
                        "co_view_sat" : str(int(mammotionDevice.mower_state().report_data.rtk.co_view_stars) >> 0 & 255) + "L1 " + str(int(mammotionDevice.mower_state().report_data.rtk.co_view_stars) >> 8 & 255) + "L2",
                        "signal_quality_robot": "", #toDo
                        "signal_quality_ref_station": "", #toDo
                        "lora_status": "Connected" if mammotionDevice.mower_state().report_data.rtk.status == 1 else "Disconnected",
                        "lora_number": "",
                    }
                    location = {}

                    if len(mammotionDevice.mower_state().report_data.locations) > 0:
                        loc = mammotionDevice.mower_state().report_data.locations[0]
                        loc.real_pos_x
                        location = {
                            "lat": str(self.get_parse_double_data(loc.real_pos_x, 4)),
                            "lon": str(self.get_parse_double_data(loc.real_pos_y, 4)),
                        }
                    work = {}

                    if(mammotionDevice.mower_state().report_data.dev.sys_status >= 13 and mammotionDevice.mower_state().report_data.dev.sys_status <= 19):
                        work = {
                            "total_area": str(mammotionDevice.mower_state().report_data.work.area & 65535) + "m²",
                            "mowing_speed": str(mammotionDevice.mower_state().report_data.work.man_run_speed / 100) + "m/s",
                            "progress": str(mammotionDevice.mower_state().report_data.work.area >> 16) + "%",
                            "total_time": str(mammotionDevice.mower_state().report_data.work.progress & 65535) + "min",
                            "elapsed_time": str((mammotionDevice.mower_state().report_data.work.progress & 65535) - (mammotionDevice.mower_state().report_data.work.progress >> 16)) + "min",
                            "left_time": str(mammotionDevice.mower_state().report_data.work.progress >> 16)+ "min",
                            "blade_height": str(mammotionDevice.mower_state().report_data.work.knife_height)+ "mm"
                        }

                    content = {
                        "device": device,
                        "rtk": rtk,
                        "location": location,
                        "work": work,
                    }

                    return json.dumps(content)
            return mammotionDevice.mower_state().device.to_json()
        else:
            return "{}"

    def get_parse_double_data(self, value, digits):
        """Converte un intero in un float con un numero specifico di cifre decimali."""
        format_string = f"{{:.{digits}f}}"
        return float(format_string.format(value))
    
    async def async_send_command(self, device_name: str, command: str, **kwargs: any) -> None:
        try:
            await self._mammotion.send_command_with_args(
                device_name, command, **kwargs
            )
        except Exception as exc:
            pass
    
    async def async_request_iot_sync(self, device_name: str) -> None:
        await self.async_send_command(
            device_name,
            "request_iot_sys",
            rpt_act=RptAct.RPT_START,
            rpt_info_type=[
                RptInfoType.RIT_CONNECT,
                RptInfoType.RIT_DEV_STA,
                RptInfoType.RIT_DEV_LOCAL,
                RptInfoType.RIT_RTK,
                RptInfoType.RIT_WORK,
            ],
            timeout=1000,
            period=3000,
            no_change_period=4000,
            count=0,
        )
    
    async def send_update_data_periodic(self, interval: int):
        while True:          
            if self._mammotion is not None:
                if self._mammotion.mqtt.is_ready:
                    logger.debug("TASK aggiornamento dati: numero devices " + str(len(self._mammotion.devices.devices)))
                    for device_name , device  in self._mammotion.devices.devices.items():
                        if (
                            len(device.mower_state().net.toapp_devinfo_resp.resp_ids) == 0
                            or device.mower_state().net.toapp_wifi_iot_status.productkey is None
                        ):
                            await self._mammotion.start_sync(device_name, 0)
                        if device.mower_state().report_data.dev.sys_status != WorkMode.MODE_WORKING:
                            await self.async_send_command(device_name, "get_report_cfg")

                        else:
                            await self.async_request_iot_sync(device_name)
            await asyncio.sleep(interval)
            
    
    async def login(self, email: str, password: str) -> bool:
        try:
            credentials = Credentials(
            email=email,
            password=password
            )   
            self._mammotion = await create_devices(ble_device=None, cloud_credentials=credentials, preference=ConnectionPreference.WIFI)
            
            return True
        except Exception as ex:
            logger.error(f"{ex}")
            logger.error(traceback.format_exc())
            return False
