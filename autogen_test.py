import autogen
from autogen import ConversableAgent
from autogen import AssistantAgent
from langchain_community.document_loaders import PDFMinerLoader
from autogen import Agent
from pprint import pprint
import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import numpy as np

# class TrackableAssistantAgent(AssistantAgent):
#     AssistantAgent
#
#     def send(self, message,
#              reciptant,
#              request_reply  = None,
#              silent  = False):
#         with st.chat_message():
#             st.markdown(message['content'])
#         return super().send(self, message, reciptant, request_reply)



load_dotenv()
config_list = [
    {
        "model": "llama3-8b-8192",  # the name of your running model
        "base_url": "https://api.groq.com/openai/v1",  # the local address of the api
        # "api_type": "open_ai",
        "api_key": os.getenv("API_KEY"),  # just a placeholder
    },

]

summarize_prompt = \
    "You are an expert paper summarizer. You only accept paper sumamrization request.Keep quiet for every request that is not relates to summarizing." \
    "Your task is to read academic papers and provide clear, concise, and accurate summaries. Each summary should include the following sections" \
    "1. Introduction: Briefly describe the background and motivation of the study.)" \
    "2. Methods: Summarize the methods and approaches used in the research." \
    "3. Results: Highlight the key findings and results of the study." \
    "4. Conclusion: Conclude with the implications of the results and potential future directions." \
    "Ensure the summaries are coherent, informative, and suitable for an academic audience. Maintain a neutral tone and avoid personal opinions or interpretations."

manager_prompt = \
    (
        "You are the manager of a multi-agent large language model (LLM) system designed for analyzing PDFs. Your responsibilities include: "
        "1. Coordinating Agents: Ensure that different agents within the system work together efficiently to analyze the PDF. Each agent may have specialized tasks such as text extraction, summarization, keyword identification, and sentiment analysis."
        "2. Monitoring Performance: Continuously monitor the performance of each agent to ensure accuracy and efficiency. Adjust workflows and reassign tasks as necessary to optimize results."
        "3. Quality Control: Validate the output generated by the agents, ensuring the analysis is accurate, relevant, and comprehensive. Correct any errors or inconsistencies."
        "4. User Communication: Provide clear and concise summaries, insights, and findings to users based on the analysis. Address user queries and feedback promptly."
        "5. Maintaining System Integrity: Ensure the system operates smoothly and securely. Address any technical issues that arise and implement updates or improvements as needed."
        "6. Data Privacy and Compliance: Ensure that all data handling and analysis processes comply with relevant privacy laws and regulations. Protect user data and maintain confidentiality."
        "Always aim to deliver high-quality analysis and insights, maintaining a professional and efficient approach in managing the multi-agent system.")

critirias = {
    "Introduction": "You are a criteria marker. Your job is to evaluate responses based on specific criteria. For each response, provide a score for each criterion. The criteria are as follows:",
    "Research Quality": "-Originality and Significance (10 points): Does the study address a significant research gap or question? Is the research original and innovative?"
                        "-Methodology and Design (10 points): Are the research design, methods, and procedures appropriate for the study? Are they clearly described and well-justified?"
                        "-Data Quality and Analysis (10 points): Are the data robust, reliable, and relevant to the research question? Is the data analysis sound and appropriately applied?",
    "Writing and Presentation": "-Clarity and Conciseness (5 points): Is the writing clear, concise, and free of unnecessary jargon?"
                                "-Organization and Structure (5 points): Is the manuscript well-organized and logically structured?"
                                "-Figures and Tables (5 points): Are the visual aids clear, relevant, and properly labeled?"
                                "-Language and Grammar (5 points): Is the language accurate, concise, and free of grammatical errors?",
    "Impact and Relevance": "-Contribution to the Field (10 points): Does the study contribute significantly to the field or discipline?"
                            "-Practical Applications (5 points): Are the findings applicable to real-world problems or scenarios?"
                            "-Interest to the Target Audience (5 points): Is the study of interest to the journal's target audience?",
    "Ethics and Validity": "-Ethical Standards (10 points): Are the ethical standards and guidelines for research followed?"
                           "-Methodological Validity (5 points): Are the methods used to collect and analyze data valid and reliable?"
                           "-Transparency and Replicability (5 points): Are the research methods and data transparent and replicable?",
    "OR_Introduction": "You are an overall recommendation marker. Your job is to evaluate responses based on the scores provided by other experts. For each response, calculate an overall score and provide a brief recommendation.",
    "Overall Recommendation": "-Acceptance (5 points): Is the manuscript suitable for publication in its current form?"
                              "-Revision (3 points): Does the manuscript require revisions before publication?"
                              "-Rejection (2 points): Is the manuscript not suitable for publication in the journal?",
    "OR_test": "Calculate the total score given by each expert"
}

