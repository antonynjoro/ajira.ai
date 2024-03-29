import datetime
import json
import os
import tiktoken
import logging

from openai import ChatCompletion


class GPTLogic:
    """contains the logic for the different types of prompts we can ask the job-seeker"""
    api_key = os.environ['OPENAI_API_KEY']

    def __init__(self):
        self.davinci_model = "text-davinci-003"
        self.functions_chat_model = "gpt-3.5-turbo-0613"
        self.chat_model = "gpt-3.5-turbo"
        self.prompts = self.load_prompts_from_file()
        self.functions = self.get_functions()
        logging.basicConfig(level=logging.INFO)

    def api_call(self, prompt: list, model: str, temperature: int, functions: list = None,
                 max_tokens: int = None, ) -> dict:
        """call the openai api"""
        logging.info(f"Using prompt: {prompt}")

        if functions is not None:
            response = ChatCompletion.create(
                model=model,
                messages=prompt,
                functions=functions,
                function_call="auto",
                temperature=temperature,
                max_tokens=max_tokens,
            )
        elif model == self.davinci_model:
            response = ChatCompletion.create(
                model=model,
                messages=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            response = ChatCompletion.create(
                model=model,
                messages=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        # Process function call
        response_message = response["choices"][0]["message"]
        if response_message.get("function_call"):
            logging.info("GPT has determined that this is the end of the conversation")
            output = {
                "choices": [
                    {
                        "message": {
                            'content': 'Thank you for using Ajira we will be sending you '
                                       'your resume shortly <END>'
                        }
                    }
                ],
            }
            return output

        return response

    def chat(self, messages_dict: list) -> dict:
        """chat with the user using the gpt-3.5-turbo model"""
        prompt = [{"role": "system", "content": self.get_prompt('chat')}] + messages_dict
        logging.info(prompt)
        response = self.api_call(prompt, self.functions_chat_model, 0, self.functions)
        return response['choices'][0]['message']

    @staticmethod
    def get_functions():
        """Create GPT function parameter that will be used to call the api when chatting with the user"""
        functions = [
            {
                "name": "generate_resume",
                "description": "This function should be triggered when the user indicates that they are satisfied with "
                               "the generated summary after giving their resume information"
                               "The function should also be called when a user asks for a resume to be generated",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                }
            }
        ]
        return functions

    @staticmethod
    def load_prompts_from_file():
        with open('prompt_library.json', 'r') as f:  # load prompts from file
            data = json.load(f)

        return data

    def get_prompt(self, method):
        """get the prompt for the given method and add the current date to the context prompt"""
        today_date = str(datetime.datetime.now())
        context = self.prompts["context"] + today_date + "\n"

        return context + self.prompts[method]

    def summarize_messages(self, messages: list) -> str:
        prompt = [
            {"role": "system", "content": self.get_prompt('summarize_messages') + "```\n" + str(messages) + "\n```"}
        ]
        logging.info(f"summarize_messages gptlogic file Messages: {messages}")
        logging.info(f"summarize_message gptlogic Prompt: {prompt}")
        response = self.api_call(prompt, self.chat_model, 0)
        return response['choices'][0]['message']['content']

    def generate_resume(self, resume_inputs: list, user_phone_number) -> str:
        prompt = [
            {
                "role": "system",
                "content": self.get_prompt('generate_resume')
                           + f"```\nPhone Number: {user_phone_number}. \n Resume Inputs: {resume_inputs}```"
            },
        ]
        logging.info("Generating Resume")
        logging.info(prompt)

        response = ChatCompletion.create(
            model=self.chat_model,
            messages=prompt,
            functions=self.functions,
            function_call="auto",
            temperature=0.5,
            max_tokens=3500,
        )
        return response['choices'][0]['message']['content']

    def get_user_name(self, summary_text: str) -> str:
        prompt = [
            {
                "role": "system",
                "content": self.get_prompt('get_user_name')
                           + f"```{summary_text}```\nName: "}
        ]
        logging.info(prompt)
        response = self.api_call(prompt, self.chat_model, 0, None)
        return response['choices'][0]['message']['content']


def num_tokens_from_messages(messages, tokenizer):
    num_tokens = 0
    for message in messages:
        num_tokens += tokenizer.tokenize(message['content']).count_tokens()
    return num_tokens


gpt_logic = GPTLogic()
