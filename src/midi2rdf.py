from mido import MidiFile, tick2second
from rdflib import Namespace, ConjunctiveGraph, RDF, URIRef, Literal, BNode
import hashlib
import gzip
from datetime import datetime
import argparse

def midi2rdf(filename, ser_format='turtle', order='uri'):
    """
    Returns a text/turtle dump of the input MIDI filename
    """

    # Read the input MIDI file using mido
    midifile = MidiFile(filename)

    # Get MD5 to identify the file
    md5_id = hashlib.md5(open(filename, 'rb').read()).hexdigest()

    # Define URIs
    mid_uri = URIRef("http://purl.org/midi-ld/midi#")
    prov_uri = URIRef("http://www.w3.org/ns/prov#")
    mid_note_uri = URIRef("http://purl.org/midi-ld/notes/")
    mid_prog_uri = URIRef("http://purl.org/midi-ld/programs/")
    m_uri = URIRef(f"http://purl.org/midi-ld/piece/{md5_id}")
    sequence_uri = URIRef("http://www.ontologydesignpatterns.org/cp/owl/sequence.owl#")

    # Define namespaces
    mid = Namespace(mid_uri)
    prov = Namespace(prov_uri)
    mid_note = Namespace(mid_note_uri)
    mid_prog = Namespace(mid_prog_uri)
    m = Namespace(m_uri)
    sequence = Namespace(sequence_uri)

    # Create RDF graph
    g = ConjunctiveGraph(identifier=m_uri)
    piece = m[md5_id]
    g.add((piece, RDF.type, mid.Piece))
    g.add((piece, mid.resolution, Literal(midifile.ticks_per_beat)))
    g.add((piece, mid['format'], Literal(midifile.type)))

    # PROV information
    agent = URIRef("https://github.com/midi-ld/midi2rdf")
    entity_d = piece
    entity_o = URIRef(f"http://purl.org/midi-ld/file/{md5_id}")
    activity = URIRef(f"{piece}-activity")

    g.add((agent, RDF.type, prov.Agent))
    g.add((entity_d, RDF.type, prov.Entity))
    g.add((entity_o, RDF.type, prov.Entity))
    g.add((entity_o, RDF.type, mid.MIDIFile))
    g.add((entity_o, mid.path, Literal(filename)))
    g.add((activity, RDF.type, prov.Activity))
    g.add((entity_d, prov.wasGeneratedBy, activity))
    g.add((entity_d, prov.wasAttributedTo, agent))
    g.add((entity_d, prov.wasDerivedFrom, entity_o))
    g.add((activity, prov.wasAssociatedWith, agent))
    g.add((activity, prov.startedAtTime, Literal(datetime.now())))
    g.add((activity, prov.used, entity_o))

    # Initialize tempo and time signature
    tempo = 500000
    bpm = 120
    time_signature_set = False
    numerator = 4
    denominator = 4

    # Track tempo and time signature changes
    tempos = [(0, tempo)]  # List of (absolute_time, tempo) tuples
    time_signatures = [(0, numerator, denominator)]

    for i, track in enumerate(midifile.tracks):
        track_uri = URIRef(f"{piece}/track{str(i).zfill(2)}")
        g.add((piece, mid.hasTrack, track_uri))
        g.add((track_uri, RDF.type, mid.Track))
        
        abs_time = 0.0
        previous_tick = 0  # Initialize previous_tick for delta time calculation

        for j, msg in enumerate(track):
            event_uri = URIRef(f"{piece}/track{str(i).zfill(2)}/event{str(j).zfill(4)}")
            g.add((track_uri, mid.hasEvent, event_uri))
            g.add((event_uri, RDF.type, mid[msg.type]))

            # Handle tempo changes
            if msg.type == 'set_tempo':
                tempo = msg.tempo
                bpm = 60000000 / tempo
                g.add((event_uri, mid.tempo, Literal(tempo)))
                g.add((event_uri, mid.bpm, Literal(bpm)))
                tempos.append((abs_time, tempo))

            # Handle time signature
            if msg.type == 'time_signature':
                numerator = msg.numerator
                denominator = msg.denominator
                time_signature_set = True
                g.add((event_uri, mid.numerator, Literal(numerator)))
                g.add((event_uri, mid.denominator, Literal(denominator)))
                time_signatures.append((abs_time, numerator, denominator))

            # Calculate delta time
            rel_time = tick2second(msg.time, midifile.ticks_per_beat, tempo)
            delta_ticks = int(rel_time * midifile.ticks_per_beat) - previous_tick
            previous_tick = int(rel_time * midifile.ticks_per_beat)
            abs_time += rel_time
            
            # Add delta time and absolute time to RDF graph
            g.add((event_uri, mid.relativeTime, Literal(rel_time)))
            g.add((event_uri, mid.deltaTime, Literal(delta_ticks)))  # Add delta time
            g.add((event_uri, mid.absoluteTime, Literal(abs_time)))

            # Handle specific MIDI message types (like note events)
            if msg.type == 'note_on':
                note_uri = URIRef(f"http://purl.org/midi-ld/notes/{msg.note}")
                g.add((event_uri, mid['note'], note_uri))
                g.add((event_uri, mid['velocity'], Literal(msg.velocity)))

            elif msg.type == 'note_off':
                note_uri = URIRef(f"http://purl.org/midi-ld/notes/{msg.note}")
                g.add((event_uri, mid['note'], note_uri))

    # Add time signature to the piece if it was found
    if time_signature_set:
        time_signature_bnode = BNode()
        g.add((piece, mid.time_signature, time_signature_bnode))
        g.add((time_signature_bnode, mid.numerator, Literal(numerator)))
        g.add((time_signature_bnode, mid.denominator, Literal(denominator)))
        
    # Bind prefixes
    g.bind('midi', mid)
    g.bind('midi-note', mid_note)
    g.bind('midi-prog', mid_prog)
    g.bind('prov', prov)
    g.bind('sequence', sequence)

    # Finish PROV timestamps
    end_time = Literal(datetime.now())
    g.add((entity_d, prov.generatedAtTime, end_time))
    g.add((activity, prov.endedAtTime, end_time))

    return g.serialize(format=ser_format)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='midi2rdf', description="MIDI to RDF converter")
    parser.add_argument('filename', nargs=1, type=str, help="Path to the MIDI file to convert")
    parser.add_argument('--format', '-f', dest='format', nargs='?', choices=['xml', 'n3', 'turtle', 'nt', 'pretty-xml', 'trix', 'trig', 'nquads', 'json-ld'], default='turtle', help="RDF serialization format")
    parser.add_argument('outfile', nargs='?', type=str, default=None, help="Output RDF file (if omitted defaults to stdout)")
    parser.add_argument('--gz', '-z', dest='gz', action='store_true', default=False, help="Compress the output of the conversion")
    parser.add_argument('--order', '-o', dest='order', nargs='?', choices=['uri', 'prop_number', 'prop_time', 'seq', 'list', 'sop'], default='uri', help="Track and event ordering strategy")
    parser.add_argument('--version', '-v', dest='version', action='version', version='0.2')
    args = parser.parse_args()

    dump = midi2rdf(args.filename[0], args.format, args.order)

    if args.outfile:
        if args.gz:
            with gzip.open(args.outfile, 'wb') as out:
                out.write(dump)
        else:
            with open(args.outfile, 'w') as out:
                out.write(dump)
    else:
        print(dump)

    exit(0)
