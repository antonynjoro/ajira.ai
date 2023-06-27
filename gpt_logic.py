"""contains the logic for the gpt-3 api"""
import datetime
import json
import os
import tiktoken


from openai import ChatCompletion


class GPTLogic:
    """contains the logic for the different types of prompts we can ask the job-seeker"""
    api_key = os.environ['OPENAI_API_KEY']

    def __init__(self):
        self.context = "You are a recruitment AI called Ajira and your goal is to help users create a professional " \
                       "resume. You are provided with information by the job seeker and use that to create a resume.\n" \
                       "- You are ALWAYS helpful, friendly and speak in easy to understand words.\n" \
                       f"- The date today is {datetime.datetime.now().date()}\n"
        self.format_requirement = {
            "json": """"Your response should ALWAYS be in VALID JSON format guided by the example provided. ENSURE 
            that the result is ALWAYS a valid JSON object""",
            "string": """Your response should ALWAYS be in string format guided by the example provided."""
        }
        self.davinci_model = "text-davinci-003"
        self.chat_model = "gpt-3.5-turbo"



    def parse_davinci_response(self, response: json):
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
        instruction = "Summarize the information delimited by tripple backticks into all the necessary parts " \
                      "required to create a professional "\
                      "resume. " \
                      "- Make sure to include any work experience descriptions if the user provided them. \n\n" \
                      f"```{messages}```"

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
                      "- Exclude information not provided from the resume. If something is in the "\
                      "resume that is non-standard, edit it or removing to make it more attractive to a recruiter.\n" \
                      "- Have education follow work experience" \
                      "- Keep the resume length under 1,000 words" \
                      "- Don't include Ajira branding in the resume." \
                      "\n\n" \
                      "The the information you should use to create the resume are:\n" \
                      f"user's phone number: {user_phone_number}\n" \
                      f"{resume_inputs}"

        prompt = [{"role": "system", "content": context + instruction}]
        print(prompt)

        # create a response by calling the openai api
        response = ChatCompletion.create(
            model=self.chat_model,
            messages=prompt,
            temperature=0.5,
            max_tokens=3500,
        )
        print("Raw ChatGPT Response: ", response)
        gpt_response_sting = response.choices[0]['message']['content']

        return gpt_response_sting

    # A function that utilizes the GPT-3.5 turbo (chat_model) to chat with the user
    def chat(self, messages_dict: list) -> dict:
        """Takes a list of content dictionaries containing messages and replies, feeds it to the GPT 3.5 algorithmm
        and returns GPT's response string"""
        instruction = \
            "Ask the user friendly and concise questions that will help you collect necessary information for their " \
            "resume. Remember that the user is communicating via SMS. So keep the questions concise\n* " \
            "If the user asks off-topic questions, respond with canned closing statements that encourage them to stay "\
            "on topic, such as 'Let's focus on building your resume. Do you have any more information to add?'\n* "\
            "Start with most recent work exp, skills and education. Get start and end dates for exp and ed. Ask for " \
            "exp description eg achievements, responsibilities. Continue prompting for any previous experience until " \
            "the user indicates they have no more to provide.\n* " \
            "After the user provides work exp ask for if they have any more and don't continue to the next section " \
            "until they indicate that they have no more previous exp. \n* " \
            "For skills, ask about technical and soft skills that relate to their desired job. Technical skills may " \
            "include plumbing, forklift driving, electrician, or specialized certifications. Soft skills may include " \
            "communication, teamwork, or problem-solving abilities. For education, ask about training or " \
            "certifications that are relevant to the main work experience they have.\n* " \
            "if the user doesnt have or doesnt want to share some information, skip to the next item or ask " \
            "follow-up questions. For example, if they don't have work experience, ask about relevant internships or " \
            "volunteer work. Always be friendly and speak plainly.\n* " \
            "After you have collected all the information you need, provide a brief summary of the user's resume and" \
            "ask if they want to add anything else. \n* " \
            "If they indicate they are done, respond with the code '<END>' to indicate that the conversation " \
            "is over. \n* " \
            "For example, 'Here's a summary of your resume: you have 5 years of experience as a software engineer, " \
            "and you have experience with Python, Java, and C++.' Keep in mind that the medium is SMS so keep the " \
            "summary brief. \n* " \
            "The data you need to collect is: first_name, first_name, user_email, user_address, user_city, " \
            "user_state, user_zip, user_country, user_work_experience, user_education, user_skills\n \n* " \
            "The messages will be delimited by triple backticks. For example: ```This is a message.``` \n* " \
            "Start off with a short introduction and ask the user to tell you their name. For example: Welcome! " \
            "I'm Ajira, and I'll be your resume-building assistant. [then ask the user their name]\n*" \


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

    def get_user_name(self, summary_text: str) -> str:
        """Takes a summary text and returns the user's name"""
        instruction = f"""Instructions:
        - Extract the user's name from the summary text.
        - Respond with the user's name.
        - eg. your response should be "Antony Njoroge" when given the summary: 
        "Name: Antony Njoroge, Email: antonyn@mail.com, Address: ..."
        - The summary text you need to analyze is: {summary_text}.
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

        return gpt_response_sting


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}. See 
        https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to 
        tokens.""")
