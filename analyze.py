# This is used to analyze the data from step 2
import math

import utils, os, json, numpy
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

PATH = "DATASET/"

raw_outfiles = os.listdir(PATH)
outfiles = [x for x in raw_outfiles if x.endswith(".out.json")]
outfiles.sort(key=lambda x: utils.get_cite_number(x))

def calc_stability(data) -> float: # key definition of stability (simple)
    assert 0 == len([x for x in data if x[0] not in ["party1", "party2"]])
    party1_count = len([x for x in data if x[0] == "party1"])
    party2_count = len([x for x in data if x[0] == "party2"])
    return float(max(party1_count, party2_count)) / (party1_count + party2_count)

num_words = []

gpt_instabilities = []
claude_instabilities = []
gemini_instabilities = []

gpt_uniqueness = []
claude_uniqueness = []
gemini_uniqueness = []

gpt_accuracy = []
gpt_numright = 0
gpt_total = 0
claude_accuracy = []
claude_numright = 0
claude_total = 0
gemini_accuracy = []
gemini_numright = 0
gemini_total = 0

gpt_claude_agree_rate = []
gpt_gemini_agree_rate = []
claude_gemini_agree_rate = []

gpt_nums = dict()
claude_nums = dict()
gemini_nums = dict()

filenames_with_stability = [] # used to create balanced subsets

# Load in the data
for outfile in outfiles:
    assert os.path.exists(PATH+outfile)
    with open(PATH + outfile, "r") as f_out_existing:
        data = json.load(f_out_existing)

    infile = outfile.replace(".out.json", ".in.txt")
    assert os.path.exists(PATH+infile)
    with open(PATH + infile, "r") as f_in:
        intext = f_in.read()

    questions = intext.split(utils.DIVIDER)
    assert len(questions) == 2, "Should be 2: the initial question and a follow-up"
    num_words.append(len(questions[0].split())) # we measure the number of words in the FIRST question

    gpt_data = data["gpt-4o-2024-11-20"]
    claude_data = data["claude-3-5-sonnet-20241022"]
    gemini_data = data["gemini-1.5-pro-002"]

    gpt_instabilities.append(   calc_stability(gpt_data))
    claude_instabilities.append(calc_stability(claude_data))
    gemini_instabilities.append(calc_stability(gemini_data))

    filenames_with_stability.append((infile, gpt_instabilities[-1],
                                     claude_instabilities[-1], gemini_instabilities[-1],
                                     num_words[-1]))

    # Note that entries [2] and [3] should be the char len of the response and the hash of the
    # response, so this should count the percent that are unique answers
    gpt_uniqueness.append(len({(x[2], x[3]) for x in gpt_data}))
    claude_uniqueness.append(len({(x[2], x[3]) for x in claude_data}))
    gemini_uniqueness.append(len({(x[2], x[3]) for x in gemini_data}))

    party1_count = len([x for x in gpt_data if x[0] == "party1"])
    party2_count = len([x for x in gpt_data if x[0] == "party2"])
    gpt_numright += party1_count # Party 1 is always the one that won in the actual case (the 2-1 majority found for it)
    gpt_total += (party1_count + party2_count)
    gpt_party1_proportion = float(party1_count)/(party1_count+party2_count)
    gpt_accuracy.append(gpt_party1_proportion)

    party1_count = len([x for x in claude_data if x[0] == "party1"])
    party2_count = len([x for x in claude_data if x[0] == "party2"])
    claude_numright += party1_count
    claude_total += (party1_count + party2_count)
    claude_party1_proportion = float(party1_count)/(party1_count+party2_count)
    claude_accuracy.append(claude_party1_proportion)

    party1_count = len([x for x in gemini_data if x[0] == "party1"])
    party2_count = len([x for x in gemini_data if x[0] == "party2"])
    gemini_numright += party1_count
    gemini_total += (party1_count + party2_count)
    gemini_party1_proportion = float(party1_count)/(party1_count+party2_count)
    gemini_accuracy.append(gemini_party1_proportion)

    gpt_claude_agree_rate.append(gpt_party1_proportion*claude_party1_proportion + \
                                 (1-gpt_party1_proportion)*(1-claude_party1_proportion))
    gpt_gemini_agree_rate.append(gpt_party1_proportion*gemini_party1_proportion + \
                                 (1-gpt_party1_proportion)*(1-gemini_party1_proportion))
    claude_gemini_agree_rate.append(claude_party1_proportion*gemini_party1_proportion + \
                                 (1-claude_party1_proportion)*(1-gemini_party1_proportion))

    gpt_nums[len(gpt_data)]       = 1 + gpt_nums.get(len(gpt_data), 0)
    claude_nums[len(claude_data)] = 1 + claude_nums.get(len(claude_data), 0)
    gemini_nums[len(gemini_data)] = 1 + gemini_nums.get(len(gemini_data), 0)

    print("{:<21}".format(infile),
          "gpt-4o stability={:.2f}, accuracy={:.2f};". format(gpt_instabilities[-1], gpt_accuracy[-1]),
          "claude-3.5 stability={:.2f}, accuracy={:.2f};".format(claude_instabilities[-1], claude_accuracy[-1]),
          "gemini-1.5 stability={:.2f}, accuracy={:.2f}".format(gemini_instabilities[-1], gemini_accuracy[-1]))

