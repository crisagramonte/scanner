from pokemontcgmanager.querybuilder import QueryBuilder


class Supertype:
    RESOURCES = "supertypes"

    @staticmethod
    def all() -> list[dict]:
        """Get all supertypes, automatically paging through data

        Returns:
            list of dict: List of dictionaries containing supertype data
        """
        return QueryBuilder(Supertype).all()
