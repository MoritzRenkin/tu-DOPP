import json
import numpy as np
import pandas as pd
from bokeh.palettes import brewer
from bokeh.plotting import figure
from bokeh.io import output_notebook, show, output_file
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar

def get_yearly_disaster_count(df: pd.DataFrame, index_cols: list | None = None, include_zero: bool = True) -> pd.Series:
    """ Calculate number of disaster occurrences grouped by index_cols for each Start_Year.

    Parameters
    ----------
    df: pd.DataFrame
        The dataframe containing the disaster data. One row represents one disaster.
    index_cols: list or None
        The columns that df should be grouped by and indexed. If None, "Start_Year" will be used.
        Default: None
    include_zero: bool
        If True zero counts will be included, otherwise the rows are dropped

    Returns
    -------
    pd.Series named "No_Disasters" indexed by index_cols

    :Authors:
        Moritz Renkin <e11807211@student.tuwien.ac.at>
    """

    default_index = ["Start_Year"]
    index = index_cols if index_cols is not None else default_index
    if not include_zero:
        return df.groupby(index).size().rename("No_Disasters")

    count_nonzero = get_yearly_disaster_count(df=df, index_cols=index_cols, include_zero=False)
    if index != default_index:
        return count_nonzero.unstack(fill_value=0).stack().rename("No_Disasters")
    return count_nonzero

def get_yearly_pct_change_to_initial(df: pd.DataFrame, index_cols: list | None = None) -> pd.Series:
    """ Calculate yearly percentage change number of disaster occurrences compared to the average of the first 10 years, grouped by the respective column.

    Parameters
    ----------
    df: pd.DataFrame
        The dataframe containing the disaster data. One row represents one disaster.
    index_cols: list or None
        The columns that df should be grouped by and indexed. If None, "Start_Year" will be used.
        Default: None

    Returns
    -------
    pd.Series named "Percent_Change" indexed by index_cols

    :Authors:
        Moritz Renkin <e11807211@student.tuwien.ac.at>
    """
    min_year = df["Start_Year"].min()
    counts: pd.Series = get_yearly_disaster_count(df=df, index_cols=index_cols, include_zero=True)
    initial_average = counts.loc[min_year:min_year+10].groupby(level=1).mean()
    if index_cols is not None:
        ret = counts.groupby(level=[1], group_keys=False).apply(lambda x: (x.div(initial_average, level=1) -1) *100).rename("Percent_Change")
    else:
        percent_change = (count_nonzero.div(count_nonzero.iloc[0]) -1) *100
        ret = percent_change.rename("Percent_Change")
    ret.replace([np.inf, -np.inf], np.nan, inplace=True)
    ret.dropna(inplace=True)
    return ret


