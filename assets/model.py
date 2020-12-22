import pandas as pd
import numpy as np
import folium


class BoroughRecommender(object):

    LONDON_COORDS = [51.5074, -0.1278]
    RENT_PICKLE = "ldn_rents.pkl"
    VENUES_PICKLE = "ldn_venues_raw.pkl"
    GROUPS_PICKLE = "ldn_groups_norm.pkl"
    LDN_GEOJSON = "london_boroughs_proper.geojson"
    ACM_TYPES = [
        'Room',
        'Studio',
        'One Bedroom',
        'Two Bedroom',
        'Three Bedroom',
        'Four Bedroom',
    ]

    def __init__(
        self,
        data_dir=".\\",
        rent_pickle=RENT_PICKLE,
        venues_pickle=VENUES_PICKLE,
        groups_pickle=GROUPS_PICKLE,
        ldn_geojson=LDN_GEOJSON,
        num_of_recs=5,
        auto_update=True,
        auto_plot=True,
        plot_venues=False,
    ):
        self.df_rent = pd.read_pickle(data_dir + rent_pickle)
        self.df_venues = pd.read_pickle(data_dir + venues_pickle)
        self.df_groups = pd.read_pickle(data_dir + groups_pickle)
        self.df_preferences = None
        self.ldn_geojson = data_dir + ldn_geojson
        self.num_of_recs = num_of_recs
        self.auto_update = auto_update
        self.auto_plot = auto_plot
        self.venue_groups = self.__allowed_groups()
        self.preferences = self.__setup_preferences()
        self.auto_update = auto_update
        self.selected_groups = self.venue_groups
        self.selected_boroughs = None
        self.accommodation_types = "All categories"
        self.rent_range = [0, 3200]
        self.map = None
        self.plot_venues = plot_venues
        self.venue_legend = None
        self.__setup_dataframes()
        self.__initialize_map()

    def __setup_dataframes(self):
        self.df_groups.set_index("Borough", inplace=True)

    def __allowed_groups(self):
        col_names = self.df_groups.columns.tolist()
        group_names = col_names[1:]
        return group_names

    def __setup_preferences(self):
        pref_dict = {grp: 1 for grp in self.venue_groups}
        df = pd.DataFrame.from_dict(pref_dict, orient="index", columns=["Preference"])
        df["Preference"] = df["Preference"] / df["Preference"].sum()
        self.df_preferences = df
        return pref_dict

    def save_map(self, file_name):
        if self.map is not None:
            self.map.save(file_name)

    def __reset_preferences(self):
        pref_dict = {grp: 0 for grp in self.venue_groups}
        self.preferences = pref_dict

    def _filter_rent_data(self):
        """
        Returns boroughs that satisfy the conditions for `categories` and `rent_range`
            
        Inputs:
            df - pandas DataFrame containing rent data -> !!! Assumes df_rent as default 
            categories - an iterable or a string specifying appropriate accommodation types
            rent_range - a list or a tuple with r_min and r_max rent ranges.
            
        Output:
            boroughs - a list of boroughs that match the condition
        
        """

        df = self.df_rent
        categories = self.accommodation_types
        rent_range = self.rent_range

        if isinstance(categories, str):
            cats = [categories]
        else:
            cats = categories

        cat_cond = df["Category"].isin(cats)
        rent_lower = rent_range[0]
        rent_higher = rent_range[1]

        # If invalid data provided
        if rent_lower > rent_higher:
            rent_higher = rent_lower

        rent_cond_1 = (df["Lower quartile"] <= rent_higher) & (
            df["Upper quartile"] >= rent_higher
        )
        rent_cond_2 = (df["Lower quartile"] <= rent_lower) & (
            df["Upper quartile"] >= rent_lower
        )
        rent_cond = rent_cond_1 | rent_cond_2
        rent_cond = (df["Lower quartile"] <= rent_higher) & (
            df["Upper quartile"] >= rent_lower
        )

        not_null = ~df["Median"].isnull()
        df_filtered = df.loc[(cat_cond & rent_cond & not_null)]
        boroughs = df_filtered["Borough"].unique().tolist()

        self.selected_boroughs = boroughs

        if self.auto_update:
            self.recommend()

    def set_rent_range(self, rent_range):
        self.rent_range = rent_range
        self._filter_rent_data()

    def set_accommodation_types(self, acc_types):
        self.accommodation_types = acc_types
        self._filter_rent_data()

    def set_preferences(self, ranking):
        "Converts `ranking` list to normalized pandas DataFrame"
        self.__reset_preferences()
        self.selected_groups = ranking

        N = len(ranking)
        for i, cat in enumerate(ranking):
            self.preferences[cat] = N - i

        df = pd.DataFrame.from_dict(
            self.preferences, orient="index", columns=["Preference"]
        )
        df["Preference"] = df["Preference"] / df["Preference"].sum()
        self.df_preferences = df

        if self.auto_update:
            self.recommend()

    def recommend(self):
        "Calculates the recommendation vector"
        W = self.df_groups.loc[self.selected_boroughs]
        p = self.df_preferences["Preference"]

        df_rec = (p * W).sum(axis=1).to_frame()
        df_rec.columns = ["Match"]
        df_rec.sort_values(by="Match", ascending=False, inplace=True)
        rec_boroughs = df_rec.head(self.num_of_recs).index.tolist()

        self.df_recommendation = df_rec
        self.recommended_boroughs = rec_boroughs

        if self.auto_plot:
            self._plot_boroughs()

    def __initialize_map(self):
        """
        Creates map object using folium
        """
        map_ldn = folium.Map(
            location=self.LONDON_COORDS, tiles="cartodbpositron", zoom_start=10
        )
        df_data = self.df_rent.loc[
            self.df_rent["Category"] == "All categories", ["Borough", "Median"]
        ]

        # Chloropleth Map of boundaries, where shading is dependent on median rent for 'All categories'
        folium.Choropleth(
            geo_data=self.ldn_geojson,
            fill_color="BuPu",
            data=df_data,
            columns=["Borough", "Median"],
            key_on="feature.properties.name",
            weight=1,
            line_color="black",
            fill_opacity=0.3,
            line_opacity=0.5,
            legend_name="Median Monthly Rent (\\xA3)",
            highlight=True,
        ).add_to(map_ldn)

        self.map = map_ldn

    def _plot_boroughs(self):
        """
        Creates map object using folium
        """
        self.__initialize_map()  # to remove previous plots

        df_matched = self.df_venues[
            (self.df_venues["Borough"].isin(self.recommended_boroughs))
            & (self.df_venues["Group"].isin(self.selected_groups))
        ]

        df_boroughs = df_matched[
            ["Borough", "BoroughLat", "BoroughLon"]
        ].drop_duplicates()

        # Add borough markers to map
        for i, row in df_boroughs.iterrows():
            borough = row["Borough"]
            coords = [row["BoroughLat"], row["BoroughLon"]]
            lbl_str = f"{borough}"  # create a label with borough name and rent range
            label = folium.Popup(
                lbl_str, parse_html=True
            )  # so that the label is used as a Popup

            # Add the marker
            folium.CircleMarker(
                coords,
                radius=10,
                popup=label,
                color="black",
                weight=1,
                fill=True,
                fill_color="black",
                fill_opacity=0.75,
                parse_html=False,
            ).add_to(self.map)

        if self.plot_venues:
            self._plot_borough_venues(df_matched)

    def _plot_borough_venues(self, df_matched, n=10):
        """
        Plots venues on the map
        """
        color_map = {
            "Eating out": "#e41a1c",
            "Entertainment": "#377eb8",
            "Going out": "#ffff33",
            "Green spaces": "#984ea3",
            "Groceries": "#ff7f00",
            "Health and Sports": "#4daf4a",
            "Other": "#999999",
            "Public Transport": "#a65628",
            "Shopping": "#f781bf",
        }

        self.venue_legend = color_map

        for i, row in df_matched.iterrows():
            # let's plot only every n-th point
            if i % n == 0:
                continue
            lat_i = row["Venue Latitude"]
            lon_i = row["Venue Longitude"]
            venue = row["Venue"]
            group = row["Group"]

            label = f"{venue}" # ({group})"

            coords = [lat_i, lon_i]
            folium.CircleMarker(
                coords,
                radius=4,
                popup=label,
                color="black",
                weight=1,
                fill=True,
                fill_color=color_map[group],
                fill_opacity=0.9,
                parse_html=False,
            ).add_to(self.map)
