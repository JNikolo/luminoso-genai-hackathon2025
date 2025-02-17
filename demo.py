import streamlit as st
import pandas as pd
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain.schema import HumanMessage, AIMessage, SystemMessage


# Load environmental variables
load_dotenv()

st.title("Claude")

# Set LLM model: gpt-4o-mini
model = ChatOpenAI(model="gpt-4o-mini", streaming=True)

# Read from csv containing review summaries
df = pd.read_csv("summarized_reviews.csv")

# Create filter tool for agent
@tool
def filter_reviews(city: str = None, start_date: str = None, end_date: str = None, address_fragment: str = None, state: str = None) -> list[str]:
    """Returns list of reviews from clients after optional filtering. Non-given arguments indicate no filter needed.
    
    Args:
        city (str, optional): Name of the city the store is located. Optional, if not given don't ask.
        start_date (str, optional): Start date in 'YYYY-MM-DD' format. Defaults to first of the month or 2024 if incomplete. Optional, if not given don't ask.
        end_date (str, optional): End date in 'YYYY-MM-DD' format. Defaults to end of month or 2024 if incomplete. Optional, if not given don't ask.
        address_fragment (str, optional): Fragment of street address of the store, will use regex matching. Optional, if not given don't ask.
        state (str, optional): Two-letter abbreviation of state the store is located in. Some stores are in Canada so no state for those. Optional, if not given don't ask.

    Returns:
        list[str]: List of reviews that match the specified filters.
    """

    filtered_df = df.copy()
    if start_date is not None:
        filtered_df = filtered_df[(filtered_df['date_Date Created'] >= start_date)]
    if end_date is not None:
        filtered_df = filtered_df[(filtered_df['date_Date Created'] <= end_date)]

    if city is not None:
        filtered_df = filtered_df[(filtered_df['string_City'].str.contains(city, case=False, na=False))]

    if state is not None:
        filtered_df = filtered_df[(filtered_df['string_State'].str.contains(state, case=False, na=False))]

    if address_fragment is not None:
        filtered_df = filtered_df[filtered_df['string_Place Location'].str.contains(address_fragment, case=False, na=False, regex=True)]

    reviews = filtered_df['summary'].tolist()
    
    return reviews if reviews else ["No reviews found for the given filters."]

# Set tools allowed
tools = [filter_reviews]

# Create system prompt to be fed to LLM
prompt = """You are a customer experience analysis assistant with access to a large number of client reviews. Your primary users are customer experience analysts who rely on you to filter and analyze reviews.
    **Your workflow:**
    1. **Filter the reviews:** Use the `filter_reviews` tool to apply any specified filters (city, date range, address fragment, state). If the client does not specify certain filters, do not apply them.
    2. **Analyze the reviews:** Use the now filtered reviews to provide an overall analysis that answers the client’s query. If comparisons are requested, apply the filtering to each subset before making the comparisons.

    **Tools available:**
    - `filter_reviews`: Use this to filter the reviews based on the client's specified criteria. If a filter is not mentioned, do not apply it.
    """

# Create memory storage
memory = MemorySaver()
config = {"configurable": {"thread_id": "daylight-testing"}}


# Create ReAct LLM to be run
agent_executor = create_react_agent(model, tools, checkpointer=memory, prompt=prompt)


if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini"



# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input from user
if user_input := st.chat_input("Enter query"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Get response from ReAct model
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        final_response = None
        
        # Stream the response
        for chunk in agent_executor.stream(
            {"messages": [HumanMessage(content=user_input)]}, config
        ):
            if isinstance(chunk, dict):
                # Skip tool messages
                if 'tools' in chunk:
                    continue
                    
                # Handle final agent response
                if 'agent' in chunk and 'messages' in chunk['agent']:
                    messages = chunk['agent']['messages']
                    if isinstance(messages, list) and len(messages) > 0:
                        final_response = messages[0].content
            
            # Update placeholder only if we have a final response
            if final_response:
                message_placeholder.markdown(final_response)
    
    # Add only the final response to chat history
    if final_response:
        st.session_state.messages.append({"role": "assistant", "content": final_response})