import React, { useState, useCallback } from "react";
import {
  View, Text, StyleSheet, TextInput, FlatList,
  ActivityIndicator, TouchableOpacity, Keyboard,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import MinifigCard from "../components/MinifigCard";
import { searchItems } from "../lib/database";
import { Minifig } from "../types";

export default function SearchScreen() {
  const navigation = useNavigation<any>();
  const [query, setQuery]     = useState("");
  const [results, setResults] = useState<Minifig[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    Keyboard.dismiss();
    setLoading(true);
    setSearched(true);
    const data = await searchItems(query.trim());
    setResults(data);
    setLoading(false);
  }, [query]);

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.searchRow}>
        <TextInput
          style={styles.input}
          placeholder="Search ID or name…  e.g. hp001, Spider-Man"
          placeholderTextColor="#8888aa"
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={handleSearch}
          returnKeyType="search"
          autoCapitalize="none"
          autoCorrect={false}
        />
        <TouchableOpacity style={styles.btn} onPress={handleSearch}>
          <Text style={styles.btnText}>Search</Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <ActivityIndicator color="#7c7cff" style={{ flex: 1 }} />
      ) : (
        <FlatList
          data={results}
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
          ListHeaderComponent={
            searched && !loading ? (
              <Text style={styles.resultCount}>
                {results.length} result{results.length !== 1 ? "s" : ""} for "{query}"
              </Text>
            ) : null
          }
          ListEmptyComponent={
            searched ? (
              <Text style={styles.empty}>No minifigures found for "{query}"</Text>
            ) : (
              <View style={styles.hint}>
                <Text style={styles.hintIcon}>🔍</Text>
                <Text style={styles.hintText}>
                  Search by minifig ID or name.{"\n"}
                  Examples: hp001, sw0001, Spider-Man, Hermione
                </Text>
              </View>
            )
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
    marginHorizontal: 16,
    marginVertical: 12,
    gap: 8,
  },
  input: {
    flex: 1,
    backgroundColor: "#1a1a2e",
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
    color: "#ffffff",
    fontSize: 14,
    borderWidth: 1,
    borderColor: "#2a2a3e",
  },
  btn: {
    backgroundColor: "#7c7cff",
    borderRadius: 10,
    paddingHorizontal: 16,
    justifyContent: "center",
  },
  btnText: { color: "#fff", fontWeight: "700", fontSize: 14 },
  grid: { paddingHorizontal: 16, paddingBottom: 24 },
  resultCount: {
    color: "#8888aa",
    fontSize: 12,
    marginBottom: 8,
    paddingHorizontal: 4,
  },
  empty: {
    color: "#8888aa",
    textAlign: "center",
    marginTop: 60,
    fontSize: 14,
  },
  hint: { alignItems: "center", marginTop: 80 },
  hintIcon: { fontSize: 48, marginBottom: 16 },
  hintText: {
    color: "#8888aa",
    textAlign: "center",
    fontSize: 14,
    lineHeight: 22,
  },
});
