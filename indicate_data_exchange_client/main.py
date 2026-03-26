import logging
import sys

from indicate_data_exchange_client.config.configuration import load_configuration
from indicate_data_exchange_client.logic import State
from indicate_data_exchange_client.web import make_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")


configuration = load_configuration()
logger.info(f"Data provider id is {configuration.provider_id}")

state = State(configuration)

base_url = f"http://{configuration.listen_address}:{configuration.listen_port}"
logger.info(f"Listening for trigger requests on {base_url}/api/trigger")
logger.info(f"Access the review interface at {base_url}/review")
sys.stdout.flush()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        make_app(configuration, state),
        host=configuration.listen_address,
        port=configuration.listen_port,
        log_level="info"
    )
