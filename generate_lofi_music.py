import numpy as np
from scipy.io import wavfile
import scipy.signal as signal

def create_lofi_track(duration_sec=35, sample_rate=44100):
    bpm = 85
    seconds_per_beat = 60.0 / bpm
    total_samples = int(duration_sec * sample_rate)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False)
    
    # 1. Warm Jazz Chords (Rhodes / E-Piano style: Cmaj7, Am7, Dm7, G7)
    # Frequencies for chords (Hz)
    chords = [
        [261.63, 329.63, 392.00, 493.88], # Cmaj7
        [220.00, 261.63, 329.63, 392.00], # Am7
        [293.66, 349.23, 440.00, 523.25], # Dm7
        [196.00, 246.94, 293.66, 349.23]  # G7
    ]
    chord_duration = 4 * seconds_per_beat  # 1 measure per chord
    
    rhodes_wave = np.zeros(total_samples)
    
    for i in range(int(duration_sec / chord_duration) + 2):
        start_sample = int(i * chord_duration * sample_rate)
        if start_sample >= total_samples:
            break
        chord_freqs = chords[i % len(chords)]
        dur_samples = int(chord_duration * sample_rate)
        end_sample = min(start_sample + dur_samples, total_samples)
        num_s = end_sample - start_sample
        
        t_chord = np.linspace(0, (end_sample - start_sample) / sample_rate, num_s, endpoint=False)
        # Soft attack and gentle decay envelope
        env = (1 - np.exp(-t_chord * 15)) * np.exp(-t_chord * 0.8)
        
        chord_signal = np.zeros(num_s)
        for freq in chord_freqs:
            # Fundamental + soft 2nd & 3rd harmonics
            note = np.sin(2 * np.pi * freq * t_chord) + 0.3 * np.sin(2 * np.pi * 2 * freq * t_chord) + 0.1 * np.sin(2 * np.pi * 3 * freq * t_chord)
            chord_signal += note
            
        rhodes_wave[start_sample:end_sample] += chord_signal * env
        
    # Tremolo effect (6 Hz modulation)
    tremolo = 0.75 + 0.25 * np.sin(2 * np.pi * 6 * t)
    rhodes_wave *= tremolo
    
    # Low-pass filter rhodes for warm lo-fi tone (800 Hz cutoff)
    b, a = signal.butter(2, 800 / (sample_rate / 2), btype='low')
    rhodes_wave = signal.filtfilt(b, a, rhodes_wave)
    
    # 2. Warm Bass Synth
    bass_freqs = [130.81, 110.00, 146.83, 98.00] # C, A, D, G bass
    bass_wave = np.zeros(total_samples)
    
    for i in range(int(duration_sec / chord_duration) + 2):
        start_sample = int(i * chord_duration * sample_rate)
        if start_sample >= total_samples:
            break
        freq = bass_freqs[i % len(chords)]
        dur_samples = int(chord_duration * sample_rate)
        end_sample = min(start_sample + dur_samples, total_samples)
        num_s = end_sample - start_sample
        
        t_bass = np.linspace(0, num_s / sample_rate, num_s, endpoint=False)
        env = (1 - np.exp(-t_bass * 20)) * np.exp(-t_bass * 0.5)
        # Sub-bass sine + triangle wave
        note = np.sin(2 * np.pi * (freq / 2) * t_bass) + 0.5 * signal.sawtooth(2 * np.pi * (freq / 2) * t_bass, width=0.5)
        bass_wave[start_sample:end_sample] += note * env
        
    # Low-pass filter bass (300 Hz cutoff)
    b_b, a_b = signal.butter(2, 300 / (sample_rate / 2), btype='low')
    bass_wave = signal.filtfilt(b_b, a_b, bass_wave)

    # 3. Lo-fi Drums (Kick, Snare, Hi-Hat)
    drum_wave = np.zeros(total_samples)
    eighth_note_dur = seconds_per_beat / 2
    num_eighths = int(duration_sec / eighth_note_dur) + 2
    
    for e in range(num_eighths):
        start_sample = int(e * eighth_note_dur * sample_rate)
        if start_sample >= total_samples:
            break
            
        beat_in_measure = (e % 8) / 2.0  # 0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5
        
        # Hi-hat on every 8th note
        dur_hat = int(0.08 * sample_rate)
        end_hat = min(start_sample + dur_hat, total_samples)
        num_h = end_hat - start_sample
        t_h = np.linspace(0, num_h / sample_rate, num_h, endpoint=False)
        noise = np.random.normal(0, 1, num_h)
        # High pass filter noise for hat
        b_h, a_h = signal.butter(2, 4000 / (sample_rate / 2), btype='high')
        hat_filtered = signal.filtfilt(b_h, a_h, noise) * np.exp(-t_h * 50)
        drum_wave[start_sample:end_hat] += hat_filtered * 0.15
        
        # Kick on beats 0, 2.5
        if beat_in_measure in [0.0, 2.5]:
            dur_k = int(0.25 * sample_rate)
            end_k = min(start_sample + dur_k, total_samples)
            num_k = end_k - start_sample
            t_k = np.linspace(0, num_k / sample_rate, num_k, endpoint=False)
            freq_sweep = 110 * np.exp(-t_k * 30) + 40
            kick = np.sin(2 * np.pi * freq_sweep * t_k) * np.exp(-t_k * 12)
            drum_wave[start_sample:end_k] += kick * 0.6
            
        # Snare / Rimshot on beats 1.0, 3.0
        if beat_in_measure in [1.0, 3.0]:
            dur_s = int(0.2 * sample_rate)
            end_s = min(start_sample + dur_s, total_samples)
            num_s = end_s - start_sample
            t_s = np.linspace(0, num_s / sample_rate, num_s, endpoint=False)
            snare_noise = np.random.normal(0, 1, num_s) * np.exp(-t_s * 25)
            b_s, a_s = signal.butter(2, [1000 / (sample_rate / 2), 5000 / (sample_rate / 2)], btype='band')
            snare_filtered = signal.filtfilt(b_s, a_s, snare_noise)
            snare_tone = np.sin(2 * np.pi * 180 * t_s) * np.exp(-t_s * 30)
            drum_wave[start_sample:end_s] += (snare_filtered * 0.4 + snare_tone * 0.2)

    # 4. Vinyl Crackle Noise
    vinyl_noise = np.random.normal(0, 0.02, total_samples)
    # Random vinyl pop clicks
    pops = np.random.uniform(0, 1, total_samples) > 0.9997
    vinyl_noise[pops] += np.random.uniform(0.1, 0.3, np.sum(pops))
    b_v, a_v = signal.butter(2, 3000 / (sample_rate / 2), btype='low')
    vinyl_noise = signal.filtfilt(b_v, a_v, vinyl_noise)

    # Mix components
    mix = 0.45 * rhodes_wave + 0.35 * bass_wave + 0.4 * drum_wave + 0.1 * vinyl_noise
    
    # Master Normalization
    mix = mix / np.max(np.abs(mix)) * 0.85
    
    # Convert to 16-bit PCM WAV
    audio_int16 = (mix * 32767).astype(np.int16)
    output_path = "/config/Desktop/Session1/heritage-food-concierge/demo_output/lofi_music.wav"
    wavfile.write(output_path, sample_rate, audio_int16)
    print(f"Lo-fi background music generated successfully at: {output_path}")
    return output_path

if __name__ == "__main__":
    create_lofi_track(duration_sec=35)
