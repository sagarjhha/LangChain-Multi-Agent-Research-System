import streamlit as st
import re
from src.agents.agents import build_search_agent, build_reader_agent, writer_chain, critic_chain

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Research Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .stTextInput > div > div > input { background-color: #262730; color: white; border: 1px solid #4B4B4B; border-radius: 10px; font-size: 18px; }
    .stButton > button { width: 100%; border-radius: 10px; height: 3em; background-color: #FF4B4B; color: white; font-weight: bold; border: none; transition: 0.3s; }
    .stButton > button:hover { background-color: #FF7575; transform: scale(1.02); }
    div[data-testid="stExpander"] { background-color: #1E2129; border: 1px solid #31333F; border-radius: 10px; }
    .main-header { font-size: 5rem; font-weight: 900; text-align: center; margin-bottom: 0; background: -webkit-linear-gradient(#FF4B4B, #FFA500); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.1; }
    .sub-header { text-align: center; color: #B0B0B0; margin-bottom: 3rem; font-size: 1.4rem; font-weight: 400; }
    .source-link { display: block; padding: 10px; background-color: #262730; border: 1px solid #4B4B4B; border-radius: 8px; color: #FF4B4B; text-decoration: none; margin-bottom: 8px; transition: 0.2s; }
    .source-link:hover { background-color: #31333F; border-color: #FF4B4B; }
    </style>
    """, unsafe_allow_html=True)

def extract_links(text):
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    return list(set(re.findall(url_pattern, text)))

# --- UPDATED PIPELINE LOGIC ---
def run_research_pipeline(topic: str, status_container):
    state = {"topic": topic}

    # 1- Search Agent (Ask for multiple sources)
    with status_container.status("🔍 Gathering Intelligence...", expanded=True) as status:
        search_agent = build_search_agent()
        search_result = search_agent.invoke({
            "messages": [("user", f"Find at least 5-10 recent, reliable and detailed sources/URLs about: {topic}. List them clearly.")]
        })
        state["search_results"] = search_result['messages'][-1].content
        status.update(label="Intelligence Gathered!", state="complete", expanded=False)

    # 2- Reader Agent (Scrape top 5)
    with status_container.status("📖 Deep Diving into Top 5 Resources...", expanded=True) as status:
        reader_agent = build_reader_agent()

        # Prompt the agent to identify the TOP 5 URLs from search results
        selection_result = reader_agent.invoke({
            "messages": [("user",
                f"Based on these search results for '{topic}', identify the top 5 most relevant URLs for a deep dive. "
                f"Return ONLY a comma-separated list of the URLs.\n\nSearch Results:\n{state['search_results']}"
            )]
        })

        urls_to_scrape = extract_links(selection_result['messages'][-1].content)[:5]

        scraped_data = []
        for i, url in enumerate(urls_to_scrape):
            st.write(f"Scraping source {i+1}/5: {url}...")
            scrape_res = reader_agent.invoke({
                "messages": [("user", f"Scrape the following URL for detailed information regarding {topic}: {url}")]
            })
            scraped_data.append(f"SOURCE: {url}\nCONTENT:\n{scrape_res['messages'][-1].content}")

        state['scraped_content'] = "\n\n" + "="*30 + "\n\n".join(scraped_data)
        status.update(label="5+ Sources Extracted!", state="complete", expanded=False)

    # 3- Writer Chain
    with status_container.status("✍️ Drafting Comprehensive Report...", expanded=True) as status:
        research_combined = (
            f"SEARCH RESULTS : \n {state['search_results']}\n\n"
            f"DETAILED SCRAPED CONTENT FROM 5 SOURCES : \n {state['scraped_content']}"
        )
        state["report"] = writer_chain.invoke({
            "topic": topic,
            "research": research_combined
        })
        status.update(label="Report Drafted!", state="complete", expanded=False)

    # 4- Critic Chain
    with status_container.status("🧐 Critiquing & Refining...", expanded=True) as status:
        state["feedback"] = critic_chain.invoke({
            "report": state['report']
        })
        status.update(label="Quality Check Passed!", state="complete", expanded=False)

    return state

# --- MAIN UI ---
def main():
    st.markdown('<p class="main-header">Research Agent</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Autonomous AI-driven market research and intelligence gathering</p>', unsafe_allow_html=True)

    with st.sidebar:
        st.title("⚙️ Configuration")
        st.markdown("---")
        temperature = st.slider("Creativity (Temperature)", 0.0, 1.0, 0.7)
        st.markdown("---")
        st.info("The Research Agent now scrapes a minimum of 5 distinct sources for higher accuracy.")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        topic = st.text_input("Enter your research topic", placeholder="e.g. The impact of Generative AI on Software Engineering 2025")
        start_btn = st.button("🚀 Launch Research")

    if start_btn:
        if not topic:
            st.warning("⚠️ Please enter a topic to begin.")
            return

        status_container = st.container()
        try:
            final_state = run_research_pipeline(topic, status_container)
            st.markdown("---")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Status", "Complete", "✅")
            m2.metric("Agents Used", "4", "🤖")
            all_links = extract_links(final_state["search_results"] + " " + final_state["scraped_content"])
            m3.metric("Sources Found", len(all_links), "🌐")
            m4.metric("Quality", "Reviewed", "⭐")

            tab1, tab2, tab3, tab4 = st.tabs(["📄 Final Intelligence Report", "🔗 Sources", "🧐 Critic's Feedback", "📂 Raw Intelligence"])

            with tab1:
                st.markdown("### 📄 Final Report")
                st.markdown(f"**Topic:** {topic}")
                st.markdown("---")
                st.markdown(final_state["report"])

            with tab2:
                st.markdown("### 🔗 Research Sources")
                if all_links:
                    for link in all_links:
                        st.markdown(f'<a class="source-link" href="{link}" target="_blank">{link}</a>', unsafe_allow_html=True)
                else:
                    st.info("No direct URLs were found.")

            with tab3:
                st.markdown("### 🧐 Quality Audit")
                st.info(final_state["feedback"])

            with tab4:
                st.markdown("### 📂 Data Source Archive")
                with st.expander("🌐 Search Agent Output"):
                    st.write(final_state["search_results"])
                with st.expander("📖 Scraped Content from 5+ Sites"):
                    st.write(final_state["scraped_content"])

        except Exception as e:
            st.error(f"💥 An error occurred: {e}")

if __name__ == "__main__":
    main()