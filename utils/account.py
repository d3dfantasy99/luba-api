import asyncio
import logging
import os
import traceback

from aiohttp import ClientSession

from pyluba import LubaHTTP
from utils.cloud_gateway import CloudIOTGateway
from pyluba.const import MAMMOTION_DOMAIN
from pyluba.mammotion.commands.mammotion_command import MammotionCommand
from utils.luba_mqtt import LubaMQTT, logger

from pyluba.http.http import Response as MammotionLoginResponse

class AccountUtils:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AccountUtils, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):  # Prevent reinitialization
            self._lubaMQTT = None
            self._initialized = True
    
    def is_login(self) -> bool:
        if (self._lubaMQTT is None):
            return False
        
    def iotId_exist(self, iotId: str):
        for device in self._lubaMQTT._cloud_client._listing_dev_by_account_response.data.data:
            if(device.iotId == iotId):
                return True
        return False
    
    def get_device_list(self):
        # Esempio di dati di dispositivi ottenuti dinamicamente
        device_list = []
        
        # Esempio di aggiunta dinamica di dati di dispositivi
        for device in self._lubaMQTT._cloud_client._listing_dev_by_account_response.data.data:
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
        
        return device_list
    
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
        print(device_list)
        return device_list
    
    async def login(self, email: str, password: str) -> bool:
        if (self._lubaMQTT is not None):
            self._lubaMQTT.disconnect()
        try:
            async with ClientSession(MAMMOTION_DOMAIN) as session:
                    cloud_client = CloudIOTGateway()
                    luba_http = await LubaHTTP.login(session, email, password)
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
                    


                    self._lubaMQTT = LubaMQTT(region_id=cloud_client._region.data.regionId,
                        product_key=cloud_client._aep_response.data.productKey,
                        device_name=cloud_client._aep_response.data.deviceName,
                        device_secret=cloud_client._aep_response.data.deviceSecret, iot_token=cloud_client._session_by_authcode_response.data.iotToken, client_id=cloud_client._client_id, iotIds = iotIds)

                    self._lubaMQTT._cloud_client = cloud_client
                    #luba.connect() blocks further calls
                    self._lubaMQTT.connect_async()
                    return True
        except Exception as ex:
            logger.error(f"{ex}")
            logger.error(traceback.format_exc())
            return False
