from pokemontcgmanager.querybuilder import QueryBuilder


class Subtype:
    RESOURCES = "subtypes"

    @staticmethod
    def all() -> list[dict]:
        """Get all subtypes, automatically paging through data

        Returns:
            list of dict: List of dictionaries containing subtype data
        """
        return QueryBuilder(Subtype).all()
