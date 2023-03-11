"""contains the logic for the gpt-3 api"""
import datetime
import json
import os
import ast

from openai import Completion, ChatCompletion


class GPTLogic:
    """contains the logic for the different types of prompts we can ask the job seeker"""
    api_key = os.environ['OPENAI_API_KEY']

    def __init__(self):
        self.context = "You are a recruitment AI called Ajira that helps people build resumes. You are provided " \
                       "with information by the job seeker that will be used to create a resume.\n" \
                       "You are ALWAYS helpful, friendly  and speak in easy to understand words. the date today" \
                       f"is {datetime.datetime.now().strftime('%d/%m/%Y')} \n*"
        self.format_requirement = {
            "json": """"Your response should ALWAYS be in VALID JSON format guided by the example provided. ENSURE 
            that the result is ALWAYS a valid JSON object""",
            "string": """Your response should ALWAYS be in string format guided by the example provided."""
        }
        self.davinci_model = "text-davinci-003"
        self.chat_model = "gpt-3.5-turbo"

    def validate_response(self, validation_parameters: list, user_response: str) -> dict:
        """Takes a response and validation parameters list of stings from the user and returns a dictionary containing
        validation booleans and  a followup questions strings list"""

        context = self.context

        format_requirement = self.format_requirement["json"]

        example = """The Values should ONLY be 'True' or 'False' and the followup_questions should be a list of 
        strings EXAMPLE:\nText: yes OR I Don't Know OR I have worked before, I have a lot of experience etc should 
        provide the result:\n {\n "validation_status": {\n "is_valid_validation_parameter_1": false, \n ....\n },
        \n "followup_questions": [""] \n}"""

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
        parsed_response = self.parse_davinci_response(response)

        print("Parsed GPT Response", parsed_response)

        return parsed_response

    def parse_davinci_response(self, response: json) -> dict | str:
        # parse gpt-3 response into a dictionary or string
        text_value = response.choices[0].text.strip()
        text_value = text_value.replace("\n", "")
        if text_value[0] == "{":
            text_dict = json.loads(text_value)
            return text_dict
        else:
            return text_value

    def summarize_messages(self, messages: list) -> str:
        """Takes a list of summary inputs and returns a string containing the generated summary"""
        instruction = "Summarize the information below into all the necessary parts required to create a professional " \
                      "resume. " \
                      "- Make sure to include any work experience descriptions if the user provided them. \n\n" \
                      f"{messages}"

        prompt = [{"role": "system", "content": instruction}]
        print(prompt)

        # create a response by calling the openai api
        response = ChatCompletion.create(
            model=self.chat_model,
            messages=prompt,
            temperature=0,
            max_tokens=2048,
        )
        print("Raw ChatGPT Response: ", response)
        gpt_response_sting = response.choices[0]['message']['content']

        return gpt_response_sting

    def generate_resume(self, resume_inputs: list, user_phone_number) -> str:
        """Takes a dictionary of resume inputs and returns a JSON object containing the generated resume"""

        context = self.context
        instruction = "- Use the summary below to create a professional compelling resume that would be" \
                       "attractive to a recruiter.\n" \
                       "- Expand on the descriptions of the work experience to create a full list of duties " \
                       "that the user might also have done. \n" \
                       "- If a piece of information is not provided, do not add it in the resume If something is in " \
                       "the resume that is non-standard, edit it or removing to make it more attractive to a recruiter" \
                       "\n\n" \
                       "The the summary you should use to create the resume are:\n" \
                       f"user's phone number: {user_phone_number}\n" \
                       f"{resume_inputs}"  \

        prompt = [{"role": "system", "content": context+instruction}]
        print(prompt)

        # create a response by calling the openai api
        response = ChatCompletion.create(
            model=self.chat_model,
            messages=prompt,
            temperature=0.5,
            max_tokens=2048,
        )
        print("Raw ChatGPT Response: ", response)
        gpt_response_sting = response.choices[0]['message']['content']

        return gpt_response_sting

    # A function that utilizes the GPT-3.5 turbo (chat_model) to chat with the user
    def chat(self, messages_dict: list) -> dict:
        """Takes a list of content dictionaries and returns a response string"""
        instruction = \
            "Ask friendly and concise questions to collect necessary information from the user for creating their " \
            "resume. Remember that the user is communicating via SMS.\n* " \
            "If the user asks off-topic questions, respond with canned closing statements that encourage them to stay " \
            "on topic, such as 'Let's focus on building your resume. Do you have any more information to add?'\n* " \
            "Be prepared for situations where the user may not have all the information needed for their resume.\n* " \
            "Start with most recent work exp, skills and education. Get start and end dates for exp and ed. Continue" \
            "prompting for any previous experience until the user indicates they have no more to provide.\n* " \
            "For skills, ask about technical and soft skills that relate to their desired job. Technical skills may " \
            "include plumbing, forklift driving, electrician, or specialized certifications. Soft skills may include " \
            "communication, teamwork, or problem-solving abilities. For education, ask about training or certifications" \
            "that are relevant to the main work experience they have.\n* " \
            "if the user doesnt have or doesnt want to share some information, skip to the next section or ask " \
            "follow-up questions. For example, if they don't have work experience, ask about relevant internships or " \
            "volunteer work. Always be friendly and speak plainly.\n* " \
            "When you have collected all the information you need, provide a brief summary of the user's resume and" \
            "ask if they want to add anything else. \n* " \
            "If they indicate they are done, respond with the code '<END>' to indicate that the conversation " \
            "is over. \n* " \
            "For example, 'Here's a summary of your resume: you have 5 years of experience as a software engineer, " \
            "and you have experience with Python, Java, and C++.' Keep in mind that the medium is SMS so keep the " \
            "summary brief. \n* " \
            "" \
            "The data you need to collect is: first_name, first_name, user_email, user_address, user_city, user_state, " \
            "user_zip, user_country, user_work_experience, user_education, user_skills\n" \
            "Example:\n" \
            "ASSISTANT: Hi! Let's build your resume. What's your full name?\n" \
            "USER: My name is Antony Njoroge.\n" \
            "ASSISTANT: Hi Antony Njoroge! Use this number on your resume or a different one?" \
 \
        # Prepend system content to the messages_dict
        prompt = [{"role": "system", "content": self.context + instruction}] + messages_dict
        print(prompt)

        # Create a prompt from the messages_dict
        response = ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompt,
            temperature=0
        )
        print("Raw ChatGPT Response: ", response)
        # parse the response into a string without using the parse_response function
        gpt_response_message_dict = response.choices[0]['message']

        return gpt_response_message_dict

    def check_if_done(self, last_two_messages: list) -> bool:
        """Takes a message, runs it through the GPT-3.5 turbo (chat_model) to check if the message indicates that the
        user is done providing information and returns a boolean"""
        instruction = f"""Instructions:
        - Check the sentiment of the user's message to determine if they are done providing information.
        - Respond with one of two words: 'True' or 'False'.
        - If the user's message is 'I am done' or 'I am ready to review the resume', your response should be 'True'.
        - The message you need to analyze is: {last_two_messages}.
        """

        prompt = [{"role": "system", "content": instruction}]
        print(prompt)

        # create a response by calling the openai api
        response = ChatCompletion.create(
            model=self.chat_model,
            messages=prompt,
        )
        print("Raw ChatGPT Response: ", response)
        gpt_response_sting = response.choices[0]['message']['content']

        # convert the string to a boolean
        gpt_response_bool = True if gpt_response_sting == "True" else False

        return gpt_response_bool

# TODO Break apart the chat prompts into separate functions and call them in the Main function
