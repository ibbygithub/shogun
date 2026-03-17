"use client";

import { useState } from "react";

interface Phrase {
  english: string;
  romaji: string;
  japanese: string;
}

interface Category {
  id: string;
  label: string;
  phrases: Phrase[];
}

const CATEGORIES: Category[] = [
  {
    id: "greetings",
    label: "Greetings",
    phrases: [
      { english: "Hello", romaji: "Konnichiwa", japanese: "こんにちは" },
      { english: "Good morning", romaji: "Ohayou gozaimasu", japanese: "おはようございます" },
      { english: "Thank you", romaji: "Arigatou gozaimasu", japanese: "ありがとうございます" },
      { english: "Excuse me / Sorry", romaji: "Sumimasen", japanese: "すみません" },
      { english: "You're welcome", romaji: "Dou itashimashite", japanese: "どういたしまして" },
      { english: "Yes / No", romaji: "Hai / Iie", japanese: "はい / いいえ" },
      { english: "Please [request]", romaji: "Onegaishimasu", japanese: "おねがいします" },
    ],
  },
  {
    id: "food",
    label: "Food",
    phrases: [
      { english: "This is delicious!", romaji: "Oishii!", japanese: "おいしい！" },
      { english: "Menu please", romaji: "Menyu wo kudasai", japanese: "メニューをください" },
      { english: "Check please", romaji: "Okaikei onegaishimasu", japanese: "おかいけいおねがいします" },
      { english: "I'll take this", romaji: "Kore wo kudasai", japanese: "これをください" },
      { english: "No spicy please", romaji: "Karai no wa nashi de", japanese: "からいのはなしで" },
      { english: "English menu?", romaji: "Eigo no menyu wa arimasu ka?", japanese: "えいごのメニューはありますか？" },
      { english: "I'm vegetarian", romaji: "Watashi wa bejitarian desu", japanese: "わたしはベジタリアンです" },
      { english: "No meat", romaji: "Niku wa nashi de", japanese: "にくはなしで" },
      { english: "Water please", romaji: "Omizu onegaishimasu", japanese: "おみずおねがいします" },
    ],
  },
  {
    id: "transit",
    label: "Transit",
    phrases: [
      { english: "Where is [X]?", romaji: "[X] wa doko desu ka?", japanese: "はどこですか？" },
      { english: "Which train to [X]?", romaji: "[X] yuki wa dore desu ka?", japanese: "ゆきはどれですか？" },
      { english: "One ticket to [X] please", romaji: "[X] made ichi-mai onegaishimasu", japanese: "まで一枚おねがいします" },
      { english: "Stop here please (taxi)", romaji: "Koko de tomete kudasai", japanese: "ここでとめてください" },
      { english: "How much?", romaji: "Ikura desu ka?", japanese: "いくらですか？" },
      { english: "Is this seat taken?", romaji: "Kono seki wa aite imasu ka?", japanese: "このせきはあいていますか？" },
    ],
  },
  {
    id: "shopping",
    label: "Shopping",
    phrases: [
      { english: "How much is this?", romaji: "Kore wa ikura desu ka?", japanese: "これはいくらですか？" },
      { english: "Do you accept cards?", romaji: "Kaado wa tsukaemasuka?", japanese: "カードはつかえますか？" },
      { english: "Too expensive", romaji: "Takai desu ne", japanese: "たかいですね" },
      { english: "Do you have a bag?", romaji: "Fukuro wa arimasu ka?", japanese: "ふくろはありますか？" },
      { english: "Can I try it on?", romaji: "Shichaku dekimasu ka?", japanese: "しちゃくできますか？" },
    ],
  },
  {
    id: "emergency",
    label: "Emergency",
    phrases: [
      { english: "Help!", romaji: "Tasukete!", japanese: "たすけて！" },
      { english: "Call an ambulance", romaji: "Kyukyusha wo yonde kudasai", japanese: "きゅうきゅうしゃをよんでください" },
      { english: "I need a doctor", romaji: "Isha ga hitsuyou desu", japanese: "いしゃがひつようです" },
      { english: "Police", romaji: "Keisatsu", japanese: "けいさつ" },
      { english: "Where is the hospital?", romaji: "Byouin wa doko desu ka?", japanese: "びょういんはどこですか？" },
      { english: "I lost my passport", romaji: "Pasupooto wo nakushimashita", japanese: "パスポートをなくしました" },
      { english: "I don't understand Japanese", romaji: "Nihongo ga wakarimasen", japanese: "にほんごがわかりません" },
    ],
  },
  {
    id: "nara",
    label: "Nara",
    phrases: [
      { english: "Deer crackers please", romaji: "Shika senbei wo kudasai", japanese: "しかせんべいをください" },
      { english: "Where is Todaiji?", romaji: "Toudaiji wa doko desu ka?", japanese: "とうだいじはどこですか？" },
    ],
  },
];

