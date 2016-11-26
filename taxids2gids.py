# Preparation: download and extract NCBI taxdumpfiles
# wget ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz && tar zxvf taxdump.tar.gz
# and download refseq catalogue
# wget ftp://ftp.ncbi.nlm.nih.gov/refseq/release/release-catalog/RefSeq-release79.catalog.gz
# preformat refseq catalogue with
# zcat RefSeq-release79.catalog.gz | awk '{print $4 "\t" $1}' | gzip >gi_taxid_refseq.gz
# useful info: nucl.dmp has ~600M lines, refseq catalog has ~110M lines

import sys
import gzip
import argparse

parser = argparse.ArgumentParser(description='Extract GI numbers from NCBI catalogue files based on taxonomy')
parser.add_argument('-i', '--include', type=int, nargs='+', help='taxids of groups to include. GI numbers belonging to all child taxids of these will be included in the results', required=True)
parser.add_argument('-e', '--exclude', type=int, nargs='+', help='taxids of groups to exclude. GI numbers belonging to all child taxids of these will be excluded from the results', default=[])
parser.add_argument('-f', '--file', help="name of the input file which maps GI number to taxid", required=True)
parser.add_argument('--silent', help="suppress progress output", default=False, action='store_true')
args = parser.parse_args()



def get_children_recursive(taxid):
    result = []
    # for all children of this taxid...
    for child in parent2child[taxid]:
        # first add the child itself
        result.append(child)
        # then if the child has children...
        if child in parent2child:
            # add the children of the child
            # note that we use extend() here rather than append()
            # extend() is the equivalent of concatenating two lists
            # if we use append() here then we get a set of nested list which is not what we want!
            result.extend(get_children_recursive(child))
    return result

def read_taxonomy():
    #store parent to child relationships
    sys.stderr.write("reading NCBI taxonomy")
    parent2child = {}

    processed = 0
    nodes = open("nodes.dmp")
    for processed, line in enumerate(nodes):
        if processed %100000 == 0:
            sys.stderr.write('.')
            sys.stderr.flush()
        taxid, parent = line.rstrip('\t|\n').split("\t|\t")[0:2]
        taxid = int(taxid)
        parent = int(parent)
        if parent not in parent2child:
            parent2child[parent] = []
        parent2child[parent].append(taxid)
    sys.stderr.write("\n")
    return parent2child

#store parent to child relationships
parent2child = read_taxonomy()

#@profile
def slow_function():


    taxids_to_include = set()
    for taxid in args.include:
        sys.stderr.write('Including children of taxid {}\n'.format(taxid))
        taxids_to_include.update(get_children_recursive(taxid))

    taxids_to_exclude = set()
    for taxid in args.exclude:
        sys.stderr.write('Excluding children of taxid {}\n'.format(taxid))
        taxids_to_exclude.update(get_children_recursive(taxid))


    sys.stderr.write("including {:,} taxids in total\n".format(len(taxids_to_include)))
    sys.stderr.write("excluding {:,} taxids in total\n".format(len(taxids_to_exclude)))

    taxids_whitelist = taxids_to_include - taxids_to_exclude
    sys.stderr.write("final whitelist includes {:,} taxids\n".format(len(taxids_whitelist)))

    found = 0
    if args.file.endswith('.gz'):
        f = gzip.open(args.file, 'rt')
    else:
        f = open(args.file, 'rt')

    for lineno, line in enumerate(f):
        if lineno > 1000000000000:
            return #for testing
        if lineno %1000000 == 0 and not args.silent:
            sys.stderr.write("processed {:,} input lines\n".format(lineno))
        #sys.stderr.write("line is" + line)
        (gi,taxid) = line.split('\t')
        taxid = int(taxid)
        #print(taxid, gi)
        if taxid in taxids_whitelist:
            sys.stdout.write(gi + '\n')
            found += 1
    sys.stderr.write("found {:,} GI numbers\n".format(found))
slow_function()
