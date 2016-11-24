# Preparation: download and extract NCBI taxdumpfiles
# wget ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz && tar zxvf taxdump.tar.gz
# and download refseq catalogue
# wget ftp://ftp.ncbi.nlm.nih.gov/refseq/release/release-catalog/RefSeq-release79.catalog.gz

import sys
import gzip

include_taxids = 10239 #viruses
exclude_taxids = 131567 # cellular organisms


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
    sys.stdout.write("reading NCBI taxonomy")
    parent2child = {}

    processed = 0
    nodes = open("nodes.dmp")
    for processed, line in enumerate(nodes):
        if processed %100000 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()
        taxid, parent = line.rstrip('\t|\n').split("\t|\t")[0:2]
        taxid = int(taxid)
        parent = int(parent)
        if parent not in parent2child:
            parent2child[parent] = []
        parent2child[parent].append(taxid)
    print("")
    return parent2child



#store parent to child relationships
parent2child = read_taxonomy()

taxids_to_include = set(get_children_recursive(include_taxids))
taxids_to_exclude = set(get_children_recursive(exclude_taxids))
taxids_whitelist = taxids_to_include - taxids_to_exclude

print("including {} taxids".format(len(taxids_to_include)))
print("excluding {} taxids".format(len(taxids_to_exclude)))
print("final whitelist includes {} taxids".format(len(taxids_whitelist)))

with gzip.open('RefSeq-release79.catalog.gz') as f:
    with open('gids.txt', 'w') as output:
        for lineno, line in enumerate(f):
            if lineno %1000000 == 0:
                print("processed {} refseq lines".format(lineno))
            taxid, _, _, gi = line.split('\t')[0:4]
            taxid = int(taxid)
            #print(taxid, gi)
            if taxid in taxids_whitelist:
                output.write(gi + '\n')
