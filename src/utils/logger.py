import logging
import logging.config
import yaml
import os
from datetime import datetime

def setup_logging(config_path: str = '../config/logging_config.yaml'):
    """Set up logging configuration"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Fallback configuration that ensures both file and console output
    basic_config = {
        'version': 1,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': f'logs/website_analyzer_{timestamp}.log'
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console', 'file']
        },
        'disable_existing_loggers': False
    }
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        config['handlers']['file']['filename'] = f'logs/website_analyzer_{timestamp}.log'
        config['disable_existing_loggers'] = False
        logging.config.dictConfig(config)
    except Exception as e:
        logging.config.dictConfig(basic_config)
    
    logger = logging.getLogger('website_analyzer')
    logger.info('Logging configured successfully')
    return logger 