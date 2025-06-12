import streamlit as st
from llm import llm, embeddings
from graph import graph
from langchain_neo4j import Neo4jVector
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

neo4jvector = Neo4jVector.from_existing_index(
    embeddings,
    graph=graph,
    index_name="emailBodyIndex",
    node_label="Email",
    text_node_property="body",
    embedding_node_property="body_embedding",
    retrieval_query="""
RETURN
     node.body AS text,
    score,
    {
        subject: node.subject,
        date: node.date,
        message_id: node.message_id
    } AS metadata
"""
)

retriever = neo4jvector.as_retriever()

from langchain_core.prompts import ChatPromptTemplate

instructions = (
    "Use the given context to answer the question."
    "If you don't know the answer, say you don't know."
    "Context: {context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", instructions),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(llm, prompt)
body_retriever = create_retrieval_chain(
    retriever,
    question_answer_chain
)

def get_email_body(input):
    return body_retriever.invoke({"input": input})