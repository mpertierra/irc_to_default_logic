# This Python file uses the following encoding: UTF-8
import re
import irc_crawler


def regex(pattern, flags=re.UNICODE | re.IGNORECASE):
    return re.compile(pattern, flags)

# First parameter specifies the lead-in, second parameter specifies the definition type
DEFINITION_TEMPLATE = ur"{0}([^,]+), the term (?:(“[^”]+”)|(‘[^’]+’)) {1}"

# See https://legcounsel.house.gov/HOLC/Drafting_Legislation/draftstyle.pdf
LEAD_INS = [
    u"For purposes of this",
    u"In this",
    u"As used in this"
]
ALL_LEAD_INS_PATTERN = u"(?:{})".format(u"|".join(LEAD_INS))

DEFINITION_TYPES = [
    u"means",
    u"includes",
    u"does not include",
    u"has the meaning",
    u"shall include",
    u"shall not include"
]
ALL_DEFINITION_TYPES_PATTERN = u"(?:{})".format(u"|".join(DEFINITION_TYPES))

LEAD_INS_REGEXS = []
# All possible lead-ins (not necessarily the ones in LEAD_INS)
LEAD_INS_REGEXS += [regex(DEFINITION_TEMPLATE.format(u"", ALL_DEFINITION_TYPES_PATTERN))]
# Only the lead-ins in LEAD_INS
LEAD_INS_REGEXS += [regex(DEFINITION_TEMPLATE.format(li, ALL_DEFINITION_TYPES_PATTERN)) for li in LEAD_INS]

TERM_DEFINITION_REGEXS = []
# All possible definition types (not necessarily the ones in DEFINITION_TYPES)
TERM_DEFINITION_REGEXS += [regex(DEFINITION_TEMPLATE.format(ALL_LEAD_INS_PATTERN, u""))]
# Only the definition types in DEFINITION_TYPES
TERM_DEFINITION_REGEXS += [regex(DEFINITION_TEMPLATE.format(ALL_LEAD_INS_PATTERN, dt)) for dt in DEFINITION_TYPES]

# Any possible lead-in and any possible definition-type
TERM_REGEX1 = regex(DEFINITION_TEMPLATE.format(u"", u""))
# No lead-in, no definition-type, just look for "the term [someterm]"
TERM_REGEX2 = regex(ur"the term (?:(“[^”]+”)|(‘[^’]+’))")
# No lead-in, just look for "the term [someterm] [somedefinitiontype]"
TERM_REGEX3 = regex(ur"the term (?:(“[^”]+”)|(‘[^’]+’)) {0}".format(ALL_DEFINITION_TYPES_PATTERN))


def count_pattern_matches(patterns):
    crawler = irc_crawler.IRCCrawler()
    num_patterns = len(patterns)
    match_counts = [0]*num_patterns
    for section in crawler.iterate_over_sections():
        text = u" ".join(section.get_sentences())
        for i in xrange(num_patterns):
            pattern = patterns[i]
            matches = pattern.findall(text)
            match_counts[i] += len(matches)
    return match_counts

def prepare_output(patterns, match_counts):
    assert len(patterns) == len(match_counts)
    num_patterns = len(patterns)
    output = []
    for i in xrange(num_patterns):
        pattern_str = patterns[i].pattern
        match_count = match_counts[i]
        output.append(u"PATTERN #{0}: /{1}/".format(i, pattern_str))
        output.append(u"MATCH COUNT #{0}: {1}\n".format(i, match_count))
    return u"\n".join(output)

def main(args):
    patterns = [TERM_REGEX1, TERM_REGEX2, TERM_REGEX3]
    patterns += LEAD_INS_REGEXS
    patterns += TERM_DEFINITION_REGEXS
    match_counts = count_pattern_matches(patterns)
    output = prepare_output(patterns, match_counts)
    with open(args.output_file, 'w') as f:
        f.write(output.encode("UTF-8"))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Calculate counts on pattern matches used for term definitions in Internal Revenue Code.")
    parser.add_argument("--output-file",
                        type=str,
                        default="pattern_counts.txt")
    args = parser.parse_args()
    main(args)
