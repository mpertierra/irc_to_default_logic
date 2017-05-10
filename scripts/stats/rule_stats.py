import os
from os.path import join, splitext
import json
from .. import irc_crawler
from .. import rule_extractor
from nltk.tokenize import word_tokenize
import numpy as np
import math
import matplotlib.pyplot as plt


def dump_rules(rules_filename):
    all_rules = dict()
    crawler = irc_crawler.IRCCrawler()
    for section in crawler.iterate_over_sections():
        rules = rule_extractor.extract_rules(section)
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
        basename = splitext(overall_rule_stats_filename)[0]
        counts_by_ruletype = {rule_type: stats["counts"] for rule_type, stats in overall_rule_stats.items()}
        filename = "{}.pdf".format(basename)
        plot_hist(counts_by_ruletype, filename, cutoff=300, bins=[10*i for i in xrange(30)])

    if args.plot_sections:
        basename = splitext(persection_rule_stats_filename)[0]
        for section_id in persection_rule_stats:
            counts_by_ruletype = {rule_type: stats["counts"] for rule_type, stats in persection_rule_stats[section_id].items()}
            filename = "{}_{}.pdf".format(basename, section_id.encode('ascii', 'ignore'))
            plot_hist(counts_by_ruletype, filename)

def plot_hist(counts_by_ruletype, filename, cutoff=float('inf'), bins="auto"):
    fig, axes = plt.subplots(nrows=len(counts_by_ruletype))

    i = 0
    for rule_type, counts in counts_by_ruletype.items():
        ax = axes[i]
        counts = np.array(counts)
        outlier_mask = is_outlier(counts, cutoff)
        num_outliers = sum(outlier_mask)
        counts = counts[~outlier_mask]
        print("{} outliers for plot for rule-type {} in file {} with cutoff {}".format(num_outliers, rule_type, filename, cutoff))
        _, bin_edges, _  = ax.hist(counts, bins=bins)
        ax.set_xlabel("Number of tokens")
        ax.set_ylabel("Frequency")
        ax.set_xticks(bin_edges)
        plt.setp(ax.get_xticklabels(), fontsize=8, rotation='vertical')
        if not math.isinf(cutoff): ax.set_xlim([0, cutoff])
        ax.set_title(rule_type)
        i += 1

    plt.tight_layout()
    fig.savefig(filename)
    plt.close()

def is_outlier(counts, cutoff):
    return np.array([c > cutoff for c in counts])

def calc_stats(counts):
    stats = {
        "counts": sorted(counts),
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
        "var": np.var(counts)
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
                        help="Generate plot for token counts over all rules.")
    parser.add_argument("--plot-sections",
                        action="store_true",
                        help="Generate plot for each section for token counts over rules.")
    args = parser.parse_args()
    main(args)
