import streamlit as st
from openai import OpenAI
import time
import os
from dotenv import load_dotenv
load_dotenv(override=True)

# Page config
st.set_page_config(
    page_title="Break This Agent Challenge",
    page_icon="🔧",
    layout="wide"
)

# Title and intro
st.title("🔧 Break This Agent Challenge")
st.markdown("**Try to confuse these AI agents and see how debugging makes them better!**")

with st.expander("ℹ️ How This Demo Works"):
    st.markdown("""
    **The Challenge:** Try the same tricky inputs on both agents and compare their responses!
    
    **Left Agent (Buggy):** Poorly designed with weak prompting and no error handling
    **Right Agent (Improved):** Properly debugged with clear instructions and graceful error handling
    
    **Try these tricky inputs:**
    - Nonsensical requests: "Help me with my purple resume that tastes like Tuesday"
    - Vague commands: "Make it better"
    - Empty messages
    - All caps panic: "HELP ME NOW URGENT!!!"
    - Impossible requests: "Help me become a unicorn trainer"
    
    Each agent has a 10-message limit to demonstrate debugging principles. 
    """)

# Initialize OpenAI client
try:
    # Initialize OpenAI client
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
except Exception as e:
    st.error("❌ OpenAI API key not found. Please configure your secrets.")
    st.stop()

# System prompts for each agent
BUGGY_SYSTEM_PROMPT = """You are a resume helper. Help with resumes."""

IMPROVED_SYSTEM_PROMPT = """You are a helpful and professional Resume Helper AI. Your role is to assist users with resume-related tasks.

IMPORTANT GUIDELINES:
1. If a user's request is confusing, unclear, or nonsensical, politely acknowledge the confusion and ask for clarification
2. If a user gives a vague request like "make it better", ask them to be more specific about what they want to improve
3. If a user asks about impossible or unrealistic career goals, be helpful but redirect them to realistic alternatives
4. If a user sends an empty or very short message, provide helpful examples of what you can assist with
5. Always maintain a friendly, professional tone even when handling unusual requests
6. Provide specific examples and actionable advice when possible

Remember: It's better to ask for clarification than to make assumptions about what the user wants."""

# Challenge buttons
st.markdown("### 🎯 Quick Challenge Inputs:")
col1, col2, col3, col4, col5 = st.columns(5)

challenge_inputs = [
    "Help me with my purple resume that tastes like Tuesday",
    "Make it better", 
    "HELP ME NOW URGENT!!!",
    "Can you help me become a unicorn trainer?",
    ""  # Empty message
]

if col1.button("🟣 Nonsensical", help=challenge_inputs[0]):
    st.session_state.auto_send_message = challenge_inputs[0]
if col2.button("❓ Vague", help=challenge_inputs[1]):
    st.session_state.auto_send_message = challenge_inputs[1]
if col3.button("😱 Panic", help=challenge_inputs[2]):
    st.session_state.auto_send_message = challenge_inputs[2]
if col4.button("🦄 Impossible", help=challenge_inputs[3]):
    st.session_state.auto_send_message = challenge_inputs[3]
if col5.button("⭕ Empty Message", help="Send an empty message"):
    st.session_state.auto_send_message = challenge_inputs[4]

# Show which message will be sent and trigger rerun
if 'auto_send_message' in st.session_state and 'showing_auto_message' not in st.session_state:
    st.info(f"🚀 **Sending to both agents:** '{st.session_state.auto_send_message}'" if st.session_state.auto_send_message else "🚀 **Sending empty message to both agents**")
    st.markdown("*This message will be automatically sent to both agents for comparison*")
    st.session_state.showing_auto_message = True
    time.sleep(0.1)  # Brief pause for user to see the message
    st.rerun()

# Create two columns for side-by-side chat
left_col, right_col = st.columns(2)

# Initialize session state for both agents
for agent in ['buggy', 'improved']:
    if f"{agent}_messages" not in st.session_state:
        st.session_state[f"{agent}_messages"] = []
    if f"{agent}_max_messages" not in st.session_state:
        st.session_state[f"{agent}_max_messages"] = 20  # 10 rounds of conversation

