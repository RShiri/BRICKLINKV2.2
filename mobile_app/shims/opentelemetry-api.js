// Stub for @opentelemetry/api — required by @supabase/supabase-js but not used at runtime
module.exports = {
  trace: { getTracer: () => ({}) },
  context: {},
  propagation: {},
  diag: { setLogger: () => {} },
};
