"""
Helpers

Methods that are helpful to have in a module.
"""


def make_bar(value, maximum, length, gradient):
    """Make a bar of length, of color value along the gradient."""
    maximum = float(maximum)
    length = float(length)
    value = min(float(value), maximum)
    if not value:
        return ''
    barcolor = gradient[max(0, (int(round((value / maximum) * len(gradient))) - 1))]
    rounded_percent = int(min(round((value / maximum) * length), length - 1))
    barstring = (("{:<%i}" % int(length)).format("%i / %i" % (int(value), int(maximum))))
    barstring = ("|555" + barcolor + barstring[:rounded_percent] + '|[011' + barstring[rounded_percent:])
    return barstring[:int(length) + 13] + "|n"


def mass_unit(value):
    """Present a suitable mass unit based on value"""
    if not value:
        return 'unknown'
    value = float(value)
    if value <= 0:
        return 'weightless'
    if value <= 999:
        return '%s g' % str(value).rstrip('0').rstrip('.')
    if value <= 999999:
        return '%s kg' % str(value/1000).rstrip('0').rstrip('.')
    if value <= 999999999:
        return '%s t' % str(value / 1000000).rstrip('0').rstrip('.')
    if value <= 999999999999:
        return '%s kt' % str(value / 1000000000).rstrip('0').rstrip('.')
    if value <= 999999999999999:
        return '%s Mt' % str(value / 1000000000000).rstrip('0').rstrip('.')
    else:
        return 'super massive'


def escape_braces(text):
    text = text if text else ''
    text = text.replace('{', '{{')
    text = text.replace('}', '}}')
    return text


def substitute_objects(text, puppet):
    if '/' not in text:
        return text
    candidates = [puppet] + puppet.contents
    if puppet.location:
        candidates = list(set(candidates + [puppet.location] + puppet.location.contents +
                              (list(puppet.location.db.hosted.keys()) if puppet.location.db.hosted else [])))
    return_text = []
    for each in text.split():
        match = None
        new_each = each
        word_end = ''
        if each.startswith('/'):  # A possible substitution to test
            if each.endswith('/'):  # Skip this one, it's /italic/
                return_text.append(new_each)
                continue
            search_word = each[1:]
            if search_word.startswith('/'):  # Skip this one, it's being escaped
                new_each = each[1:]
            else:  # Marked for substitution, try to find a match
                if "'" in each:  # Test for possessive or contraction:  's  (apostrophe before end of grouping)
                    pass
                if each[-1] in ".,!?":
                    search_word, word_end = search_word[:-1], each[-1]
                match = puppet.search(search_word, quiet=True, candidates=candidates)
        return_text.append(new_each if not match else (match[0].get_display_name(puppet) + word_end))
    return ' '.join(return_text)
