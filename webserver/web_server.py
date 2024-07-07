from flask import Flask, jsonify, render_template, request
import threading
import json
import time

from utils.account import AccountUtils

class WebServer:
    def __init__(self):
        self.app = Flask(
            __name__,
            template_folder='htdocs/templates', 
            static_folder='htdocs/static',
            static_url_path='/static'
        )
        self._setup_routes()
        self.thread = None
        self.running = False
        self.account_utils = AccountUtils()

    def _setup_routes(self):
        @self.app.route('/<string:iotId>', methods=['GET'])
        def dashboard_by_iotId(iotId):
            if(self.account_utils.is_login() == False):
                return jsonify({"status": False, "data": {}, "error": "Not logget in"}), 404
            if(self.account_utils.iotId_exist(iotId) == False):
                return jsonify({"status": False, "data": {}, "error": "IotId not found"}), 404
            if(self.account_utils._lubaMQTT._isMQTTConnected == False):
                return jsonify({"status": False, "data": {}, "error": "MQTT not connected"}), 404
            device = self.account_utils.get_device_by_iotId(iotId)
            return render_template('index.html', device=device)


        @self.app.route('/api/<string:iotId>/status', methods=['GET'])
        def get_status_by_iotId(iotId):
            if(self.account_utils.is_login() == False):
                return jsonify({"status": False, "data": {}, "error": "Not logget in"}), 404
            if(self.account_utils.iotId_exist(iotId) == False):
                return jsonify({"status": False, "data": {}, "error": "IotId not found"}), 404
            if(self.account_utils._lubaMQTT._isMQTTConnected == False):
                return jsonify({"status": False, "data": {}, "error": "MQTT not connected"}), 404
            format = request.args.get('format')
            if format:
                if format == "human":
                    out = {
                        "status" : True,
                        "error" : "",
                        "data" : json.loads(self.account_utils._lubaMQTT.get_device_status_by_iotId(iotId, format=format))
                    }
                    return jsonify(out)  
            out = {
                    "status" : True,
                    "error" : "",
                    "data" : json.loads(self.account_utils._lubaMQTT.get_device_status_by_iotId(iotId, format=None))
                }
            return jsonify(out)


        @self.app.route('/api/devices', methods=['GET'])
        def get_devices():
            if(self.account_utils.is_login() == False):
                return jsonify({"status": False, "data": [], "error": "Not logget in"}), 404
            if(self.account_utils._lubaMQTT._isMQTTConnected == False):
                return jsonify({"status": False, "data": [], "error": "MQTT not connected"}), 404
            if(self.account_utils._lubaMQTT._isMQTTConnected == False):
                return jsonify({"status": False, "data": [], "error": "MQTT not connected"}), 404
            out = {
                "status" : True,
                "error" : "",
                "data" : self.account_utils.get_device_list()
            }
            return jsonify(out)
            

    def run(self):
        self.app.run(debug=True, use_reloader=False, port=5000)

    def start(self):
        if self.thread is None:
            self.thread = threading.Thread(target=self.run)
            self.thread.start()
            self.running = True
        

    def stop(self):
        self.running = False



