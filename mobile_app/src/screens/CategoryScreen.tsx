import React, { useEffect, useState, useCallback } from "react";
import {
  View, Text, StyleSheet, FlatList, TextInput,
  ActivityIndicator, TouchableOpacity,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRoute, useNavigation } from "@react-navigation/native";
import MinifigCard from "../components/MinifigCard";
import { getItemsByPrefix } from "../lib/database";
import { Minifig, SortOption, Theme } from "../types";

const SORTS: { key: SortOption; label: string }[] = [
  { key: "profit",   label: "Profit" },
  { key: "newPrice", label: "New Price" },
  { key: "usedPrice",label: "Used Price" },
  { key: "name",     label: "Name" },
  { key: "year",     label: "Year" },
];

export default function CategoryScreen() {
  const route = useRoute<any>();
  const navigation = useNavigation<any>();
  const theme: Theme = route.params.theme;

  const [all, setAll]       = useState<Minifig[]>([]);
  const [shown, setShown]   = useState<Minifig[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [sort, setSort]     = useState<SortOption>("profit");

  useEffect(() => {
    navigation.setOptions({ title: `${theme.icon} ${theme.name}` });
    (async () => {
      const items = await getItemsByPrefix(theme.prefix);
      setAll(items);
      setLoading(false);
    })();
  }, [theme]);

  useEffect(() => {
    let filtered = all;
    if (search.trim()) {
      const q = search.toLowerCase();
      filtered = all.filter(
        (f) => f.name.toLowerCase().includes(q) || f.id.toLowerCase().includes(q)
      );
    }
    filtered = [...filtered].sort((a, b) => {
      switch (sort) {
        case "profit":    return b.profit - a.profit;
        case "newPrice":  return b.newPrice - a.newPrice;
        case "usedPrice": return b.usedPrice - a.usedPrice;
        case "name":      return a.name.localeCompare(b.name);
        case "year":      return b.yearInt - a.yearInt;
      }
    });
    setShown(filtered);
  }, [all, search, sort]);

  return (
    <SafeAreaView style={styles.safe}>
      {/* Search bar */}
      <View style={styles.searchRow}>
        <TextInput
          style={styles.search}
          placeholder="Search name or ID…"
          placeholderTextColor="#8888aa"
          value={search}
          onChangeText={setSearch}
        />
        {search ? (
          <TouchableOpacity onPress={() => setSearch("")} style={styles.clear}>
            <Text style={styles.clearText}>✕</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      {/* Sort pills */}
      <View style={styles.sortRow}>
        {SORTS.map((s) => (
          <TouchableOpacity
            key={s.key}
            style={[styles.pill, sort === s.key && styles.pillActive]}
            onPress={() => setSort(s.key)}
          >
            <Text style={[styles.pillText, sort === s.key && styles.pillTextActive]}>
              {s.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Count */}
      <Text style={styles.count}>
        {loading ? "Loading…" : `${shown.length} of ${all.length} figures`}
      </Text>

      {loading ? (
        <ActivityIndicator color="#7c7cff" style={{ flex: 1 }} />
      ) : (
        <FlatList
          data={shown}
          keyExtractor={(f) => f.id}
          numColumns={2}
          renderItem={({ item }) => (
            <MinifigCard
              fig={item}
              onPress={(fig) => navigation.navigate("MinifigDetail", { fig })}
            />
          )}
          contentContainerStyle={styles.grid}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <Text style={styles.empty}>
              {search ? "No figures match your search." : "No figures in database yet.\nRun the scraper to populate."}
            </Text>
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#0f0f1a" },
  searchRow: {
    flexDirection: "row",
    alignItems: "center",
    marginHorizontal: 16,
    marginVertical: 8,
    backgroundColor: "#1a1a2e",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#2a2a3e",
  },
  search: {
    flex: 1,
    color: "#fff",
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 14,
  },
  clear: { paddingHorizontal: 12 },
  clearText: { color: "#8888aa", fontSize: 14 },
  sortRow: {
    flexDirection: "row",
    paddingHorizontal: 16,
    marginBottom: 6,
    gap: 6,
  },
  pill: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
    backgroundColor: "#1a1a2e",
    borderWidth: 1,
    borderColor: "#2a2a3e",
  },
  pillActive: {
    backgroundColor: "#7c7cff",
    borderColor: "#7c7cff",
  },
  pillText: { fontSize: 11, color: "#8888aa" },
  pillTextActive: { color: "#ffffff", fontWeight: "700" },
  count: {
    fontSize: 11,
    color: "#8888aa",
    paddingHorizontal: 20,
    marginBottom: 4,
  },
  grid: { paddingHorizontal: 16, paddingBottom: 24 },
  empty: {
    color: "#8888aa",
    textAlign: "center",
    marginTop: 60,
    fontSize: 14,
    lineHeight: 22,
  },
});
