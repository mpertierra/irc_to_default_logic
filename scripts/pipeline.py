import irc_crawler
import definition_extractor
import rule_extractor
import candc_boxer_api
import parse_amr
import default_logic
import amr2fol
from nltk.sem.logic import Expression


def parse_fol(sentences):
    ccboxer = candc_boxer_api.CCBoxerAPI()
    # drss = ccboxer.interpret(sentences)
    # Hack to make sure this doesn't fail because input is too large
    drss = [ccboxer.interpret([sentence]) for sentence in sentences]
    # results = [drs.fol() for drs in drss]
    results = []
    for drs in drss:
        assert len(drs) == 1
        results.append(drs[0].fol())
    return results

def stringify_output(sentences, results):
    output = []
    for s, r in zip(sentences, results):
        output.extend([s, u'\n', unicode(r), u'\n\n'])
    return u''.join(output)

def main(args):
    crawler = irc_crawler.IRCCrawler()
    try:
        level = crawler.get_level(args.level_id)
    except irc_crawler.LevelDoesNotExistException:
        raise Exception("Invalid level-id arg: {0}".format(args.level_id))

    # TODO
    # Do we just take all the sentences within the given 'level'?
    # Or can C&C/Boxer and Cornell AMR parse phrases?
    # sentences = ["Every man loves a woman.", "Every man has a cat."]
    # sentences = level.get_sentences() # This will not work with C&C/Boxer when sentences are long
    sentences = level.get_sentence_fragments()

    if args.representation == "fol":
        try:
            results = parse_fol(sentences)
        except candc_boxer_api.CCBoxerAPIException:
            print("Warning: C&C/Boxer API Failed. Using AMR parser and AMR to FOL translation instead.")
            amr_results = parse_amr.parse_amr(sentences, parser="camr")
            results = [amr2fol.translate(amr) for amr in amr_results]
    elif args.representation == "amr":
        results = parse_amr.parse_amr(sentences, parser="camr")
    elif args.representation == "amr2fol":
        # CAMR seems to do better than Cornell AMR
        amr_results = parse_amr.parse_amr(sentences, parser="camr")
        results = [amr2fol.translate(amr) for amr in amr_results]
    elif args.representation == "default_logic":
        # TODO #1
        # Need to form backround theory by extracting definitions
        # TODO #2
        # Maybe the caller will have a set of keywords to look for? (e.g. interest, deductible, etc.)
        # TODO #3
        # Need user to specify part of background theory.
        # However, this could actually be done later, when we actually want to "run" the default logic.
        definitions_as_fol = definition_extractor.fol_definitions(level)
        background_theory = [Expression.fromstring(d["fol"]) for d in definitions_as_fol]

        scope_level_id = level.id.get_section_id()
        scope_level = crawler.get_level(scope_level_id)
        if args.dl_hack:
            if scope_level_id == "s163":
                # Missing "obvious" rule that personal interest is interest; "interest" is not a defined term
                background_theory.append(Expression.fromstring(u"all x.({}(x) -> interest(x))".format(definition_extractor.term_to_predicate(u"personal interest"))))
                # Missing the user's background info (namely that the user's interest is personal interest; the user wants to know if it is deductible)
                background_theory.append(Expression.fromstring(u"{}(y)".format(definition_extractor.term_to_predicate(u"personal interest"))))
                default_rules = [
                    Expression.fromstring(u"all x.({}(x) -> deductible(x))".format(definition_extractor.term_to_predicate(u"qualified residence interest"))),
                    Expression.fromstring(u"all x.({}(x) -> -deductible(x))".format(definition_extractor.term_to_predicate(u"personal interest"))),
                    Expression.fromstring(u"all x.({}(x) -> deductible(x))".format(definition_extractor.term_to_predicate(u"interest")))
                ]
            else:
                default_rules = []
                print("Warning: Hard-coding option not a available for section {}.".format(scope_level_id))
        else:
            default_rules_sentences = rule_extractor.extract_rules(scope_level)

            try:
                default_rules = [parse_fol(sentences) for sentences in default_rules_sentences]
            except candc_boxer_api.CCBoxerAPIException:
                print("Warning: C&C/Boxer API Failed. Using AMR parser and AMR to FOL translation instead.")
                default_rules = []
                for sentences in default_rules_sentences:
                    amr_results = parse_amr.parse_amr(sentences, parser="camr")
                    results = [amr2fol.translate(amr) for amr in amr_results]
                    default_rules.extend(results)

            default_rules = [Expression.fromstring(e) for e in default_rules]
            # Earlier rules have lower priority
            default_rules.reverse()

        default_theory = default_logic.SupernormalDefaultTheory(background_theory, default_rules)
        with open(args.output_file, 'w') as f:
            f.write("# Background Theory:\n")
            for e in default_theory.background_theory:
                f.write(unicode(e).encode("UTF-8"))
                f.write("\n")
            f.write("# Default Rules:\n")
            for e in default_theory.default_rules:
                f.write(unicode(e).encode("UTF-8"))
                f.write("\n")
        return
    else:
        raise Exception("Invalid representation arg: {0}".format(args.representation))

    output = stringify_output(sentences, results)
    with open(args.output_file, 'w') as f:
        f.write(output.encode("UTF-8"))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Parse sections from the Internal Revenue Code.")
    parser.add_argument("--level-id",
                        type=str,
                        default="s163/h/2",
                        help="Specifies the level (section, subsection, paragraph, etc.) to find. " + \
                              "Should have pattern s[section]/[subsection]/[paragraph]/[subparagraph]/[clause]/[subclause]/[item]. " + \
                              "For example, 's163/h/1' specifies section 163, subsection h, paragraph 1.")
    parser.add_argument("--representation", choices=["fol", "amr", "amr2fol", "default_logic"], default="fol")
    parser.add_argument("--output-file", type=str, default="pipeline.out")
    parser.add_argument("--dl-hack", action="store_true", help="Hard-code part of default logic for section 163(h).")
    args = parser.parse_args()
    main(args)