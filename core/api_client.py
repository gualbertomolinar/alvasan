import requests
import pandas as pd
from django import db
from django.conf import settings
from cryptography.fernet import Fernet
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor

import io

class ExternalAPIClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ExternalAPIClient, cls).__new__(cls)
            cls._instance.session = cls._instance._setup_session()
            cls._instance.config = {}
        return cls._instance

    def _setup_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _load_config(self):
        # Evitamos importar modelos al inicio para prevenir importaciones circulares
        from cfg.models import Cfg
        keys = ["Cookie", "Base_Url", "url_obtenerLista", "login_url", "url_lista", "usr", "pwd"]
        self.config = {c.clave: c.valor for c in Cfg.objects.filter(clave__in=keys)}
        
        cipher_suite = Fernet(settings.KEY_CH)
        if "pwd" in self.config:
            self.config["pwd"] = cipher_suite.decrypt(self.config["pwd"]).decode('utf-8')

    def login(self):
        self._load_config()
        base_url = self.config.get("Base_Url", "").rstrip('/')
        login_url = f"{base_url}/{self.config.get('login_url')}"
        
        payload = {"j_username": self.config.get('usr'), "j_password": self.config.get('pwd')}
        headers = {"Content-Type": "application/json; charset=utf-8", "User-Agent": "Python-Client"}
        
        response = self.session.post(login_url, params=payload, timeout=15)
        response.raise_for_status()
        return True

    def fetch_detalle(self, url, params):
        """Función auxiliar para el ThreadPool"""
        try:
            res = self.session.get(url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                # Verifica si la clave exacta es esta, a veces cambia según el piLis
                detalle = data.get("dsPrecios", {}).get("ePrecios", [])
                return detalle
            else:
                print(f"Error {res.status_code} en params {params}")
                return []
        except Exception as e:
            print(f"Excepción en hilo: {e}")
            return []
        
    def post_data(self, endpoint, json_payload):
        """Método genérico para POST que ya incluye headers y sesión"""
        base_url = self.config.get("Base_Url", "").rstrip('/')
        url = f"{base_url}/{endpoint.lstrip('/')}"
        
        # No necesitas pasar 'Cookie' manualmente, self.session ya las tiene del login()
        response = self.session.post(url, json=json_payload, timeout=20)
        response.raise_for_status()
        return response.json()

    def download_file(self, relative_url):
        base_url = self.config.get("Base_Url", "").rstrip('/')
        url = f"{base_url}/{relative_url.lstrip('/')}"
        response = self.session.get(url, timeout=60, stream=True)
        response.raise_for_status()
        # Retornamos BytesIO para que el archivo sea buscable (seekable)
        return io.BytesIO(response.content)


