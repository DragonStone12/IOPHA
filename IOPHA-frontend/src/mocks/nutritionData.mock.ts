import type { NutritionResponseData } from "../components/NutritionResponse/NutritionResponse";

export const MOCK_NUTRITION_RESPONSE: NutritionResponseData = {
  introText:
    "Based on your profile and current clinical guidelines, here are three evidence-based dietary adjustments most effective for your risk factors. Because your assessment noted irregular meal timing, aligning your eating window with your waking hours is particularly impactful.",
  tips: [
    {
      number: 1,
      title: "Time-restricted eating — 10-hour window",
      description:
        "Limit food intake to a consistent window such as 8 AM–6 PM. This alone reduces average daily caloric intake by 15–20% without strict counting and improves insulin sensitivity within 2 weeks.",
    },
    {
      number: 2,
      title: "Protein-first meals",
      description:
        "Begin each meal with 25–30g of lean protein (eggs, chicken, legumes). This slows gastric emptying, regulates appetite hormones, and reduces overall meal calories without hunger.",
    },
    {
      number: 3,
      title: "Eliminate liquid calories",
      description:
        "Replacing sweetened beverages with water, black coffee, or unsweetened tea removes an average of 350 excess calories per day — one of the highest-return single changes for your profile.",
    },
  ],
  physician: {
    id: "dr-chen",
    name: "Dr. Emily Chen, MD",
    specialty: "Obesity & Metabolic Medicine",
    distance: "1.8 miles",
    rating: 4.9,
    reviewCount: 234,
    nextAvailable: "Today, 3:30 PM",
    imageUrl:
      // eslint-disable-next-line no-secrets/no-secrets
      "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=200&h=200&fit=crop&auto=format",
  },
  followUpChips: [
    "Exercise tips",
    "Book Dr. Chen",
    "Sleep advice",
    "More nutrition guidance",
  ],
};
