import streamlit as st
import pandas as pd
import os

# =====================================================
#              BASIC APP CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Conversational BI - Demo",
    page_icon="💬",
    layout="wide",
)

st.title("💬 Conversational BI - Demo (Gemini → Python Code)")
st.write(
    """
This demo loads a dataset from Google Sheets and uses **Gemini** only to
generate Python code that works on the `df` DataFrame.

Gemini **never sees the raw data**. It only knows:
- The column names.
- A short description of each column.

Based on the user's question, Gemini generates a function `answer(df)`
and Python executes it to obtain the result.
"""
)

# =====================================================
#           1. LOAD DATASET FROM GOOGLE SHEETS
# =====================================================

SHEET_ID = "1cj1bUUFXmv3dAgja0i2q24dA0gfgN6YcwEOdQPONk5s"


@st.cache_data
def load_google_sheet(sheet_id: str) -> pd.DataFrame:
    """Load data from a public Google Sheets file by exporting it as CSV."""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"❌ Error loading Google Sheets: {e}")
        return pd.DataFrame()


df = load_google_sheet(SHEET_ID)

if df.empty:
    st.error(
        "⚠️ Could not load the dataset from Google Sheets.\n\n"
        "Please make sure the file is shared as 'Anyone with the link'."
    )
    st.stop()

st.success("✅ Dataset successfully loaded from Google Sheets.")
st.write("### Dataset preview")
st.dataframe(df.head())

st.write("### Basic info")
st.write(f"- Rows: **{df.shape[0]}**")
st.write(f"- Columns: **{df.shape[1]}**")
st.write("Columns:")
st.write(list(df.columns))

st.session_state["dataset"] = df

# =====================================================
#   2. LOGIC: GEMINI GENERATES PYTHON CODE (answer(df))
# =====================================================

def answer_with_llm(question: str, df: pd.DataFrame):
    """
    Uses Gemini ONLY to generate Python code.
    The generated code is then executed locally over `df`.

    Gemini does NOT see the raw data, only:
    - column names
    - short descriptions of each column

    Returns a dict:
      {
        "explanation": str,
        "value": anything (number, text, dict with data, etc),
        "_code": Python code as a string
      }
    """
    try:
        import google.generativeai as genai
    except ImportError:
        return {
            "explanation": (
                "To answer this question I need the `google-generativeai` library.\n\n"
                "Please install it in your environment:\n\n"
                "```bash\npip install google-generativeai\n```"
                "\n\nAnd set your API key in the `GEMINI_API_KEY` environment variable."
            ),
            "value": None,
            "_code": "",
        }

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "explanation": (
                "I could not find the `GEMINI_API_KEY` environment variable.\n\n"
                "Set it before running Streamlit, for example:\n\n"
                "```powershell\n$env:GEMINI_API_KEY = \"YOUR_API_KEY_HERE\"\n```"
            ),
            "value": None,
            "_code": "",
        }

    genai.configure(api_key=api_key)

    # --- Describe the dataset WITHOUT sending any rows, only structure ---
    schema = {
        "event_time": "Timestamp of the user event",
        "event_type": "Type of event (view, cart, purchase, etc.)",
        "product_id": "Product ID",
        "category_id": "Category ID",
        "category_code": "Category path (e.g. 'electronics.smartphone')",
        "brand": "Product brand",
        "price": "Numeric price of the product",
        "user_id": "User ID",
        "user_session": "User session ID",
    }

    schema_lines = "\n".join(
        f"- {col}: {desc}"
        for col, desc in schema.items()
        if col in df.columns
    )

    cols_text = ", ".join(df.columns)

    # --- Prompt: ask for a single answer(df) function returning a dict ---
    # IMPORTANT: always answer in English, even if the question is in Spanish.
    prompt = f"""
You are a senior Business Intelligence analyst and an expert in pandas.

There is a pandas DataFrame called `df` with these columns:
{cols_text}

Column descriptions:
{schema_lines}

Your job is to generate a SINGLE Python function called `answer(df)` that:

1. Computes the answer to the following business question using the DataFrame `df`:

   \"\"\"{question}\"\"\"

2. Returns a Python dictionary with at least these keys:
   - "explanation": str
        Text in **English** explaining the result, with a style like:
        "According to your question, the relevant value is XXX.
         I calculated it by doing YYY (average/sum/count, etc.)
         and filtering only by ZZZ."

   - "value": the main value for the answer:
        * If the question is NUMERIC (average price, counts, etc.),
          you can return a number or a short text.
        * If the question asks for a CHART (words like 'chart',
          'graph', 'bar chart', 'bars', 'plot'), then in "value"
          you must return a Python dictionary where:
              - keys are labels for the X axis (e.g. product_id, brand)
              - values are numeric values ready to be plotted as a bar chart.
          Do NOT generate images and do NOT use matplotlib;
          just prepare the aggregated data.

3. You can use standard pandas operations:
   - filters: df[condition]
   - groupby, agg, mean, sum, count, sort_values, etc.
   - Do NOT import new libraries.
   - Do NOT read or write files.
   - Do NOT use input() or print().

4. Very important: ALWAYS answer in English, even if the user's question is in Spanish.

Write ONLY the function code, no comments and NO ``` or markdown.
Generic example of the shape (do not copy it literally):

def answer(df):
    # logic...
    return {{"explanation": "...", "value": 123}}

Now write the actual implementation adapted to the user's question.
"""

    # --- Call Gemini to generate the function code ---
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        code_raw = (response.text or "").strip()
    except Exception as e:
        return {
            "explanation": f"There was an error calling Gemini to generate code: {e}",
            "value": None,
            "_code": "",
        }

    # --- Clean ```python / ``` if Gemini wrapped the code ---
    code = (
        code_raw.replace("```python", "")
        .replace("```Python", "")
        .replace("```", "")
        .strip()
    )

    # --- Execute the generated code in a controlled environment ---
    local_vars = {}
    try:
        exec_env = {"pd": pd}
        exec(code, exec_env, local_vars)

        if "answer" not in local_vars or not callable(local_vars["answer"]):
            return {
                "explanation": "Gemini did not return a valid `answer(df)` function.",
                "value": None,
                "_code": code,
            }

        result = local_vars["answer"](df)

    except Exception as e:
        return {
            "explanation": f"There was an error while executing the generated code: {e}",
            "value": None,
            "_code": code,
        }

    # --- Normalize the result ---
    if isinstance(result, dict):
        explanation = result.get("explanation") or "The function did not return an explanation."
        value = result.get("value", None)
        return {"explanation": explanation, "value": value, "_code": code}

    # If it's not a dict, just convert to text
    return {
        "explanation": str(result),
        "value": None,
        "_code": code,
    }


