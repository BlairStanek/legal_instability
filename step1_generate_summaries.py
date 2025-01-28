# Runs through raw court opinion texts, gets an LLM to summarize them, and writes them out

import json, os, re
import call_utils, utils

PATH = "f3d/"
total_files_considered = 0

# First, we construct the list of all candidate files and their location
candidates = [] # will have tuples of (outfile_name, infile_location)
for vol_dir in sorted(os.listdir(PATH)): # sorting makes order predictable
    if os.path.isdir(PATH+"/"+vol_dir):
        for filename in sorted(os.listdir(PATH+"/"+ vol_dir)): # sorting makes order predictable
            if filename != "CasesMetadata.json" and filename.endswith(".json"):
                total_files_considered += 1
                infilename = PATH + vol_dir+"/"+filename
                with open(infilename, "r") as f:
                    caseinfo = json.load(f)

                # We want only cases with two opinions: a majority, and a dissent
                if len(caseinfo["casebody"]["opinions"]) == 2:
                    casetext = ""
                    for opinion in caseinfo["casebody"]["opinions"]:
                        casetext += opinion["text"] + "\n\n"
                    casetext = casetext.strip()

                    diversity = False
                    if "diversity jurisdiction" in casetext.lower() or \
                        "diversity action" in casetext.lower() or \
                        "complete diversity" in casetext.lower() or \
                        "diversity of citizenship" in casetext.lower() or \
                        "amount in controversy" in casetext.lower() or \
                        re.match(r"\s28\s*u\.?s\.?c\.?.{1,10}1332", casetext.lower()) != None:
                        diversity = True

                    # print(filename, "{:11d}".format(len(casetext)), caseinfo["citations"][0]["cite"], diversity)

                    has_dissent = False
                    if not diversity:
                        for opinion in caseinfo["casebody"]["opinions"]:
                            if opinion["type"] == "dissent":
                                has_dissent = True

                    # target size is 10,000 to 50,000 chars
                    if has_dissent and  \
                            not diversity and \
                            10000 < len(casetext.strip()) < 50000 and \
                            caseinfo["citations"][0]["cite"].split()[2].isnumeric():
                        # Items where caseinfo["citations"][0]["cite"].split()[2].isnumeric() fails are withdrawn opinions
                        outfile_name = caseinfo["citations"][0]["cite"].strip().replace(" ", "_") + ".txt"
                        candidates.append((outfile_name, infilename))
                        print(outfile_name)

candidates.sort(key=lambda x: utils.get_cite_number(x[0])) # sort by outfile name, digits-aware

for x in candidates:
    print(x)
print("len(candidates)=", len(candidates))
print("total_files_considered=", total_files_considered)

# Now, run through and create the summaries as needed
OUTPATH = "Summaries/"
num_written = 0
for candidate in candidates:
    outfile = OUTPATH+candidate[0]
    if os.path.exists(outfile):
        print(outfile, "already exists, skipping")
    else:
        infile = candidate[1]
        print("Working on infile", infile, "to be written to", outfile)
        with open(candidate[1], "r") as f:
            caseinfo = json.load(f)

        assert len(caseinfo["casebody"]["opinions"]) == 2
        casetext = ""
        for opinion in caseinfo["casebody"]["opinions"]:
            casetext += opinion["text"] + "\n\n"
        casetext = casetext.strip()

        messages = []
        user_prompt = \
            "Below is the full text of a federal appeals court decision, " + \
            "including a dissenting opinion.  Your task is " + \
            "detailed at the end of the decision.  Here is the decision:\n\n\n\n"

        user_prompt += casetext.strip()

        user_prompt += \
            "\n\n\n\nEnd of the decision.  Your task is to summarize the central " + \
            "facts and legal issues, " + \
            "while also changing the names of all people, and of all entities " + \
            "that are not government entities (e.g. the FBI, the California Highway Patrol).  " + \
            "Also change all place names *other* than the name of states (e.g. Ohio) " + \
            "and countries (e.g. the United States).  " + \
            "Do **not** change the names of any statutes, laws, cases (e.g. 'Brown v. Smith', " + \
            "'In re Cooke'), legal doctrines, acts, etc. " + \
            "For courts, use only their generic name, like 'the district court', " + \
            "'the court below', 'the bankruptcy court', 'the state supreme court'. " + \
            "In the paragraph " + \
            "labeled (1), list JUST the names of the two main parties, separated by a " + \
            "single semicolon, using the changed names you've chosen, with the party that " + \
            "the majority agreed with (or mostly agreed with) listed FIRST.  " + \
            "(Thus, the party that the dissent agreed with or mostly agreed with is listed second).  " + \
            "In paragraph (1) " + \
            "list nothing other than the names of the two parties with a semicolon in between.  " + \
            "Then, in paragraphs " + \
            "labeled (2), (3) and (4), summarize all the facts relevant to the case, " + \
            "including how the two main parties relate to the facts. " + \
            "Give equal weight to the facts discussed in the majority opinion and in " + \
            "the dissent in determining the relevant facts.  " + \
            "Then, in paragraph (5) summarize (at length) the strongest legal arguments " +\
            "set out in the opinion for the first party winning, " +\
            "including any key statutes, acts, or precedent the arguments rely on. " +\
            "Then, in paragraph (6) summarize (at length) the strongest legal arguments " +\
            "set out in the opinion for the other party winning, " +\
            "including any key statutes, acts, or precedent the arguments rely on. " +\
            "Make the summaries in paragraphs (5) and (6) appear equally strong " + \
            "and convincing.  " + \
            "In all paragraphs do **not** give **any** hint of how " + \
            "the appeals courts decision above actually analyzed the legal issues presented " + \
            "and do **not** give **any** hint of how the appeals court decision above came " + \
            "out (e.g. reversed, affirmed, vacated, etc.).  Do **not** give **any** hint " + \
            "of which party prevailed in the opinion. " + \
            "Do **not** mention the dissenting opinion or the majority opinion in any way."

        messages.append({"role": "user", "content": user_prompt})

        summary_text = call_utils.call_api(messages, "o1")
        messages.append({"role": "assistant", "content": summary_text})  # store!
        call_utils.log_messages(messages, "o1")
        print("SUMMARY:", summary_text)

        with open(outfile, "w") as f_out:
            f_out.write(caseinfo["citations"][0]["cite"].strip()+"\n")
            f_out.write(summary_text.strip() + "\n")
        num_written += 1
        print("So far, num_written=", num_written)
        if num_written >= 500:
            exit(1)
