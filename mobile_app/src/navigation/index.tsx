import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { Ionicons } from "@expo/vector-icons";

import HomeScreen from "../screens/HomeScreen";
import BrowseScreen from "../screens/BrowseScreen";
import CategoryScreen from "../screens/CategoryScreen";
import CollectionScreen from "../screens/CollectionScreen";
import SearchScreen from "../screens/SearchScreen";
import MinifigDetailScreen from "../screens/MinifigDetailScreen";

const Tab   = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

const SCREEN_OPTIONS = {
  headerStyle: { backgroundColor: "#0f0f1a" },
  headerTintColor: "#ffffff",
  headerTitleStyle: { fontWeight: "700" as const },
  contentStyle: { backgroundColor: "#0f0f1a" },
};

function BrowseStack() {
  return (
    <Stack.Navigator screenOptions={SCREEN_OPTIONS}>
      <Stack.Screen name="BrowseRoot" component={BrowseScreen} options={{ title: "Browse Themes" }} />
      <Stack.Screen name="Category"   component={CategoryScreen} />
      <Stack.Screen name="MinifigDetail" component={MinifigDetailScreen} options={{ title: "" }} />
    </Stack.Navigator>
  );
}

function HomeStack() {
  return (
    <Stack.Navigator screenOptions={SCREEN_OPTIONS}>
      <Stack.Screen name="HomeRoot" component={HomeScreen} options={{ headerShown: false }} />
      <Stack.Screen name="MinifigDetail" component={MinifigDetailScreen} options={{ title: "" }} />
    </Stack.Navigator>
  );
}

function CollectionStack() {
  return (
    <Stack.Navigator screenOptions={SCREEN_OPTIONS}>
      <Stack.Screen name="CollectionRoot" component={CollectionScreen} options={{ title: "My Collections" }} />
      <Stack.Screen name="MinifigDetail" component={MinifigDetailScreen} options={{ title: "" }} />
    </Stack.Navigator>
  );
}

function SearchStack() {
  return (
    <Stack.Navigator screenOptions={SCREEN_OPTIONS}>
      <Stack.Screen name="SearchRoot" component={SearchScreen} options={{ title: "Search" }} />
      <Stack.Screen name="MinifigDetail" component={MinifigDetailScreen} options={{ title: "" }} />
    </Stack.Navigator>
  );
}

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarStyle: {
            backgroundColor: "#0f0f1a",
            borderTopColor: "#1a1a2e",
            borderTopWidth: 1,
          },
          tabBarActiveTintColor: "#7c7cff",
          tabBarInactiveTintColor: "#555577",
          tabBarIcon: ({ focused, color, size }) => {
            const icons: Record<string, keyof typeof Ionicons.glyphMap> = {
              Home:       focused ? "home"          : "home-outline",
              Browse:     focused ? "grid"           : "grid-outline",
              Collection: focused ? "bookmark"       : "bookmark-outline",
              Search:     focused ? "search"         : "search-outline",
            };
            return <Ionicons name={icons[route.name] ?? "help"} size={size} color={color} />;
          },
        })}
      >
        <Tab.Screen name="Home"       component={HomeStack} />
        <Tab.Screen name="Browse"     component={BrowseStack} />
        <Tab.Screen name="Collection" component={CollectionStack} />
        <Tab.Screen name="Search"     component={SearchStack} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
