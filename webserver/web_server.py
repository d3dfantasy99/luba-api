from flask import Flask, jsonify, render_template, request, session, redirect, url_for
import threading
import json
import time
from pymammotion.mammotion.commands.mammotion_command import MammotionCommand

from utils.account import AccountUtils

class WebServer:
    def __init__(self):
        self.app = Flask(
            __name__,
            template_folder='htdocs/templates', 
            static_folder='htdocs/static',
            static_url_path='/static'
        )
        self.app.secret_key = '81ac3226b77cce9cd203a5e2c7b5d35a62838b98111d6cc4'
        self._setup_routes()
        self.thread = None
        self.running = False
        self.account_utils = AccountUtils()

    def _setup_routes(self):
        @self.app.route('/api/<string:iotId>/command', methods=['POST'])
        async def send_command_to_device(iotId):
            if(self.account_utils.is_login() == False):
                return jsonify({"status": False, "data": {}, "error": "Not logget in"}), 401
            if(self.account_utils.iotId_exist(iotId) == False):
                return jsonify({"status": False, "data": {}, "error": "IotId not found"}), 404
            
            device_name, device = self.account_utils.get_mammotion_cloud_device_by_iotId(iotId)
            cmd = request.form['cmd']
            if cmd:
                match cmd:
                    case 'recharge':
                        mammontionCommand = MammotionCommand(device_name=device_name).return_to_dock()
                        await self.account_utils.async_send_command(device_name, "return_to_dock")
                        return jsonify({"status": True, "data": {}, "error": ""}), 200
                    case 'cancel_recharge':
                        mammontionCommand = MammotionCommand(device_name=device_name).cancel_return_to_dock()
                        await self.account_utils.async_send_command(device_name, mammontionCommand)
                        return jsonify({"status": True, "data": {}, "error": ""}), 200
                    case 'end_job':
                        mammontionCommand = MammotionCommand(device_name=device_name).cancel_job()
                        await self.account_utils.async_send_command(device_name, mammontionCommand)
                        return jsonify({"status": True, "data": {}, "error": ""}), 200
                    case 'pause_job':
                        mammontionCommand = MammotionCommand(device_name=device_name).pause_execute_task()
                        await self.account_utils.async_send_command(device_name, mammontionCommand)
                        return jsonify({"status": True, "data": {}, "error": ""}), 200
                    case 'resume_job':
                        mammontionCommand = MammotionCommand(device_name=device_name).resume_execute_task()
                        await self.account_utils.async_send_command(device_name, mammontionCommand)
                        return jsonify({"status": True, "data": {}, "error": ""}), 200
                    case 'leave_dock':
                        mammontionCommand = MammotionCommand(ddevice_name=device_name).leave_dock()
                        await self.account_utils.async_send_command(device_name, "leave_dock")
                        return jsonify({"status": True, "data": {}, "error": ""}), 200
                    case 'start_fpv':
                        mammontionCommand = MammotionCommand(device_name=device_name).device_agora_join_channel_with_position(1)
                        await self.account_utils.async_send_command(device_name, mammontionCommand)
                        return jsonify({"status": True, "data": {}, "error": ""}), 200
                    case 'stop_fpv':
                        mammontionCommand = MammotionCommand(device_name=device_name).device_agora_join_channel_with_position(0)
                        await self.account_utils.async_send_command(device_name, mammontionCommand)
                        return jsonify({"status": True, "data": {}, "error": ""}), 200
                    case 'set_blade_control':
                        param = request.form['value']
                        if param == None or param == "":
                            return jsonify({"status": False, "data": {}, "error": "Missing param"}), 500
                        if(int(param) != 0 and int(param) != 1):
                            return jsonify({"status": False, "data": {}, "error": "incorrect param - Or 0 or 1"}), 500
                        mammontionCommand = MammotionCommand(device_name=device_name).set_blade_control(int(param))
                        await self.account_utils.async_send_command(device_name, mammontionCommand)
                        return jsonify({"status": True, "data": {}, "error": ""}), 200
                    case 'set_sidelight':
                        param = request.form['value']
                        if param == None or param == "":
                            return jsonify({"status": False, "data": {}, "error": "Missing param"}), 500
                        if(int(param) != 0 and int(param) != 1):
                            return jsonify({"status": False, "data": {}, "error": "incorrect param - Or 0 or 1"}), 500
                        mammontionCommand = MammotionCommand(device_name=device_name).read_and_set_sidelight(True if int(param) == 1 else False, 1)
                        await self.account_utils.async_send_command(device_name, mammontionCommand)
                        return jsonify({"status": True, "data": {}, "error": ""}), 200
                    
            return jsonify({"status": False, "data": {}, "error": "Command missing or not found"}), 404
        
        @self.app.route('/<string:iotId>/map', methods=['GET'])
        def map_by_iotId(iotId):
            if(self.account_utils.is_login() == False):
                return jsonify({"status": False, "data": {}, "error": "Not logget in"}), 401
            if(self.account_utils.iotId_exist(iotId) == False):
                return jsonify({"status": False, "data": {}, "error": "IotId not found"}), 404
            device = self.account_utils.get_device_by_iotId(iotId)
            return render_template('map.html.twig', device=device)
        
        @self.app.route('/<string:iotId>', methods=['GET'])
        def dashboard_by_iotId(iotId):

            if(self.account_utils.is_login() == False):
                return jsonify({"status": False, "data": {}, "error": "Not logget in"}), 401
            if(self.account_utils.iotId_exist(iotId) == False):
                return jsonify({"status": False, "data": {}, "error": "IotId not found"}), 404
            device = self.account_utils.get_device_by_iotId(iotId)

            imagePath = ""
            if(device.get('deviceName','').startswith(("Luba-VS"))):
                imagePath = "newui_icon_main_bg_car_pro.png"
            elif (device.get('deviceName','').startswith(("Luba-"))):
                imagePath = "newui_icon_main_bg_car.png"
            elif (device.get('deviceName','').startswith(("Yuka-"))):
                imagePath = "newui_type_yuka.png"
            else:
                imagePath = "newui_icon_main_bg_rtk.png"
            
            return render_template('index.html.twig', device=device, imagePath=imagePath)

        

        @self.app.route('/api/<string:iotId>/status', methods=['GET'])
        def get_status_by_iotId(iotId):
            if(self.account_utils.is_login() == False):
                return jsonify({"status": False, "data": {}, "error": "Not logget in"}), 401
            if(self.account_utils.iotId_exist(iotId) == False):
                return jsonify({"status": False, "data": {}, "error": "IotId not found"}), 404
            format = request.args.get('format')
            if format:
                if format == "human":
                    out = {
                        "status" : True,
                        "error" : "",
                        "data" : json.loads(self.account_utils.get_device_status_by_iotId(iotId, format=format))
                    }
                    return jsonify(out)  
            out = {
                    "status" : True,
                    "error" : "",
                    "data" : json.loads(self.account_utils.get_device_status_by_iotId(iotId, format=None))
                }
            return jsonify(out)


        @self.app.route('/api/devices', methods=['GET'])
        def get_devices():
            if(self.account_utils.is_login() == False):
                return jsonify({"status": False, "data": [], "error": "Not logget in"}), 404
            out = {
                "status" : True,
                "error" : "",
                "data" : self.account_utils.get_device_list()
            }
            return jsonify(out)
            

    def run(self):
        self.app.run(host="0.0.0.0", debug=True, use_reloader=False, port=5000)

    def start(self):
        if self.thread is None:
            self.thread = threading.Thread(target=self.run)
            self.thread.start()
            self.running = True
        

    def stop(self):
        self.running = False



