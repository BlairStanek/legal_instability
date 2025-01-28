# Runs through summaries and repeatedly calls LLM to see which wins
import call_utils, utils
import os, json, sys
import Levenshtein

if len(sys.argv) != 2:
    print("Usage: Sole argument is the model name to use")
    exit(1)

MODEL = sys.argv[1]
MODEL_SET = ["gpt-4o-2024-11-20", "claude-3-5-sonnet-20241022", "gemini-1.5-pro-002", "o1"] # only ones used in these experiments
if MODEL not in MODEL_SET:
    print("MODEL passed is", MODEL, "but that is not one of the acceptable ones:", MODEL_SET)
    exit(1)

print("MODEL = ", MODEL)

file_percentages = []

PATH = "Summaries/" # This can be changed to run against other directories (e.g. old versions) if necessary

MIN_NUM = 20 # minimum number of runs per case+model combination
MAX_NUM = 20 # maximum number of runs per case+model combination

def run_more(data):
    assert 0 == len([x for x in data if x[0] not in ["party1", "party2"]])
    if len(data) < MIN_NUM:
        return True
    if len(data) >= MAX_NUM:
        return False


known_stability = dict()
if MODEL == "o1": # do only subset for o1, which is so expensive
    infiles = []
    with open("o1_subset.txt", "r") as f_subset:
        subset_text = f_subset.read()
    for linein in subset_text.split("\n"):
        if len(linein) > 0:
            assert linein[0] == "<"
            infiles.append(linein[1:linein.find(">")])
            print(infiles[-1])
            known_stability[infiles[-1]] = linein
else:
    raw_infiles = os.listdir(PATH)
    infiles = [x for x in raw_infiles if x.endswith(".in.txt")]
    infiles.sort(key=lambda x: utils.get_cite_number(x))

for infile in infiles:
    outdata = None
    outfile = infile.replace(".in.txt", ".out.json")
    if os.path.exists(PATH+outfile):
        with open(PATH + outfile, "r") as f_out_existing:
            outdata = json.load(f_out_existing)
    else:
        outdata = {MODEL: []}
    if MODEL not in outdata:
        outdata[MODEL] = []
    # outdata[MODEL] = [] # Uncomment this line and the line below to start from scratch
    # new_data = True
    new_data = False

    print(infile,"------------------------------")
    if infile in known_stability:
        print("Known Stability on gpt-4o:", known_stability[infile])
    with open(PATH + infile, "r") as f_in:
        in_text = f_in.read().strip()

    # Load the prompts
    questions = in_text.split(utils.DIVIDER)
    assert len(questions) == 2, "Should be main plus the follow-up"
    user_prompt = questions[0]
    follow_up = questions[1]

    # Figure out the parties
    parts = follow_up.split(utils.TEXT_ANSWER_ONLY_WITH)
    assert len(parts) == 2
    parties = parts[1].split(utils.TEXT_OR_THE_STRING)
    assert len(parties) == 2, "Should be exactly 2 parties"
    party1 = parties[0]
    party2 = parties[1]
    assert party2[-1] == ".", "Should end in period"
    party2 = party2[:-1]

    print("Already has", len(outdata[MODEL]),"from infile")

    while run_more(outdata[MODEL]):
        messages = []

        messages.append({"role": "user", "content": user_prompt})
        reasoning_text = call_utils.call_api(messages, MODEL).strip()
        messages.append({"role": "assistant", "content": reasoning_text})  # store!

        messages.append({"role": "user", "content": follow_up}) # follow-up question to clarify
        winner_text = call_utils.call_api(messages, MODEL).strip()
        messages.append({"role": "assistant", "content": winner_text})  # store!

        timestamp = call_utils.log_messages(messages, MODEL)

        chars_hash = hash(reasoning_text) % 1000
        print("Winner", winner_text, end=" ")
        if Levenshtein.distance(winner_text.lower(), party1.lower()) < \
                Levenshtein.distance(winner_text.lower(), party2.lower()):
            outdata[MODEL].append(("party1", timestamp, len(reasoning_text), chars_hash))
            print("party1" , end=" ")
        else:
            outdata[MODEL].append(("party2", timestamp, len(reasoning_text), chars_hash))
            print("party2", end = " ")
        new_data = True
        print("charlen=", len(reasoning_text),"hash=", chars_hash) # to determine similarity

    # write everything out, making sure to load the latest version so that nothing is locked out
    if new_data:
        if os.path.exists(PATH + outfile):
            with open(PATH + outfile, "r") as f_out_latest:
                latest_outdata = json.load(f_out_latest)
            latest_outdata[MODEL] = outdata[MODEL]
        else:
            latest_outdata = outdata
        with open(PATH + outfile, "w") as f_out:
            json.dump(latest_outdata, f_out)

    party1_count = len([x for x in outdata[MODEL] if x[0] == "party1"])
    party2_count = len([x for x in outdata[MODEL] if x[0] == "party2"])
    print("party1_count =", party1_count)
    print("party2_count =", party2_count)
    if party1_count != 0 and party2_count !=0 :
        print("UNSTABLE!")
    if party1_count+party2_count != 0:
        stability_percent = float(max(party1_count,party2_count))/(party1_count+party2_count)
        print("FILE {:15s} {:.3f}".format(infile, stability_percent))
        file_percentages.append((infile, stability_percent))

# Final printout of the most to least reproducible:
file_percentages.sort(key=lambda x: x[1], reverse=True) # we want least stable ones towards the end for easy inspection
for file_perc in file_percentages:
    print("{:15s} {:.3f}".format(file_perc[0], file_perc[1]))

print("Number considered:", len(file_percentages))
print("Number unstable:", len([x for x in file_percentages if x[1] != 0]))