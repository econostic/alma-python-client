import requests

from alma.response import Response


class RequestError(Exception):
    def __init__(self, error, url, response):
        self.error = error
        self.url = url
        self.response = response


class Request:
    def __init__(self, context, url):
        self.context = context
        self.url = url

        self.headers = {
            "User-Agent": self.context.user_agent_string(),
            "Authorization": f"Alma-Auth {self.context.api_key}",
            "Accept": "application/json",
        }
        self.params = {}
        self.body = None

    def set_body(self, value):
        self.body = value
        return self

    def get(self):
        res = requests.get(self.url, self.params, headers=self.headers)
        return self._process_response(res)

    def post(self):
        res = requests.post(self.url, json=self.body, headers=self.headers)
        return self._process_response(res)

    def _process_response(self, resp):
        response = Response(resp)

        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            if "message" in response.json:
                error = response.json["message"]
            else:
                error = e.strerror

            raise RequestError(error, self, response)

        return response