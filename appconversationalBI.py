import os

import altair as alt
import pandas as pd
import streamlit as st

# =====================================================
#              BASIC APP CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="OHM Store · Ask the data · Juan Parrado",
    page_icon="⚡",
    layout="wide",
)

# "OHM" electronics-store identity: charcoal, electric yellow, warm off-white, narrow bold type
BG, SURFACE, LINE = "#121316", "#1C1D22", "#2C2E35"
TEXT, MUTED = "#F4F1EA", "#9A9FAA"
VOLT, VOLT_DIM = "#F5E50A", "#5B5621"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Barlow:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap');
    html, body, [class*="css"], .stMarkdown, p, li, label, button, input, textarea { font-family: 'Barlow', sans-serif; }
    .stApp { background: #121316; color: #F4F1EA; }
    .block-container { padding-top: 1.2rem; max-width: 1180px; }
    h1, h2, h3 { font-family: 'Barlow Condensed', sans-serif !important; text-transform: uppercase; letter-spacing: .01em; color: #F4F1EA; }
    .brandbar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 14px; padding: 10px 0 14px; border-bottom: 1px solid #2C2E35; margin-bottom: 26px; }
    .logo { font-family: 'Barlow Condensed', sans-serif; font-weight: 800; font-size: 26px; letter-spacing: .04em; color: #121316; background: #F5E50A; padding: 0 10px; border-radius: 4px; line-height: 34px; }
    .brandbar .t { font-family: 'Barlow Condensed', sans-serif; font-weight: 600; font-size: 18px; text-transform: uppercase; letter-spacing: .06em; }
    .brandbar .src { margin-left: auto; font-family: 'DM Mono', monospace; font-size: 12px; color: #9A9FAA; }
    .hero { font-family: 'Barlow Condensed', sans-serif !important; font-weight: 800; text-transform: uppercase; font-size: clamp(44px, 6vw, 84px) !important; line-height: .92 !important; letter-spacing: -.005em; margin: 0 0 14px; color: #F4F1EA; }
    .hero span { color: #F5E50A; }
    .lede { font-size: 18px; color: #C9CCD3; max-width: 62ch; margin-bottom: 26px; }
    .facts { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1px; background: #2C2E35; border: 1px solid #2C2E35; border-radius: 10px; overflow: hidden; margin-bottom: 30px; }
    .facts div { background: #1C1D22; padding: 16px 18px; }
    .facts .v { font-family: 'Barlow Condensed', sans-serif; font-weight: 700; font-size: 38px; line-height: 1; color: #F4F1EA; }
    .facts .v.volt { color: #F5E50A; }
    .facts .l { font-size: 14px; color: #9A9FAA; margin-top: 6px; }
    .ask { font-family: 'DM Mono', monospace; font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: #9A9FAA; margin: 6px 0 8px; }
    [data-testid="stChatMessage"] { background: #1C1D22; border: 1px solid #2C2E35; border-radius: 12px; }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li { color: #F4F1EA; }
    .stButton > button { background: #1C1D22; color: #F4F1EA; border: 1px solid #3A3D46; border-radius: 999px; font-weight: 500; }
    .stButton > button:hover { border-color: #F5E50A; color: #F5E50A; }
    [data-testid="stExpander"] { background: #1C1D22; border: 1px solid #2C2E35; border-radius: 10px; }
    code, pre { font-family: 'DM Mono', monospace !important; }
    .note { font-size: 13px; color: #9A9FAA; }
    @media (max-width: 760px) { .facts { grid-template-columns: 1fr 1fr; } .brandbar .src { margin-left: 0; } }
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================================
#           1. LOAD DATASET FROM GOOGLE SHEETS
# =====================================================

SHEET_ID = "1cj1bUUFXmv3dAgja0i2q24dA0gfgN6YcwEOdQPONk5s"


@st.cache_data(ttl=3600)
def load_google_sheet(sheet_id: str) -> pd.DataFrame:
    """Load data from a public Google Sheets file by exporting it as CSV."""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Error loading Google Sheets: {e}")
        return pd.DataFrame()


df = load_google_sheet(SHEET_ID)
if df.empty:
    st.error("Could not load the dataset from Google Sheets. Please make sure the file is shared as 'Anyone with the link'.")
    st.stop()
st.session_state["dataset"] = df

purchases = df[df["event_type"] == "purchase"]
revenue = purchases["price"].sum()
brand_rev = purchases.groupby("brand")["price"].sum().sort_values(ascending=False)
top_brand, top_share = brand_rev.index[0], brand_rev.iloc[0] / revenue

# =====================================================
#                     2. HEADER
# =====================================================

st.markdown(
    '<div class="brandbar"><span class="logo">OHM</span><span class="t">Store analytics · ask the data</span>'
    '<span class="src">Portfolio project · public eCommerce dataset (Kaggle) · built by Juan Parrado</span></div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="hero">Ask the store<br><span>anything.</span></div>', unsafe_allow_html=True)
st.markdown(
    f'<p class="lede">Type a business question in plain English. The AI writes the analysis code, runs it on '
    f'{len(df):,} store events and answers with a chart. It never sees a single customer row: only the column names.</p>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="facts">'
    f'<div><div class="v">{len(df):,}</div><div class="l">store events, November 2019</div></div>'
    f'<div><div class="v">{len(purchases):,}</div><div class="l">purchases ({len(purchases) / len(df):.1%} of events)</div></div>'
    f'<div><div class="v volt">${revenue:,.0f}</div><div class="l">revenue from those purchases</div></div>'
    f'<div><div class="v">{top_share:.0%}</div><div class="l">of revenue comes from {top_brand.title()}</div></div>'
    f'</div>',
    unsafe_allow_html=True,
)

# =====================================================
#   3. LOGIC: GEMINI GENERATES PYTHON CODE (answer(df))
# =====================================================

def answer_with_llm(question: str, df: pd.DataFrame):
    """
    Uses Gemini ONLY to generate Python code, which is then executed locally over `df`.
    Gemini does NOT see the raw data, only column names and short descriptions.
    Returns {"explanation": str, "value": any, "_code": str}.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        return {"explanation": "The `google-generativeai` library is not installed.", "value": None, "_code": ""}

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"explanation": "The AI key is not configured on this server (`GEMINI_API_KEY`).", "value": None, "_code": ""}

    genai.configure(api_key=api_key)

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
    schema_lines = "\n".join(f"- {col}: {desc}" for col, desc in schema.items() if col in df.columns)
    cols_text = ", ".join(df.columns)

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
        Text in **English** explaining the result for a business reader, in 2-3 short sentences:
        the answer first, then how it was calculated (average/sum/count, filters used).

   - "value": the main value for the answer:
        * If the question is NUMERIC (average price, counts, etc.), return a number or a short text.
        * If the question asks for a CHART or a ranking (words like 'chart', 'graph', 'bars', 'top',
          'plot'), return a Python dictionary where keys are labels (e.g. brand) and values are numbers.
          Do NOT generate images and do NOT use matplotlib; just prepare the aggregated data.

3. You can use standard pandas operations (filters, groupby, agg, mean, sum, count, sort_values).
   Do NOT import new libraries. Do NOT read or write files. Do NOT use input() or print().

4. Very important: ALWAYS answer in English, even if the user's question is in Spanish.

Write ONLY the function code, no comments and NO ``` or markdown.
Generic example of the shape (do not copy it literally):

def answer(df):
    # logic...
    return {{"explanation": "...", "value": 123}}

Now write the actual implementation adapted to the user's question.
"""

    try:
        model = genai.GenerativeModel("gemini-3.5-flash")
        response = model.generate_content(prompt)
        code_raw = (response.text or "").strip()
    except Exception as e:
        return {"explanation": f"There was an error calling Gemini to generate code: {e}", "value": None, "_code": ""}

    code = code_raw.replace("```python", "").replace("```Python", "").replace("```", "").strip()

    local_vars = {}
    try:
        exec(code, {"pd": pd}, local_vars)
        if "answer" not in local_vars or not callable(local_vars["answer"]):
            return {"explanation": "Gemini did not return a valid `answer(df)` function.", "value": None, "_code": code}
        result = local_vars["answer"](df)
    except Exception as e:
        return {"explanation": f"There was an error while executing the generated code: {e}", "value": None, "_code": code}

    if isinstance(result, dict):
        return {"explanation": result.get("explanation") or "No explanation returned.", "value": result.get("value"), "_code": code}
    return {"explanation": str(result), "value": None, "_code": code}


def bar_chart(values: dict):
    """Horizontal bars in OHM colours, biggest first; the leader in electric yellow."""
    s = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    if s.empty:
        return None
    d = s.sort_values(ascending=False).head(15).reset_index()
    d.columns = ["label", "value"]
    d["label"] = d["label"].astype(str)
    d["lead"] = d.index == 0
    base = alt.Chart(d).encode(
        y=alt.Y("label:N", sort="-x", title=None, axis=alt.Axis(labelColor=TEXT, labelFont="Barlow", labelFontSize=13, labelLimit=260, domain=False, ticks=False)),
        x=alt.X("value:Q", title=None, axis=alt.Axis(labelColor=MUTED, gridColor=LINE, domain=False, ticks=False, labelFont="Barlow")),
        tooltip=[alt.Tooltip("label:N", title="Label"), alt.Tooltip("value:Q", title="Value", format=",.2f")],
    )
    bars = base.mark_bar(cornerRadiusEnd=3, height=18).encode(color=alt.condition("datum.lead", alt.value(VOLT), alt.value("#6B6F7A")))
    text = base.mark_text(align="left", dx=6, color=TEXT, font="Barlow", fontWeight=600).encode(text=alt.Text("value:Q", format=",.0f"))
    return (bars + text).properties(height=max(120, 28 * len(d)), background=SURFACE).configure_view(stroke=None)


def show_result(result: dict):
    explanation, value, code = result.get("explanation", ""), result.get("value"), result.get("_code", "")
    st.markdown(explanation)
    if isinstance(value, dict):
        chart = bar_chart(value)
        if chart is not None:
            st.altair_chart(chart, width="stretch")
        else:
            st.dataframe(pd.Series(value, name="value"))
    elif value is not None:
        st.markdown(f"**Answer:** {value}")
    if code:
        with st.expander("See the code the AI wrote"):
            st.code(code, language="python")


# =====================================================
#                 4. CHAT INTERFACE
# =====================================================

EXAMPLE_Q = "Which 10 brands brought in the most revenue?"
EXAMPLE_CODE = '''def answer(df):
    sales = df[df["event_type"] == "purchase"]
    top = sales.groupby("brand")["price"].sum().sort_values(ascending=False).head(10)
    return {"explanation": "...", "value": top.round(0).to_dict()}'''

if "messages" not in st.session_state:
    # A worked example computed locally, so the first screen already shows what the app does
    top10 = brand_rev.head(10).round(0)
    st.session_state["messages"] = [
        {"role": "user", "content": EXAMPLE_Q},
        {"role": "assistant", "result": {
            "explanation": (f"{top_brand.title()} leads by far with ${top10.iloc[0]:,.0f}, about {top_share:.0%} of all revenue, "
                            f"followed by {brand_rev.index[1].title()} and {brand_rev.index[2].title()}. "
                            "I summed the price of every purchase event and grouped it by brand."),
            "value": top10.to_dict(), "_code": EXAMPLE_CODE}},
    ]

st.markdown('<p class="ask">Try a question</p>', unsafe_allow_html=True)
examples = {
    "View → purchase rate": "What share of product views turn into a purchase?",
    "Browsed, not bought": "Which categories get the most views but the fewest purchases?",
    "Avg price by brand": "Show the average price by brand for the top 10 brands",
    "Best day to sell": "On which day of the week do people buy the most?",
}
picked = None
cols = st.columns(len(examples))
for c, (label, q) in zip(cols, examples.items()):
    if c.button(label, key="ex_" + label, help=q, width="stretch"):
        picked = q

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"], avatar="⚡" if msg["role"] == "assistant" else None):
        if "result" in msg:
            show_result(msg["result"])
        else:
            st.markdown(msg["content"])

user_input = st.chat_input("Ask about sales, brands, categories, customers…") or picked
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant", avatar="⚡"):
        with st.spinner("Writing and running the analysis…"):
            result = answer_with_llm(user_input, df)
        show_result(result)
    st.session_state["messages"].append({"role": "assistant", "result": result})

with st.expander("About the data"):
    st.markdown(
        f"{len(df):,} events sampled from the public *eCommerce behavior data from multi category store* dataset (Kaggle, "
        "November 2019). Each row is one view, add-to-cart or purchase. The AI only receives the column names below, never the rows."
    )
    st.dataframe(df.head(20), width="stretch")
st.markdown('<p class="note">Answers are generated by Gemini and executed as Python on this server. Check the code for anything important.</p>', unsafe_allow_html=True)
