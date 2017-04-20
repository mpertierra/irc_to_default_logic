import penman


class AMRCodecNoInvert(penman.AMRCodec):
    def is_relation_inverted(self, relation):
        return False

    def invert_relation(self, relation):
        raise Exception("Unexpected!")

CODEC = AMRCodecNoInvert


def read_from_file(filepath, graph=False):
    graphs = penman.load(filepath, cls=CODEC)
    if graph:
        return graphs
    codec = CODEC()
    amrs = []
    for g in graphs:
        amr = codec.encode(g)
        amrs.append(amr)
    return amrs



