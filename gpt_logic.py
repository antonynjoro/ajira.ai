"""contains the logic for the gpt-3 api"""
import os
from pprint import pprint

import requests
import json
import datetime
from openai import api_key, Engine, Completion
from mongo_db_logic import UserData


class GPTLogic:
    """contains the logic for the different types of prompts we can ask the job seeker"""
    api_key = os.environ['OPENAI_API_KEY']
    def __init__(self):
        self.context = """You are a recruitment AI that helps people build resumes. You are provided with information about a
                    job seeker and you expand the information to provide a full resume. You are ALWAYS helpful, friendly 
                    and speak in easy to understand words."""
        self.format_requirement = {
            "json": """"Your response should ALWAYS be in VALID JSON format guided by the example provided. ENSURE that the result is ALWAYS a valid JSON object""",
            "string": """Your response should ALWAYS be in string format guided by the example provided."""
        }
        self.davinci_model = "text-davinci-003"
        self.chat_model = "gpt-3.5-turbo"

    def validate_response(self, validation_parameters: list, user_response: str) -> dict:
        """Takes a response and validation parameters list of stings from the user and returns a dictionary containing
        validation booleans and  a followup questions strings list"""

        context = self.context

        format_requirement = self.format_requirement["json"]

        example = """The Values should ONLY be 'True' or 'False' and the followup_questions should be a list of strings
                    EXAMPLE:\nText: yes OR I Don't Know OR I have worked before, I have a lot of experience etc should provide the result:\n
                    {\n
                      "validation_status": {\n
                          "is_valid_validation_parameter_1": false, \n
                          ....\n
                        },\n
                        "followup_questions": [""]
                        \n}"""

        instructions = f"""Instructions: \n
                         1. Does this text contain valid {validation_parameters}: {user_response}\n
                         2.  If any of the elements are False, Create followup questions that would help elicit the 
                         response that would make it return 'true', if the response is true, have the 
                         followup_question be blank\n\n"""

        prompt = f"{context}\n{format_requirement}\n{example}\n{instructions}"

        # create a response by calling the openai api
        response = Completion.create(
            model=self.chat_model,
            prompt=prompt,
            temperature=0,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        print("Unparsed GPT Response", response)

        # parse the response into a json object
        parsed_response = self.parse_response(response)

        print("Parsed GPT Response", parsed_response)

        return parsed_response

    def parse_response(self, response: json) -> dict | str:
        # parse gpt-3 response into a dictionary or string
        text_value = response.choices[0].text.strip()
        text_value = text_value.replace("\n", "")
        if text_value[0] == "{":
            text_dict = json.loads(text_value)
            return text_dict
        else:
            return text_value


    def generate_resume(self, resume_inputs:dict) -> dict:
        """Takes a dictionary of resume inputs and returns a JSON object containing the generated resume"""

        context = self.context
        # TODO: add example of resume json object
        example = ""

        format_requirement = self.format_requirement["json"]

        instructions = "Instruction:\n Generate a resume based on the data below\n"+json.dumps(resume_inputs, indent=4)

        prompt = f"{context}\n{format_requirement}\n{example}\n{instructions}"

        # create a response by calling the openai api
        response = Completion.create(
            model=self.chat_model,
            prompt=prompt,
            temperature=0,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        # parse the response into a json object
        response = self.parse_response(response)

        return response
    
    def generate_question_from_example(self, response: str, example_question:str) -> str:
        """Takes a response from the user and returns a question to ask them that leads them to providing better information that will help generate a better resume"""
        context = self.context
        example = f"""EXAMPLE:\n
                    Text: 'Hello' OR 'I want a resume' OR 'start' OR 'I dont know' etc should result to a question like:\n
                    '{example_question}'"""

        instructions = f"""Instructions: \n
                            Generate a question that is similar to '{example_question}' but that takes into account the response: '{response}'\n"""

        prompt = f"{context}\n\n{example}\n{instructions}"

        # create a response by calling the openai api
        response = Completion.create(
            model=self.chat_model,
            prompt=prompt,
            temperature=0,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        print("Unparsed GPT Response", response)

        # parse the response into a string
        parsed_response = self.parse_response(response)

        print("Parsed GPT Response", parsed_response)

        return parsed_response

    def generate_question_from_missing_data(self, user_data, message):
        """Takes a user data dictionary and message string and returns a response string"""
        context = self.context
        example = f"""EXAMPLE:\n
                    Text: if the name is missing from the user_data, the response should be: 'What is your name?' OR 'What should I call you?, etc\n'"""

        instructions = f"""Instructions: \n
                            Generate a question that seeks to fill in the missing information in the user_data dictionary but that takes into account the response: '{message}'\n
                            The user_data dictionary is: {user_data}"""

        prompt = f"{context}\n\n{example}\n{instructions}"

        # create a response by calling the openai api
        response = Completion.create(
            model=self.chat_model,
            prompt=prompt,
            temperature=0,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        # parse the response into a string
        response = self.parse_response(response)

        return response

    def extract_data(self, message:str, expected_data_name:str) -> str:
        """Takes a message and expected data name and returns the extracted data"""
        context = self.context
        example = f"""EXAMPLE:\n
                    Text: if the message is 'My name is John Doe' and the expected_data_name is 'name', the response should be: 'John Doe'"""

        instructions = f"""Instructions: \n
                            Extract the data from the message: '{message}' that corresponds to the expected_data_name: '{expected_data_name}'\n"""

        prompt = f"{context}\n\n{example}\n{instructions}"

        # create a response by calling the openai api
        response = Completion.create(
            model=self.chat_model,
            prompt=prompt,
            temperature=0,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        # parse the response into a string
        response = self.parse_response(response)

        return response

    # A function that utilizes the GPT-3.5 turbo (chat_model) to chat with the user
    def chat(self, messages_dict: list) -> str:
        """Takes a list of message dictionaries and returns a response string"""
        # Prepend system message to the messages_dict
        messages_dict = [{"role": "system", "message": "Hello, I am a resume generator. I will ask you a few questions to help me generate a resume for you. You can type 'start' to begin or 'quit' to exit the chat."}] + messages_dict
        print (messages_dict)

        




# test chat

# create a chatbot object
chatbot = Chatbot()
