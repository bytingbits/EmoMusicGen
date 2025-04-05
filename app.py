import os
import random
import time
import streamlit as st
import pretty_midi
import io

# Set page configuration (must be at the top)
st.set_page_config(page_title="Emotional Music Generation", layout="centered")
#st.set_page_config(layout="wide")

video_html = """
		<style>

		#myVideo {
		  position: fixed;
		  right: 0;
		  bottom: 0;
		  min-width: 100%; 
		  min-height: 100%;
		}

		.content {
		  position: fixed;
		  bottom: 0;
		  background: rgba(0, 0, 0, 0.5);
		  color: #f1f1f1;
		  width: 100%;
		  padding: 20px;
		}

		</style>	
		<video autoplay muted loop id="myVideo">
		  <source src="https://mega.nz/file/hWcU3SrR#R-qzlhkmsjwBrjFyJutSJFkwcBaWMyKLjsORf2E-NIA")>
		  Your browser does not support HTML5 video.
		</video>
        """

st.markdown(video_html, unsafe_allow_html=True)
st.title('Video page')
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
cola, colb = st.columns(2)
val=""
arou=""
with cola:
	val=st.selectbox("Valence", ["high", "low"])
with colb:
	val=st.selectbox("Arousal", ["high", "low"])
if val=="high" and arou =="high":
	selected_class="CLASS1"	
elif val=="low" and arou =="high":
	selected_class="CLASS2"
elif val=="low" and arou =="low":
	selected_class="CLASS3"
else:
	selected_class="CLASS4"

# Generate MIDI section
st.header("Generate MIDI")
if st.button("✨ Generate Music ✨"):
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
        "F": -2, "F#": -1, "G": 1, "G#": 2, "A (inc)":3 , "A# (inc)": 4, "B (inc)": 5, "B# (inc)": 6,
        "C (inc)": 7, "C# (inc)": 8, "D (inc)": 9, "D# (inc)": 10, "E (inc)": 11, "E# (inc)": 12
        }
        
        # Dropdown for selecting transposition
        transpose = st.selectbox("Scale (Raga)", list(semitone_mapping.keys()))
        
        # Get the semitone shift value
        transpose = semitone_mapping[transpose]
        #transpose = st.slider("Transpose (Semitones)", -12, 12, 0)
    
    with col2:
        time_signature_numerator = st.slider("Time Signature - Numerator (Tala)", 2, 8, 4)
        time_signature_denominator = st.slider("Time Signature - Denominator (tala)", 2, 8, 4)
        tempo = 120
    
    with col3:
        selected_instrument = st.selectbox("Choose an Instrument", list(INSTRUMENTS.values()))

        # Get the corresponding instrument code
        instrument_code = [code for code, name in INSTRUMENTS.items() if name == selected_instrument][0]

        
    staccato = st.checkbox("Apply Staccato Effect", key="staccato_checkbox")

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
            if modified_midi.instruments:
                modified_midi.instruments[0].program = instrument_code
            
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
