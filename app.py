import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Used Car Listings: What Drives Price?", layout="wide")

CONDITION_ORDER = ["salvage", "fair", "good", "excellent", "like new", "new"]
TEMPLATE = "plotly_white"


# ---------------------------------------------------------------- data
@st.cache_data
def load_data():
    df = pd.read_csv("notebooks/vehicles_us.csv", parse_dates=["date_posted"])
    df["age"] = df["date_posted"].dt.year - df["model_year"]
    df["is_4wd"] = df["is_4wd"].fillna(0).astype(int).map({1: "4WD", 0: "2WD"})
    df["paint_color"] = df["paint_color"].fillna("unknown")
    df["condition"] = pd.Categorical(df["condition"], CONDITION_ORDER, ordered=True)
    return df


raw = load_data()

# ------------------------------------------------------------- sidebar
st.sidebar.header("Filters")
min_price = st.sidebar.slider(
    "Minimum price ($)", 0, 5000, 500, step=100,
    help="~800 listings are priced at $1, which are placeholder prices, not real "
         "sale prices. Raising this removes them.",
)
max_price = st.sidebar.slider("Maximum price ($)", 10000, 150000, 100000, step=5000)
max_age = st.sidebar.slider("Maximum vehicle age (years)", 5, 60, 30)
types = st.sidebar.multiselect(
    "Vehicle type", sorted(raw["type"].unique()), default=sorted(raw["type"].unique())
)

df = raw[
    raw["price"].between(min_price, max_price)
    & (raw["age"].between(0, max_age))
    & raw["type"].isin(types)
].copy()

if df.empty:
    st.warning("No listings match the current filters. Widen the price range or pick at least one vehicle type.")
    st.stop()

# plain text so plotly doesn't choke on categories with no rows (order is set with category_orders)
df["condition"] = df["condition"].astype(str)

# -------------------------------------------------------------- header
st.title("Used car listings: what drives price, and what drives sales?")
st.markdown(
    "Each dot or bar below summarizes real listings from May 2018 to April 2019. "
    "The question: **which listing attributes are related to asking price and to how "
    "long a car takes to sell?** Some relationships are strong and others turn out to "
    "be non-existent. Both are findings."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Listings in view", f"{len(df):,}", f"{len(df) / len(raw):.0%} of {len(raw):,}")
c2.metric("Median price", f"${df['price'].median():,.0f}")
c3.metric("Median age", f"{df['age'].median():.0f} yrs")
c4.metric("Median days listed", f"{df['days_listed'].median():.0f}")

tab_price, tab_dep, tab_sell, tab_corr = st.tabs(
    ["1. What drives price?", "2. Depreciation", "3. What drives time-to-sell?", "4. Correlations"]
)

# ------------------------------------------------------------ tab 1
with tab_price:
    st.subheader("Price falls as cars get older and accumulate miles")
    left, right = st.columns(2)

    sample = df.dropna(subset=["odometer"]).sample(min(6000, len(df.dropna(subset=["odometer"]))), random_state=0)
    fig = px.scatter(
        sample[sample["odometer"] < 400_000], x="odometer", y="price", color="condition",
        category_orders={"condition": CONDITION_ORDER}, opacity=0.5, log_y=True,
        labels={"odometer": "Odometer (miles)", "price": "Price ($, log scale)", "condition": "Condition"},
        title="Price vs mileage (6,000-listing sample)", template=TEMPLATE,
    )
    left.plotly_chart(fig, use_container_width=True)

    sample2 = df.sample(min(6000, len(df)), random_state=0)
    fig = px.strip(
        sample2, x="age", y="price", log_y=True, stripmode="overlay", color_discrete_sequence=["#4C78A8"],
        labels={"age": "Vehicle age (years)", "price": "Price ($, log scale)"},
        title="Price vs age (6,000-listing sample)", template=TEMPLATE,
    )
    fig.update_traces(opacity=0.3, marker_size=4)
    right.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Log scale on price: a straight downward trend means each extra year or mile "
        "removes a roughly constant *percentage* of value."
    )

    st.subheader("Condition, drivetrain, engine and body type all shift the median price")
    a, b = st.columns(2)
    cond = df.groupby("condition", observed=True)["price"].agg(["median", "count"]).reset_index()
    fig = px.bar(
        cond, x="condition", y="median", text="count",
        labels={"median": "Median price ($)", "condition": "Condition"},
        title="Median price by condition (label = # listings)", template=TEMPLATE,
        color_discrete_sequence=["#4C78A8"],
    )
    fig.update_traces(texttemplate="n=%{text:,}", textposition="outside")
    a.plotly_chart(fig, use_container_width=True)

    typ = df.groupby("type")["price"].agg(["median", "count"]).reset_index()
    typ = typ[typ["count"] >= 100].sort_values("median")
    fig = px.bar(
        typ, x="median", y="type", orientation="h", text="count",
        labels={"median": "Median price ($)", "type": ""},
        title="Median price by vehicle type (types with 100+ listings)", template=TEMPLATE,
        color_discrete_sequence=["#4C78A8"],
    )
    fig.update_traces(texttemplate="n=%{text:,}", textposition="outside")
    b.plotly_chart(fig, use_container_width=True)

    a, b = st.columns(2)
    fig = px.box(
        df, x="is_4wd", y="price", log_y=True, category_orders={"is_4wd": ["2WD", "4WD"]},
        labels={"is_4wd": "", "price": "Price ($, log scale)"},
        title="Price distribution: 4WD vs 2WD", template=TEMPLATE,
    )
    a.plotly_chart(fig, use_container_width=True)

    cyl = df.dropna(subset=["cylinders"])
    cyl = cyl[cyl["cylinders"].isin([4, 6, 8])]
    fig = px.box(
        cyl, x="cylinders", y="price", log_y=True,
        labels={"cylinders": "Cylinders", "price": "Price ($, log scale)"},
        title="Price distribution by engine size (4, 6, 8 cyl)", template=TEMPLATE,
    )
    b.plotly_chart(fig, use_container_width=True)
    st.info(
        "**Caveat:** these effects overlap. 4WD vehicles skew toward trucks and SUVs, and "
        "8-cylinder engines skew toward trucks, so part of each gap is really a body-type "
        "effect. This is correlation, not causation."
    )

