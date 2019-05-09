from collections import OrderedDict


def suggestion_list(inp, options):
    """
     Given an invalid input string and a list of valid options, returns a filtered
     list of valid options sorted based on their similarity with the input.
    """
    options_by_distance = OrderedDict()
    input_threshold = len(inp) / 2

    for option in options:
        distance = lexical_distance(inp, option)
        threshold = max(input_threshold, len(option) / 2, 1)
        if distance <= threshold:
            options_by_distance[option] = distance

    return sorted(
        list(options_by_distance.keys()), key=lambda k: options_by_distance[k]
    )


def lexical_distance(a, b):
    """
     Computes the lexical distance between strings A and B.
     The "distance" between two strings is given by counting the minimum number
     of edits needed to transform string A into string B. An edit can be an
     insertion, deletion, or substitution of a single character, or a swap of two
     adjacent characters.
     This distance can be useful for detecting typos in input or sorting
     @returns distance in number of edits
    """

    d = [[i] for i in range(len(a) + 1)] or []
    d_len = len(d) or 1
    for i in range(d_len):
        for j in range(1, len(b) + 1):
            if i == 0:
                d[i].append(j)
            else:
                d[i].append(0)

    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1

            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)

            if i > 1 and j < 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + cost)

    return d[len(a)][len(b)]
