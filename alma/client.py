import logging
import platform
from typing import Optional, Dict

from . import endpoints
from .api_modes import ApiModes
from .context import Context
from .credentials import MerchantIdCredentials, AlmaSessionCredentials, ApiKeyCredentials
from .version import __version__ as alma_version


class Client:
    SANDBOX_API_URL = "https://api.sandbox.getalma.eu"
    LIVE_API_URL = "https://api.getalma.eu"

    @classmethod
    def with_api_key(cls, api_key: str, **options):
        options = {**options, "credentials": ApiKeyCredentials(api_key)}
        return cls(None, **options)

    @classmethod
    def with_merchant_id(cls, merchant_id: str, **options):
        options = {**options, "credentials": MerchantIdCredentials(merchant_id)}
        return cls(None, **options)

    @classmethod
    def with_alma_session(cls, session_id: str, cookie_name: str = "alma_sess", **options):
        options = {**options, "credentials": AlmaSessionCredentials(session_id, cookie_name)}
        return cls(None, **options)

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Create a new instance of the Alma API Client.

        It is recommended to use one the convenience methods instead of the default constructor:
        - Client.with_api_key
        - Client.with_merchant_id
        - Client.with_alma_session

        :param  api_key:    Deprecated - use Client.with_api_key("<api_key>") instead
        :type   api_key:    str

        :keyword    credentials A `Credentials` instance to be used to configure requests made to the API
                                This would typically be set by one of the convenience methods mentioned above
        :keyword    mode        API mode to be used: either ApiModes.LIVE or ApiModes.TEST
        :keyword    logger      A logger instance to be used instead of the default one
        :keyword    api_root    root URL(s) to call Alma's API at. You probably don't want to change it!

                                Expected types:
                                -------------
                                str: the provided URL will be used for both LIVE and TEST modes
                                dict: must have two keys, ApiModes.LIVE and ApiModes.TEST, each value must be
                                      the URL to be used for each mode

        """
        default_mode = ApiModes.LIVE
        credentials = kwargs.get("credentials")

        if isinstance(credentials, ApiKeyCredentials):
            api_key = credentials.api_key

        if api_key:
            default_mode = ApiModes.LIVE if api_key.startswith("sk_live") else ApiModes.TEST

            # Backward compatibility with the older init method
            if not credentials:
                credentials = ApiKeyCredentials(api_key)

        if not credentials:
            raise ValueError("Valid credentials are required to instantiate a new Client")

        options = {
            "api_root": {ApiModes.TEST: self.SANDBOX_API_URL, ApiModes.LIVE: self.LIVE_API_URL},
            "mode": default_mode,
            "logger": logging.getLogger("alma-python-client"),
            "credentials": credentials,
            **kwargs,
        }

        if type(options["api_root"]) is str:
            options["api_root"] = {
                ApiModes.TEST: options["api_root"],
                ApiModes.LIVE: options["api_root"],
            }
        elif type(options["api_root"]) is not dict:
            raise ValueError("`api_root` option must be a dict or a string")

        if options["mode"] not in (ApiModes.LIVE, ApiModes.TEST):
            raise ValueError(
                "`mode` option must be one of ({LIVE}, {TEST})".format(
                    LIVE=ApiModes.LIVE.value, TEST=ApiModes.TEST.value
                )
            )

        self.context = Context(options)

        self.init_user_agent()
        self._endpoints: Dict[str, endpoints.Base] = {}

    def add_user_agent_component(self, component, version):
        self.context.add_user_agent_component(component, version)

    def init_user_agent(self):
        self.add_user_agent_component("Python", platform.python_version())
        self.add_user_agent_component("alma-client", alma_version)

    def _endpoint(self, endpoint_name):
        endpoint = self._endpoints.get(endpoint_name)

        if endpoint is None:
            endpoint = getattr(endpoints, endpoint_name)(self.context)
            self._endpoints[endpoint] = endpoint

        return endpoint

    @property
    def payments(self) -> endpoints.Payments:
        return self._endpoint("Payments")

    @property
    def merchants(self) -> endpoints.Merchants:
        return self._endpoint("Merchants")

    @property
    def orders(self) -> endpoints.Orders:
        return self._endpoint("Orders")

    @property
    def exports(self) -> endpoints.Exports:
        return self._endpoint("Exports")
