import streamlit as st
from utils import write_message
from agent import generate_response

st.set_page_config("EmailBot", page_icon=":email:")

st.title("Fake Company EMail Assistant")
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi, I'm your Email Assistant! How can I help you with company emails?"},
    ]

def handle_submit(message):

    with st.spinner('Thinking...'):
        response = generate_response(message)
        write_message('assistant', response)

for message in st.session_state.messages:
    write_message(message['role'], message['content'], save=False)

if question := st.chat_input("What is up?"):
    write_message('user', question)

    handle_submit(question)
