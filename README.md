# List.MID
A MIDI-based benchmark for RDF lists

## MIDI Linked Data lists

This benchmark uses the data in the [MIDI Linked Data cloud dataset](https://www.albertmeronyo.org/wp-content/uploads/2017/07/ISWC2017_paper_343.pdf) to generate RDF lists according to various RDF list models.

## RDF List models

The currently supported RDF list models are:

- **uri** for lists that encode their ordering via URI elements (e.g. integer identifiers)
- **prop_number** for lists that encode their ordering via a numeric property
- **prop_time** for lists that encoder their ordering via a timestamp
- **seq** for lists using the [`rdf:Seq`](https://www.w3.org/TR/rdf-schema/#ch_seq) facility
- **list** for lists using the [`rdf:List`](https://www.w3.org/TR/rdf-schema/#ch_list) facility
- **sop** for lists using modelling solutions with the same expressivity as the [Sequence Ontology Pattern](http://ontologydesignpatterns.org/wiki/Submissions:Sequence)

## Data generator

We propose a data generator based on the `midi2rdf` algorithm that is compatible with all the aforementioned RDF list models. The syntax is:

```
midi2rdf [-h]
         [--format [{xml,n3,turtle,nt,pretty-xml,trix,trig,nquads}]]
         [--gz] [--order [{uri,prop_number,prop_time,seq,list,sop}]]
         [--version]
         filename [outfile]
```

The executable files can be found in the [src](/src) directory.

## Queries

The SPARQL queries retrieving the list content according to these models can be found in the [queries](/queries) directory.
