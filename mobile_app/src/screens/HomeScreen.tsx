import React, { useEffect, useState } from "react";
import {
  View, Text, StyleSheet, ScrollView,
  FlatList, ActivityIndicator, TouchableOpacity,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import StatCard from "../components/StatCard";
import MinifigCard from "../components/MinifigCard";
import { getDashboardStats, getTopDeals } from "../lib/database";
import { Minifig } from "../types";
import { formatPrice } from "../lib/utils";

export default function HomeScreen() {
  const navigation = useNavigation<any>();
  const [stats, setStats] = useState({ totalItems: 0, excellentDeals: 0, topProfit: 0, avgProfit: 0 });
  const [topDeals, setTopDeals] = useState<Minifig[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const [s, deals] = await Promise.all([getDashboardStats(), getTopDeals(20)]);
      setStats(s);
      setTopDeals(deals);
      setLoading(false);
    })();
  }, []);

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.logo}>🧱 BrickLink Sniper</Text>
          <Text style={styles.subtitle}>LEGO Investment Tracker</Text>
        </View>

        {/* Stats */}
        {loading ? (
          <ActivityIndicator color="#7c7cff" style={{ marginVertical: 32 }} />
        ) : (
          <>
            <View style={styles.statsRow}>
              <StatCard label="Minifigures" value={stats.totalItems.toLocaleString()} icon="🧩" color="#7c7cff" />
              <StatCard label="Top Deals" value={stats.excellentDeals.toLocaleString()} icon="🎯" color="#00e676" />
            </View>
            <View style={styles.statsRow}>
              <StatCard label="Best Profit" value={formatPrice(stats.topProfit)} icon="💰" color="#ffd700" />
              <StatCard label="Avg Profit" value={formatPrice(stats.avgProfit)} icon="📈" color="#ff7043" />
            </View>

            {/* Top deals */}
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>🎯 Top Deals Right Now</Text>
              <TouchableOpacity onPress={() => navigation.navigate("Browse")}>
                <Text style={styles.seeAll}>See all →</Text>
              </TouchableOpacity>
            </View>

            <FlatList
              data={topDeals}
              keyExtractor={(f) => f.id}
              numColumns={2}
              renderItem={({ item }) => (
                <MinifigCard
                  fig={item}
                  onPress={(fig) => navigation.navigate("MinifigDetail", { fig })}
                />
              )}
              scrollEnabled={false}
              contentContainerStyle={styles.grid}
            />
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#0f0f1a" },
  scroll: { flex: 1 },
  header: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 24,
  },
  logo: {
    fontSize: 26,
    fontWeight: "900",
    color: "#ffffff",
  },
  subtitle: {
    fontSize: 13,
    color: "#8888aa",
    marginTop: 2,
  },
  statsRow: {
    flexDirection: "row",
    paddingHorizontal: 16,
    marginBottom: 4,
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    marginTop: 24,
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: "700",
    color: "#ffffff",
  },
  seeAll: {
    fontSize: 13,
    color: "#7c7cff",
  },
  grid: {
    paddingHorizontal: 16,
    paddingBottom: 24,
  },
});
