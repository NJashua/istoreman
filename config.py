# inventory_management_system/config.py

class Config:
    SNOWFLAKE_USER = 'Nithin'
    SNOWFLAKE_PASSWORD = 'Nithin@2024'
    SNOWFLAKE_ACCOUNT = 'bdhriyc-ke24872'
    SNOWFLAKE_DATABASE = 'INVENTORY'
    SNOWFLAKE_SCHEMA = 'PUBLIC'

    @staticmethod
    def as_dict():
        return {
            'user': Config.SNOWFLAKE_USER,
            'password': Config.SNOWFLAKE_PASSWORD,
            'account': Config.SNOWFLAKE_ACCOUNT,
            'database': Config.SNOWFLAKE_DATABASE,
            'schema': Config.SNOWFLAKE_SCHEMA
        }

# inventory_management_system/security.py

def get_snowflake_config():
    config = Config.as_dict()
    config['password'] = hide_sensitive_data(config['password'])
    return config

def hide_sensitive_data(data):
    # Implement a secure way to hide sensitive data,
    # such as encryption or hashing, before returning the config.
    return '****'