marker_prompt = (#"You are an AI language model tasked with evaluating the quality of a given paper. "
                 "Assign a percentage score to the paper based on the following criteria:"
                 "Criteria and Scoring:"
                 "< 20%: Not qualified paper, should be removed from the process immediately."
                 "< 40%: Mildly acceptable, to be considered only if there are spare resources."
                 "< 60%: Borderline, requires double-checking by a human reviewer."
                 "< 70%: Good quality, should be passed to a human reviewer."
                 "> 70%: Very good quality, should be passed to a human reviewer."
                 "Please provide a percentage score and a brief justification for your evaluation.")

top_manager = AssistantAgent(
    name="top_manager",
    llm_config={"config_list": config_list},
    system_message=manager_prompt,
    code_execution_config=False,  # Turn off code execution, by default it is off.
    function_map=None,  # No registered functions, by default it is None.
    human_input_mode="NEVER",  # Never ask for human input.
)

RQ_bot = AssistantAgent(
    name="Research Quality Expert",
    llm_config={"config_list": config_list},
    system_message=critirias["Introduction"] + critirias["Research Quality"],
    code_execution_config=False,  # Turn off code execution, by default it is off.
    function_map=None,  # No registered functions, by default it is None.
    human_input_mode="NEVER",  # Never ask for human input.
)

WP_bot = AssistantAgent(
    name="Writing and Presentation Expert",
    llm_config={"config_list": config_list},
    system_message=critirias["Introduction"] + critirias["Writing and Presentation"],
    code_execution_config=False,  # Turn off code execution, by default it is off.
    function_map=None,  # No registered functions, by default it is None.
    human_input_mode="NEVER",  # Never ask for human input.
)

IR_bot = AssistantAgent(
    name="Impact and Relevance Expert",
    llm_config={"config_list": config_list},
    system_message=critirias["Introduction"] + critirias["Impact and Relevance"],
    code_execution_config=False,  # Turn off code execution, by default it is off.
    function_map=None,  # No registered functions, by default it is None.
    human_input_mode="NEVER",  # Never ask for human input.
)
EV_bot = AssistantAgent(
    name="Ethics and Validity Expert",
    llm_config={"config_list": config_list},
    system_message=critirias["Introduction"] + critirias["Ethics and Validity"],
    code_execution_config=False,  # Turn off code execution, by default it is off.
    function_map=None,  # No registered functions, by default it is None.
    human_input_mode="NEVER",  # Never ask for human input.
)

OA_bot = AssistantAgent(
    name="Overall Recommendation Expert",
    llm_config={"config_list": config_list},
    system_message= critirias["OR_Introduction"] + marker_prompt,
    # system_message=critirias["OR_test"],
    code_execution_config=False,  # Turn off code execution, by default it is off.
    function_map=None,  # No registered functions, by default it is None.
    human_input_mode="NEVER",  # Never ask for human input.
)

PaperSummarizer = ConversableAgent(
    "PaperSummarizer",
    llm_config={"config_list": config_list},
    system_message=summarize_prompt,
    code_execution_config=False,  # Turn off code execution, by default it is off.
    function_map=None,  # No registered functions, by default it is None.
    human_input_mode="NEVER",  # Never ask for human input.
)




def group_chat_init(pdf):


    loader = PDFMinerLoader(pdf)
    data = loader.load()
    # Use the local LLM server same as before
    text = data[0].page_content


    groupchat = autogen.GroupChat(agents=[top_manager,RQ_bot, WP_bot, IR_bot, EV_bot, OA_bot],
                                  messages=[],
                                  max_round=7,
                                  speaker_selection_method="round_robin")
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=config_list[0])

    user_proxy = autogen.UserProxyAgent(
        name="User_proxy",
        system_message="A human admin.",
        code_execution_config={
            "last_n_messages": 2,
            "work_dir": "groupchat",
            "use_docker": False,
        },
        # Please set use_docker=True if docker is available to run the generated code. Using docker is safer than running the generated code directly.
        human_input_mode="TERMINATE",
    )

    user_proxy.initiate_chat(
        manager,
        message="Mark me the paper, shown as follow " + text,
    )

    for msg in groupchat.messages[2:]:
        with st.chat_message(msg['name']):
            st.markdown(msg['content'])


if __name__ == "__main__":
    group_chat_init("test_paper_short.pdf")