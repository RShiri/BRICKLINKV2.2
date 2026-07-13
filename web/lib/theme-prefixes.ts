/**
 * Curated theme registry: maps URL slugs to BrickLink minifig-id prefixes.
 * Mirrors the legacy Streamlit theme pages (pages/04..23) plus the
 * keyword-classified Marvel/DC views (pages/1_Marvel.py / 2_DC.py) — the
 * items table is keyed by BrickLink ids, so prefix queries stay the backbone.
 */
export type ThemeDef = {
  slug: string;
  name: string;
  prefix: string;
  icon: string;
  description: string;
  /** 'marvel' | 'dc' apply the keyword classifier on top of the sh prefix. */
  classifier?: "marvel" | "dc";
};

export const THEMES: ThemeDef[] = [
  { slug: "marvel", name: "Marvel", prefix: "sh", icon: "🦸", description: "Marvel Universe minifigures", classifier: "marvel" },
  { slug: "dc", name: "DC", prefix: "sh", icon: "🦇", description: "DC Universe minifigures", classifier: "dc" },
  { slug: "star-wars", name: "Star Wars", prefix: "sw", icon: "🚀", description: "A galaxy far, far away" },
  { slug: "harry-potter", name: "Harry Potter", prefix: "hp", icon: "⚡", description: "The Wizarding World" },
  { slug: "ninjago", name: "Ninjago", prefix: "njo", icon: "🐉", description: "Masters of Spinjitzu" },
  { slug: "cmf", name: "Collectible Minifigs", prefix: "col", icon: "🎭", description: "Collectible Minifigure series" },
  { slug: "lego-movie", name: "The LEGO Movie", prefix: "tlm", icon: "🎬", description: "Everything is awesome" },
  { slug: "lord-of-the-rings", name: "Lord of the Rings", prefix: "lor", icon: "💍", description: "Middle-earth" },
  { slug: "hobbit", name: "The Hobbit", prefix: "hob", icon: "🧙", description: "An unexpected journey" },
  { slug: "jurassic-world", name: "Jurassic World", prefix: "jw", icon: "🦕", description: "Dinosaurs and DNA" },
  { slug: "indiana-jones", name: "Indiana Jones", prefix: "iaj", icon: "🎩", description: "Archaeological adventures" },
  { slug: "pirates-caribbean", name: "Pirates of the Caribbean", prefix: "poc", icon: "🏴‍☠️", description: "On stranger tides" },
  { slug: "chima", name: "Legends of Chima", prefix: "loc", icon: "🦁", description: "The power of CHI" },
  { slug: "nexo-knights", name: "Nexo Knights", prefix: "nex", icon: "🛡️", description: "Knights of Knighton" },
  { slug: "elves", name: "Elves", prefix: "elf", icon: "🧝", description: "Elvendale magic" },
  { slug: "friends", name: "Friends", prefix: "frnd", icon: "👧", description: "Heartlake City" },
  { slug: "toy-story", name: "Toy Story", prefix: "toy", icon: "🤠", description: "To infinity and beyond" },
  { slug: "speed-champions", name: "Speed Champions", prefix: "sc", icon: "🏎️", description: "Racing legends" },
  { slug: "hidden-side", name: "Hidden Side", prefix: "hs", icon: "👻", description: "Ghost hunting" },
  { slug: "monkie-kid", name: "Monkie Kid", prefix: "mk", icon: "🐒", description: "Legends of the Monkey King" },
  { slug: "city", name: "City / Town", prefix: "cty", icon: "🏙️", description: "Everyday heroes" },
  { slug: "superheroes", name: "All Superheroes", prefix: "sh", icon: "🌐", description: "Marvel + DC combined" },
];

export function themeBySlug(slug: string): ThemeDef | undefined {
  return THEMES.find((t) => t.slug === slug);
}

/* Keyword classifiers ported from pages/1_Marvel.py and pages/2_DC.py. */