# ------------------------------------------------------------ tab 2
with tab_dep:
    st.subheader("How quickly does each condition class lose value?")
    dep = (
        df.groupby(["age", "condition"], observed=True)["price"]
        .agg(["median", "count"]).reset_index()
    )
    dep = dep[dep["count"] >= 20]  # hide noisy cells
    dep["condition"] = dep["condition"].astype(str)
    fig = px.line(
        dep, x="age", y="median", color="condition", markers=True,
        category_orders={"condition": CONDITION_ORDER},
        labels={"age": "Vehicle age (years)", "median": "Median price ($)", "condition": "Condition"},
        title="Median price by age and condition (cells with 20+ listings)", template=TEMPLATE,
    )
    st.plotly_chart(fig, use_container_width=True)

    overall = df.groupby("age")["price"].median()
    if 1 in overall.index and 10 in overall.index:
        keep = overall.loc[10] / overall.loc[1]
        st.markdown(
            f"**Reading it:** a typical 10-year-old car lists for about "
            f"**{keep:.0%}** of the price of a typical 1-year-old car "
            f"(${overall.loc[10]:,.0f} vs ${overall.loc[1]:,.0f}). At the same age, the lines for "
            "good, excellent and like new sit close together, and only fair is clearly cheaper. "
            "Most of the condition gap in tab 1 comes from age, since better-rated cars are newer."
        )

    st.subheader("Mileage and age tell nearly the same story")
    odo = df.dropna(subset=["odometer"])
    odo = odo[odo["odometer"] < 400_000]
    odo = odo.assign(
        mileage_band=pd.cut(
            odo["odometer"], [0, 25_000, 50_000, 100_000, 150_000, 200_000, 400_000],
            labels=["<25k", "25-50k", "50-100k", "100-150k", "150-200k", "200k+"],
        )
    )
    heat = odo.assign(age_band=pd.cut(odo["age"], [-1, 2, 5, 10, 15, 30], labels=["0-2", "3-5", "6-10", "11-15", "16+"]))
    heat = heat.pivot_table(index="age_band", columns="mileage_band", values="price", aggfunc="median", observed=True)
    fig = px.imshow(
        heat, text_auto=",.0f", aspect="auto", color_continuous_scale="Blues",
        labels={"x": "Mileage", "y": "Vehicle age (years)", "color": "Median price ($)"},
        title="Median price by age band and mileage band", template=TEMPLATE,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Read down a column to see the effect of age at fixed mileage, and across a row to "
        "see mileage at fixed age. Both matter, but the diagonal (old *and* high-mileage) is where prices bottom out."
    )

