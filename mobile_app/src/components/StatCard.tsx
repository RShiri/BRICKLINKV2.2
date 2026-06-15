import React from "react";
import { View, Text, StyleSheet } from "react-native";

interface Props {
  label: string;
  value: string;
  icon: string;
  color?: string;
}

export default function StatCard({ label, value, icon, color = "#7c7cff" }: Props) {
  return (
    <View style={[styles.card, { borderTopColor: color }]}>
      <Text style={styles.icon}>{icon}</Text>
      <Text style={[styles.value, { color }]}>{value}</Text>
      <Text style={styles.label}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    backgroundColor: "#1a1a2e",
    borderRadius: 12,
    padding: 12,
    margin: 4,
    alignItems: "center",
    borderTopWidth: 3,
  },
  icon: {
    fontSize: 20,
    marginBottom: 4,
  },
  value: {
    fontSize: 18,
    fontWeight: "800",
  },
  label: {
    fontSize: 10,
    color: "#8888aa",
    marginTop: 2,
    textAlign: "center",
  },
});
