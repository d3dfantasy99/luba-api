import asyncio
import logging
import os
import traceback
import json

from aiohttp import ClientSession
from typing import List

from pymammotion import MammotionHTTP
from pymammotion.aliyun.cloud_gateway import CloudIOTGateway
from pymammotion.const import MAMMOTION_DOMAIN
from pymammotion.mammotion.commands.mammotion_command import MammotionCommand
from pymammotion.mqtt.mammotion_mqtt import MammotionMQTT, logger

from pymammotion.http.http import Response as MammotionLoginResponse
from pymammotion.mammotion.devices.mammotion import MammotionBaseCloudDevice

from pymammotion.data.model.enums import RTKStatus
from pymammotion.utility.constant.device_constant import WorkMode, device_mode

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
            self._initialized = True
    
    def is_login(self) -> bool:
        if (self._mammotionMQTT is None):
            return False
        
    def iotId_exist(self, iotId: str):
        device = next((device for device in self._devices_list if device.iot_id == iotId), None)
        return True if device else False
    
    def get_device_list(self):
        # Esempio di dati di dispositivi ottenuti dinamicamente
        device_list = []
        
        # Esempio di aggiunta dinamica di dati di dispositivi
        for device in self._mammotionMQTT._cloud_client._listing_dev_by_account_response.data.data:
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
        device = next((device for device in self._devices_list if device.iot_id == iotId), None)
        return device
    
    def get_device_by_iotId(self, iotId: str):
        # Esempio di dati di dispositivi ottenuti dinamicamente
        device = None
        
        # Esempio di aggiunta dinamica di dati di dispositivi
        for device in self._mammotionMQTT._cloud_client._listing_dev_by_account_response.data.data:
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
        mammotionDevice = next((device for device in self._devices_list if device.iot_id == iotId), None)
        if mammotionDevice:
            if format is not None:
                if format == "human":
                    device = {
                        "battery_status": f"{str(mammotionDevice.mower.device.sys.toapp_report_data.dev.battery_val)}%" + (" (Charging)" if mammotionDevice.mower.device.sys.toapp_report_data.dev.charge_state == 1 else ""),
                        "wifiRSSI": f"{str(mammotionDevice.mower.device.sys.toapp_report_data.connect.wifi_rssi)}dBm",
                        "bleRSSI": f"{str(mammotionDevice.mower.device.sys.toapp_report_data.connect.ble_rssi)}dBm",
                        "robot_status": device_mode(mammotionDevice.mower.device.sys.toapp_report_data.dev.sys_status)
                    }
                    rtk = {
                        "pos_status": str(RTKStatus.from_value(mammotionDevice.mower.device.sys.toapp_report_data.rtk.status)),
                        "robot_sat": str(mammotionDevice.mower.device.sys.toapp_report_data.rtk.gps_stars),
                        "ref_station_sat": str(int(mammotionDevice.mower.device.sys.toapp_report_data.rtk.dis_status) >> 16 & 255) + "L1 " + str(int(mammotionDevice.mower.device.sys.toapp_report_data.rtk.dis_status) >> 24 & 255) + "L2",
                        "co_view_sat" : str(int(mammotionDevice.mower.device.sys.toapp_report_data.rtk.co_view_stars) >> 0 & 255) + "L1 " + str(int(mammotionDevice.mower.device.sys.toapp_report_data.rtk.co_view_stars) >> 8 & 255) + "L2",
                        "signal_quality_robot": "", #toDo
                        "signal_quality_ref_station": "", #toDo
                        "lora_status": "Connected" if mammotionDevice.mower.device.sys.toapp_report_data.rtk.lora_info.lora_connection_status == 1 else "Disconnected",
                        "lora_number": str(mammotionDevice.mower.device.sys.toapp_report_data.rtk.lora_info.pair_code_scan) + "." + str(data.sys.toapp_report_data.rtk.lora_info.pair_code_channel) + "." + str(data.sys.toapp_report_data.rtk.lora_info.pair_code_locid) + "." + str(data.sys.toapp_report_data.rtk.lora_info.pair_code_netid),
                    }
                    location = {}

                    if len(mammotionDevice.mower.device.sys.toapp_report_data.locations) > 0:
                        loc = mammotionDevice.mower.device.sys.toapp_report_data.locations[0]
                        loc.real_pos_x
                        location = {
                            "lat": str(self.get_parse_double_data(loc.real_pos_x, 4)),
                            "lon": str(self.get_parse_double_data(loc.real_pos_y, 4)),
                        }
                    work = {}

                    if(mammotionDevice.mower.device.sys.toapp_report_data.dev.sys_status >= 13 and mammotionDevice.mower.device.sys.toapp_report_data.dev.sys_status <= 19):
                        work = {
                            "total_area": str(mammotionDevice.mower.device.sys.toapp_report_data.work.area & 65535) + "m²",
                            "mowing_speed": str(mammotionDevice.mower.device.sys.toapp_report_data.work.man_run_speed / 100) + "m/s",
                            "progress": str(mammotionDevice.mower.device.sys.toapp_report_data.work.area >> 16) + "%",
                            "total_time": str(mammotionDevice.mower.device.sys.toapp_report_data.work.progress & 65535) + "min",
                            "elapsed_time": str((mammotionDevice.mower.device.sys.toapp_report_data.work.progress & 65535) - (mammotionDevice.mower.device.sys.toapp_report_data.work.progress >> 16)) + "min",
                            "left_time": str(mammotionDevice.mower.device.sys.toapp_report_data.work.progress >> 16)+ "min",
                            "blade_height": str(mammotionDevice.mower.device.sys.toapp_report_data.work.knife_height)+ "mm"
                        }

                    content = {
                        "device": device,
                        "rtk": rtk,
                        "location": location,
                        "work": work,
                    }

                    return json.dumps(content)
            return mammotionDevice.mower.device.to_json()
        else:
            return "{}"

    def get_parse_double_data(self, value, digits):
        """Converte un intero in un float con un numero specifico di cifre decimali."""
        format_string = f"{{:.{digits}f}}"
        return float(format_string.format(value))
    
    async def send_update_data_periodic(self, interval: int):
        while True:
            logger.debug("TASK aggiornamento dati: numero devices " + str(len(self._devices_list)))
            for device in self._devices_list:
                if self._mammotionMQTT._cloud_client is not None:
                    logger.debug(f"Try send update for {device.iot_id}")
                    await device.start_sync(0) 
            await asyncio.sleep(interval)
            
    
    async def login(self, email: str, password: str) -> bool:
        if (self._mammotionMQTT is not None):
            self._mammotionMQTT.disconnect()
        try:
            async with ClientSession(MAMMOTION_DOMAIN) as session:
                    cloud_client = CloudIOTGateway()
                    luba_http = await MammotionHTTP.login(session, email, password)
                    country_code = luba_http.data.userInformation.domainAbbreviation
                    logger.debug("CountryCode: " + country_code)
                    logger.debug("AuthCode: " + luba_http.data.authorization_code)
                    cloud_client.get_region(country_code, luba_http.data.authorization_code)
                    await cloud_client.connect()
                    await cloud_client.login_by_oauth(country_code, luba_http.data.authorization_code)
                    cloud_client.aep_handle()
                    cloud_client.session_by_auth_code()
                    cloud_client.list_binding_by_account()

                    
                    iotIds = []
                    for device in self.get_device_list_init(cloud_client._listing_dev_by_account_response):
                        iotIds.append(device.get('iotID'))
                    


                    self._mammotionMQTT = MammotionMQTT(region_id=cloud_client._region.data.regionId,
                        product_key=cloud_client._aep_response.data.productKey,
                        device_name=cloud_client._aep_response.data.deviceName,
                        device_secret=cloud_client._aep_response.data.deviceSecret, iot_token=cloud_client._session_by_authcode_response.data.iotToken, client_id=cloud_client._client_id)

                    self._mammotionMQTT._cloud_client = cloud_client
                    #luba.connect() blocks further calls
                    self._mammotionMQTT.connect_async()

                    self._devices_list: List[MammotionBaseCloudDevice] = []
                    for device in cloud_client._listing_dev_by_account_response.data.data:
                        if(device.deviceName.startswith(("Luba-", "Yuka-"))):
                            dev = MammotionBaseCloudDevice (
                                mqtt_client=self._mammotionMQTT,
                                iot_id=device.iotId,
                                device_name=device.deviceName,
                                nick_name=device.nickName
                            )
                            self._devices_list.append(dev)
                    return True
        except Exception as ex:
            logger.error(f"{ex}")
            logger.error(traceback.format_exc())
            return False