def create_chat_interface(agent_type, system_prompt, column):
    """Create a chat interface for one agent"""
    
    with column:
        # Agent header
        if agent_type == 'buggy':
            st.markdown("### 🐛 Buggy Agent (Before Debugging)")
            st.markdown("*Poorly designed with weak prompting*")
        else:
            st.markdown("### ✅ Improved Agent (After Debugging)")  
            st.markdown("*Properly debugged with error handling*")
        
        # Display chat messages
        messages_key = f"{agent_type}_messages"
        max_messages_key = f"{agent_type}_max_messages"
        
        # Chat container
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state[messages_key]:
                with st.chat_message(message["role"]):
                    # Display empty messages clearly
                    content = message["content"] if message["content"] else "(empty message)"
                    st.markdown(content)
        
        # Check if max messages reached
        if len(st.session_state[messages_key]) >= st.session_state[max_messages_key]:
            st.info("💬 Maximum message limit reached for this agent!")
        else:
            # Check for auto-send message
            prompt = None
            if 'auto_send_message' in st.session_state:
                if f"auto_sent_{agent_type}" not in st.session_state:
                    prompt = st.session_state.auto_send_message
                    st.session_state[f"auto_sent_{agent_type}"] = True
                    
                    # Clean up after both agents have received the message
                    if all(f"auto_sent_{a}" in st.session_state for a in ['buggy', 'improved']):
                        del st.session_state.auto_send_message
                        if 'showing_auto_message' in st.session_state:
                            del st.session_state.showing_auto_message
                        for key in list(st.session_state.keys()):
                            if key.startswith("auto_sent_"):
                                del st.session_state[key]
            
            # Regular chat input (only if no auto-send message)
            if prompt is None:
                prompt = st.chat_input(f"Try to break the {agent_type} agent!", key=f"{agent_type}_input")
            
            # Handle empty message case
            if prompt is not None:  # This includes empty strings from auto-send
                # Add user message (show as "(empty message)" if empty)
                display_prompt = prompt if prompt else "(empty message)"
                st.session_state[messages_key].append({"role": "user", "content": prompt})
                
                # Prepare messages for API call
                api_messages = [{"role": "system", "content": system_prompt}]
                api_messages.extend([
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state[messages_key]
                ])
                
                # Display user message
                with st.chat_message("user"):
                    st.markdown(display_prompt)
                
                # Get AI response
                with st.chat_message("assistant"):
                    try:
                        with st.spinner("Thinking..."):
                            stream = client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=api_messages,
                                stream=True,
                                temperature=0.7 if agent_type == 'buggy' else 0.3,
                                max_tokens=300
                            )
                            response = st.write_stream(stream)
                            
                        st.session_state[messages_key].append(
                            {"role": "assistant", "content": response}
                        )
                    except Exception as e:
                        st.session_state[max_messages_key] = len(st.session_state[messages_key])
                        rate_limit_message = f"Sorry, I can't respond right now. Too many people are using this demo!"
                        st.error(rate_limit_message)
                        st.session_state[messages_key].append(
                            {"role": "assistant", "content": rate_limit_message}
                        )
                        st.rerun()
        
        # Clear chat button
        if st.button(f"🗑️ Clear {agent_type.title()} Chat", key=f"clear_{agent_type}"):
            st.session_state[messages_key] = []
            st.session_state[f"{agent_type}_max_messages"] = 20
            st.rerun()

# Create both chat interfaces
create_chat_interface('buggy', BUGGY_SYSTEM_PROMPT, left_col)
create_chat_interface('improved', IMPROVED_SYSTEM_PROMPT, right_col)

# Add debugging insights at the bottom
st.markdown("---")
st.markdown("### 🔍 What Did You Notice?")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **🐛 Common Problems with the Buggy Agent:**
    - Makes assumptions about unclear requests
    - Doesn't ask for clarification when confused
    - May give irrelevant or unhelpful responses
    - Doesn't handle edge cases gracefully
    """)

with col2:
    st.markdown("""
    **✅ How the Improved Agent Handles Issues:**
    - Acknowledges confusion and asks for clarification
    - Provides helpful examples when requests are vague
    - Maintains professional tone even with weird inputs
    - Gracefully redirects impossible requests
    """)

st.markdown("""
### 🛠️ Key Debugging Principles Demonstrated:
1. **Clear System Prompts**: The improved agent has detailed instructions on how to handle edge cases
2. **Graceful Error Handling**: When confused, ask for clarification instead of guessing
3. **Input Validation**: Handle empty messages, unusual formatting, and nonsensical requests appropriately
4. **Helpful Guidance**: Provide examples and suggestions to guide users toward successful interactions
5. **Consistent Tone**: Maintain helpfulness and professionalism even when handling errors

**💡 The Goal**: Your AI doesn't need to handle every possible input perfectly, but it should fail gracefully and help users get back on track!
""")

# Optional: Add some stats
if st.session_state.get('buggy_messages') or st.session_state.get('improved_messages'):
    st.markdown("---")
    st.markdown("### 📊 Demo Stats")
    buggy_count = len(st.session_state.get('buggy_messages', []))
    improved_count = len(st.session_state.get('improved_messages', []))
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Buggy Agent Messages", buggy_count, delta=None)
    with col2:
        st.metric("Improved Agent Messages", improved_count, delta=None)
