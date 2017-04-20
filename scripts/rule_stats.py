import os
from os.path import join, splitext
import re
import json
from irc_crawler import IRCCrawler
from nltk.tokenize import word_tokenize
import numpy as np
import matplotlib.pyplot as plt

def only_letters(text):
    pattern = re.compile("[^a-zA-Z]+", re.UNICODE)
    return pattern.sub("", text)

def find_rules(section):
    rules = dict()
    for level in section.preorder_transversal():
        if level.heading is None:
            continue
        heading = only_letters(level.heading).lower()
        level_rules = dict()
        if heading == "generalrule":
            level_rules["general-rule"] = level.get_sentences()
        elif heading == "exceptions":
            level_rules["exceptions"] = level.get_sentences()
        elif heading == "specialrules":
            level_rules["special-rules"] = level.get_sentences()
        if len(level_rules) > 0:
            rules[level.id.val] = level_rules
    return rules

def dump_rules(rules_filename):
    all_rules = dict()
    crawler = IRCCrawler()
    for section in crawler.iterate_over_sections():
        rules = find_rules(section)
        if len(rules) == 0:
            continue
        all_rules[section.id.val] = rules
    with open(rules_filename, 'w') as f:
        json.dump(all_rules, f, indent=4, sort_keys=True, encoding="UTF-8")
    return all_rules

def dump_stats(all_rules, persection_rule_stats_filename, overall_rule_stats_filename):
    overall_token_counts = {
        "general-rule": [],
        "exceptions": [],
        "special-rules": []
    }
    persection_rule_stats = dict()
    basename = splitext(persection_rule_stats_filename)[0]
    for section_id in all_rules:
        rules = all_rules[section_id]
        section_token_counts = {
            "general-rule": [],
            "exceptions": [],
            "special-rules": []
        }
        for level_id in rules:
            level_rules = rules[level_id]
            for rule_type in level_rules:
                rule = level_rules[rule_type]
                for sentence in rule:
                    token_count = len(word_tokenize(sentence))
                    section_token_counts[rule_type].append(token_count)
        for rule_type in overall_token_counts:
            overall_token_counts[rule_type].extend(section_token_counts[rule_type])
            if len(section_token_counts[rule_type]) > 0:
                if section_id not in persection_rule_stats:
                    persection_rule_stats[section_id] = dict()
                persection_rule_stats[section_id][rule_type] = calc_stats(section_token_counts[rule_type])

  
    with open(persection_rule_stats_filename, 'w') as f:
        json.dump(persection_rule_stats, f, indent=4, sort_keys=True, encoding="UTF-8")

    with open(overall_rule_stats_filename, 'w') as f:
        overall_rule_stats = dict()
        for rule_type in overall_token_counts:
            if len(overall_token_counts[rule_type]) == 0:
                overall_rule_stats[rule_type] = dict()
            else:
                overall_rule_stats[rule_type] = calc_stats(overall_token_counts[rule_type])
        json.dump(overall_rule_stats, f, indent=4, sort_keys=True, encoding="UTF-8")

    if args.plot:
        basename = splitext(persection_rule_stats_filename)[0]
        for section_id in persection_rule_stats:
            for rule_type in persection_rule_stats[section_id]:
                stats = persection_rule_stats[section_id][rule_type]
                title = "{}_{}".format(section_id.encode('ascii', 'ignore'), rule_type)
                filename = "{}_{}.pdf".format(basename, title)
                plot_hist(stats, filename, title)
        basename = splitext(overall_rule_stats_filename)[0]
        for rule_type in overall_rule_stats:
            stats = overall_rule_stats[rule_type]
            title = "overall_{}".format(rule_type)
            filename = "{}_{}.pdf".format(basename, title)
            plot_hist(stats, filename, title)
        
        
def plot_hist(stats, filename, title_str):
    hist = stats["histogram"]["hist"]
    bin_edges = np.array(stats["histogram"]["bin-edges"])

    width = np.diff(bin_edges)
    center = (bin_edges[:-1] + bin_edges[1:]) / 2

    fig, ax = plt.subplots()
    ax.bar(center, hist, align='center', width=width)
    ax.set_xticks(bin_edges)
    plt.setp(ax.get_xticklabels(), fontsize=4, rotation='vertical')
    plt.title(title_str)
    fig.savefig(filename)
    plt.close()

        
def calc_stats(counts):
    hist, bin_edges = np.histogram(counts, bins="auto")
    stats = {
        "number": len(counts),
        "min": np.amin(counts),
        "max": np.amax(counts),
        "range": np.ptp(counts),
        "25th-percentile": np.percentile(counts, 25),
        "50th-percentile": np.percentile(counts, 50),
        "75th-percentile": np.percentile(counts, 75),
        "median": np.median(counts),
        "mean": np.mean(counts),
        "std": np.std(counts),
        "var": np.var(counts),
        "histogram": {"hist": hist.tolist(), "bin-edges": bin_edges.tolist()}
    }
    return stats

def main(args):
    # Make directory to store our output files
    os.mkdir(args.output_dir)
    # Dump all rules here, level-id => general-rule/exceptions/special-rules => rule
    rules_filename = join(args.output_dir, "rules.json")

    # Dump stats here
    persection_rule_stats_filename = join(args.output_dir, "persection_rule_stats.json")
    overall_rule_stats_filename = join(args.output_dir, "overall_rule_stats.json")

    all_rules = dump_rules(rules_filename)

    dump_stats(all_rules, persection_rule_stats_filename, overall_rule_stats_filename)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Calculate stats on rules in Internal Revenue Code.")
    parser.add_argument("--output-dir",
                        type=str,
                        default="rule_stats")
    parser.add_argument("--plot",
                        action="store_true",
                        default=False)
    args = parser.parse_args()
    main(args)
