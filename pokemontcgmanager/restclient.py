import dotenv
import os
import requests

dotenv.load_dotenv()


class RestClient:
    api_key = None

    @classmethod
    def configure(cls, api_key: str = None):
        cls.api_key = api_key

    @classmethod
    def get(cls, url: str, params: dict = {}) -> dict or None:
        """Invoke an HTTP GET request on a url

        Args:
            url (string): URL endpoint to request
            params (dict): Dictionary of url parameters
        Returns:
            dict: JSON response as a dictionary
        """
        request_url = url

        headers = {"User-Agent": "Mozilla/5.0"}
        api_key = (
            cls.api_key if cls.api_key is not None else os.getenv("POKEMONTCG_API_KEY")
        )
        if api_key:
            headers["X-Api-Key"] = api_key

        response = requests.get(request_url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
