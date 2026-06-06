from enum import IntEnum


class Brain(IntEnum):
    GENERAL = 1
    LEAD_AND_UNKNOWN = 2
    GUEST_PRE_ARRIVAL = 3
    GUEST_IN_STAY = 4
    GUEST_POST_STAY = 5
    PAST_GUEST = 6