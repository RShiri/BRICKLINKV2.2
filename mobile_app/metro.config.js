const { getDefaultConfig } = require("expo/metro-config");

const config = getDefaultConfig(__dirname);

// Stub missing optional peer dependencies that Supabase references but doesn't need at runtime
config.resolver.extraNodeModules = {
  ...config.resolver.extraNodeModules,
  "@opentelemetry/api": require.resolve("./shims/opentelemetry-api.js"),
};

module.exports = config;
