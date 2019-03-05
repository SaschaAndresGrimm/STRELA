import logging
import requests
import time
import json

__author__ = "SasG"
__date__ = "27/02/19"
__version__ = "0.1"
__reviewer__ = ""

class Client():
    def __init__(self, ip, port=80, verbosity=0):
        self.ip = ip
        self.port = port
        self._verbosity = verbosity

    def query(self, module, task, param, key=None, timeout=5, returnContent=False):
        url = self._getURL(module, task, param)
        try:
            if key is not None:
                resp = requests.put(url, json={"value":key}, timeout=timeout)
            else:
                resp = requests.get(url, timeout=timeout)
            logging.debug(resp)
            if resp.status_code == 200:
                if returnContent:
                    return resp.content
                else:
                    return resp.json()
            else:
                logging.error("status code {}: {}".format(resp.status_code, resp.content))
                return None

        except Exception as e:
            logging.error("requesting {} with param {}. Error: {}".format(url,key,e))
            if self._verbosity > 1:
                logging.error(str(e))
            return None

    def _getURL(self, module, task, param, api="1.6.0"):
        return "http://{0}/{1}/api/{2}/{3}/{4}".format(self.ip, module, api, task, param)

    def listFiles(self):
        files = self.query("filewriter","data","")
        if files:
            return {file:self._getURL("filewriter", "data", file)
                for file in files["value"]}
        else:
            return {}
