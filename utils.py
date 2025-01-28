# General purpose utilities

def get_cite_number(item):
    if item.endswith(".in.txt"):
        item2 = item[:-len(".in.txt")]
    elif item.endswith(".txt"):
        item2 = item[:-len(".txt")]
    elif item.endswith(".out.json"):
        item2 = item[:-len(".out.json")]
    else:
        item2 = item
    cite_components = item2.split("_")
    assert len(cite_components) == 3
    assert cite_components[1].strip().lower() == "f.3d"
    assert cite_components[0].isnumeric()
    assert cite_components[2].isnumeric()
    return (int(cite_components[0]) * 10000) + int(cite_components[2])

# These are used in creating the *.in.txt files (and for decoding those files)
DIVIDER = "\n---FOLLOW-UP QUESTION:--------------------------------\n"
TEXT_ANSWER_ONLY_WITH = ".  Answer with ONLY the string "
TEXT_OR_THE_STRING = " or the string "