from input_processor import process_audio_input, process_image_input
import asyncio

file_path = "./downloads/audio (4).wav"

# result = asyncio.run(process_image_input(file_path))
result=  asyncio.run(process_audio_input(file_path))

print(result)