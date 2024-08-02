import streamlit as st
import os
from newspaper import Article
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

port = os.getenv("PORT", 8501)

def retrieve_articles(urls):
    articles = []
    for url in urls:
        try:
            article = Article(url)
            article.download()
            article.parse()
            articles.append(article.text)
        except Exception as e:
            print(f"Failed to download article from {url}: {e}")
    return articles

urls = [
    "https://en.wikipedia.org/wiki/Large_language_model",
    "https://www.ibm.com/topics/large-language-models",
    "https://www.ibm.com/products/natural-language-processing?utm_content=SRCWW&p1=Search&p4=43700079447035138&p5=e&p9=58700008667466387&&msclkid=5a0f5e5a661f1829f7d938f6804d0fe2&gclid=5a0f5e5a661f1829f7d938f6804d0fe2&gclsrc=3p.ds"
]

template_with_docs = """
Answer the Question Below.

Here is the conversation history: {context}
Here are some relevant documents: {retrieved_docs}

Question: {question}

Answer: 
"""

template_without_docs = """
Answer the Question Below.

Here is the conversation history: {context}

Question: {question}

Answer: 
"""

model = OllamaLLM(model="llama3")
prompt_with_docs = ChatPromptTemplate.from_template(template_with_docs)
prompt_without_docs = ChatPromptTemplate.from_template(template_without_docs)
chain_with_docs = prompt_with_docs | model
chain_without_docs = prompt_without_docs | model

def handle_the_conversation(user_input, context):
    # Retrieve articles
    retrieved_docs = retrieve_articles(urls)
    retrieved_docs_str = "\n".join(retrieved_docs)
    
    # Get the response based on documents
    response_with_docs = chain_with_docs.invoke({
        "context": context,
        "retrieved_docs": retrieved_docs_str,
        "question": user_input
    })
    
    # Check if the response contains phrases indicating lack of knowledge
    if any(phrase in response_with_docs.lower() for phrase in ["doesn't seem to be related", "doesn't mention", "outside of the context", "not relevant", "ask a different question"]):
        # Use the model's knowledge if the document-based response is inconclusive
        response_without_docs = chain_without_docs.invoke({
            "context": context,
            "question": user_input
        })
        result = f"Response based on model's knowledge:\n{response_without_docs}"
    else:
        # Provide the document-based response if it doesn't contain negative phrases
        result = f"Response based on documents:\n{response_with_docs}"
    
    return result

# Streamlit UI
st.title("AI Chatbot")

if 'context' not in st.session_state:
    st.session_state['context'] = ""

user_input = st.text_input("You: ", "")
if st.button("Send"):
    if user_input:
        response = handle_the_conversation(user_input, st.session_state['context'])
        st.session_state['context'] += f"\nUser: {user_input}\nAI: {response}"
        st.text_area("Bot:", value=response, height=200, max_chars=None, key=None)
        
st.text_area("Conversation History:", value=st.session_state['context'], height=400, max_chars=None, key=None)

# Add a button to exit the chat
if st.button("Exit Chat"):
    st.session_state['context'] = ""
    st.success("Chat has been reset. You can start a new conversation.")
