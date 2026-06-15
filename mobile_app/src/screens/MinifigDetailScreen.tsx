import React from "react";
import {
  View, Text, StyleSheet, ScrollView, Dimensions,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRoute, useNavigation } from "@react-navigation/native";
import { Image } from "expo-image";
import { Minifig } from "../types";
import { ratingColor, formatPrice, formatProfit } from "../lib/utils";
import { LinearGradient } from "expo-linear-gradient";

const W = Dimensions.get("window").width;

export default function MinifigDetailScreen() {
  const route = useRoute<any>();
  const navigation = useNavigation();
  const fig: Minifig = route.params.fig;

  React.useEffect(() => {
    navigation.setOptions({ title: fig.id });
  }, [fig]);

  const rc = ratingColor(fig.rating);

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Hero image */}
        <LinearGradient colors={["#1a1a2e", "#0f0f1a"]} style={styles.hero}>
          <Image
            source={{ uri: fig.imageUrl }}
            style={styles.image}
            contentFit="contain"
          />
        </LinearGradient>

        <View style={styles.body}>
          {/* Name + year */}
          <Text style={styles.name}>{fig.name}</Text>
          <Text style={styles.meta}>{fig.id}  ·  {fig.year}</Text>

          {/* Rating badge */}
          {fig.rating && fig.rating !== "N/A" && (
            <View style={[styles.ratingBadge, { backgroundColor: rc + "22", borderColor: rc }]}>
              <Text style={[styles.ratingText, { color: rc }]}>
                {fig.rating}
              </Text>
            </View>
          )}

          {/* Price cards */}
          <View style={styles.priceRow}>
            <View style={styles.priceCard}>
              <Text style={styles.priceLabel}>New</Text>
              <Text style={styles.priceValue}>{formatPrice(fig.newPrice)}</Text>
            </View>
            <View style={styles.priceCard}>
              <Text style={styles.priceLabel}>Used</Text>
              <Text style={styles.priceValue}>{formatPrice(fig.usedPrice)}</Text>
            </View>
          </View>

          {/* Profit row */}
          {fig.profit > 0 && (
            <View style={[styles.profitBox, { borderColor: rc }]}>
              <View>
                <Text style={styles.profitLabel}>Estimated Profit</Text>
                <Text style={[styles.profitValue, { color: rc }]}>
                  {formatProfit(fig.profit)}
                </Text>
              </View>
              <View>
                <Text style={styles.profitLabel}>Margin</Text>
                <Text style={[styles.profitValue, { color: rc }]}>
                  {fig.margin > 0 ? `${fig.margin.toFixed(0)}%` : "—"}
                </Text>
              </View>
            </View>
          )}

          {/* Last updated */}
          <Text style={styles.updated}>
            Last updated: {new Date(fig.updatedAt).toLocaleDateString()}
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#0f0f1a" },
  hero: {
    alignItems: "center",
    paddingVertical: 32,
  },
  image: {
    width: W * 0.55,
    height: W * 0.55,
  },
  body: {
    padding: 20,
  },
  name: {
    fontSize: 22,
    fontWeight: "800",
    color: "#ffffff",
    lineHeight: 28,
  },
  meta: {
    fontSize: 13,
    color: "#8888aa",
    marginTop: 4,
    fontFamily: "monospace",
  },
  ratingBadge: {
    alignSelf: "flex-start",
    borderRadius: 8,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 5,
    marginTop: 12,
  },
  ratingText: {
    fontSize: 13,
    fontWeight: "800",
    letterSpacing: 1,
  },
  priceRow: {
    flexDirection: "row",
    gap: 12,
    marginTop: 20,
  },
  priceCard: {
    flex: 1,
    backgroundColor: "#1a1a2e",
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#2a2a3e",
  },
  priceLabel: {
    fontSize: 11,
    color: "#8888aa",
    marginBottom: 4,
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  priceValue: {
    fontSize: 22,
    fontWeight: "800",
    color: "#ffffff",
  },
  profitBox: {
    flexDirection: "row",
    justifyContent: "space-around",
    backgroundColor: "#1a1a2e",
    borderRadius: 12,
    padding: 16,
    marginTop: 12,
    borderWidth: 1,
  },
  profitLabel: {
    fontSize: 11,
    color: "#8888aa",
    textAlign: "center",
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  profitValue: {
    fontSize: 24,
    fontWeight: "900",
    textAlign: "center",
    marginTop: 4,
  },
  updated: {
    fontSize: 11,
    color: "#555577",
    marginTop: 24,
    textAlign: "center",
  },
});
