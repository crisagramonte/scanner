from pokemontcgmanager.restclient import RestClient

BASE_URL = "https://api.pokemontcg.io/v2/"


class QueryBuilder:
    def __init__(self, type):
        self.params = {}
        self.type = type

    def find(self, id: str):
        """Get a resource by its id

        Args:
            id (string): Resource id
        Returns:
            object: Instance of the resource type
        """
        url = f"{BASE_URL}/{self.type.RESOURCE}/{id}"
        response = RestClient.get(url)["data"]
        return response

    def where(self, **kwargs):
        """Adds a parameter to the dictionary of query parameters

        Args:
            **kwargs: Arbitrary keyword arguments.
        Returns:
            list of object: List of resource objects
        """
        for key, value in kwargs.items():
            self.params[key] = value

        return self.all()

    def all(self):
        """Get all resources, automatically paging through data

        Returns:
            list of object: List of resource objects
        """
        data_list = []
        fetch_all = True
        url = f"{BASE_URL}/{self.type.RESOURCE}"

        if "page" in self.params:
            fetch_all = False
        else:
            self.params["page"] = 1

        while True:
            response = RestClient.get(url, self.params)["data"]
            if len(response) > 0:
                data_list.extend(response)

                if fetch_all:
                    self.params["page"] += 1
                else:
                    break
            else:
                break

        return data_list
