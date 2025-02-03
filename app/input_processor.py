from langchain_groq import ChatGroq

#Here we are only creating function to take audio/image and processing them.
#As Text can be directly passed to the agent.

audio_model = ChatGroq(
    model="whisper-large-v3-turbo",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)
 
async def process_audio_input(audio_file_path : str):
    """This Function will take audio file as an input,
    and process it for extracting information.
    audio_file : str (path for audio to be processed) 
    """
    pass

async def process_image_input(image_file_path : str):
    """This function will take image as input and process it,
    for extracting information.
    image : str (path for image to be processed)
    """
    pass

