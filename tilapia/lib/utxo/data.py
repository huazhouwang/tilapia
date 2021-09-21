import enum


@enum.unique
class UTXOStatus(enum.IntEnum):
    SPENDABLE = 10
    CHOSEN = 20
    SPENT = 30

    @classmethod
    def to_choices(cls):
        return (
            (cls.SPENDABLE, "Spendable"),
            (cls.CHOSEN, "Chosen"),
            (cls.SPENT, "Spent"),
        )
