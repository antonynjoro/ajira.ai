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

    def api_call(self, prompt: list, model: str, temperature: int,  functions: list = None , max_tokens: int = None,) -> dict:
        """call the openai api"""
        logging.info(f"Using prompt: {prompt}")

        if functions is not None:
            response = ChatCompletion.create(
                model=model,
                messages=prompt,
                functions=functions,
                function_call= "auto",
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
        with open('prompt_library.json', 'r') as f: # load prompts from file
            data = json.load(f)

        return data

    def get_prompt(self, method):
        """get the prompt for the given method and add the current date to the context prompt"""
        today_date = str(datetime.datetime.now())
        context = self.prompts["context"] + today_date + "\n"

        return context + self.prompts[method]



    def summarize_messages(self, messages: list) -> str:
        prompt = [{"role": "system", "content": self.get_prompt('summarize_messages')}] + messages
        logging.info(f"summarize_messages gptlogic file Messages: {messages}")
        logging.info(f"summarize_message gptlogic Prompt: {prompt}")
        response = self.api_call(prompt, self.chat_model, 0)
        return response['choices'][0]['message']['content']



    def generate_resume(self, resume_inputs: list, user_phone_number) -> str:
        prompt = [
            {
                "role": "system",
                "content": self.get_prompt('generate_resume') + f"Phone Number: {user_phone_number}. Resume Inputs: {resume_inputs}"
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
        prompt = [{"role": "system", "content": self.get_prompt('get_user_name') + f"{summary_text}"}]
        logging.info(prompt)
        response = self.api_call(prompt, self.chat_model, 0, None)
        return response['choices'][0]['message']['content']


def num_tokens_from_messages(messages, tokenizer):
    num_tokens = 0
    for message in messages:
        num_tokens += tokenizer.tokenize(message['content']).count_tokens()
    return num_tokens

gpt_logic = GPTLogic()


messages = [{'role': 'user', 'content': 'Hi!'}, {'role': 'assistant', 'content': "Hello! I'm Ajira, a recruitment AI. I'm here to help you create a professional resume. Let's get started! Can you please provide me with your first name?"}, {'role': 'user', 'content': 'My First name is Antony'}, {'role': 'assistant', 'content': 'Nice to meet you, Antony! Could you also provide me with your last name?'}, {'role': 'user', 'content': 'Mutharia'}, {'role': 'assistant', 'content': 'Thank you, Antony Mutharia! Could you please provide me with your email address? This will allow potential employers to contact you.'}, {'role': 'user', 'content': 'my email address is antonynjoro@gmail.com'}, {'role': 'assistant', 'content': 'Thank you for providing your email address, Antony. Now, could you please provide me with your current address? This will help potential employers know your location.'}, {'role': 'user', 'content': 'My address is 135 Keedwell St'}, {'role': 'assistant', 'content': 'Thank you for providing your address, Antony. Could you also provide me with the city you reside in?'}, {'role': 'user', 'content': 'I live in Saskatoon'}, {'role': 'assistant', 'content': 'Great! And in which state or province is Saskatoon located?'}, {'role': 'user', 'content': "It's in Saskatchewan Canada"}, {'role': 'assistant', 'content': 'Thank you for providing that information, Antony. Lastly, could you please provide me with your zip code and country?'}, {'role': 'user', 'content': 'the Zip code is S7W 0A3'}, {'role': 'assistant', 'content': 'Thank you for providing your zip code, Antony. And just to confirm, your country is Canada, correct?'}, {'role': 'user', 'content': 'Yes. '}, {'role': 'assistant', 'content': "Thank you for confirming, Antony. Now let's move on to your work experience. Please provide me with the details of your most recent work experience. Start with the job title, the name of the company, and the dates of employment (start and end dates)."}, {'role': 'user', 'content': 'Most recently, I work in a software company called Coconut Software. I am a UX designer. I do research and create designs. I also work closely with developers to build out the desings. I started in August of last year and still working there.'}, {'role': 'assistant', 'content': "That's great, Antony! It sounds like you have valuable experience as a UX designer at Coconut Software. Could you please provide me with a brief description of your responsibilities and any notable achievements in this role?"}, {'role': 'user', 'content': 'I create designs, work with devs, work with the PM. The biggest achievement is creating an assignments page that Is used by admins to assign locations and services to staff in the branches they manage.'}, {'role': 'assistant', 'content': "That's impressive, Antony! Creating an assignments page that is used by admins to assign locations and services is a significant achievement. It shows your ability to collaborate with different teams and deliver practical solutions. Now, do you have any previous work experience before your role at Coconut Software? If yes, please provide me with the details starting with the most recent one."}, {'role': 'user', 'content': 'I have also worked in FactoryFix as a UX designer. I was working on a messaging page that allows recruiters to contact applicants and engage with them'}, {'role': 'assistant', 'content': "That's great, Antony! Working as a UX designer at FactoryFix and focusing on a messaging page for recruiters to contact applicants shows your versatility in designing user-friendly interfaces. Could you please provide me with the dates of your employment at FactoryFix (start and end dates) and a brief description of your responsibilities and achievements in that role?"}, {'role': 'user', 'content': 'Started in January of 2022 ended last month'}, {'role': 'assistant', 'content': 'Thank you for providing the dates of your employment at FactoryFix, Antony. Could you please provide me with a brief description of your responsibilities and any notable achievements during your time there?'}, {'role': 'user', 'content': "The messaging page was the biggest one of them. I also did lot's of use research with them and talked to dozens of users to help understand their needs. "}, {'role': 'assistant', 'content': "That's fantastic, Antony! Your work on the messaging page and conducting user research at FactoryFix demonstrates your dedication to creating user-centered designs. It's great that you took the initiative to understand the needs of the users and incorporate their feedback into your designs. \n\nNow, let's move on to your education. Could you please provide me with details about your highest level of education or any relevant certifications you have obtained?"}, {'role': 'user', 'content': 'I have obtained several NNg certifications in UX design. I also did a degree in Marketing from Chuka University. I graduated in 2013'}, {'role': 'assistant', 'content': "That's impressive, Antony! Your NNg certifications in UX design showcase your expertise in the field. Additionally, your degree in Marketing from Chuka University provides a well-rounded background. Thank you for sharing that information. \n\nNow, let's move on to your skills. Could you please provide me with a list of technical skills that are relevant to your desired job as a UX designer?"}, {'role': 'user', 'content': 'I have experience in Figma and have also been learning to code. I created the Ajira Application (you) that helps people create resumes. I created it in Python.'}, {'role': 'assistant', 'content': "That's wonderful, Antony! Your experience with Figma and your ongoing learning of coding, particularly in Python, are valuable technical skills for a UX designer. It's impressive that you created the Ajira Application to help people create resumes. \n\nIn addition to technical skills, do you have any soft skills that are relevant to your desired job? Soft skills can include things like communication, teamwork, problem-solving, or leadership abilities."}, {'role': 'user', 'content': 'I am a maker and explorer that loves learning and growing.'}, {'role': 'assistant', 'content': "That's fantastic, Antony! Being a maker and explorer with a passion for learning and growth is a valuable soft skill. It shows your curiosity, adaptability, and willingness to take on new challenges. These qualities can greatly contribute to your success as a UX designer. \n\nNow that I have gathered all the necessary information, let me provide you with a brief summary of your resume:\n\nName: Antony Mutharia\nEmail: antonynjoro@gmail.com\nAddress: 135 Keedwell St, Saskatoon, Saskatchewan, S7W 0A3, Canada\n\nWork Experience:\n1. UX Designer at Coconut Software\n   - Responsibilities: Creating designs, collaborating with developers and project managers.\n   - Notable Achievement: Creating an assignments page used by admins to assign locations and services.\n\n2. UX Designer at FactoryFix\n   - Responsibilities: Designing a messaging page for recruiters to contact applicants, conducting user research.\n   - Notable Achievement: Developing a user-friendly messaging page.\n\nEducation:\n- NNg Certifications in UX Design\n- Degree in Marketing from Chuka University (Graduated in 2013)\n\nSkills:\n- Technical Skills: Figma, Python (created the Ajira Application)\n- Soft Skills: Curiosity, adaptability, willingness to learn and grow.\n\nIs there anything else you would like to add or any changes you would like to make, Antony?"}, {'role': 'user', 'content': 'This is good . '}, {'role': 'assistant', 'content': 'Thank you for using Ajira we will be sending you your resume shortly <END>'}, {'role': 'user', 'content': 'This is good . '}, {'role': 'assistant', 'content': 'Thank you for using Ajira we will be sending you your resume shortly <END>'}, {'role': 'user', 'content': 'This is good . '}, {'role': 'assistant', 'content': 'Thank you for using Ajira we will be sending you your resume shortly <END>'}, {'role': 'user', 'content': 'This is good . '}, {'role': 'assistant', 'content': 'Thank you for using Ajira we will be sending you your resume shortly <END>'}, {'role': 'user', 'content': 'This is good . '}]
summarized_messages = gpt_logic.summarize_messages(messages=messages)

print(f"Summarized messages: {summarized_messages}")