"""Who owes what, after a group of people have paid for things.

Amounts are integer cents throughout. Floats are not used anywhere in this
module, because binary floating point cannot represent 0.10 exactly and money
arithmetic that drifts by a fraction of a cent per operation is the classic
way a ledger stops balancing.
"""


def split_evenly(amount_cents, participants):
    """Divide one expense between the people who shared it.

    Returns {person: cents_they_owe}.
    """
    share = amount_cents // len(participants)
    return {person: share for person in participants}


def balances(expenses, people):
    """Net position per person, in cents. Positive means they are owed money.

    Every expense moves money twice: the payer is credited the full amount, and
    each participant is debited their share. Across a complete set of expenses
    those two movements should cancel exactly, so the net positions sum to zero.

    If they don't sum to zero, money has been invented or destroyed somewhere
    upstream -- which is not something this function can correct on its own
    without hiding the cause.
    """
    net = {person: 0 for person in people}
    for expense in expenses:
        net[expense["paid_by"]] += expense["amount_cents"]
        shares = split_evenly(expense["amount_cents"], expense["participants"])
        for person, share in shares.items():
            net[person] -= share
    return net


def validate_expense(expense):
    """Check an incoming expense before it reaches the ledger.

    Returns a list of human-readable problems; an empty list means it is valid.
    Everything is reported at once so a client can fix a request in one go.
    """
    if not isinstance(expense, dict):
        return ["expense must be a JSON object"]

    errors = []

    amount = expense.get("amount_cents")
    if amount is None:
        errors.append("amount_cents is required")
    # bool is a subclass of int, and a float would break the integer-cents rule.
    elif not isinstance(amount, int) or isinstance(amount, bool):
        errors.append("amount_cents must be an integer number of cents")
    elif amount <= 0:
        errors.append("amount_cents must be greater than zero")

    paid_by = expense.get("paid_by")
    if paid_by is None:
        errors.append("paid_by is required")
    elif not isinstance(paid_by, str) or not paid_by.strip():
        errors.append("paid_by must be a non-empty string")

    participants = expense.get("participants")
    if participants is None:
        errors.append("participants is required")
    elif not isinstance(participants, list) or not participants:
        errors.append("participants must be a non-empty list")
    elif not all(isinstance(p, str) and p.strip() for p in participants):
        errors.append("participants must all be non-empty strings")
    # Duplicates would collapse in split_evenly's dict and lose a share.
    elif len(set(participants)) != len(participants):
        errors.append("participants must not contain duplicates")

    return errors
