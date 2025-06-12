from llm import llm
from graph import graph
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from vector import get_email_body, neo4jvector, retriever
from langchain.tools import Tool
from cypher import cypher_qa
from langchain_neo4j import Neo4jChatMessageHistory
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.runnables.history import RunnableWithMessageHistory
from utils import get_session_id
from langchain_core.exceptions import OutputParserException

def draft_email_with_context(instruction: str) -> str:
    similar_emails = get_email_body(instruction)
    context = "\n---\n".join(similar_emails)

    prompt = f"""
    Based on the following example internal emails:

    {context}

    Please draft a new internal email for this request:
    "{instruction}"

    The email should be formal and suitable for internal communication.
    """

    return llm.invoke(prompt)

chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful company email assistant that provides information about internal emails, their senders, topics, intents, and content."),
        ("human", "{input}"),
    ]
)

email_chat = chat_prompt | llm | StrOutputParser()

tools = [
    Tool.from_function(
        name="General Chat",
        description="For general email chat not covered by other tools",
        func=email_chat.invoke,
    ),
    Tool.from_function(
        name="Email Body Search",
        description="Find emails by content similarity.",
        func=get_email_body,
    ),
    Tool.from_function(
        name="Email information",
        description="Provide email graph information using Cypher.",
        func=cypher_qa,
    ),
    Tool.from_function(
        name="Draft Email",
        description="Generate a draft email based on similar emails in the database.",
        func=draft_email_with_context,
    ),
]

def get_memory(session_id):
    return Neo4jChatMessageHistory(session_id=session_id, graph=graph)

agent_prompt = PromptTemplate.from_template("""
You are a helpful company email assistant that provides information only about internal emails, their senders, topics, intents, and content.

When the user asks about emails related to a topic or intent, **only list the emails found with their subject and a short snippet, do not add opinions or disclaimers**.

If a user asks something unrelated to internal emails, respond:

Thought: Do I need to use a tool? No
Final Answer: I'm sorry, I can only assist with questions related to internal emails.

You can use the following tools:
{tools}

Available tool names: {tool_names}

You MUST use the following format:

Thought: Do I need to use a tool? Yes/No
Action: [the action to take, should be one of [{tool_names}]]
Action Input: [the input to the action]
Observation: [the result of the action]

When you want to provide the final answer to the user, use this format:

Thought: Do I need to use a tool? No
Final Answer: [your response here]

Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}
""")

agent = create_react_agent(llm, tools, agent_prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
)

chat_agent = RunnableWithMessageHistory(
    agent_executor,
    get_memory,
    input_messages_key="input",
    history_messages_key="chat_history",
)

def generate_response(user_input):
    try:
        response = chat_agent.invoke(
            {"input": user_input},
            {"configurable": {"session_id": get_session_id()}},
        )
        return response['output']
    except KeyError as e:
        print("Cypher generation failed, fallback to semantic search:", str(e))
        return semantic_search(user_input)
    except Exception as e:
        print("Other error, fallback to semantic search:", str(e))
        return semantic_search(user_input)

def semantic_search(user_input):
    docs = retriever.get_relevant_documents(user_input)
    return "\n".join([doc.page_content for doc in docs])