# NOW, WRITE OUT THE GRAPHS
fig, ax = plt.subplots(1, 3, figsize=(7.875, 3))
bins = [0.475 + 0.05 * i for i in range(11)]
xticks = [0.5, 0.6, 0.7, 0.8, 0.9]
xtick_labels = ['50%', '60%', '70%', '80%', '90%']
y_top = 60
y_axis_title = "Number of Questions"
ax[0].hist([x for x in gpt_instabilities if x < 1], bins=bins, label='GPT-4o', rwidth=0.9, log=False)
ax[0].set_ylim(0, y_top)
ax[0].set_xticks(xticks)
ax[0].set_xticklabels(xtick_labels)
ax[0].set_title("GPT-4o")
ax[0].set_xlabel("Stability")
ax[0].set_ylabel(y_axis_title)

ax[1].hist([x for x in claude_instabilities if x < 1], bins=bins, label='Claude-3.5', rwidth=0.9, log=False)
ax[1].set_ylim(0, y_top)
ax[1].set_xticks(xticks)
ax[1].set_xticklabels(xtick_labels)
ax[1].set_title("Claude-3.5")
ax[1].set_xlabel("Stability")
ax[1].set_ylabel(y_axis_title)

ax[2].hist([x for x in gemini_instabilities if x < 1], bins=bins, label='Gemini-1.5', rwidth=0.9, log=False)
ax[2].set_ylim(0, y_top)
ax[2].set_xticks(xticks)
ax[2].set_xticklabels(xtick_labels)
ax[2].set_title("Gemini-1.5")
ax[2].set_xlabel("Stability")
ax[2].set_ylabel(y_axis_title)

plt.tight_layout()
fig.subplots_adjust(left=0.07, right=0.999, top=0.91, bottom=0.16)
# plt.show()
plt.savefig('stability_histogram.pdf', format='pdf')

# Now calculate important statistics and print in LATEX usable form------------------------
print("INDIVIDUAL MODEL STABILITY STATISTICS -----------------------")
print(r"\textbf{Model} & \textbf{Number Unstable} & \textbf{Percent Stable} \\")
print(r"\midrule")
Z = 1.960 # for 95% confidence intervals with large N

num_unstable = len([x for x in claude_instabilities if x<1])
num = len(claude_instabilities)
p_hat = float(num_unstable)/num
conf_interval = Z * math.sqrt(p_hat * (1-p_hat))/math.sqrt(num)
print("Claude-3.5 & \\phantom{0}" + str(num_unstable), "/", num,
      " & {:.1f} $\pm$ {:.1f} \\\\".format(100*p_hat, 100*conf_interval))

num_unstable = len([x for x in gpt_instabilities if x<1])
num = len(gpt_instabilities)
p_hat = float(num_unstable)/num
conf_interval = Z * math.sqrt(p_hat * (1-p_hat))/math.sqrt(num)
print("GPT-4o & " + str(num_unstable), "/", num,
      " & {:.1f} $\pm$ {:.1f} \\\\".format(100*p_hat, 100*conf_interval))

num_unstable = len([x for x in gemini_instabilities if x<1])
num = len(gemini_instabilities)
p_hat = float(num_unstable)/num
conf_interval = Z * math.sqrt(p_hat * (1-p_hat))/math.sqrt(num)
print("Gemini-1.5 & " + str(num_unstable), "/", num,
      " & {:.1f} $\pm$ {:.1f} \\\\".format(100*p_hat, 100*conf_interval))

