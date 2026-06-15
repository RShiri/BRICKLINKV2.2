import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def filter_by_collection(df: pd.DataFrame, collection_ids: set) -> pd.DataFrame:
    """Mirrors the collection filtering logic in dashboard.py."""
    if df.empty:
        return df
    return df[df["ID"].str.lower().isin(collection_ids)].copy()


def make_df(ids, prices=None):
    prices = prices or [100] * len(ids)
    return pd.DataFrame({
        "ID": ids,
        "Name": [f"Item {i}" for i in ids],
        "New Price": prices,
        "Stale": [False] * len(ids),
    })


class TestCollectionFilter:
    def test_returns_only_matching_items(self):
        df = make_df(["75001", "75002", "75003"])
        result = filter_by_collection(df, {"75001", "75003"})
        assert set(result["ID"]) == {"75001", "75003"}
        assert len(result) == 2

    def test_case_insensitive_matching(self):
        df = make_df(["SW0450", "SH0232"])
        result = filter_by_collection(df, {"sw0450", "sh0232"})
        assert len(result) == 2

    def test_collection_ids_must_be_lowercase(self):
        # dashboard.py always lowercases IDs before building the set;
        # passing uppercase IDs will NOT match because only df["ID"] is lowercased
        df = make_df(["sw0450"])
        result = filter_by_collection(df, {"SW0450"})  # uppercase — won't match
        assert result.empty

    def test_lowercase_collection_ids_match_any_case_df(self):
        df = make_df(["SW0450"])  # uppercase in dataframe
        result = filter_by_collection(df, {"sw0450"})  # lowercase collection IDs
        assert len(result) == 1

    def test_empty_collection_returns_empty(self):
        df = make_df(["75001", "75002"])
        result = filter_by_collection(df, set())
        assert result.empty

    def test_empty_dataframe_returns_empty(self):
        result = filter_by_collection(pd.DataFrame(), {"75001"})
        assert result.empty

    def test_no_matches_returns_empty(self):
        df = make_df(["75001", "75002"])
        result = filter_by_collection(df, {"99999"})
        assert result.empty

    def test_all_items_match(self):
        df = make_df(["75001", "75002", "sh0001"])
        result = filter_by_collection(df, {"75001", "75002", "sh0001"})
        assert len(result) == 3

    def test_result_is_independent_copy(self):
        df = make_df(["75001", "75002"])
        result = filter_by_collection(df, {"75001"})
        result["New Price"] = 999
        assert df.loc[df["ID"] == "75001", "New Price"].values[0] == 100


class TestStaleEmojiBadge:
    def test_stale_true_maps_to_warning_emoji(self):
        df = make_df(["75001"])
        df["Stale"] = [True]
        df["Stale"] = df["Stale"].map({True: "⚠️", False: ""})
        assert df.iloc[0]["Stale"] == "⚠️"

    def test_stale_false_maps_to_empty_string(self):
        df = make_df(["75001"])
        df["Stale"] = [False]
        df["Stale"] = df["Stale"].map({True: "⚠️", False: ""})
        assert df.iloc[0]["Stale"] == ""

    def test_mixed_stale_values(self):
        df = make_df(["75001", "75002", "75003"])
        df["Stale"] = [True, False, True]
        df["Stale"] = df["Stale"].map({True: "⚠️", False: ""})
        assert list(df["Stale"]) == ["⚠️", "", "⚠️"]
