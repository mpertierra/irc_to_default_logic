import requests
from nltk.sem.boxer import BoxerOutputDrsParser, NltkDrtBoxerDrsInterpreter


class CCBoxerAPIException(Exception):
    pass

class CCBoxerAPI(object):
    def __init__(self, ip_address="128.52.170.142", port=8888):
        self._base_url = "http://{0}:{1}/json/pipeline".format(ip_address, port)
        ### Taken from https://github.com/nltk/nltk/blob/develop/nltk/sem/boxer.py
        self._boxer_drs_interpreter = NltkDrtBoxerDrsInterpreter()

    def interpret(self, sentences, debug=False):
        payload = u'\n'.join(sentences)
        options = {"instantiate": "true", "format": "prolog"}
        boxer_out = self._send_request(payload, options=options)
        if debug: print "Server Error Message: |{}|".format(boxer_out["err"].replace('\n', '-newline-'))
        drs_dict = self._parse_to_drs_dict(boxer_out["out"], False)
        if len(drs_dict) == 0:
            raise CCBoxerAPIException("Recieved empty response.")
        # drs_dict has form {'1': DRS1, '2': DRS2, ... }
        drss = [None]*len(drs_dict)
        for s in drs_dict:
            index = int(s) - 1
            assert drss[index] is None
            drss[index] = drs_dict[s]
        return drss

    def _send_request(self, payload, options=dict()):
        params = ""
        if len(options) > 0:
            params = '?' + '&'.join([key + '=' + value for (key, value) in options.iteritems()])
        url = self._base_url + params
        response = requests.post(url, data=payload.encode("UTF-8"), headers={'Content-type': 'text/plain; charset=UTF-8'})
        try:
            response.raise_for_status()
        except requests.HTTPError, error:
            raise CCBoxerAPIException(str(error))
        return response.json()

    ### Taken from https://github.com/nltk/nltk/blob/develop/nltk/sem/boxer.py
    def _parse_to_drs_dict(self, boxer_out, use_disc_id):
        lines = boxer_out.split('\n')
        drs_dict = {}
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith('id('):
                comma_idx = line.index(',')
                discourse_id = line[3:comma_idx]
                if discourse_id[0] == "'" and discourse_id[-1] == "'":
                    discourse_id = discourse_id[1:-1]
                drs_id = line[comma_idx+1:line.index(')')]
                i += 1
                line = lines[i]
                assert line.startswith('sem({0},'.format(drs_id))
                if line[-4:] == "').'":
                    line = line[:-4] + ")."
                assert line.endswith(').'), "can't parse line: {0}".format(line)

                search_start = len('sem({0},['.format(drs_id))
                brace_count = 1
                drs_start = -1
                for j,c in enumerate(line[search_start:]):
                    if(c == '['):
                        brace_count += 1
                    if(c == ']'):
                        brace_count -= 1
                        if(brace_count == 0):
                            drs_start = search_start + j + 1
                            if line[drs_start:drs_start+3] == "','":
                                drs_start = drs_start + 3
                            else:
                                drs_start = drs_start + 1
                            break
                assert drs_start > -1

                drs_input = line[drs_start:-2].strip()
                parsed = self._parse_drs(drs_input, discourse_id, use_disc_id)
                drs_dict[discourse_id] = self._boxer_drs_interpreter.interpret(parsed)
            i += 1
        return drs_dict

    ### Taken from https://github.com/nltk/nltk/blob/develop/nltk/sem/boxer.py
    def _parse_drs(self, drs_string, discourse_id, use_disc_id):
        return BoxerOutputDrsParser([None,discourse_id][use_disc_id]).parse(drs_string)


def example():
    ccboxer = CCBoxerAPI()
    sentences = ["Every man loves a woman.", "Every dog loves a man."]
    drss = ccboxer.interpret(sentences, debug=True)
    for i, drs in enumerate(drss):
        fol = drs.fol()
        print u"SENTENCE: {0}".format(sentences[i])
        print u"DRS:"
        drs.pretty_print()
        print u"FOL: {0}".format(fol)

if __name__ == "__main__":
    example()