print("\nSTABILITY CORRELATION STATISTICS -----------------------")
# print(r"\textbf{Model Pair} & \textbf{Correlation} & \textbf{p-value} \\")
gpt_unstable_indices =    {i for i in range(len(gpt_instabilities))    if gpt_instabilities[i] < 1}
claude_unstable_indices = {i for i in range(len(claude_instabilities)) if claude_instabilities[i] < 1}
gemini_unstable_indices = {i for i in range(len(gemini_instabilities)) if gemini_instabilities[i] < 1}

print(r"\midrule")
correlation, p_value = pearsonr(gpt_instabilities, claude_instabilities)
overlap_coefficient = float(len(gpt_unstable_indices &     claude_unstable_indices))/  \
                        min(len(gpt_unstable_indices), len(claude_unstable_indices))
print("GPT-4o vs. Claude-3.5 & {:.3f} & {:.3f} & {:.3f} \\\\".format(correlation, p_value, overlap_coefficient))

correlation, p_value = pearsonr(gpt_instabilities, gemini_instabilities)
overlap_coefficient = float(len(gpt_unstable_indices &     gemini_unstable_indices))/  \
                        min(len(gpt_unstable_indices), len(gemini_unstable_indices))
print("GPT-4o vs. Gemini-1.5 & {:.3f} & {:.3f} & {:.3f} \\\\".format(correlation, p_value, overlap_coefficient))

correlation, p_value = pearsonr(claude_instabilities, gemini_instabilities)
overlap_coefficient = float(len(claude_unstable_indices &     gemini_unstable_indices))/  \
                        min(len(claude_unstable_indices), len(gemini_unstable_indices))
print("Claude-3.5 vs. Gemini-1.5 & {:.3f} & {:.3f} & {:.3f} \\\\".format(correlation, p_value, overlap_coefficient))

print("SET INTERSECTIONS ON INSTABILITY--------------------")
print("gpt only:     ", len((gpt_unstable_indices - claude_unstable_indices) - gemini_unstable_indices))
print("claude only:  ", len((claude_unstable_indices - gpt_unstable_indices) - gemini_unstable_indices))
print("gemini only:  ", len((gemini_unstable_indices - gpt_unstable_indices) - claude_unstable_indices))
print("All three:    ", len(gpt_unstable_indices & claude_unstable_indices & gemini_unstable_indices))
print("gpt&claude:   ", len((gpt_unstable_indices & claude_unstable_indices) - gemini_unstable_indices))
print("gpt&gemini:   ", len((gpt_unstable_indices & gemini_unstable_indices) - claude_unstable_indices))
print("claude&gemini:", len((claude_unstable_indices & gemini_unstable_indices) - gpt_unstable_indices))
print("all stable   :", len(gpt_instabilities) - len(claude_unstable_indices | gemini_unstable_indices | gpt_unstable_indices))



print("\nSTABILITY CORRELATION with LENGTH -----------------------")
print(r"  & \textbf{Correlation of} &  \\") # & \textbf{Mean Stability} \\")
print(r" \textbf{Model} & \textbf{Length vs. Stability} & \textbf{p-value} \\") # & \textbf{Mean Stability} \\")
print(r"\midrule")


correlation, p_value = pearsonr(gpt_instabilities, num_words)
print("GPT-4o vs. length & {:.3f} & {:.3f} \\\\".format(correlation, p_value))
correlation, p_value = pearsonr(claude_instabilities, num_words)
print("Claude-3.5 vs. length & {:.3f} & {:.3f} \\\\".format(correlation, p_value))
correlation, p_value = pearsonr(gemini_instabilities, num_words)
print("Gemini-1.5 vs. length & {:.3f} & {:.3f} \\\\".format(correlation, p_value))





# NOT using Spearman correlation, since these are scalar numbers, and close to continuous
# correlation, p_value = spearmanr(gpt_instabilities, claude_instabilities)
# print("Stability Spearman correlation: ", correlation, "p-value:", p_value)

print("\nMODEL AGREEMENT STATISTICS -----------------------")
print(r"\midrule")

p_hat = float(gpt_numright)/gpt_total
conf_interval = Z * math.sqrt(p_hat * (1-p_hat))/math.sqrt(gpt_total)
print("GPT-4o \\& Court & {:.2f} $\\pm$ {:.2f} \\\\".format(p_hat*100, conf_interval*100))

