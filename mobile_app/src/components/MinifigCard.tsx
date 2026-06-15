import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Dimensions } from "react-native";
import { Image } from "expo-image";
import { Minifig } from "../types";
import { ratingColor } from "../lib/utils";

const CARD_WIDTH = (Dimensions.get("window").width - 48) / 2;

interface Props {
  fig: Minifig;
  onPress?: (fig: Minifig) => void;
}

export default function MinifigCard({ fig, onPress }: Props) {
  return (
    <TouchableOpacity
      style={styles.card}
      onPress={() => onPress?.(fig)}
      activeOpacity={0.8}
    >
      <Image
        source={{ uri: fig.imageUrl }}
        style={styles.image}
        contentFit="contain"
        placeholder={{ uri: "https://img.bricklink.com/ItemImage/MN/0/placeholder.png" }}
      />

      <View style={styles.info}>
        <Text style={styles.id}>{fig.id}</Text>
        <Text style={styles.name} numberOfLines={2}>{fig.name}</Text>
        <Text style={styles.year}>{fig.year}</Text>

        <View style={styles.prices}>
          <Text style={styles.priceLabel}>New</Text>
          <Text style={styles.price}>
            {fig.newPrice > 0 ? `₪${fig.newPrice.toFixed(0)}` : "—"}
          </Text>
        </View>
        <View style={styles.prices}>
          <Text style={styles.priceLabel}>Used</Text>
          <Text style={styles.price}>
            {fig.usedPrice > 0 ? `₪${fig.usedPrice.toFixed(0)}` : "—"}
          </Text>
        </View>

        {fig.profit > 0 && (
          <View style={[styles.ratingBadge, { backgroundColor: ratingColor(fig.rating) + "33" }]}>
            <Text style={[styles.ratingText, { color: ratingColor(fig.rating) }]}>
              {fig.rating}  +₪{fig.profit.toFixed(0)}
            </Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    width: CARD_WIDTH,
    backgroundColor: "#1a1a2e",
    borderRadius: 12,
    margin: 4,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "#2a2a3e",
  },
  image: {
    width: "100%",
    height: CARD_WIDTH * 0.9,
    backgroundColor: "#0f0f1a",
  },
  info: {
    padding: 8,
  },
  id: {
    fontSize: 10,
    color: "#8888aa",
    fontFamily: "monospace",
  },
  name: {
    fontSize: 12,
    color: "#ffffff",
    fontWeight: "600",
    marginTop: 2,
    lineHeight: 16,
  },
  year: {
    fontSize: 10,
    color: "#6666aa",
    marginTop: 2,
  },
  prices: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 4,
  },
  priceLabel: {
    fontSize: 10,
    color: "#8888aa",
  },
  price: {
    fontSize: 11,
    color: "#ccccff",
    fontWeight: "600",
  },
  ratingBadge: {
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 3,
    marginTop: 6,
    alignSelf: "flex-start",
  },
  ratingText: {
    fontSize: 10,
    fontWeight: "700",
  },
});
