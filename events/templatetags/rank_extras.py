from django import template

register = template.Library()


@register.filter
def with_ranks(entries):
    """Assign competition ranks (1,2,2,4) to an entry list ordered by -vote_count."""
    ranked = []
    prev_count = None
    rank = 0
    for i, e in enumerate(entries, start=1):
        if e.vote_count != prev_count:
            rank = i
            prev_count = e.vote_count
        e.rank = rank
        ranked.append(e)
    return ranked
