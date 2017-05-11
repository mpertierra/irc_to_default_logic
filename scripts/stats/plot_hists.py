import json
import numpy as np
import math
import matplotlib.pyplot as plt


def plot_definition_hist(counts, crash_counts, filename, title, cutoff=float('inf'), bins="auto"):
    counts = np.array(counts)
    outlier_mask = is_outlier(counts, cutoff)
    num_outliers = sum(outlier_mask)
    counts = counts[~outlier_mask]
    print("{} outliers for plot in file {} with cutoff {}".format(num_outliers, filename, cutoff))

    fig, ax = plt.subplots()
    ax.hist(counts, bins, alpha=0.5, label='total')
    _, bin_edges, _ = ax.hist(crash_counts, bins, alpha=0.5, label='crash')
    ax.legend(loc='upper right')
    ax.set_xlabel("Number of tokens")
    ax.set_ylabel("Frequency")
    ax.set_xticks(bin_edges)
    plt.setp(ax.get_xticklabels(), fontsize=8, rotation='vertical')
    if not math.isinf(cutoff): ax.set_xlim([0, cutoff])
    ax.set_title(title)
    plt.tight_layout()
    fig.savefig(filename)
    plt.close()

def plot_rule_hist(counts_by_ruletype, crash_counts, filename, cutoff=float('inf'), bins="auto"):
    fig, axes = plt.subplots(nrows=len(counts_by_ruletype))

    i = 0
    for rule_type, counts in counts_by_ruletype.items():
        ax = axes[i]
        counts = np.array(counts)
        outlier_mask = is_outlier(counts, cutoff)
        num_outliers = sum(outlier_mask)
        counts = counts[~outlier_mask]
        print("{} outliers for plot for rule-type {} in file {} with cutoff {}".format(num_outliers, rule_type, filename, cutoff))
        ax.hist(counts, bins, alpha=0.5, label='total')
        _, bin_edges, _ = ax.hist(crash_counts[rule_type], bins, alpha=0.5, label='crash')
        ax.legend(loc='upper right')
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

def main():
    with open("semparsing_stats.json", 'r') as f:
        semparsing_stats = json.load(f)

    with open("definition_stats/overall_definition_stats.json", 'r') as f:
        overall_definition_stats = json.load(f)

    with open("rule_stats/overall_rule_stats.json", 'r') as f:
        overall_rule_stats = json.load(f)

    definition_crash_counts = []
    for section_id in semparsing_stats["definitions"]:
        token_counts = semparsing_stats["definitions"][section_id]
        definition_crash_counts.extend(token_counts)

    rule_crash_counts = {
        "general-rule": [],
        "exceptions": [],
        "special-rules": []
    }
    
    for rule_type in semparsing_stats["rules"]:
        for section_id in semparsing_stats["rules"][rule_type]:
            token_counts = semparsing_stats["rules"][rule_type][section_id]
            rule_crash_counts[rule_type].extend(token_counts)

    plot_definition_hist(
        overall_definition_stats["counts"],
        definition_crash_counts,
        "defplot.pdf",
        "definitions",
        cutoff=300,
        bins=[10*i for i in xrange(30)]
    )
    plot_rule_hist(
        {rule_type: stats["counts"] for rule_type, stats in overall_rule_stats.items()},
        rule_crash_counts,
        "ruleplot.pdf",
        cutoff=300,
        bins=[10*i for i in xrange(30)]
    )

if __name__ == "__main__":
    main()

