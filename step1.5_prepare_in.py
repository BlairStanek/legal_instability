# This takes the raw output from o1 in files ending in just *.txt and changes it to
# the files with the two actual questions, which end in *.in.txt.
# It runs in between step1 and step2, but is very simple.
import os, utils

PATH = "DATASET/" # This can be changed to run against other directories (e.g. old versions) if necessary

all_files = os.listdir(PATH)
raw_files = [x for x in all_files if x.endswith(".txt") and not x.endswith(".in.txt")]
raw_files.sort(key=lambda x: utils.get_cite_number(x))

for rawfile in raw_files:
    with open(PATH + rawfile, "r") as f_raw:
        raw_text = f_raw.read().strip()

    # Construct the prompt we will use.
    # Start by getting the two party names
    parties = "\n".join(raw_text.strip().split("\n")[1:])
    assert parties.startswith("(1)")
    parties = parties[len("(1)"):].strip() # gets rid of any newline after the (1) but before the parties
    parties = parties.split("\n")[0]
    party_list = parties.split(";")
    assert len(party_list) == 2
    party1 = party_list[0].strip()
    party2 = party_list[1].strip()
    # print("Parties:", party1, ";", party2)
    assert len(party1) > 1
    assert len(party2) > 1
    # Now construct the actual text
    first_question = \
        "You will be doing legal analysis of how you think a court " + \
        "should decide based on the facts below:\n\n\n"

    start_idx = raw_text.find("\n(2)")
    assert start_idx > 0
    assert raw_text[start_idx+4:].find("\n(2)") < 0, "should only have one (2) paragraph"
    body_summary_text = raw_text[start_idx:].strip()
    assert body_summary_text.startswith("(2)")
    body_summary_text = body_summary_text[len("(2)"):].strip()
    body_summary_text = body_summary_text.replace("\n(3)", "\n")
    body_summary_text = body_summary_text.replace("\n(4)", "\n")
    body_summary_text = body_summary_text.replace("\n(5)", "\n")
    body_summary_text = body_summary_text.replace("\n(6)", "\n")
    body_summary_text = body_summary_text.replace("\n(7)", "\n")
    body_summary_text = body_summary_text.replace("\n(8)", "\n")
    body_summary_text = body_summary_text.strip()
    first_question += body_summary_text
    first_question += \
        "\n\n\nBased on the facts above and your knowledge of the law, think step by step " + \
        "to figure out which party should prevail: " + party1 + " or " + party2

    # Now also construct the follow-up question
    follow_up_question = "To summarize, which of the two parties do you think should prevail: " + \
                        party1 + " or " + party2 + utils.TEXT_ANSWER_ONLY_WITH + party1 + \
                         utils.TEXT_OR_THE_STRING + party2 + "."

    # write it all out
    assert rawfile.endswith(".txt")
    assert not rawfile.endswith(".in.txt")
    intxt_file = rawfile.replace(".txt", ".in.txt")
    print(rawfile, "\t-->", intxt_file)
    with open(PATH + intxt_file, "w") as f_intxt:
        f_intxt.write(first_question + utils.DIVIDER + follow_up_question)

