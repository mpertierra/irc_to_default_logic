import os
from os.path import join, splitext
import json
from irc_crawler import IRCCrawler
import definition_extractor
from nltk.tokenize import word_tokenize
import numpy as np
import matplotlib.pyplot as plt


def dump_definitions(defined_terms_filename, definitions_filename):
    all_definitions = dict()
    crawler = IRCCrawler()
    for section in crawler.iterate_over_sections():
        defined_terms, definitions = definition_extractor.extract_definitions(section)
        if len(defined_terms) == 0:
            continue
        all_definitions[section.id.val] = definitions
        with open(defined_terms_filename, 'a') as f:
            for term in defined_terms:
                f.write(u"{}\n".format(term).encode("UTF-8"))
    with open(definitions_filename, 'w') as f:
        json.dump(all_definitions, f, indent=4, sort_keys=True, encoding="UTF-8")
    return all_definitions

def dump_stats(all_definitions, persection_definition_stats_filename, overall_definition_stats_filename):
    overall_token_counts = []
    persection_definition_stats = dict()
    for section_id in all_definitions:
        definitions = all_definitions[section_id]
        section_token_counts = []
        for defined_term in definitions:
            definition = definitions[defined_term]["sentence"]
            token_count = len(word_tokenize(definition))
            section_token_counts.append(token_count)
        overall_token_counts.extend(section_token_counts)
        persection_definition_stats[section_id] = calc_stats(section_token_counts)

    with open(persection_definition_stats_filename, 'w') as f:
        json.dump(persection_definition_stats, f, indent=4, sort_keys=True, encoding="UTF-8")

    with open(overall_definition_stats_filename, 'w') as f:
        overall_definition_stats = calc_stats(overall_token_counts)
        json.dump(overall_definition_stats, f, indent=4, sort_keys=True, encoding="UTF-8")

    if args.plot:
        basename = splitext(persection_definition_stats_filename)[0]
        for section_id in persection_definition_stats:
            stats = persection_definition_stats[section_id]
            title = section_id.encode('ascii', 'ignore')
            filename = "{}_{}.pdf".format(basename, title)
            plot_hist(stats, filename, title)
        stats = overall_definition_stats
        title = "overall"
        filename = overall_definition_stats_filename.replace('.json','.pdf')
        plot_hist(stats, filename, title)


def plot_hist(stats, filename, title_str):
    # FIXME: histogram for overall stats can't display bin edges because
    # there's too many, it's unreadable. so we don't show them
    hist = stats["histogram"]["hist"]
    bin_edges = np.array(stats["histogram"]["bin-edges"])

    width = np.diff(bin_edges)
    center = (bin_edges[:-1] + bin_edges[1:]) / 2

    fig, ax = plt.subplots()
    ax.bar(center, hist, align='center', width=width)
    # See the FIXME above 
    # ax.set_xticks(bin_edges)
    # plt.setp(ax.get_xticklabels(), fontsize=4, rotation='vertical')
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
    # Dump all defined terms here
    defined_terms_filename = join(args.output_dir, "defined_terms.txt")
    # Dump all definitions here, section-id => defined-term => definition
    definitions_filename = join(args.output_dir, "definitions.json")

    # Dump stats here
    persection_definition_stats_filename = join(args.output_dir, "persection_definition_stats.json")
    overall_definition_stats_filename = join(args.output_dir, "overall_definition_stats.json")

    all_definitions = dump_definitions(defined_terms_filename, definitions_filename)

    dump_stats(all_definitions, persection_definition_stats_filename, overall_definition_stats_filename)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Calculate stats on term definitions in Internal Revenue Code.")
    parser.add_argument("--output-dir",
                        type=str,
                        default="definition_stats")
    parser.add_argument("--plot",
                        action="store_true")
    args = parser.parse_args()
    main(args)
