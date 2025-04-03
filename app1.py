import os
import random
import time
import streamlit as st
import pretty_midi
import io

# Set page configuration (must be at the top)
st.set_page_config(page_title="MIDI Maestro", layout="centered")

# Constants
CLASSES = ["CLASS1", "CLASS2", "CLASS3", "CLASS4"]
INSTRUMENTS = {
    0: "Acoustic Grand Piano",
    40: "Violin",
    73: "Flute",
    25: "Acoustic Guitar (nylon)",
    33: "Electric Bass (finger)"
}
# Base note names for semitone offsets (we assume base note "C" for 0)
note_names = ["C", "C#/Db", "D", "D#/Eb", "E", "F", 
              "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"]

def load_midi_files():
    midi_files = {}
    for cls in CLASSES:
        cls_path = os.path.join(os.getcwd(), cls)
        if os.path.exists(cls_path):
            midi_files[cls] = [
                os.path.join(cls_path, f)
                for f in os.listdir(cls_path)
                if f.endswith(('.mid', '.midi'))
            ]
    return midi_files

# Initialize session state
if 'original_midi' not in st.session_state:
    st.session_state.original_midi = None

# App title
st.title("🎹 MIDI Maestro")
st.markdown("---")

# Load MIDI files
midi_files = load_midi_files()

# Class selection
selected_class = st.selectbox("Select Music Class", CLASSES, key='class_select')

# Generate MIDI section
st.header("Generate MIDI")
if st.button("✨ Generate Random MIDI"):
    if not midi_files.get(selected_class):
        st.error(f"No MIDI files found in {selected_class}!")
        st.stop()
    
    # Create progress bar with random wait time
    wait_time = random.randint(7, 10)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(wait_time):
        status_text.text(f"🎧 Composing masterpiece... {i+1}/{wait_time} sec")
        progress_bar.progress((i + 1) / wait_time)
        time.sleep(1)
    
    progress_bar.empty()
    status_text.empty()
    
    # Load random MIDI file
    try:
        selected_midi = random.choice(midi_files[selected_class])
        st.session_state.original_midi = pretty_midi.PrettyMIDI(selected_midi)
        st.success("🎉 MIDI generated! Customize it below!")
    except Exception as e:
        st.error(f"Error loading MIDI: {e}")

# Customization controls (only show if a MIDI file was loaded)
if st.session_state.original_midi:
    st.markdown("---")
    st.header("Customization Options")
    
    # Create three columns:
    # Column 1: Scale (Raga) select slider for transposition
    # Column 2: Time Signature numerator and denominator (in one column)
    # Column 3: Instrument selection
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Use select_slider to display the semitone offset along with the base note label.
        scale = st.select_slider(
            "Scale (Raga)",
            options=list(range(-12, 13)),
            value=0,
            format_func=lambda x: f"{x} ({note_names[x % 12]})"
        )
    
    with col2:
        ts_num = st.slider("Time Signature Numerator", min_value=2, max_value=8, value=4)
        ts_den = st.slider("Time Signature Denominator", min_value=2, max_value=8, step=2, value=4,
                           help="Choose 2, 4, or 8 for common time signatures")
    
    with col3:
        instrument_program = st.selectbox(
            "Select Instrument",
            options=list(INSTRUMENTS.keys()),
            format_func=lambda x: INSTRUMENTS[x]
        )
    
    # Staccato checkbox remains
    staccato = st.checkbox("Apply Staccato (Reduce note durations by 0.5 sec)", key="staccato_checkbox")
    
    # MIDI processing function with instrument change and time signature transformation.
    def process_midi():
        try:
            # Use default tempo of 120 BPM since tempo slider is removed.
            fixed_tempo = 120

            # Create a copy of the original MIDI
            midi_buffer = io.BytesIO()
            st.session_state.original_midi.write(midi_buffer)
            midi_buffer.seek(0)
            modified_midi = pretty_midi.PrettyMIDI(midi_buffer)
            
            # Transpose notes based on chosen scale (raga)
            for inst in modified_midi.instruments:
                for note in inst.notes:
                    note.pitch = max(0, min(127, note.pitch + scale))
            
            # Change all instrument programs to the user-selected instrument
            for inst in modified_midi.instruments:
                inst.program = instrument_program

            # ---- Remap note timings based on new time signature ----
            # Assume original MIDI is in 4/4
            original_measure_length = 4 * (60 / fixed_tempo)  # seconds per measure in 4/4
            # Calculate new measure length:
            # For a time signature A/B, one measure = A * (60/fixed_tempo) * (4/B) seconds.
            new_measure_length = ts_num * (60 / fixed_tempo) * (4 / ts_den)

            for instrument in modified_midi.instruments:
                for note in instrument.notes:
                    orig_start = note.start
                    orig_end = note.end
                    # Determine measure index assuming original 4/4 timing
                    measure_index = int(orig_start // original_measure_length)
                    # Fractional position within the original measure
                    fraction = (orig_start % original_measure_length) / original_measure_length
                    # New start time in the new measure grid
                    new_start = measure_index * new_measure_length + fraction * new_measure_length
                    # Scale the duration proportionally
                    duration = orig_end - orig_start
                    new_duration = duration * (new_measure_length / original_measure_length)
                    note.start = new_start
                    note.end = new_start + new_duration

            # ---- Update MIDI Metadata for fixed tempo and new time signature ----
            modified_midi.tempo_changes = [(0, fixed_tempo)]
            modified_midi.time_signature_changes = [
                pretty_midi.TimeSignature(ts_num, ts_den, 0)
            ]

            # Apply Staccato effect if selected
            if staccato:
                for instrument in modified_midi.instruments:
                    for note in instrument.notes:
                        new_duration = max(0.1, (note.end - note.start) - 0.5)
                        note.end = note.start + new_duration

            # Save the modified MIDI to a buffer and return its bytes
            output_buffer = io.BytesIO()
            modified_midi.write(output_buffer)
            return output_buffer.getvalue()

        except Exception as e:
            st.error(f"Error processing MIDI: {e}")
            return None

    # Generate processed MIDI data
    midi_data = process_midi()

    if midi_data:
        st.download_button(
            label="⬇️ Download Custom MIDI",
            data=midi_data,
            file_name="custom_midi.mid",
            mime="audio/midi",
            help="Click to download your customized MIDI file"
        )
