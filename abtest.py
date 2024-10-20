import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats
from scipy.stats import norm
import altair as alt

st.set_page_config(
    page_title="A/B Testing App", page_icon="📊", initial_sidebar_state="expanded",
    
)

def conversion_rate(conversions:int, visitors:int):
    """
    return the conversion rate for a given number 
    of conversions and number of visitors 

    Args:
        conversions (int): total number of conversions
        visitors (int): total number of unique visitors
    
    return float
  """
    return (conversions / visitors) * 100


def lift(cra:float, crb:float):
  """
    In A/B testing, relative uplift in conversion rate is a 
    metric that measures the percentage increase or decrease 
    in conversion rate between a test group and a control group. 
    It provides a clear and comparable way to assess the effectiveness 
    of a new treatment or variation.

    Test Conversion Rate: The conversion rate of the group that received the new treatment or variation.
    Control Conversion Rate: The conversion rate of the group that received the original or standard treatment.
    
    positive relative uplift = new treatment resulted in higher conversion rate than control group
    negative relative uplift = new treatment resulted in lower conversion rate than the control group
    zero = no difference
    
    Args:
        CR_A (float): conversion rate of group A
        CR_B (float): conversion rate of group B
    return float
  """
  return ((crb - cra) / cra) * 100


def std_err(cr:float, visitors:float):
  """
    returns the standard error of the conversion rate
    
    standard error is used to calculate the deviation in conversion rates 
    for specific group if experiment is repeated multiple times
  
    conversion rate (conv_rate)
    number of trials (visitors)
    
    standard error = square root of ( conv_rate * (1 - conv_rate) / visitors)

    Args:
        conv_rate (float): conversion rate of a group (either A or B)
        visitors (float): total number of unique visitors
    
    returns float   the standard error of conversion rate
  """
  return np.sqrt((cr / 100 * (1 - cr / 100)) / visitors)


def std_err_diff(sea:float, seb:float):
    """
    returns the z-score test statistic

    Args:
        SE_A (float): standard error of conversion rate of group A
        SE_B (float): standard error of conversion rate of group B
    
    return float    
      standard error of the sampling distribution difference
      between group A and group B
    """
    return np.sqrt(sea ** 2 + seb ** 2)


def z_score(cra:float, crb:float, error:float):
    """Returns the z-score test statistic measuring exactly how many
    standard deviations above or below the mean a data point is.
    Parameters
    ----------
    cra: float
        Conversion rate of Group A
    crb: float
        Conversion rate of Group B
    error: float
        Standard error of the sampling distribution difference between
        Group A and Group B
    Returns
    -------
    float
        z-score test statistic
    """
    return ((crb - cra) / error) / 100


def p_value(z:float, hypothesis:str):
    """
    returns the p-value which is the probability of obtaining 
    test results at least as extreme as the results actually observed
    assumption is that the null hypothesis is correct

    Args:
        z_score (float): z-score test statistic
        hypothesis (str): Type of hypothesis test: "One-sided" or "Two-sided"
          [One-sided] is statistical hypothesis test to show that 
            the sample mean would be higher or lower than the population mean
            but not both
          [Two-sided] is statistical hypothesis test which the critical area of
            of the distribution is two-sided and tests whether  a sample greater
            or less than a range of values
    
    return float
      p-value
    """
    if hypothesis == "One-sided" and z < 0:
        return 1 - norm().sf(z)
    elif hypothesis == "One-sided" and z >= 0:
        return norm().sf(z) / 2
    else:
        return norm().sf(z)


def significance(alpha:float, p:float):
    """
    returns whether the p-value is statistically significant or not.
    A p-value (p) less than the significance level (alpha) is statistically significant

    Args:
        alpha (float): 
          the significance level (α) is the probability of a Type 1 Error
          which is rejecting the null hypothesis when it is true
          
        p_value (float): the p value
    
    returns str
      "Yes" if significant ; else "No"
    """
    return "YES" if p < alpha else "NO"


