import os 
from common.logger import printe 
from config.dotenv_loader import load_project_dotenv
from config.opt_file import load_yaml 

load_project_dotenv()

CONF_DIR = os.path.dirname(__file__) 

__all__ = [ 
    'settings_conf' 
] 


class RedisArgs: 
    host = None 
    port = None 
    db = None 
    password = None 


class Settings(object): 

    def __init__(self): 
        self.env = os.environ.get('DJANGO_ENV', 'debug') 
        printe(f"当前环境: {self.env}") 
        self._settings_debug = 'settings_debug.yaml' 
        self._settings_pro = 'settings_pro.yaml' 
        self._settings_test = 'settings_test.yaml' 
        self._settings_room_pro = 'settings_room_pro.yaml' 

        self.config = self._load_config() 

        # 核心配置加载
        self.mysql_config = self._load_database_config('database') 
        self.redis_config = self._load_redis_config('redis')
        # 根据环境变量判断是否开启 debug 模式
        self.debug = True if self.env == 'debug' else False
        self.allowed_hosts = self.config.get('allowed_hosts', ['*'])

    def _load_config(self): 
        name = { 
            "debug": self._settings_debug, 
            "production": self._settings_pro, 
            "pro": self._settings_pro, 
            "test": self._settings_test, 
            "room_pro": self._settings_room_pro, 
        }.get(self.env, self._settings_debug) 
        file_name = os.path.join(CONF_DIR, name) 
        if os.path.exists(file_name): 
            return load_yaml(file_name) 
        else: 
            raise Exception(f'没有可用的配置文件:{file_name}') 

    def _load_database_config(self, name): 
        ret = self.config.get(name, None) 
        if ret is None: 
            raise Exception(f'没有可用{name}的配置!') 
        return ret 

    def _load_redis_config(self, name): 
        ret = self.config.get(name, None) 
        if ret is None: 
            return None
        conf = RedisArgs() 
        conf.host = ret.get("host") 
        conf.port = ret.get("port") 
        conf.db = ret.get("db") 
        conf.password = ret.get("password") 
        return conf 

    @property
    def redis_url(self):
        conf = self.redis_config
        if not conf:
            return os.environ.get('CELERY_BROKER_URL', 'redis://redis_db:6379/0')
        auth = f":{conf.password}@" if conf.password else ""
        return f"redis://{auth}{conf.host}:{conf.port}/{conf.db}"


_SETTINGS = Settings() 


def settings_conf(): 
    return _SETTINGS 


if __name__ == '__main__': 
    SETTINGS_PROVIDER = settings_conf() 
    print(SETTINGS_PROVIDER.mysql_config)
