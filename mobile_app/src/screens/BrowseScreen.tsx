import React from "react";
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import { Theme } from "../types";

const THEMES: Theme[] = [
  { name: "Star Wars",           prefix: "sw",   icon: "🚀", desc: "sw0001–sw2000" },
  { name: "Superheroes",         prefix: "sh",   icon: "🦸", desc: "Marvel + DC" },
  { name: "Harry Potter",        prefix: "hp",   icon: "⚡", desc: "Wizarding World" },
  { name: "Ninjago",             prefix: "njo",  icon: "🐉", desc: "All seasons" },
  { name: "CMF",                 prefix: "col",  icon: "🎭", desc: "Collectible Minifig Series" },
  { name: "The LEGO Movie",      prefix: "tlm",  icon: "🎬", desc: "Movie 1 & 2" },
  { name: "Lord of the Rings",   prefix: "lor",  icon: "💍", desc: "LotR" },
  { name: "The Hobbit",          prefix: "hob",  icon: "🧙", desc: "Hobbit trilogy" },
  { name: "Jurassic World",      prefix: "jw",   icon: "🦕", desc: "JW / Jurassic Park" },
  { name: "Indiana Jones",       prefix: "iaj",  icon: "🎩", desc: "All movies" },
  { name: "Pirates Caribbean",   prefix: "poc",  icon: "☠️", desc: "POTC" },
  { name: "Legends of Chima",    prefix: "loc",  icon: "🦁", desc: "Chima" },
  { name: "Nexo Knights",        prefix: "nex",  icon: "🛡️", desc: "Nexo Knights" },
  { name: "Friends",             prefix: "frnd", icon: "👧", desc: "LEGO Friends" },
  { name: "Speed Champions",     prefix: "sc",   icon: "🏎️", desc: "Cars & drivers" },
  { name: "Monkie Kid",          prefix: "mk",   icon: "🐒", desc: "Monkie Kid" },
  { name: "City / Town",         prefix: "cty",  icon: "🏙️", desc: "City & Town" },
  { name: "Hidden Side",         prefix: "hs",   icon: "👻", desc: "Hidden Side" },
  { name: "Toy Story",           prefix: "toy",  icon: "🤠", desc: "Toy Story" },
  { name: "Castle",              prefix: "cas",  icon: "🏰", desc: "Classic Castle" },
  { name: "Batman Movie",        prefix: "bat",  icon: "🦇", desc: "LEGO Batman Movie" },
  { name: "Disney",              prefix: "dis",  icon: "🏰", desc: "Disney figs" },
  { name: "Minecraft",           prefix: "min",  icon: "⛏️", desc: "Minecraft" },
  { name: "Classic Space",       prefix: "sp",   icon: "🌌", desc: "Classic Space" },
  { name: "Classic Pirates",     prefix: "pi",   icon: "⚓", desc: "Classic Pirates" },
];

export default function BrowseScreen() {
  const navigation = useNavigation<any>();

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.header}>
        <Text style={styles.title}>📂 Browse by Theme</Text>
        <Text style={styles.subtitle}>{THEMES.length} themes in database</Text>
      </View>
      <FlatList
        data={THEMES}
        keyExtractor={(t) => t.prefix}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.row}
            onPress={() => navigation.navigate("Category", { theme: item })}
            activeOpacity={0.7}
          >
            <Text style={styles.icon}>{item.icon}</Text>
            <View style={styles.rowText}>
              <Text style={styles.name}>{item.name}</Text>
              <Text style={styles.desc}>{item.desc}</Text>
            </View>
            <Text style={styles.arrow}>›</Text>
          </TouchableOpacity>
        )}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#0f0f1a" },
  header: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#1a1a2e",
  },
  title: { fontSize: 22, fontWeight: "800", color: "#ffffff" },
  subtitle: { fontSize: 12, color: "#8888aa", marginTop: 2 },
  list: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 32 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#1a1a2e",
    borderRadius: 12,
    padding: 14,
    marginVertical: 4,
    borderWidth: 1,
    borderColor: "#2a2a3e",
  },
  icon: { fontSize: 24, width: 36 },
  rowText: { flex: 1, marginLeft: 8 },
  name: { fontSize: 15, fontWeight: "700", color: "#ffffff" },
  desc: { fontSize: 11, color: "#8888aa", marginTop: 2 },
  arrow: { fontSize: 20, color: "#7c7cff", fontWeight: "300" },
});
