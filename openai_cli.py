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
            "description": "write into the Meal schema and Restaurant schema from email data like uber eats, opentable, tock etc. If you can not find the exact information, you should output None in the corresponding field.",
            "parameters": {
                "type": "object",
                "properties": {
                    "Restaurant": {
                        "type": "string",
                        "description": "This is the name of the restaurant. Only digits, letters, spaces, and !#$%&+,./:?@'are allowed.",
                    },
                    "Time": {
                        "type": "string",
                        "description": "datetime format of the time of this event in ISO 8601 format",
                    },
                    "Meal Type":{
                        "type": "string",
                        "enum": ["Breakfast", "Lunch", "Dinner", "Brunch"],
                        "description": "Breakfast, Lunch, Dinner, Brunch, etc. Judge by eating time"
                    },
                    # "Detailed Address":{
                    #     "type": "string",
                    #     "description": "This is the detailed address of the restaurant"
                    # },
                    "Address1":{
                        "type": "string",
                        "description": "The first line of the restaurant's address. Only digits, letters, spaces, and '/#&,.: are allowed. An empty string is allowed; this will specifically match certain service businesses that have no street address."
                    },
                    "city":{
                        "type": "string",
                        "description": "This is the city of the restaurant. Only digits, letters, spaces, and '.() are allowed."
                    },
                    "state":{
                        "type": "string",
                        "description": "This is the state of the restaurant.  ISO 3166-2 (with a few exceptions) "
                    },
                    # "country":{
                    #     "type": "string",
                    #     "description": "This is the country of the restaurant. ISO 3166-1 alpha-2"
                    # },
                    "Zip Code":{
                        "type": "string",
                        "description": "This is the zip code of the restaurant"
                    },
                    "Method":{
                        "type": "string",
                        "enum": ["Delivery", "Reservation"],
                        "description": "Delivery, Reservation, etc. Judge by the way of eating"
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