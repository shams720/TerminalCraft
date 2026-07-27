import streamlit as st
from groq import Groq
import re
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="TerminalCraft | Ultimate Linux AI Suite",
    page_icon="🐧",
    layout="wide"
)

# --- INITIALIZE SESSION STATE ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- SIDEBAR CONFIGURATION ---
st.sidebar.title("⚙️ Target Environment")

distro = st.sidebar.selectbox(
    "Linux Distribution",
    ["Ubuntu / Debian", "Arch Linux", "Fedora / RHEL", "Alpine Linux"]
)

shell = st.sidebar.selectbox(
    "Shell Environment",
    ["Bash", "Zsh", "Fish"]
)

strict_safety = st.sidebar.toggle("Enforce Strict Safety Checks", value=True)

# --- SIDEBAR: HISTORY & EXPORT ---
st.sidebar.divider()
st.sidebar.subheader("📜 Session History")

if st.session_state.history:
    for item in reversed(st.session_state.history):
        with st.sidebar.expander(f"⏱️ {item['time']} - {item['type']}"):
            st.caption(f"**Target:** {item['distro']} ({item['shell']})")
            st.code(item['command'], language="bash")
    
    col_clear, col_export = st.sidebar.columns(2)
    with col_clear:
        if st.button("🗑️ Clear", use_container_width=True, key="sidebar_clear"):
            st.session_state.history = []
            st.rerun()
    
    with col_export:
        # Compile session history into a Markdown cheat sheet
        md_content = f"# TerminalCraft Session Cheat Sheet\n\n"
        md_content += f"*Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  \n"
        md_content += f"*Environment: {distro} / {shell}*\n\n---\n\n"
        
        for idx, item in enumerate(st.session_state.history, 1):
            md_content += f"## {idx}. [{item['type']}] ({item['time']})\n\n"
            md_content += f"**Target:** {item['distro']} ({item['shell']})\n\n"
            md_content += f"```bash\n{item['command']}\n```\n\n"
        
        st.download_button(
            label="📥 Export",
            data=md_content,
            file_name=f"terminalcraft_cheatsheet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True,
            help="Download session history as a Markdown cheat sheet",
            key="sidebar_export"
        )
else:
    st.sidebar.caption("No queries run in this session yet.")

# --- MAIN UI HEADER ---
st.title("🐧 TerminalCraft: Ultimate Linux AI Suite")
st.caption(f"Configured for **{distro}** using **{shell}**")