def get_yearly_deaths(df: pd.DataFrame, custom_index: list | None = None, include_zero: bool = True) -> pd.Series:
    """ Calculate yearly disaster deaths, assuming a discrete uniform distribution of deaths between Start_Year and End_Year of each disaster.

    Parameters
    ----------
    df: pd.DataFrame
        The original DataFrame
    custom_index: list or None
        The columns to group the deaths by. All elements must be columns of df, but not "Start_Year" or "End_Year".
        Note that df is not normalized. Only independent columns should be passed in order to avoid anomalies. Example: [Country, Disaster_Type] -> ok. [Disaster_Type, Disaster_Subtype] -> NOT ok.
    include_zero: bool
        Include rows with 0 deaths.
        Note that enabling this option in combination with a custom_index will lengthen the returned series' index considerably.

    Returns
    -------
    pd.Series indexed by "Year" and custom_index if present

    :Authors:
        Moritz Renkin <e11807211@student.tuwien.ac.at>
    """
    df: pd.DataFrame = df.copy()
    min_start_year = df["Start_Year"].min()
    max_start_year = df["Start_Year"].max()

    alternate_cust_idx = ["__CUST_IDX"]
    if custom_index is None:
        custom_index = alternate_cust_idx
        df[alternate_cust_idx] = 0

    df = df.loc[:, ["Start_Year", "End_Year", "Total_Deaths"] + custom_index]
    df["Duration_CalendarYears"] = df["End_Year"].subtract(df["Start_Year"], fill_value=0)
    df.drop("End_Year", axis=1, inplace=True)
    df["Yearly_Disaster_Deaths"] = df["Total_Deaths"].div(df["Duration_CalendarYears"] + 1, fill_value=np.NaN)
    df.rename(columns={"Start_Year": "Year"}, inplace=True)

    index_labels = ["Year"] + custom_index
    intra_year_disasters = df.loc[df["Duration_CalendarYears"] == 0, ["Total_Deaths"] + index_labels]
    perennial_disasters = df.loc[df["Duration_CalendarYears"] != 0, ["Yearly_Disaster_Deaths", "Duration_CalendarYears"] + index_labels]

    intra_year_disaster_deaths = intra_year_disasters.groupby(index_labels).sum()
    intra_year_disaster_deaths = intra_year_disaster_deaths.loc[:, "Total_Deaths"]

    deaths_per_year: pd.Series
    if include_zero:
        custom_index_values = [list(df[label].unique()) for label in custom_index]
        complete_year_range = range(min_start_year, max_start_year + 1)
        result_index = pd.MultiIndex.from_product(iterables=[complete_year_range]+custom_index_values, names=index_labels).dropna()
        empty_series = pd.Series(data=0, name="Total_Deaths", index=result_index)
        deaths_per_year = empty_series.add(intra_year_disaster_deaths, fill_value=0).astype("float32")  # will be filled with perennial disaster_deaths later

    else:
        deaths_per_year = intra_year_disaster_deaths

    def _flatten_death_distr(year_df: pd.DataFrame) -> None:
        nonlocal deaths_per_year
        curr_year = year_df['Year'].iloc[0]
        year_df.dropna(axis=0, inplace=True)
        if len(year_df) == 0:
            return

        yearly_deaths_by_duration: pd.DataFrame = year_df[["Duration_CalendarYears", "Yearly_Disaster_Deaths"] + custom_index]\
            .groupby(["Duration_CalendarYears"] + custom_index, sort=False).sum()

        duration_df: pd.DataFrame
        for Duration_CalendarYears, duration_df in yearly_deaths_by_duration.groupby(level="Duration_CalendarYears", sort=False):
            duration_df.reset_index(inplace=True)
            duration_df.drop("Duration_CalendarYears", axis=1, inplace=True)

            year_range = np.arange(start=curr_year, stop=curr_year + Duration_CalendarYears + 1)
            year_idx_array: np.ndarray = np.asarray(year_range).repeat(len(duration_df))

            add_df: pd.DataFrame = pd.concat([duration_df] * len(year_range), ignore_index=True)
            add_df["Year"] = year_idx_array
            add_df.set_index(index_labels, inplace=True)
            add_series: pd.Series = add_df["Yearly_Disaster_Deaths"]
            add_series.rename("Total_Deaths", inplace=True)

            deaths_per_year = deaths_per_year.add(add_series, fill_value=0)

    perennial_disasters.groupby("Year", as_index=False, sort=False).apply(_flatten_death_distr)

    if custom_index == alternate_cust_idx:
        deaths_per_year.reset_index(level=custom_index, inplace=True, drop=True)
    if not include_zero:
        deaths_per_year = deaths_per_year[deaths_per_year!=0]

    return deaths_per_year.astype(np.float64)


def plot_world_map(merged, title) -> None:
    """ Plot world maps.

    Parameters
    ----------
    merged: pd.DataFrame
        Dataframe merged with coordinates df
    """
    # Read data to json.
    merged_json = json.loads(merged.to_json())
    # Convert to String like object.
    json_data = json.dumps(merged_json)
    # Input GeoJSON source that contains features for plotting.
    geosource = GeoJSONDataSource(geojson=json_data)
    # Define a sequential multi-hue color palette.
    palette = brewer['YlGnBu'][8]
    # Reverse color order so that dark blue is highest obesity.
    palette = palette[::-1]
    # Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
    color_mapper = LinearColorMapper(palette=palette, low=0, high=1)
    # Create color bar.
    color_bar = ColorBar(color_mapper=color_mapper, label_standoff=8, width=500, height=20,
                         border_line_color=None, location=(0, 0), orientation='horizontal')
    # Create figure object.
    p = figure(title=title, plot_height=600, plot_width=950,
               toolbar_location=None)
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    # Add patch renderer to figure.
    p.patches('xs', 'ys', source=geosource, fill_color={'field': 'Total_Deaths', 'transform': color_mapper},
              line_color='black', line_width=0.25, fill_alpha=1)
    # Specify figure layout.
    p.add_layout(color_bar, 'below')
    # Display figure inline in Jupyter Notebook.
    output_notebook()
    # Display figure.
    show(p)
