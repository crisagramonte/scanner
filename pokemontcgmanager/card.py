from pokemontcgmanager.querybuilder import QueryBuilder


class Card:
    RESOURCE = "cards"

    @staticmethod
    def find(id: str) -> dict or None:
        """Get a card by its id

        Args:
            id (string): Card id
        Returns:
            dict: Dictionary containing card data
        """
        return QueryBuilder(Card).find(id)

    @staticmethod
    def where(**kwargs) -> list[dict]:
        """Adds a parameter to the dictionary of query parameters

        Args:
            **kwargs: Dictionary of query parameters
        Returns:
            list of dict: List of dictionaries containing card data
        """
        return QueryBuilder(Card).where(**kwargs)
