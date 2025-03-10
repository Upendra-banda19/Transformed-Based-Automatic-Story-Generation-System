import openai

# Set your OpenAI API key (replace with your actual API key)
OPENAI_API_KEY = "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"

def generate_story_image(prompt):
    """Generates an AI image based on the story prompt using DALL·E."""
    openai.api_key = OPENAI_API_KEY

    response = openai.Image.create(
        prompt=f"An epic sci-fi story scene based on: {prompt}",
        n=1,
        size="512x512"
    )
    
    return response['data'][0]['url']
