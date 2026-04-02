import gradio as gr
import torch
from chatterbox.tts import ChatterboxTTS

# Imposta device (aggiusta per Intel ARC o altro)
device = "xpu" if hasattr(torch, "xpu") and torch.xpu.is_available() else "cpu"

model = ChatterboxTTS.from_pretrained(device=device)

def genera_audio(text, audio_prompt_path, exaggeration, temperature, cfg_weight):
    wav = model.generate(
        text,
        audio_prompt_path=audio_prompt_path,
        exaggeration=exaggeration,
        temperature=temperature,
        cfg_weight=cfg_weight
    )
    return (model.sr, wav.squeeze(0).numpy())

with gr.Blocks() as demo:
    text_input = gr.Textbox(placeholder="Inserisci testo qui", lines=4)
    audio_prompt_input = gr.Audio(source="upload", type="filepath", label="File audio voce")
    exaggeration_slider = gr.Slider(0.25, 2, value=0.5, label="Esagerazione")
    temperature_slider = gr.Slider(0.1, 2, value=0.8, label="Temperatura")
    cfg_weight_slider = gr.Slider(0, 1, value=0.5, label="CFG Weight")
    output_audio = gr.Audio(label="Audio generato")

    btn_generate = gr.Button("Genera")
    btn_generate.click(
        fn=genera_audio,
        inputs=[text_input, audio_prompt_input, exaggeration_slider, temperature_slider, cfg_weight_slider],
        outputs=output_audio
    )

demo.launch()