export default function PhrasesPage() {
  const [activeCategory, setActiveCategory] = useState("greetings");
  const [copied, setCopied] = useState<string | null>(null);

  const currentCategory = CATEGORIES.find((c) => c.id === activeCategory)!;

  function handleCopy(japanese: string) {
    navigator.clipboard.writeText(japanese).then(() => {
      setCopied(japanese);
      setTimeout(() => setCopied(null), 1500);
    }).catch(() => {
      // Clipboard not available — silently ignore
    });
  }

  return (
    <div style={{ padding: "1.5rem", maxWidth: "800px" }}>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 900, marginBottom: "0.25rem" }}>
        Japanese Phrases
      </h1>
      <p style={{ fontSize: "0.85rem", color: "#6b7280", marginBottom: "1.25rem" }}>
        Tap any card to copy the Japanese text to clipboard.
      </p>

      {/* Category tabs */}
      <div style={{
        display: "flex",
        gap: "0.4rem",
        flexWrap: "wrap",
        marginBottom: "1.25rem",
      }}>
        {CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            style={{
              padding: "0.4rem 0.9rem",
              borderRadius: "999px",
              border: "1px solid",
              borderColor: activeCategory === cat.id ? "#3b82f6" : "#e2e8f0",
              background: activeCategory === cat.id ? "#3b82f6" : "white",
              color: activeCategory === cat.id ? "white" : "#374151",
              fontWeight: activeCategory === cat.id ? 700 : 400,
              fontSize: "0.8rem",
              cursor: "pointer",
              transition: "all 0.15s",
            }}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Phrase cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
        {currentCategory.phrases.map((phrase) => {
          const isCopied = copied === phrase.japanese;
          return (
            <div
              key={phrase.english}
              onClick={() => handleCopy(phrase.japanese)}
              style={{
                background: isCopied ? "#f0fdf4" : "white",
                borderRadius: "10px",
                padding: "0.85rem 1rem",
                boxShadow: "0 1px 3px rgba(0,0,0,0.07)",
                cursor: "pointer",
                border: isCopied ? "1px solid #22c55e" : "1px solid #f1f5f9",
                transition: "all 0.15s",
                userSelect: "none",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div style={{ flex: 1 }}>
                  {/* English meaning — large */}
                  <div style={{ fontSize: "1rem", fontWeight: 700, color: "#111827", marginBottom: "0.2rem" }}>
                    {phrase.english}
                  </div>
                  {/* Romanization — medium, colored */}
                  <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "#2563eb", marginBottom: "0.15rem" }}>
                    {phrase.romaji}
                  </div>
                  {/* Japanese — small, grey */}
                  <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>
                    {phrase.japanese}
                  </div>
                </div>
                <div style={{
                  fontSize: "0.7rem",
                  color: isCopied ? "#16a34a" : "#94a3b8",
                  fontWeight: isCopied ? 700 : 400,
                  minWidth: "3rem",
                  textAlign: "right",
                  paddingTop: "0.1rem",
                }}>
                  {isCopied ? "Copied!" : "tap to copy"}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
