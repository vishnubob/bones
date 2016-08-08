
class CoverageMap(object):
    def __init__(self):
        pass
    
    def parse_coverage_file(self, coverage_fn):
        f = open(coverage_fn)
        last_coord = 0
        for line in f:
            line = line.strip()
            (reference_name, coord, coverage) = line.split('\t')
            last_coord = coord