def process_question(question: str, df: pd.DataFrame):
    """Every question goes to Gemini → generates code → executed on df."""
    return answer_with_llm(question, df)


# =====================================================
#                 3. CHAT INTERFACE
# =====================================================

st.write("---")
st.subheader("💬 Conversational BI Chatbot (Gemini → Python Code)")

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "assistant",
            "content": (
                "Hi 👋, I'm your BI assistant.\n\n"
                "I don't see the raw data directly. Instead, I use Gemini to generate "
                "Python code that works on the `df` DataFrame and computes the answer "
                "to your question.\n\n"
                "I always respond in **English**, even if you ask in Spanish.\n\n"
                "Examples of questions:\n"
                "- What is the average price?\n"
                "- Which brand seems to have the highest prices?\n"
                "- How many unique users are there?\n"
                "- Give me general insights about user behaviour.\n"
                "- Build a bar chart with the 10 products with the highest price.\n"
            ),
        }
    ]

# Show message history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_input = st.chat_input("Type your question about the dataset here...")

if user_input:
    # Save user message
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate answer
    with st.chat_message("assistant"):
        with st.spinner("Analyzing your question and generating code..."):
            result = process_question(user_input, df)

            explanation = result.get("explanation", "No explanation.")
            value = result.get("value", None)
            code = result.get("_code", "")

            # 1) Main explanation
            st.markdown(explanation)

            # 2) Show computed value
            if value is not None:
                if isinstance(value, dict):
                    # Data for chart / table
                    st.markdown("**Computed data:**")
                    s = pd.Series(value)
                    st.dataframe(s)

                    # If values are numeric, plot bar chart
                    try:
                        numeric_series = pd.to_numeric(s, errors="coerce")
                        if numeric_series.notna().all():
                            st.markdown("**Bar chart:**")
                            st.bar_chart(numeric_series)
                    except Exception:
                        pass
                else:
                    # Simple numeric or text value
                    st.markdown(f"\n**Computed value:** {value}")

            # 3) Show generated code
            if code:
                st.markdown(
                    "\n---\n\n_Generated code by Gemini:_\n\n```python\n"
                    + code
                    + "\n```"
                )

    # Store a compact summary in history
    summary_text = explanation
    if isinstance(value, dict):
        summary_text += "\n\n(Computed tabular data / chart.)"
    elif value is not None:
        summary_text += f"\n\nValue: {value}"

    st.session_state["messages"].append(
        {"role": "assistant", "content": summary_text}
    )

