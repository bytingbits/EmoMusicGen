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
st.title("🎹 Emotional Music Generation")
st.text("Shakthi, Sreya, Sharada")
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
        st.error(f"Error loading: {e}")

# Customization controls
if st.session_state.original_midi:
    st.markdown("---")
    st.header("Customization Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        semitone_mapping = {
        "Original": 0,
        "A": -12, "A#": -11, "B": -10, "B#": -9,
        "C": -8, "C#": -7, "D": -6, "D#": -5, "E": -4, "E#": -3,
        "F": -2, "F#": -1, "G": 1, "G#": 2
        }
        
        # Dropdown for selecting transposition
        transpose = st.selectbox("Transpose", list(semitone_mapping.keys()))
        
        # Get the semitone shift value
        #transpose_value = semitone_mapping[transpose]
        #transpose = st.slider("Transpose (Semitones)", -12, 12, 0)
    
    with col2:
        time_signature_numerator = st.slider("Time Signature - Numerator", 2, 8, 4)
        tempo = 120
    
    with col3:
        
        time_signature_denominator = st.selectbox("Time Signature - Denominator", [2, 4, 8], index=1)

    staccato = st.checkbox("Apply Staccato (Reduce note durations by 0.5 sec)", key="staccato_checkbox")

    # MIDI processing function with remapped timing
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

            # ---- Remap note timings based on new time signature and tempo ----
            # Assuming original MIDI is in 4/4:
            # Original measure length: 4 beats at current tempo (seconds per beat = 60/tempo)
            original_measure_length = 4 * (60 / tempo)
            # New measure length calculation:
            # For time signature A/B, one measure is A * (60/tempo)*(4/B) seconds.
            new_measure_length = time_signature_numerator * (60 / tempo) * (4 / time_signature_denominator)

            for instrument in modified_midi.instruments:
                for note in instrument.notes:
                    orig_start = note.start
                    orig_end = note.end
                    # Determine the measure index (assuming original 4/4)
                    measure_index = int(orig_start // original_measure_length)
                    # Fractional position within the original measure
                    fraction = (orig_start % original_measure_length) / original_measure_length
                    # Calculate new start time based on new measure length
                    new_start = measure_index * new_measure_length + fraction * new_measure_length
                    # Scale duration proportionally
                    duration = orig_end - orig_start
                    new_duration = duration * (new_measure_length / original_measure_length)
                    # Update note timing
                    note.start = new_start
                    note.end = new_start + new_duration

            # ---- Update MIDI Metadata for tempo and time signature ----
            modified_midi.tempo_changes = [(0, tempo)]
            modified_midi.time_signature_changes = [
                pretty_midi.TimeSignature(time_signature_numerator, time_signature_denominator, 0)
            ]

            # Apply Staccato effect if selected
            if staccato:
                for instrument in modified_midi.instruments:
                    for note in instrument.notes:
                        new_duration = max(0.1, (note.end - note.start) - 0.5)
                        note.end = note.start + new_duration

            # Save the modified MIDI to a buffer
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
