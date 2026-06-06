from app.models.brain import Brain


def get_brain_name(brain_id: Brain) -> str:
    match brain_id:
        case Brain.GENERAL:
            return "general"

        case Brain.LEAD_AND_UNKNOWN:
            return "lead_and_unknown"

        case Brain.GUEST_PRE_ARRIVAL:
            return "guest_pre_arrival"

        case Brain.GUEST_IN_STAY:
            return "guest_in_stay"

        case Brain.GUEST_POST_STAY:
            return "guest_post_stay"

        case Brain.PAST_GUEST:
            return "past_guest"

    raise ValueError(f"Unknown brain: {brain_id}")