def plot_chart(df:pd.DataFrame):
    """
    Diplays a bar chart of conversion rates of A/B test groups,
    with the y-axis denoting the conversion rates.
    Parameters
    ----------
    df: pd.DataFrame
        The source DataFrame containing the data to be plotted
    Returns
    -------
    streamlit.altair_chart
        Bar chart with text above each bar denoting the conversion rate
    """
    chart = (
        alt.Chart(df)
        .mark_bar(color='cyan') # "#61b33b"
        .encode(
            x=alt.X("Group:O", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Conversion:Q", title="Conversion rate (%)"),
            opacity="Group:O",
        )
        .properties(width=500, height=500)
    )

    # Place conversion rate as text above each bar
    chart_text = chart.mark_text(
        align="center", baseline="middle", dy=-10, color="black"
    ).encode(text=alt.Text("Conversion:Q", format=",.3g"))

    return st.altair_chart((chart + chart_text).interactive())


def style_negative(v, props=""):
    """Helper function to color text in a DataFrame if it is negative.
    Parameters
    ----------
    v: float
        The text (value) in a DataFrame to color
    props: str
        A string with a CSS attribute-value pair. E.g "color:red;"
        See: https://pandas.pydata.org/pandas-docs/stable/user_guide/style.html
    Returns
    -------
    A styled DataFrame with negative values colored in red.
    Example
    -------
    df.style.map(style_negative, props="color:red;")
    """
    return props if v < 0 else None


def style_p_value(v, props=""):
    """Helper function to color p-value in DataFrame. If p-value is
    statististically significant, text is colored green; else red.
    Parameters
    ----------
    v: float
        The text (value) in a DataFrame to color
    props: str
        A string with a CSS attribute-value pair. E.g "color:green;"
        See: https://pandas.pydata.org/pandas-docs/stable/user_guide/style.html
    Returns
    -------
    A styled DataFrame with negative values colored in red.
    Example
    -------
    >>> df.style.apply(style_p_value, props="color:red;", axis=1, subset=["p-value"])
    """
    return np.where(v < st.session_state.alpha, "color:green;", props)


def calculate_significance(
    conversions_a, conversions_b, visitors_a, visitors_b, hypothesis, alpha
):
    """
      calculates all metrics to be displayed including:
        conversion rates, relative uplift, standard errors,
        z-score, p-value, significance and stores them as 
        session state variables

      Args:
          conversions_a (int): 
            number of users who converted when shown variant. group A
          
          conversions_b (int): 
            number of users who converted when shown variant. group B
          
          visitors_a (int): 
            total number of users shown variant. group A
          
          visitors_b (int): 
            total number of users shown variant. group B
          
          hypothesis (str): type of hypothesis: "One-sided" or "Two-sided"
            ["One-sided"] is a statistical hypothesis test set up to
              show that the sample mean would be higher or lower than the
              population mean, but not both.
            ["Two-sided"] is a statistical hypothesis test in which the
              critical area of a distribution is two-sided and tests whether
              a sample is greater or less than a range of values.
          
          alpha (float): 
            the significance level: the probability of Type 1 Error 
            (probability of rejecting the null hypothesis when it is true)

      """
  
    # [ Streamlit session state ] allows you to store and retrieve data across different parts of the Streamlit app
    # persistence data stored across multiple requests
    # global access for all components
    # various data types can be stored
    # ---> avoid storing sensitive data, it gets stored on the server
    # ---> avoid using with large datasets 
    # ---> clear session state when needed      st.experimental_rerun( clear_cache )
    
    st.session_state.cra = conversion_rate(int(conversions_a), int(visitors_a))
    st.session_state.crb = conversion_rate(int(conversions_b), int(visitors_b))
    st.session_state.uplift = lift(st.session_state.cra, st.session_state.crb)
    st.session_state.sea = std_err(st.session_state.cra, float(visitors_a))
    st.session_state.seb = std_err(st.session_state.crb, float(visitors_b))
    st.session_state.sed = std_err_diff(st.session_state.sea, st.session_state.seb)
    st.session_state.z = z_score(
        st.session_state.cra, st.session_state.crb, st.session_state.sed
    )
    st.session_state.p = p_value(st.session_state.z, st.session_state.hypothesis)
    st.session_state.significant = significance(
        st.session_state.alpha, st.session_state.p
    )



st.write(
    """
    # A/B Testing App
    Upload your experiment results to see the significance of your A/B test.
"""
)

st.sidebar.subheader("About")

st.sidebar.write("""
  A/B testing (also known as bucket testing, split-run testing, or split testing) is a user experience research method.
  A/B tests consist of a randomized experiment that usually involves two variants (A and B).
  
  It includes application of statistical hypothesis testing or "two-sample hypothesis testing" as used in the field of statistics. 
  A/B testing is a way to compare multiple versions of a single variable, for example by testing a subject's response 
  to variant A against variant B, and determining which of the variants is more effective.
""")

uploaded_file = st.file_uploader("Upload CSV", type=".csv")
if uploaded_file is not None:
  st.write("File uploaded :white_check_mark: ")


use_example_file = st.checkbox(
    "Use example file", True, help="Use in-built example file to demo the app"
)

ab_default = None
result_default = None

# If CSV is not uploaded and checkbox is filled, use values from the example file
# and pass them down to the next if block
if use_example_file:
    uploaded_file = "Website_Results.csv"
    ab_default = ["variant"]
    result_default = ["converted"]


if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.markdown("### Data preview")
    st.dataframe(df.head())

    st.markdown("### Select columns for analysis")
    with st.form(key="my_form"):
        ab = st.multiselect(
            "A/B column",
            options=df.columns,
            help="Select which column refers to your A/B testing labels.",
            default=ab_default,
        )
        if ab:
            control = df[ab[0]].unique()[0]
            treatment = df[ab[0]].unique()[1]
            decide = st.radio(
                f"Is *{treatment}* Group B?",
                options=["Yes", "No"],
                help="Select yes if this is group B (or the treatment group) from your test.",
            )
            if decide == "No":
                control, treatment = treatment, control
            visitors_a = df[ab[0]].value_counts()[control]
            visitors_b = df[ab[0]].value_counts()[treatment]

        result = st.multiselect(
            "Result column",
            options=df.columns,
            help="Select which column shows the result of the test.",
            default=result_default,
        )

        if result:
            conversions_a = (
                df[[ab[0], result[0]]].groupby(ab[0]).agg("sum")[result[0]][control]
            )
            conversions_b = (
                df[[ab[0], result[0]]].groupby(ab[0]).agg("sum")[result[0]][treatment]
            )

        with st.expander("Adjust test parameters"):
            st.markdown("### Parameters")
            st.radio(
                "Hypothesis type",
                options=["One-sided", "Two-sided"],
                index=0,
                key="hypothesis",
                help="TBD",
            )
            st.slider(
                "Significance level (α)",
                min_value=0.01,
                max_value=0.10,
                value=0.05,
                step=0.01,
                key="alpha",
                help=" The probability of mistakenly rejecting the null hypothesis, if the null hypothesis is true. This is also called false positive and type I error. ",
            )

        submit_button = st.form_submit_button(label="Submit")

    if not ab or not result:
        st.warning("Please select both an **A/B column** and a **Result column**.")
        st.stop()

    # type(uploaded_file) == str, means the example file was used
    name = (
        "Website_Results.csv" if isinstance(uploaded_file, str) else uploaded_file.name
    )
    st.write("")
    st.write("## Results for A/B test from ", name)
    st.write("")

    # Obtain the metrics to display
    calculate_significance(
        conversions_a,
        conversions_b,
        visitors_a,
        visitors_b,
        st.session_state.hypothesis,
        st.session_state.alpha,
    )

    mcol1, mcol2 = st.columns(2)

    # Use st.metric to diplay difference in conversion rates
    with mcol1:
        st.metric(
            "Delta",
            value=f"{(st.session_state.crb - st.session_state.cra):.3g}%",
            delta=f"{(st.session_state.crb - st.session_state.cra):.3g}%",
        )
    # Display whether or not A/B test result is statistically significant
    with mcol2:
        st.metric("Significant?", value=st.session_state.significant)

    # Create a single-row, two-column DataFrame to use in bar chart
    results_df = pd.DataFrame(
        {
            "Group": ["Control", "Treatment"],
            "Conversion": [st.session_state.cra, st.session_state.crb],
        }
    )
    st.write("")
    st.write("")

    # Plot bar chart of conversion rates
    plot_chart(results_df)



    table = pd.DataFrame(
        {
            "Converted": [conversions_a, conversions_b],
            "Total": [visitors_a, visitors_b],
            "% Converted": [st.session_state.cra, st.session_state.crb],
        },
        index=pd.Index(["Control", "Treatment"]),
    )

    # Format "% Converted" column values to 3 decimal places

    metrics = pd.DataFrame(
        {
            "p-value": [st.session_state.p],
            "z-score": [st.session_state.z],
            "relative uplift": [st.session_state.uplift],
        },
        index=pd.Index(["Metrics"]),
    )

    # Color negative values red; color significant p-value green and not significant red
    
    col5, col6 = st.columns(2)
    col6.write(table.style.format(formatter={("% Converted"): "{:.3g}%"}))
    col5.write( metrics.style.format(
            formatter={("p-value", "z-score"): "{:.3g}", ("uplift"): "{:.3g}%"}
        )
        .map(style_negative, props="color:red;")
        .apply(style_p_value, props="color:red;", axis=1, subset=["p-value"])
    ) 
    