# ------------------------------------------------------------ tab 3
with tab_sell:
    st.subheader("Does a lower price, a better condition or a nicer color sell a car faster?")
    st.markdown(
        "If price drives demand, cheaper cars should leave the lot sooner. "
        "Let's check whether that actually shows up."
    )
    a, b = st.columns(2)
    banded = df.assign(
        price_band=pd.cut(
            df["price"], [0, 3000, 6000, 10000, 15000, 25000, 1e7],
            labels=["<$3k", "$3-6k", "$6-10k", "$10-15k", "$15-25k", "$25k+"],
        )
    )
    pb = banded.groupby("price_band", observed=True)["days_listed"].agg(
        median="median", q25=lambda s: s.quantile(0.25), q75=lambda s: s.quantile(0.75)
    ).reset_index()
    fig = px.line(
        pb, x="price_band", y="median", markers=True, error_y=pb["q75"] - pb["median"],
        error_y_minus=pb["median"] - pb["q25"],
        labels={"price_band": "Price band", "median": "Days listed (median, IQR bars)"},
        title="Days listed by price band", template=TEMPLATE,
    )
    fig.update_yaxes(range=[0, None])
    a.plotly_chart(fig, use_container_width=True)

    fig = px.box(
        df, x="condition", y="days_listed", category_orders={"condition": CONDITION_ORDER},
        labels={"days_listed": "Days listed", "condition": "Condition"},
        title="Days listed by condition", template=TEMPLATE,
    )
    b.plotly_chart(fig, use_container_width=True)

    a, b = st.columns(2)
    fig = px.histogram(
        df, x="days_listed", nbins=60, labels={"days_listed": "Days listed"},
        title="How long do listings stay up?", template=TEMPLATE, color_discrete_sequence=["#4C78A8"],
    )
    a.plotly_chart(fig, use_container_width=True)

    color_tbl = df.groupby("paint_color").agg(
        median_price=("price", "median"), median_days=("days_listed", "median"), n=("price", "size")
    ).reset_index()
    color_tbl = color_tbl[color_tbl["n"] >= 100]
    fig = px.scatter(
        color_tbl, x="median_days", y="median_price", size="n", text="paint_color",
        labels={"median_days": "Median days listed", "median_price": "Median price ($)"},
        title="Paint color: median price vs median days listed", template=TEMPLATE,
    )
    fig.update_traces(textposition="top center")
    b.plotly_chart(fig, use_container_width=True)

    rho = df[["price", "days_listed"]].corr(method="spearman").iloc[0, 1]
    st.warning(
        f"**Finding: essentially none.** Median days listed is ~33 in nearly every price "
        f"band, condition class and color (Spearman correlation between price and days listed "
        f"is {rho:+.2f}). In this dataset, the listing attributes that so strongly explain "
        "*price* do not explain *time-to-sell*. The likely culprits are factors that were not "
        "recorded, such as photos, location, seller type, or how the listing is priced "
        "relative to the market, or the field may be capped by how listings expire."
    )

# ------------------------------------------------------------ tab 4
with tab_corr:
    st.subheader("Rank correlations between numeric fields")
    num = df[["price", "age", "odometer", "cylinders", "days_listed"]]
    corr = num.corr(method="spearman").round(2)
    fig = px.imshow(
        corr, text_auto=True, zmin=-1, zmax=1, color_continuous_scale="RdBu_r",
        title="Spearman correlation (current filters)", template=TEMPLATE,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        "- **Price** is most strongly tied to **age** (negative) and **odometer** (negative).\n"
        "- **Cylinders** has a moderate positive link to price, largely because big engines "
        "come in trucks.\n"
        "- **Days listed** is uncorrelated with everything.\n\n"
        "Spearman is used because price and mileage are heavily skewed, and rank correlation "
        "is robust to the extreme outliers in this data."
    )

with st.expander("Data notes and cleaning"):
    st.markdown(
        f"- {len(raw):,} raw listings. Missing values: model year ({raw['model_year'].isna().sum():,}), "
        f"cylinders ({raw['cylinders'].isna().sum():,}), odometer ({raw['odometer'].isna().sum():,}), "
        f"paint color ({(raw['paint_color'] == 'unknown').sum():,}). Charts using a missing field drop those rows "
        "rather than imputing values.\n"
        "- `is_4wd` only holds `1` or blank in the source, so blanks are treated as 2WD.\n"
        "- `age` = year posted minus model year.\n"
        "- Sidebar filters remove placeholder prices (~$1) and extreme outliers."
    )
