from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored  

# read ./streamlit/secrets.toml
def read_toml(path):
    import toml
    with open(path, 'r') as f:
        config = toml.load(f)
    return config

tools = [
    {
        "type": "function",
        "function": {
            "name": "write_into_database",
            "description": "write into the Meal schema and Restaurant schema from email data like uber eats, opentable, tock etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "Restaurant": {
                        "type": "string",
                        "description": "This is the name of the restaurant",
                    },
                    "Time": {
                        "type": "string",
                        "description": "datetime format of the time of this event",
                    },
                    "Meal Type":{
                        "type": "string",
                        "enum": ["Breakfast", "Lunch", "Dinner", "Brunch"],
                        "description": "Breakfast, Lunch, Dinner, Brunch, etc."
                    },
                },
                "required": ["location", "format"],
            },
        }
    },
]

def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "function": "magenta",
    }
    
    for message in messages:
        if message["role"] == "system":
            print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "user":
            print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and message.get("function_call"):
            print(colored(f"assistant: {message['function_call']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and not message.get("function_call"):
            print(colored(f"assistant: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "function":
            print(colored(f"function ({message['name']}): {message['content']}\n", role_to_color[message["role"]]))

class OpenAIClient:
    def __init__(self, config):
        self.config = config
        self.api_key = config['OPENAI_API_KEY']
        self.client = OpenAI(api_key=self.api_key)
        self.model = config['GPT_MODEL']
        
    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def chat_completion_request(self, messages, tools=None, tool_choice=None, model='gpt-3.5-turbo-0613'):
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
            )
            return response
        except Exception as e:
            print("Unable to generate ChatCompletion response")
            print(f"Exception: {e}")
            return e
        
    def extract_info_from_email(self, email_content: str):
        messages = []
        messages.append({"role": "system", "content": "Use the email content from user to extract information. And I will use the function 'write_into_database' to write the extracted information into the database."})
        messages.append({"role": "user", "content": email_content})
        chat_response = self.chat_completion_request(
            messages, 
            tools=tools, 
            tool_choice={"type": "function", "function": {"name": "write_into_database"}},
            model=self.model,
        )
        return chat_response.choices[0].message


if __name__ == "__main__":
    toml_file = read_toml('./.streamlit/secrets.toml')
    config = dict(
        OPENAI_API_KEY=toml_file["OPENAI_API_KEY"],
        GPT_MODEL="gpt-3.5-turbo-0613"
    )