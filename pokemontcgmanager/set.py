from pokemontcgmanager.querybuilder import QueryBuilder


class Set:
    RESOURCE = "sets"

    @staticmethod
    def find(id: str) -> dict or None:
        """Get a set by its id

        Args:
            id (string): Set id
        Returns:
            Set: Instance of the Set
        """
        return QueryBuilder(Set).find(id)

    @staticmethod
    def where(**kwargs) -> list[dict]:
        """Adds a parameter to the dictionary of query parameters

        Args:
            **kwargs: Arbitrary keyword arguments.
        Returns:
            list of dict: List of dictionaries containing set data
        """
        return QueryBuilder(Set).where(**kwargs)

    @staticmethod
    def all():
        """Get all sets, automatically paging through data

        Returns:
            list of dict: List of dictionaries containing set data
        """
        return QueryBuilder(Set).all()
