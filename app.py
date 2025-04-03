import os
import random
import time
import streamlit as st
#from pretty_midi import PrettyMIDI, TempoChange
import pretty_midi
import io

# Set page configuration
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

# Customization controls
if st.session_state.original_midi:
    st.markdown("---")
    st.header("Customization Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        transpose = st.slider("Transpose (Semitones)", -12, 12, 0)
    
    with col2:
        tempo = st.slider("Speed (speed up or down)", 0.125, 8, 1)
    
    with col3:
        instrument = st.selectbox("Instrument", options=list(INSTRUMENTS.items()),
                           format_func=lambda x: x[1])

    # MIDI processing function
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

        # Adjust tempo
        tempo_factor = tempo
        for time_signature in modified_midi.time_signature_changes:
            time_signature.time /= tempo_factor
        
        for tempo_change in modified_midi.get_tempo_changes()[1]:  # Modify existing tempo changes
            modified_midi._tick_scales *= tempo_factor  # Scale all tempo changes
        
        # Change instrument
        for inst in modified_midi.instruments:
            inst.program = instrument[0]

        # Save to buffer
        output_buffer = io.BytesIO()
        modified_midi.write(output_buffer)
        return output_buffer.getvalue()
    
    except Exception as e:
        st.error(f"Error processing MIDI: {e}")
        return None

    midi_data = process_midi()

# Example usage: Doubling the tempo (speeding up)
#change_midi_tempo("input.mid", "output.mid", 2.0)
            
            
    if midi_data:
    # Download button
        st.download_button(
            label="⬇️ Download Custom MIDI",
            data=process_midi,
            file_name="custom_midi.mid",
            mime="audio/midi",
            help="Click to download your customized MIDI file"
        )

