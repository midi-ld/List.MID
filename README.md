# List.MID
A MIDI-based benchmark for RDF lists

## RDF List models

The currently supported RDF list models are:

- **uri** for lists that encode their ordering via URI elements (e.g. integer identifiers)
- **prop_number** for lists that encode their ordering via a numeric property
- **prop_time** for lists that encoder their ordering via a timestamp
- **seq** for lists using the [`rdf:Seq`](https://www.w3.org/TR/rdf-schema/#ch_seq) facility
- **list** for lists using the [`rdf:List`](https://www.w3.org/TR/rdf-schema/#ch_list) facility
- **sop** for lists using modelling solutions with the same expressivity as the [Sequence Ontology Pattern](http://ontologydesignpatterns.org/wiki/Submissions:Sequence)

## Data generator

We propose a data generator based on the `midi2rdf` algorithm that is compatible with all the aforementioned RDF list models. This specific version of `midi2rdf` is included in the [src](/src) directory. The syntax is:

```
midi2rdf [-h]
         [--format [{xml,n3,turtle,nt,pretty-xml,trix,trig,nquads}]]
         [--gz] [--order [{uri,prop_number,prop_time,seq,list,sop}]]
         [--version]
         filename [outfile]
```

The executable files can be found in the [src](/src) directory.

For example, to generate RDF lists according to the **seq** model (`rdf:Seq`) on a MIDI of 30k events, we do

```
midi2rdf.py --format turtle --order seq midi/30k.mid ex_seq_30k.ttl
```

An example of the resulting RDF file can be found at [data/30k-seq.ttl](/data/30k-seq.ttl). Various other examples of input MIDI data and output benchmark data can be found in the [midi](/midi) and [data](/data) directories, respectively.

## Queries

The SPARQL queries retrieving the list content according to these models can be found in the [queries](/queries) directory. The queries cover for three different use cases (the wildcard \* is used as shorthand for the different RDF list models):

- **ALL-\*.sparql**. Retrieve all elements of an RDF list in their sequential order
- **A950-\*.sparql**. Retrieve *one* element of an RDF list (element in position 950 in this example)
- **W100-850-\*.sparql**. Retrieve an *a-b window* of all RDF list elements between elements *a* and *b* (from 100 to 850 in this example)

## MIDI Linked Data lists

This benchmark uses the data in the [MIDI Linked Data cloud dataset](https://www.albertmeronyo.org/wp-content/uploads/2017/07/ISWC2017_paper_343.pdf) to generate RDF lists according to various RDF list models.

**Size**. To aid the selection of source MIDI lists of the desired sized, [this query](http://grlc.io/api/midi-ld/queries/#/default/get_events_count_per_track_piece) will return all MIDI tracks of the dataset and their number of (linked) events. Since the query is quite expensive, we have included a dump of the response in the file [list-sizes.csv.gz](list-sizes.csv.gz). The list can be searched for the identifier of a MIDI file that contains the list of the chosen size.

Use that identifier as the parameter of [this query](http://grlc.io/api/midi-ld/queries/#/default/get_pattern_graph) to download an RDF dump of the MIDI. To convert that dump into a MIDI file for the following step, use the `rdf2midi` program included in the [src](/src) directory.

We provide a number of examples in the [midi](/midi) directory, with MIDI lists of 1k, 30k, 60k, 90k, and 120k elements.