# Check for API key early
if "GROQ_API_KEY" not in st.secrets:
    st.error("⚠️ `GROQ_API_KEY` not found in `.streamlit/secrets.toml`. Please configure your secrets.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

MODEL_NAME = "llama-3.3-70b-versatile"


def generate_groq_text(system_prompt, user_prompt):
    """Generate text using Groq API."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as exc:
        st.error(f"Generation failed: {exc}")
        return None


# Helper function to extract bash blocks
def extract_bash_command(text):
    """Extract bash code block from generated text."""
    match = re.search(r"```(?:bash|sh)?\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else "See full output"


# --- TABS INTERFACE ---
tab1, tab2, tab3, tab4 = st.tabs([
    "⚡ Command Generator",
    "🔍 Explainer & Debugger",
    "📜 Script Builder",
    "🧩 Pipe & Filter Builder"
])

# ==========================================
# TAB 1: COMMAND GENERATOR & IMPACT VISUALIZER
# ==========================================
with tab1:
    st.markdown("### Translate Natural English to Shell Commands")
    
    col1, col2, col3 = st.columns(3)
    preset_prompt = ""
    if col1.button("📁 Find files larger than 100MB", key="btn_files"):
        preset_prompt = "Find all files in /var/log larger than 100MB and list details."
    if col2.button("🔌 Active listening ports", key="btn_ports"):
        preset_prompt = "Show all open listening ports and process names attached to them."
    if col3.button("🔄 Stop process on 8080", key="btn_process"):
        preset_prompt = "Find whatever process is running on port 8080 and stop it."

    user_input = st.text_area(
        "What do you want to do?",
        value=preset_prompt if preset_prompt else "",
        placeholder="e.g., Recursively change all directory permissions to 755...",
        height=100,
        key="tab1_input"
    )

    if st.button("🚀 Generate Command", type="primary", use_container_width=True, key="btn_generate_cmd"):
        if not user_input.strip():
            st.warning("Please enter a request.")
        else:
            system_prompt = f"""
You are a senior Linux SysAdmin. Translate the request into a command for {distro} running {shell}.
Format EXACTLY like this:

RISK_LEVEL: [LOW / MODERATE / HIGH]

### 💻 Command
```bash
<command here>
```

### 📋 Explanation
1-2 sentence explanation of what this command does.

### 🔍 Flag & Argument Breakdown
- Bullet points breaking down each flag and argument
- Include short descriptions for clarity

### 🎯 Dry-Run Impact Scope
- Bullet points detailing exactly which directories, files, or system services will be touched or modified
- Include file patterns and scope limits
{"### 🛡️ Safety Warning\n**CAUTION:** Include a bold safety warning explaining risks if destructive." if strict_safety else ""}
"""

            with st.spinner("Analyzing request and computing impact scope..."):
                text = generate_groq_text(system_prompt, user_input)
                
                if text:
                    # Render Risk Level Badge
                    if "RISK_LEVEL: HIGH" in text:
                        st.error("🚨 **RISK LEVEL: HIGH / DESTRUCTIVE** — Exercise extreme caution before executing!")
                    elif "RISK_LEVEL: MODERATE" in text:
                        st.warning("⚠️ **RISK LEVEL: MODERATE** — Modifies system state or configuration.")
                    else:
                        st.success("✅ **RISK LEVEL: LOW** — Safe read-only or standard operational command.")
                    
                    # Display output (stripping out raw RISK_LEVEL text)
                    clean_text = re.sub(r"RISK_LEVEL:\s*(LOW|MODERATE|HIGH)", "", text).strip()
                    st.markdown(clean_text)
                    
                    # Save to history
                    cmd = extract_bash_command(clean_text)
                    st.session_state.history.append({
                        "type": "Translate",
                        "command": cmd,
                        "distro": distro,
                        "shell": shell,
                        "time": datetime.now().strftime("%H:%M:%S")
                    })
                    st.rerun()

# ==========================================
# TAB 2: COMMAND EXPLAINER & ERROR DEBUGGER
# ==========================================
with tab2:
    st.markdown("### Deconstruct Syntax or Debug Error Logs")
    
    mode = st.radio(
        "Select Mode",
        ["🔍 Explain Command", "🐛 Debug Error Log"],
        horizontal=True,
        key="tab2_mode"
    )
    
    if mode == "🔍 Explain Command":
        cmd_to_explain = st.text_area(
            "Paste a Linux command you want explained:",
            placeholder="e.g., ps aux | grep python | awk '{print $2}' | xargs kill -9",
            height=90,
            key="tab2_explain_input"
        )

        if st.button("🔍 Explain Syntax", type="primary", use_container_width=True, key="btn_explain"):
            if not cmd_to_explain.strip():
                st.warning("Please paste a command to explain.")
            else:
                system_prompt = f"""
You are an expert Linux instructor. Explain the following command in simple, structured English.
Break down every pipe (|), flag, and argument step-by-step.
Tailor your explanation knowing the user is using {shell} on {distro}.
Format your response with clear headings and bullet points.
"""

                with st.spinner("Deconstructing syntax..."):
                    text = generate_groq_text(system_prompt, f"Explain this command: {cmd_to_explain}")
                    if text:
                        st.markdown(text)
    
    else:  # Debug Error Log
        error_log = st.text_area(
            "Paste your cryptic error message or stack trace:",
            placeholder="e.g., E: Could not get lock /var/lib/dpkg/lock-frontend... or Permission denied (publickey) or ModuleNotFoundError: No module named 'xyz'",
            height=90,
            key="tab2_debug_input"
        )

        if st.button("🛠️ Diagnose & Fix", type="primary", use_container_width=True, key="btn_debug"):
            if not error_log.strip():
                st.warning("Please paste an error log.")
            else:
                system_prompt = f"""
You are a veteran Linux troubleshooting expert. Analyze the provided error log for {distro}.
Provide a clear response with these sections:

1. **🔍 Root Cause Diagnosis**: Why did this error happen? (1-2 sentences)
2. **🛠️ Immediate Fix Command**: The precise one-liner command to resolve it immediately.
3. **🛡️ Prevention Tip**: How to avoid this error in the future.

Be concise and actionable.
"""

                with st.spinner("Analyzing error stack trace..."):
                    text = generate_groq_text(system_prompt, f"Diagnose this error on {distro}: {error_log}")
                    if text:
                        st.markdown(text)

# ==========================================
# TAB 3: SCRIPT BUILDER
# ==========================================
with tab3:
    st.markdown("### Generate Multi-Step Shell Scripts (.sh)")

    script_prompt = st.text_area(
        "Describe a multi-step workflow to automate:",
        placeholder="e.g., Backup PostgreSQL database, compress with date in filename, upload to remote server via SCP, and remove local temp files...",
        height=120,
        key="tab3_input"
    )

    if st.button("📜 Build Full Script", type="primary", use_container_width=True, key="btn_build_script"):
        if not script_prompt.strip():
            st.warning("Please describe a workflow.")
        else:
            system_prompt = f"""
You are an expert DevOps engineer writing a production-ready shell script for {distro} running {shell}.
Generate a fully commented bash script with:
- Error handling (set -e at the top)
- Clear variable definitions
- Step-by-step comments
- Safe defaults and validation where appropriate

Output ONLY the bash code block first (```bash...```), followed by a brief summary of how to run it.
"""

            with st.spinner("Writing production script..."):
                script_text = generate_groq_text(system_prompt, script_prompt)
                
                if script_text:
                    st.markdown(script_text)
                    
                    # Extract pure script for download
                    raw_script = extract_bash_command(script_text)
                    if raw_script != "See full output":
                        st.download_button(
                            label="📥 Download Script as script.sh",
                            data=raw_script,
                            file_name="script.sh",
                            mime="text/x-sh",
                            use_container_width=True,
                            key="btn_download_script"
                        )
                    
                    # Save to history
                    st.session_state.history.append({
                        "type": "Script",
                        "command": f"# Multi-step script: {script_prompt[:60]}...",
                        "distro": distro,
                        "shell": shell,
                        "time": datetime.now().strftime("%H:%M:%S")
                    })

# ==========================================
# TAB 4: INTERACTIVE PIPE & FILTER BUILDER
# ==========================================
with tab4:
    st.markdown("### Build Complex Data Pipelines (grep, awk, sed, jq)")
    st.caption("Chain filters to transform data streams into actionable insights.")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        data_source = st.selectbox(
            "Source Data Format",
            ["Plain Text Log File", "JSON Stream", "CSV / Delimited Data", "Process / System Output"],
            key="tab4_source"
        )
    with col_p2:
        filter_goal = st.text_input(
            "Transformation Goal",
            placeholder="e.g., extract column 3, filter out status 200, and count unique IP addresses",
            key="tab4_goal"
        )

    if st.button("⚡ Construct Pipeline", type="primary", use_container_width=True, key="btn_pipeline"):
        if not filter_goal.strip():
            st.warning("Please specify a transformation goal.")
        else:
            system_prompt = f"""
You are a Linux command-line wizard specializing in data manipulation and stream processing.
Construct a clean, robust pipeline using standard tools (grep, awk, sed, cut, sort, uniq, jq, xargs, etc.) for {distro} running {shell}.

Input data format: {data_source}
Objective: {filter_goal}

Provide:
1. The complete pipeline command (```bash...```)
2. A brief breakdown of how each pipe segment transforms the data stream
3. Optional: a small usage example showing sample input and output

Make it production-ready and efficient.
"""

            with st.spinner("Chaining filters and building pipeline..."):
                text = generate_groq_text(system_prompt, filter_goal)
                if text:
                    st.markdown(text)
                    
                    # Extract and offer download if applicable
                    raw_pipeline = extract_bash_command(text)
                    if raw_pipeline != "See full output" and raw_pipeline:
                        st.download_button(
                            label="📥 Download Pipeline as script.sh",
                            data=raw_pipeline,
                            file_name="pipeline.sh",
                            mime="text/x-sh",
                            use_container_width=True,
                            key="btn_download_pipeline"
                        )