p_hat = float(claude_numright)/claude_total
conf_interval = Z * math.sqrt(p_hat * (1-p_hat))/math.sqrt(claude_total)
print("Claude-3.5 \\& Court & {:.2f} $\\pm$ {:.2f} \\\\".format(p_hat*100, conf_interval*100))

p_hat = float(gemini_numright)/gemini_total
conf_interval = Z * math.sqrt(p_hat * (1-p_hat))/math.sqrt(gemini_total)
print("Gemini-1.5 \\& Court & {:.2f} $\\pm$ {:.2f} \\\\".format(p_hat*100, conf_interval*100))

print(r"\midrule")


assert gpt_total == claude_total == gemini_total

agree_rate = numpy.mean(gpt_claude_agree_rate)
conf_interval = Z * math.sqrt(agree_rate * (1-agree_rate))/math.sqrt(gpt_total)
print("GPT-4o \\& Claude-3.5 ",
      "& {:.2f} $\\pm$ {:.2f} \\\\".format(agree_rate*100, conf_interval*100))

agree_rate = numpy.mean(gpt_gemini_agree_rate)
conf_interval = Z * math.sqrt(agree_rate * (1-agree_rate))/math.sqrt(gpt_total)
print("GPT-4o \\& Gemini1.5 ",
      "& {:.2f} $\\pm$ {:.2f} \\\\".format(agree_rate*100, conf_interval*100))

agree_rate = numpy.mean(claude_gemini_agree_rate)
conf_interval = Z * math.sqrt(agree_rate * (1-agree_rate))/math.sqrt(gpt_total)
print("Gemini-1.5 \\& Claude-3.5",
      "& {:.2f} $\\pm$ {:.2f} \\\\".format(agree_rate*100, conf_interval*100))

print("\nACCURACY CORRELATION STATISTICS -----------------------")
print(r"\textbf{Model Pair} & \textbf{Correlation} & \textbf{p-value} \\")
print(r"\midrule")
correlation, p_value = pearsonr(gpt_accuracy, claude_accuracy)
print("GPT-4o vs. Claude-3.5 & {:.3f} & {:.1e} \\\\".format(correlation, p_value))
correlation, p_value = pearsonr(gpt_accuracy, gemini_accuracy)
print("GPT-4o vs. Gemini-1.5 & {:.3f} & {:.1e} \\\\".format(correlation, p_value))
correlation, p_value = pearsonr(gemini_accuracy, claude_accuracy)
print("Claude-3.5 vs. Gemini-1.5 & {:.3f} & {:.1e} \\\\".format(correlation, p_value))

print("\n INDIVIDUAL UNIQUENESS STATISTICS -----------------------")
print("GPT-4o", numpy.mean(gpt_uniqueness))
print("Claude", numpy.mean(claude_uniqueness), "median=", numpy.median(claude_uniqueness), "stddev=", numpy.std(claude_uniqueness))
print("Gemini", numpy.mean(gemini_uniqueness))

print("\nCOUNT FREQUENCIES -----------------------")
print("GPT frequency:", gpt_nums)
print("Claude frequency:", claude_nums)
print("Gemini frequency:", gemini_nums)

print("\nDATASET STATISTICS ------------------")
print("mean   ", numpy.mean(num_words))
print("stddev ", numpy.std(num_words))
print("median ", numpy.median(num_words))
print("min    ", numpy.min(num_words))
print("max    ", numpy.max(num_words))


# # A way to visualize the distribution of the words
# plt.close()
# plt.hist(num_words, bins=20)
# plt.show()

# print a subset of 50 based on stability
# filenames_with_stability.sort(key=lambda x: x[1]) # sort based on stability
# for i in range(5, 505, 10):
#     print("<" +filenames_with_stability[i][0] + "> has stability on gpt-4o of", filenames_with_stability[i][1])

files_3x_unstable = [x for x in filenames_with_stability if x[1] < 1 and x[2] < 1 and x[3] < 1]
files_3x_unstable.sort(key=lambda x: x[1]+x[2]+x[3], reverse=True)
for file in files_3x_unstable:
    print("{:<20} gpt {:.3f} claude {:.3f} gemini {:.3f} words {:3d}". format(file[0], file[1], file[2], file[3], file[4]))






