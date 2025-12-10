import random
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd

# --- Config ---
st.set_page_config(page_title="MomPrep", page_icon="🤰", layout="centered")
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

SYSTEM_INSTRUCTION = """You are a seasoned Software Engineer and a technical interview coach with a knack for explaining complex topics in a way that is easy to understand and engaging.
You are preparing a staff software engineer with background in payments platform who has been on a year long break and is a new mom with no sleep to interview for a new role in big techand go back to work."""

# --- Cache Data (Minimize API Calls) ---
@st.cache_data(ttl=60)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_curriculum = conn.read(worksheet="Curriculum")
    df_todos = conn.read(worksheet="Todos")
    return df_curriculum, df_todos

def update_status(topic, new_status):
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Re-read to get fresh data
    df = conn.read(worksheet="Curriculum")
    # Update status
    df.loc[df['topic'] == topic, 'status'] = new_status
    conn.update(worksheet="Curriculum", data=df)
    st.cache_data.clear() # Clear cache to show update immediately

# --- Load Data ---
try:
    df_curriculum, df_todos = load_data()
except Exception:
    st.error("Could not connect to Google Sheets. Check secrets.")
    st.stop()

# --- Header ---
st.title("MomPrep 🤰💻")
mode = st.radio("Current Mode:", ["🤱 Breastfeeding (5m)", "☕ Nap Time (15m)", "💻 Laptop (1h)"], horizontal=True)

# --- Logic to pick a topic ---
# Map mode to difficulty loosely
difficulty_map = {
    "🤱 Breastfeeding (5m)": "5 minutes",
    "☕ Nap Time (15m)": "15 minutes",
    "💻 Laptop (1h)": "1-2 hours"
}
target_diff = difficulty_map[mode]

# Filter for New items
queue = df_curriculum[(df_curriculum['status'] == 'New') | (df_curriculum['status'] == 'Revision')]
# If we have items for this difficulty, show them, otherwise fallback to any New item
filtered_queue = queue[queue['difficulty'] == target_diff]
if filtered_queue.empty:
    current_topic_row = queue.iloc[random.randint(0, len(queue) - 1)] if not queue.empty else None
else:
    current_topic_row = filtered_queue.iloc[random.randint(0, len(filtered_queue) - 1)]

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📚 Learn", "💬 Chat", "✅ Todos"])

with tab1:
    if current_topic_row is None:
        st.success("You finished your queue! Add more topics to the sheet.")
    else:
        topic = current_topic_row['topic']
        category = current_topic_row['category']
        cached_content = current_topic_row['content_cache']

        st.subheader(f"{topic}")
        st.caption(f"Category: {category} | Est: {target_diff}")

        # Content Generation Logic
        if pd.isna(cached_content) or cached_content == "":
            if st.button("Generate Nugget ✨"):
                with st.spinner("Asking Gemini..."):
                    model = genai.GenerativeModel(
                        'gemini-3-pro-preview', 
                        system_instruction = SYSTEM_INSTRUCTION
                    )
                    prompt = f"""
                    Explain '{topic}'. Make it engaging and interesting.
                    Keep the read less than {target_diff}.
                    Structure:
                    1. The "What" (High level concept)
                    2. The "Why" (Why it matters in Payments/Platform)
                    3. How is it relevant to the interview process?
                    4. Feel free to add any deeper dive links or resources.
                    """
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                    
                    # Store in session state for Chat context
                    st.session_state['current_content'] = response.text
                    
                    # (Optional) We could write this back to sheets to cache it, 
                    # but for now let's keep it simple and just display.
        else:
            st.markdown(cached_content)
            st.session_state['current_content'] = cached_content

        st.divider()
        c1, c2 = st.columns(2)
        if c1.button("Mark Done ✅"):
            update_status(topic, "Done")
            st.rerun()
        if c2.button("Need Revision 🔄"):
            update_status(topic, "Revision")
            st.rerun()

with tab2:
    st.caption("Chat about the current topic")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a follow up..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Contextualize with the lesson
        context = st.session_state.get('current_content', 'No specific topic loaded.')
        full_prompt = f"Context: {context}\n\nUser Question: {prompt}"

        model = genai.GenerativeModel(
            'gemini-flash-latest', 
            system_instruction = SYSTEM_INSTRUCTION
        )
        response = model.generate_content(full_prompt)
        
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})

with tab3:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Simple form to add tasks
    with st.form("add_task"):
        new_task = st.text_input("New Task")
        tag = st.selectbox
        tag = st.selectbox("Tag", ["Mobile/Nursing", "Laptop/Focus"])
        submitted = st.form_submit_button("Add")
        if submitted:
            new_row = pd.DataFrame([{"task": new_task, "tag": tag, "status": "Pending"}])
            updated_df = pd.concat([df_todos, new_row], ignore_index=True)
            conn.update(worksheet="Todos", data=updated_df)
            st.success("Task added!")
            st.rerun()

    st.subheader("Your List")
    # Show Mobile tasks first if in mobile mode?
    st.dataframe(df_todos)