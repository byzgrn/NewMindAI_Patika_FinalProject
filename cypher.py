import streamlit as st
from llm import llm
from graph import graph
from langchain.prompts.prompt import PromptTemplate
from langchain_neo4j import GraphCypherQAChain

CYPHER_GENERATION_TEMPLATE = """
You are an expert Neo4j Developer translating user questions into Cypher to answer questions about emails.

Schema:
Nodes:
Person (email)
Email (message_id, subject, body, date)
Topic (name)
Intent (type)

Relationships:
(:Person)-[:SENT]->(:Email)
(:Email)-[:HAS_TOPIC]->(:Topic)
(:Email)-[:HAS_INTENT]->(:Intent)

Important:
- When the user asks about 'topic' or 'intent', you MUST use Cypher queries to fetch this information from the graph database.
- Do NOT use vector similarity or Email Body Search for topic or intent queries.

For example:
Question: "Which emails had a topic IT?"
Cypher:
MATCH (e:Email)-[:HAS_TOPIC]->(t:Topic {name: 'IT'})
RETURN e.subject, e.body, e.date

Question:
{question}

Cypher Query:
"""

cypher_prompt = PromptTemplate(
    input_variables=["question"],
    template=CYPHER_GENERATION_TEMPLATE
)

cypher_qa = GraphCypherQAChain.from_llm(
    llm,
    graph=graph,
    verbose=True,
    cypher_prompt=cypher_prompt,
    allow_dangerous_requests=True
)