from flask import Flask, jsonify
import threading
import json
import time

from utils.account import AccountUtils

class WebServer:
    def __init__(self):
        self.app = Flask(__name__)
        self._setup_routes()
        self.thread = None
        self.running = False
        self.account_utils = AccountUtils()

    def _setup_routes(self):
        @self.app.route('/api/<string:iotId>/status', methods=['GET'])
        def get_status_by_iotId(iotId):
            if(self.account_utils.is_login() == False):
                return jsonify({"error": "Not logget in"}), 404
            if(self.account_utils.iotId_exist(iotId) == False):
                return jsonify({"error": "IotId not found"}), 404
            if(self.account_utils._lubaMQTT._isMQTTConnected == False):
                return jsonify({"error": "MQTT not connected"}), 404
            return jsonify(json.loads(self.account_utils._lubaMQTT.get_device_status_by_iotId(iotId)))

        @self.app.route('/api/devices', methods=['GET'])
        def get_devices():
            if(self.account_utils.is_login() == False):
                return jsonify({"error": "Not logget in"}), 404
            if(self.account_utils._lubaMQTT._isMQTTConnected == False):
                return jsonify({"error": "MQTT not connected"}), 404
            if(self.account_utils._lubaMQTT._isMQTTConnected == False):
                return jsonify({"error": "MQTT not connected"}), 404
            return jsonify(self.account_utils.get_device_list())
            

    def run(self):
        self.app.run(debug=True, use_reloader=False)

    def start(self):
        if self.thread is None:
            self.thread = threading.Thread(target=self.run)
            self.thread.start()
            self.running = True
        

    def stop(self):
        self.running = False



