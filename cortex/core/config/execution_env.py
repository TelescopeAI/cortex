import os
from enum import Enum

from cortex.core.types.telescope import TSModel


class EnvLevel(Enum):
    LOCAL = "LOCAL"
    DEV = "DEV"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


class ExecutionEnv(TSModel):
    https: bool = False
    level: EnvLevel = EnvLevel.LOCAL
    profiling: bool = False

    @staticmethod
    def get_key(key: str) -> str | bool:
        return os.getenv(key, False)

    @staticmethod
    def get_env():
        https_enabled = ExecutionEnv.https_enabled()
        level_env = ExecutionEnv.get_key('EXECUTION_ENV').upper()
        level = EnvLevel(level_env)
        return ExecutionEnv(https=https_enabled, level=level)

    @staticmethod
    def get_profile():
        https_enabled = ExecutionEnv.https_enabled()
        level_env = ExecutionEnv.get_key('EXECUTION_ENV').upper()
        level = EnvLevel(level_env)
        profiling_enabled = True if ExecutionEnv.get_key('ENABLE_PROFILING') == "True" else False
        return ExecutionEnv(https=https_enabled, level=level, profiling=profiling_enabled)

    @staticmethod
    def https_enabled() -> bool:
        https_enabled: bool = False
        https_enabled_value: str = ExecutionEnv.get_key('HTTPS')
        if https_enabled_value == "True" or https_enabled_value == "true":
            https_enabled = True
        return https_enabled

    @staticmethod
    def is_local() -> bool:
        return ExecutionEnv.get_env().level == EnvLevel.LOCAL

    @staticmethod
    def is_profiling_enabled() -> bool:
        if ExecutionEnv.get_profile().profiling:
            return True
