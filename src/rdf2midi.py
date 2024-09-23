from mido import MidiFile, MidiTrack, Message, MetaMessage
from rdflib import Namespace, Graph, RDF, RDFS, URIRef, Literal
import sys
from unidecode import unidecode

# Mapping RDF MIDI event types to Mido event types
MIDI_EVENT_MAPPING = {
    "http://purl.org/midi-ld/midi#set_tempo": "set_tempo",
    "http://purl.org/midi-ld/midi#time_signature": "time_signature",
    "http://purl.org/midi-ld/midi#end_of_track": "end_of_track",
    "http://purl.org/midi-ld/midi#track_name": "track_name",
    "http://purl.org/midi-ld/midi#note_on": "note_on",
    "http://purl.org/midi-ld/midi#note_off": "note_off"
}

def rdf2midi(input_filename, output_filename):
    mid_uri = URIRef("http://purl.org/midi-ld/midi#")
    mid = Namespace(mid_uri)

    # Read the input RDF file
    g = Graph()
    g.parse(input_filename, format="xml")

    # Initialize the MIDI file (resolution and format)
    p_resolution = 96
    p_format = 1
    for s, p, o in g.triples((None, mid.resolution, None)):
        p_resolution = int(o)
    for s, p, o in g.triples((None, mid['format'], None)):
        p_format = int(o)

    # Create a new MIDI file using mido
    midifile = MidiFile(type=p_format, ticks_per_beat=p_resolution)

    # Retrieve the tracks
    for s, p, o in sorted(g.triples((None, RDF.type, mid.Track))):
        # Create a new track
        track = MidiTrack()
        midifile.tracks.append(track)

        # Initialize variables
        current_tempo = 500000  # Default tempo (120 BPM)
        tempo = current_tempo
        previous_tick = 0
        time_signature = (4, 4)  # Default time signature

        # Retrieve all events on this track
        for x, y, z in sorted(g.triples((s, mid.hasEvent, None))):
            # Determine event type
            event_type = g.value(subject=z, predicate=RDF.type)
            midi_event_type = MIDI_EVENT_MAPPING.get(str(event_type))
            if midi_event_type is None:
                print(f"Unrecognized event type: {event_type}")
                continue

            # Fetch the absolute time for the event
            tick = None
            for p in g.objects(z, mid.absoluteTime):
                tick = float(p)  # Ensure that absolute time is float for calculation

            # Convert absolute tick to relative tick (delta time)
            delta_ticks = int(tick * p_resolution) - previous_tick
            previous_tick = int(tick * p_resolution)

            # Handle specific events
            if midi_event_type == "note_on":
                channel = velocity = pitch = None
                for p in g.objects(z, mid.channel):
                    channel = int(p)
                for p in g.objects(z, mid.velocity):
                    velocity = int(p)
                for p in g.objects(z, mid.note):
                    pitch = int(p.split('/')[-1])  # Parse note value
                
                channel = channel if channel is not None else 0
                velocity = velocity if velocity is not None else 64
                pitch = pitch if pitch is not None else 60
                
                channel = max(0, min(channel, 15))
                velocity = max(0, min(velocity, 127))
                pitch = max(0, min(pitch, 127))
                
                track.append(Message('note_on', channel=channel, note=pitch, velocity=velocity, time=delta_ticks))

            elif midi_event_type == "note_off":
                channel = pitch = velocity = None
                for p in g.objects(z, mid.channel):
                    channel = int(p)
                for p in g.objects(z, mid.note):
                    pitch = int(p.split('/')[-1])
                for p in g.objects(z, mid.velocity):
                    velocity = int(p)
                
                channel = channel if channel is not None else 0
                velocity = velocity if velocity is not None else 64
                pitch = pitch if pitch is not None else 60
                
                channel = max(0, min(channel, 15))
                velocity = max(0, min(velocity, 127))
                pitch = max(0, min(pitch, 127))
                
                track.append(Message('note_off', channel=channel, note=pitch, velocity=velocity, time=delta_ticks))

            elif midi_event_type == "set_tempo":
                tempo = None
                for p in g.objects(z, mid.mpqn):
                    tempo = int(float(p))
                if tempo is None:
                    for p in g.objects(z, mid.bpm):
                        bpm = float(p)
                        tempo = int(60000000 // bpm)
                if tempo is not None:
                    track.append(MetaMessage('set_tempo', tempo=tempo, time=delta_ticks))
                    current_tempo = tempo  # Update current tempo

            elif midi_event_type == "time_signature":
                numerator = denominator = None
                for p in g.objects(z, mid.numerator):
                    numerator = int(p)
                for p in g.objects(z, mid.denominator):
                    denominator = int(p)

                numerator = numerator if numerator is not None else 4
                denominator = denominator if denominator is not None else 4
                denominator = denominator if denominator in [1, 2, 4, 8, 16] else 4
                
                track.append(MetaMessage('time_signature', numerator=numerator, denominator=denominator, time=delta_ticks))
                time_signature = (numerator, denominator)  # Update current time signature

            elif midi_event_type == "end_of_track":
                track.append(MetaMessage('end_of_track', time=delta_ticks))

            elif midi_event_type == "track_name":
                text = None
                for p in g.objects(z, RDFS.label):
                    text = str(unidecode(p))
                
                text = text if text else "Unnamed Track"
                
                track.append(MetaMessage('track_name', name=text, time=delta_ticks))

    # Save the MIDI file
    midifile.save(output_filename)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <rdf input file> <midi output file>")
        exit(2)

    input_filename = sys.argv[1]
    output_filename = sys.argv[2]
    rdf2midi(input_filename, output_filename)
