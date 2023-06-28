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
        self.chat_model = "gpt-3.5"
        self.prompts = self.load_prompts_from_file()
        logging.basicConfig(level=logging.INFO)

    @staticmethod
    def load_prompts_from_file():
        with open('prompt_library.json', 'r') as f: # load prompts from file
            data = json.load(f)

        return data

    def get_prompt(self, method):
        context = self.prompts["context"]

        return context + self.prompts[method]

    def parse_davinci_response(self, response: json):
        # parse gpt-3 response into a dictionary or string
        text_value = response.choices[0].text.strip()
        text_value = text_value.replace("\n", "")
        if text_value[0] == "{":
            text_dict = json.loads(text_value)
            return text_dict
        else:
            return text_value

    def api_call(self, prompt, model, temperature, max_tokens):
        response = ChatCompletion.create(
            model=model,
            messages=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response

    def summarize_messages(self, messages: list) -> str:
        prompt = [{"role": "system", "content": self.get_prompt('summarize_messages').format(messages=messages)}]
        logging.info(prompt)
        response = self.api_call(prompt, self.chat_model, 0, 2048)
        return response.choices[0]['message']['content']

    def generate_resume(self, resume_inputs: list, user_phone_number) -> str:
        prompt = [
            {"role": "system", "content": self.get_prompt('generate_resume').format(resume_inputs=resume_inputs,
                                                                                    user_phone_number=user_phone_number)}]
        logging.info(prompt)
        response = self.api_call(prompt, self.chat_model, 0.5, 3500)
        return response.choices[0]['message']['content']

    def chat(self, messages_dict: list) -> dict:
        prompt = [{"role": "system", "content": self.get_prompt('chat')}] + messages_dict
        logging.info(prompt)
        response = self.api_call(prompt, "gpt-3.5-turbo", 0, None)
        return response.choices[0]['message']

    def check_if_done(self, last_two_messages: list) -> bool:
        prompt = [{"role": "system", "content": self.get_prompt('check_if_done').format(last_two_messages=last_two_messages)}]
        logging.info(prompt)
        response = self.api_call(prompt, self.chat_model, 0, None)
        gpt_response_sting = response.choices[0]['message']['content']
        gpt_response_bool = True if gpt_response_sting == "True" else False
        return gpt_response_bool

    def get_user_name(self, summary_text: str) -> str:
        prompt = [{"role": "system", "content": self.get_prompt('get_user_name').format(summary_text=summary_text)}]
        logging.info(prompt)
        response = self.api_call(prompt, self.chat_model, 0, None)
        return response.choices[0]['message']['content']


def num_tokens_from_messages(messages, tokenizer):
    num_tokens = 0
    for message in messages:
        num_tokens += tokenizer.tokenize(message['content']).count_tokens()
    return num_tokens
