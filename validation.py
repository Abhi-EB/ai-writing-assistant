def find_placeholders(text: str) -> list:
    """Find unfinished placeholders enclosed in square brackets."""

    if not isinstance(text, str):
        raise TypeError("Input must be a string.")

    placeholders = []
    remaining_text = text

    while True:
        opening = remaining_text.find("[")

        if opening == -1:
            break

        closing = remaining_text.find("]", opening + 1)

        if closing == -1:
            break

        item = remaining_text[opening:closing + 1]

        if item[1:-1].strip():
            placeholders.append(item)

        remaining_text = remaining_text[closing + 1:]

    return list(dict.fromkeys(placeholders))
