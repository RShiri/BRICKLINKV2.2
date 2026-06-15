import React, { useEffect, useState } from "react";
import {
  View, Text, StyleSheet, FlatList,
  ActivityIndicator, TouchableOpacity,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import MinifigCard from "../components/MinifigCard";
import StatCard from "../components/StatCard";
import { getCollectionMinifigs } from "../lib/database";
import { Minifig } from "../types";
import { formatPrice } from "../lib/utils";

const COLLECTIONS = ["Ram's Collection", "Udi's Collection"];

export default function CollectionScreen() {
  const navigation = useNavigation<any>();
  const [selected, setSelected] = useState(COLLECTIONS[0]);
  const [figs, setFigs] = useState<Minifig[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getCollectionMinifigs(selected).then((data) => {
      setFigs(data);
      setLoading(false);
    });
  }, [selected]);

  const totalNew  = figs.reduce((s, f) => s + f.newPrice, 0);
  const totalUsed = figs.reduce((s, f) => s + f.usedPrice, 0);
  const bestProfit = figs.reduce((m, f) => Math.max(m, f.profit), 0);

  return (
    <SafeAreaView style={styles.safe}>
      {/* Collection switcher */}
      <View style={styles.tabs}>
        {COLLECTIONS.map((c) => (
          <TouchableOpacity
            key={c}
            style={[styles.tab, selected === c && styles.tabActive]}
            onPress={() => setSelected(c)}
          >
            <Text style={[styles.tabText, selected === c && styles.tabTextActive]}>
              {c}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <ActivityIndicator color="#7c7cff" style={{ flex: 1 }} />
      ) : (
        <>
          {/* Stats */}
          <View style={styles.statsRow}>
            <StatCard label="Figures" value={figs.length.toString()} icon="🧩" color="#7c7cff" />
            <StatCard label="Value (New)" value={formatPrice(totalNew)} icon="💎" color="#00e676" />
            <StatCard label="Best Profit" value={formatPrice(bestProfit)} icon="💰" color="#ffd700" />
          </View>

          <FlatList
            data={figs}
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
              <Text style={styles.empty}>No figures in this collection yet.</Text>
            }
          />
        </>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#0f0f1a" },
  tabs: {
    flexDirection: "row",
    marginHorizontal: 16,
    marginVertical: 12,
    backgroundColor: "#1a1a2e",
    borderRadius: 10,
    padding: 3,
  },
  tab: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: "center",
  },
  tabActive: { backgroundColor: "#7c7cff" },
  tabText: { fontSize: 13, color: "#8888aa", fontWeight: "600" },
  tabTextActive: { color: "#ffffff" },
  statsRow: {
    flexDirection: "row",
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  grid: { paddingHorizontal: 16, paddingBottom: 32 },
  empty: {
    color: "#8888aa",
    textAlign: "center",
    marginTop: 60,
    fontSize: 14,
  },
});
