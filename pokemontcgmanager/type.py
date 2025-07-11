from pokemontcgmanager.querybuilder import QueryBuilder


class Type:
    RESOURCES = "types"

    @staticmethod
    def all() -> list[dict]:
        """Get all types, automatically paging through data

        Returns:
            list of dict: List of dictionaries containing type data
        """
        return QueryBuilder(Type).all()
