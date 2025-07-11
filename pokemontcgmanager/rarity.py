from pokemontcgmanager.querybuilder import QueryBuilder


class Rarity:
    RESOURCES = "rarities"

    @staticmethod
    def all() -> list[dict]:
        """Get all rarities, automatically paging through data

        Returns:
            list of dict: List of dictionaries containing rarity data
        """
        return QueryBuilder(Rarity).all()