export const MARVEL_KEYWORDS = [
  "spider", "iron man", "captain america", "thor", "hulk", "black widow", "hawkeye",
  "avengers", "guardians", "star-lord", "groot", "rocket", "gamora", "drax",
  "ant-man", "wasp", "doctor strange", "scarlet witch", "vision", "falcon",
  "winter soldier", "black panther", "deadpool", "wolverine", "x-men", "cyclops",
  "storm", "magneto", "professor x", "venom", "carnage", "thanos", "loki",
  "ultron", "nebula", "war machine", "nick fury", "maria hill", "agent",
  "daredevil", "punisher", "jessica jones", "luke cage", "iron fist",
  "fantastic four", "thing", "human torch", "mr. fantastic", "invisible woman",
  "silver surfer", "galactus", "doctor doom", "green goblin", "doc ock",
  "sandman", "mysterio", "vulture", "shocker", "rhino", "scorpion",
  "miles morales", "gwen stacy", "spider-gwen", "silk", "prowler",
  "shang-chi", "ms. marvel", "kamala khan", "she-hulk", "moon knight",
  "blade", "ghost rider", "elektra", "kingpin", "bullseye",
  "peter parker", "tony stark", "rescue", "pepper potts", "aim agent", "chitauri",
  "outrider", "surtur", "hela", "valkyrie", "korg", "miek", "heimdall", "odin",
  "bruce banner", "steve rogers", "natasha romanoff", "clint barton", "wanda maximoff",
  "pietro maximoff", "quicksilver", "sam wilson", "bucky barnes", "t'challa", "shuri",
  "okoye", "nakia", "killmonger", "m'baku", "klaue", "crossbones", "zemo", "red skull",
  "arnim zola", "mandarin", "aldrich killian", "justin hammer", "whiplash", "obadiah stane",
  "iron monger", "abomination", "leader", "yellowjacket", "ghost", "taskmaster",
  "red guardian", "yelena belova", "melina vostokoff", "agatha harkness", "kang",
  "modok", "high evolutionary", "adam warlock", "kang the conqueror",
];

export const DC_KEYWORDS = [
  "batman", "robin", "joker", "harley quinn", "catwoman", "penguin", "riddler",
  "two-face", "bane", "poison ivy", "mr. freeze", "scarecrow", "ra's al ghul",
  "superman", "supergirl", "lex luthor", "general zod", "brainiac", "doomsday",
  "wonder woman", "aquaman", "flash", "green lantern", "cyborg", "shazam",
  "green arrow", "black canary", "nightwing", "batgirl", "deathstroke",
  "teen titans", "raven", "starfire", "beast boy", "justice league", "suicide squad",
  "deadshot", "killer croc", "captain boomerang", "enchantress", "el diablo", "katana",
  "rick flag", "darkseid", "steppenwolf", "parademons", "apokolips", "martian manhunter",
  "hawkman", "hawkgirl", "atom", "firestorm", "blue beetle", "booster gold", "zatanna",
  "constantine", "lobo", "swamp thing", "plastic man", "mera", "ocean master",
  "black adam", "sinestro", "atrocitus", "larfleeze", "reverse flash", "captain cold",
  "heatwave", "weather wizard", "gorilla grodd", "cheetah", "ares", "circe", "giganta",
];

const MARVEL_ID_OVERRIDES = new Set([
  "sh0569", "sh0570", "sh0571", "sh0572", "sh0573", "sh0574", "sh0575", "sh0578",
  "sh0580", "sh0582", "sh0584", "sh0601", "sh0610", "sh0613", "sh0615", "sh0616",
  "sh0618", "sh0620", "sh0622", "sh0624", "sh0625", "sh0626", "sh0627",
]);

function matchesAny(name: string, keywords: string[]): boolean {
  return keywords.some((k) =>
    new RegExp(`\\b${k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`).test(name),
  );
}

export function classifyUniverse(itemId: string, name: string): "marvel" | "dc" | null {
  const lower = name.toLowerCase();
  if (MARVEL_ID_OVERRIDES.has(itemId)) return "marvel";
  let isMarvel = matchesAny(lower, MARVEL_KEYWORDS);
  let isDc = matchesAny(lower, DC_KEYWORDS);
  if (lower.includes("red hood") && lower.includes("spider")) isDc = false;
  if (isMarvel && !isDc) return "marvel";
  if (isDc && !isMarvel) return "dc";
  if (isMarvel && isDc) return "dc"; // DC blocklist wins, as in the legacy page
  return null;
}
