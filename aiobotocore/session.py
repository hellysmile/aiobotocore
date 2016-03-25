import asyncio
import botocore.credentials
import botocore.session
from botocore import retryhandler, translate

from .client import AioClientCreator


class AioSession(botocore.session.Session):

    def __init__(self, *args, **kwargs):
        loop = kwargs.pop('loop', None)

        super().__init__(*args, **kwargs)
        self._loop = loop

    def create_client(self, service_name, region_name=None, api_version=None,
                      use_ssl=True, verify=None, endpoint_url=None,
                      aws_access_key_id=None, aws_secret_access_key=None,
                      aws_session_token=None, config=None):

        default_client_config = self.get_default_client_config()

        if config is not None and default_client_config is not None:
            config = default_client_config.merge(config)
        elif default_client_config is not None:
            config = default_client_config

        if region_name is None:
            if config and config.region_name is not None:
                region_name = config.region_name
            else:
                region_name = self.get_config_variable('region')

        # Figure out the verify value base on the various
        # configuration options.
        if verify is None:
            verify = self.get_config_variable('ca_bundle')

        loader = self.get_component('data_loader')
        event_emitter = self.get_component('event_emitter')
        response_parser_factory = self.get_component(
            'response_parser_factory')
        if aws_secret_access_key is not None:
            credentials = botocore.credentials.Credentials(
                access_key=aws_access_key_id,
                secret_key=aws_secret_access_key,
                token=aws_session_token)
        else:
            credentials = self.get_credentials()
        endpoint_resolver = self.get_component('endpoint_resolver')

        client_creator = AioClientCreator(
            loader, endpoint_resolver, self.user_agent(), event_emitter,
            retryhandler, translate, response_parser_factory, loop=self._loop)
        client = client_creator.create_client(
            service_name, region_name, use_ssl, endpoint_url, verify,
            credentials, scoped_config=self.get_scoped_config(),
            client_config=config, api_version=api_version)
        return client


def get_session(*, env_vars=None, loop=None):
    """
    Return a new session object.
    """
    loop = loop or asyncio.get_event_loop()
    return AioSession(session_vars=env_vars, loop=loop)
