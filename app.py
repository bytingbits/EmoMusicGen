def process_midi():
    try:
        # Create a copy of the original MIDI
        midi_buffer = io.BytesIO()
        st.session_state.original_midi.write(midi_buffer)
        midi_buffer.seek(0)
        modified_midi = pretty_midi.PrettyMIDI(midi_buffer)

        # Transpose notes
        for inst in modified_midi.instruments:
            for note in inst.notes:
                note.pitch = max(0, min(127, note.pitch + transpose))

        # ---- New Transformation: Remap note timings ----
        # Here we assume the original is in 4/4.
        # Original measure length (seconds) based on 4 beats at the new tempo:
        original_measure_length = 4 * (60 / tempo)
        # New measure length based on the new time signature.
        # Note: For a time signature A/B, one measure = A * (60/tempo)*(4/B) seconds.
        new_measure_length = time_signature_numerator * (60 / tempo) * (4 / time_signature_denominator)

        for instrument in modified_midi.instruments:
            for note in instrument.notes:
                # Store original timing
                orig_start = note.start
                orig_end = note.end
                # Determine which measure the note falls in (assuming original 4/4)
                measure_index = int(orig_start // original_measure_length)
                # Fractional position within the measure
                fraction = (orig_start % original_measure_length) / original_measure_length
                # Recalculate the start time based on the new measure length
                new_start = measure_index * new_measure_length + fraction * new_measure_length
                # Scale duration by the ratio of the new to original measure lengths
                duration = orig_end - orig_start
                new_duration = duration * (new_measure_length / original_measure_length)
                # Update note timings
                note.start = new_start
                note.end = new_start + new_duration

        # ---- Update MIDI Metadata for tempo and time signature ----
        # Set new tempo (this is the playback speed in BPM)
        modified_midi.tempo_changes = [(0, tempo)]
        # Update time signature metadata so that MIDI players display it correctly
        modified_midi.time_signature_changes = [
            pretty_midi.TimeSignature(time_signature_numerator, time_signature_denominator, 0)
        ]

        # Apply Staccato (Reduce all note durations by 0.5 sec) if selected
        if staccato:
            for instrument in modified_midi.instruments:
                for note in instrument.notes:
                    # Calculate current duration and then reduce it, keeping a minimum duration of 0.1 sec
                    new_duration = max(0.1, (note.end - note.start) - 0.5)
                    note.end = note.start + new_duration

        # Save the modified MIDI to buffer
        output_buffer = io.BytesIO()
        modified_midi.write(output_buffer)
        return output_buffer.getvalue()

    except Exception as e:
        st.error(f"Error processing MIDI: {e}")
        return None
