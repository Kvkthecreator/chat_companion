/**
 * Quiz Mode Data
 * - "What's Your Red Flag?" (Romantic Trope Quiz)
 * - "How Freaky Are You?" (Freak Level Quiz)
 */

import type { QuizQuestion, RomanticTrope } from "@/types";

// Freak Level type
export type FreakLevel = "vanilla" | "spicy" | "unhinged" | "feral" | "menace";

// Freak Level question type
export interface FreakQuizQuestion {
  id: number;
  question: string;
  options: { text: string; level: FreakLevel }[];
}

export const QUIZ_QUESTIONS: QuizQuestion[] = [
  {
    id: 1,
    question: "They finally text back after 6 hours. You:",
    options: [
      { text: "Wait exactly 6 hours and 1 minute to respond. Balance.", trope: "push_pull" },
      { text: "Already drafted 4 versions of your reply in Notes", trope: "slow_burn" },
      { text: '"Finally! I was starting to spiral" (send immediately)', trope: "all_in" },
      { text: "Check if they've been active elsewhere first", trope: "slow_reveal" },
      { text: "Wonder if this is the universe giving you a second chance", trope: "second_chance" },
    ],
  },
  {
    id: 2,
    question: "Your ex likes your Instagram story. You:",
    options: [
      { text: "Screenshot it and send to the group chat for analysis", trope: "slow_burn" },
      { text: "Already know what it means. Time to have The Talk.", trope: "all_in" },
      { text: "Like something of theirs back. The game is on.", trope: "push_pull" },
      { text: "Ignore it but check their profile 3 times that day", trope: "slow_reveal" },
      { text: "Feel a flutter. Maybe the timing is finally right?", trope: "second_chance" },
    ],
  },
  {
    id: 3,
    question: "On a first date, you're most likely to:",
    options: [
      { text: "Ask about their last relationship (for research purposes)", trope: "second_chance" },
      { text: "Tell them you're having a great time. Out loud. With words.", trope: "all_in" },
      { text: "Tease them until they're slightly confused but intrigued", trope: "push_pull" },
      { text: "Give them just enough to want a second date", trope: "slow_reveal" },
      { text: "Enjoy the tension of not knowing where this is going", trope: "slow_burn" },
    ],
  },
  {
    id: 4,
    question: "When you catch feelings, you:",
    options: [
      { text: "Tell them. Life's too short for games.", trope: "all_in" },
      { text: "Create situations to see if they feel it too", trope: "push_pull" },
      { text: "Sit with it for weeks before doing anything", trope: "slow_burn" },
      { text: "Drop hints and see if they're paying attention", trope: "slow_reveal" },
      { text: "Wonder if this is fate correcting a past mistake", trope: "second_chance" },
    ],
  },
  {
    id: 5,
    question: "Your biggest dating dealbreaker is someone who:",
    options: [
      { text: "Rushes things before the tension has time to build", trope: "slow_burn" },
      { text: "Plays too hard to get (that's YOUR move)", trope: "push_pull" },
      { text: "Can't handle emotional honesty", trope: "all_in" },
      { text: "Asks too many questions too soon", trope: "slow_reveal" },
      { text: "Refuses to believe people can change", trope: "second_chance" },
    ],
  },
  {
    id: 6,
    question: "Your ideal rom-com moment:",
    options: [
      { text: "Running into your ex at a wedding, both single", trope: "second_chance" },
      { text: "The slow realization after years of friendship", trope: "slow_burn" },
      { text: "Confessing your feelings in the rain, no hesitation", trope: "all_in" },
      { text: "The enemies-to-lovers arc where banter becomes more", trope: "push_pull" },
      { text: "They finally see the real you after breaking down your walls", trope: "slow_reveal" },
    ],
  },
];

/**
 * Calculate the result trope from quiz answers
 */
export function calculateTrope(answers: Record<number, RomanticTrope>): RomanticTrope {
  const scores: Record<RomanticTrope, number> = {
    slow_burn: 0,
    second_chance: 0,
    all_in: 0,
    push_pull: 0,
    slow_reveal: 0,
  };

  let lastAnswered: RomanticTrope = "slow_burn";

  for (const trope of Object.values(answers)) {
    scores[trope]++;
    lastAnswered = trope;
  }

  // Find max score
  const maxScore = Math.max(...Object.values(scores));
  const winners = Object.entries(scores)
    .filter(([, score]) => score === maxScore)
    .map(([trope]) => trope as RomanticTrope);

  // Single winner - return it
  if (winners.length === 1) {
    return winners[0];
  }

  // Tie-breaker 1: last answered wins if it's among the winners
  if (winners.includes(lastAnswered)) {
    return lastAnswered;
  }

  // Tie-breaker 2: random selection among winners (for fairness)
  return winners[Math.floor(Math.random() * winners.length)];
}

/**
 * Trope result content - elaborate version inspired by 16personalities/BuzzFeed
 */
export const TROPE_CONTENT: Record<RomanticTrope, {
  title: string;
  tagline: string;
  description: string;
  shareText: string;
  // New elaborate sections
  inRelationships: string;
  strengths: string[];
  challenges: string[];
  advice: string;
  compatibleWith: RomanticTrope[];
  yourPeople: string[];
}> = {
  slow_burn: {
    title: "SLOW BURN",
    tagline: "the tension is the whole point and you know it",
    description: "You'd rather wait three seasons for a kiss than rush it. You've said \"I just think it's better when it builds\" at least once this month. Eye contact across a room? That's your whole love language.",
    shareText: "I'm a SLOW BURN — the tension is the whole point. What's yours?",
    inRelationships: "You're the person who makes every glance feel loaded. You don't rush because you genuinely believe the buildup is where the magic happens. Your partners often say they didn't realize they were falling until they'd already fallen.",
    strengths: [
      "You create anticipation that makes everything feel more meaningful",
      "You're patient and observant — you notice the little things",
      "When you finally commit, it's deep and considered",
    ],
    challenges: [
      "Sometimes you wait so long the moment passes",
      "Partners can misread your patience as disinterest",
      "You might overthink instead of just feeling",
    ],
    advice: "Not everything needs to marinate. Sometimes the best things happen when you let yourself be surprised.",
    compatibleWith: ["slow_reveal", "push_pull"],
    yourPeople: ["darcy & elizabeth", "jim & pam", "connell & marianne"],
  },
  second_chance: {
    title: "SECOND CHANCE",
    tagline: "you never really closed that chapter, did you",
    description: "You still think about the one that got away. Not in a sad way — in a \"the timing was just wrong\" way. You believe some people are meant to find their way back to each other.",
    shareText: "I'm a SECOND CHANCE — some stories deserve a sequel. What's yours?",
    inRelationships: "You're a romantic who believes in fate and timing. You see potential where others see endings. Your exes probably still have a soft spot for you because you never really burn bridges — you just... postpone crossings.",
    strengths: [
      "You see the best in people, even when they've let you down",
      "You're forgiving and believe in growth",
      "You bring depth to relationships because you understand history matters",
    ],
    challenges: [
      "You might romanticize the past instead of seeing it clearly",
      "New partners can feel like they're competing with ghosts",
      "You risk missing what's in front of you while looking backward",
    ],
    advice: "Some chapters close for a reason. The best sequel might be with someone entirely new.",
    compatibleWith: ["all_in", "slow_burn"],
    yourPeople: ["mia & sebastian", "noah & allie", "jesse & céline"],
  },
  all_in: {
    title: "ALL IN",
    tagline: "when you know, you know — and you KNEW",
    description: "You don't do slow. You don't do games. When you feel it, you say it, and honestly? That's terrifying to most people. You've been called \"intense\" like it's a bad thing. It's not.",
    shareText: "I'm ALL IN — when I know, I know. What's yours?",
    inRelationships: "You're the person who texts back immediately and doesn't apologize for it. You bring your whole heart to the table from day one. Some people find it overwhelming; the right person finds it refreshing.",
    strengths: [
      "You're brave — you put yourself out there when others hide",
      "No one ever has to guess how you feel",
      "You create deep connections fast because you're genuinely present",
    ],
    challenges: [
      "Your intensity can scare people off before they get to know you",
      "You might invest heavily in people who haven't earned it yet",
      "Rejection hits you harder because you were never holding back",
    ],
    advice: "Your openness is a gift, not a flaw. But matching energy matters — save your full heart for people who show up.",
    compatibleWith: ["second_chance", "slow_reveal"],
    yourPeople: ["rachel & nick", "lara jean & peter", "jake & amy"],
  },
  push_pull: {
    title: "PUSH & PULL",
    tagline: "you want them to work for it (and you'll work for it too)",
    description: "Hot then cold. Close then distant. It's not games — it's tension, and you're fluent in it. You flirt by arguing. You show love by teasing. The chase is half the fun.",
    shareText: "I'm PUSH & PULL — the chase is half the fun. What's yours?",
    inRelationships: "You keep things interesting. Your partners never quite know what they're going to get, and that's exactly why they stick around. You need someone who can match your energy — and challenge it.",
    strengths: [
      "You keep the spark alive long after the honeymoon phase",
      "You're never boring — every day feels a little different",
      "You understand that attraction needs friction",
    ],
    challenges: [
      "Some partners just want consistency, not a rollercoaster",
      "Your signals can be genuinely confusing",
      "You might create drama when things get too comfortable",
    ],
    advice: "Tension is exciting, but stability isn't the enemy. The best relationships have both.",
    compatibleWith: ["slow_burn", "push_pull"],
    yourPeople: ["kat & patrick", "jess & nick", "lorelai & luke"],
  },
  slow_reveal: {
    title: "SLOW REVEAL",
    tagline: "they have to earn the real you",
    description: "You're not cold — you're careful. There's a version of you that most people get, and then there's the version that only comes out when someone proves they're paying attention.",
    shareText: "I'm a SLOW REVEAL — you have to earn the real me. What's yours?",
    inRelationships: "You're a puzzle worth solving. You test people without them knowing, rewarding curiosity and punishing assumptions. When someone finally sees the real you, they feel like they've won something.",
    strengths: [
      "You protect your energy — not everyone deserves access",
      "The people who stick around really know you",
      "You create deep intimacy through gradual trust",
    ],
    challenges: [
      "People might give up before they get to the good parts",
      "You can seem distant even when you're interested",
      "Your walls might be protecting you from the wrong things",
    ],
    advice: "Mystery is magnetic, but someone has to get in eventually. Consider letting the right people see you sooner.",
    compatibleWith: ["slow_burn", "all_in"],
    yourPeople: ["jane & rochester", "fleabag & the priest", "bella & edward"],
  },
};

// =============================================================================
// FREAK LEVEL QUIZ - "How Freaky Are You?"
// =============================================================================

export const FREAK_QUIZ_QUESTIONS: FreakQuizQuestion[] = [
  {
    id: 1,
    question: "Someone cute asks what you're into. You say:",
    options: [
      { text: "I'm pretty normal, honestly", level: "vanilla" },
      { text: "Depends on the vibe... why, what are YOU into?", level: "spicy" },
      { text: "How much time do you have?", level: "unhinged" },
      { text: "*just stares silently until they get nervous*", level: "feral" },
      { text: "I'll show you. Clear your schedule.", level: "menace" },
    ],
  },
  {
    id: 2,
    question: "Your browser history is:",
    options: [
      { text: "Recipes and weather. I'm a simple person.", level: "vanilla" },
      { text: "Fine... mostly. We don't talk about that one tab.", level: "spicy" },
      { text: "In incognito mode permanently for a reason", level: "unhinged" },
      { text: "A liability in at least 3 states", level: "feral" },
      { text: "I AM the thing people are searching for", level: "menace" },
    ],
  },
  {
    id: 3,
    question: "Your friends come to you for advice about:",
    options: [
      { text: "Normal stuff. Career, relationships, life.", level: "vanilla" },
      { text: "Slightly spicier stuff they can't ask anyone else", level: "spicy" },
      { text: "Things they're too embarrassed to Google", level: "unhinged" },
      { text: "Situations that require me to ask 'legally speaking, or...'", level: "feral" },
      { text: "They don't ask. They know I'll volunteer.", level: "menace" },
    ],
  },
  {
    id: 4,
    question: "At a party, you're the one who:",
    options: [
      { text: "Leaves by 10pm after good conversations", level: "vanilla" },
      { text: "Stays until things get interesting", level: "spicy" },
      { text: "IS the reason things got interesting", level: "unhinged" },
      { text: "Somehow ends up in a restricted area", level: "feral" },
      { text: "Gets invited specifically because of what happened last time", level: "menace" },
    ],
  },
  {
    id: 5,
    question: "Your 'type' is best described as:",
    options: [
      { text: "Kind, stable, good communicator", level: "vanilla" },
      { text: "A little mysterious, keeps me guessing", level: "spicy" },
      { text: "Probably concerning if I'm being honest", level: "unhinged" },
      { text: "Anyone my parents would hate", level: "feral" },
      { text: "I don't have a type. Types have me.", level: "menace" },
    ],
  },
  {
    id: 6,
    question: "When someone says 'we need to talk', you think:",
    options: [
      { text: "Uh oh, something's wrong", level: "vanilla" },
      { text: "This better be about something good", level: "spicy" },
      { text: "Which thing did they find out about?", level: "unhinged" },
      { text: "Finally, someone ready to match my energy", level: "feral" },
      { text: "Yes. Yes we do. *cracks knuckles*", level: "menace" },
    ],
  },
];

/**
 * Freak Level result content
 */
export const FREAK_CONTENT: Record<FreakLevel, {
  title: string;
  tagline: string;
  description: string;
  shareText: string;
  emoji: string;
  color: string;
  yourPeople: string[];
}> = {
  vanilla: {
    title: "VANILLA BEAN",
    tagline: "you like what you like and that's valid",
    description: "You're classic, comfortable, and confident in your preferences. While others are out here doing the most, you know that sometimes the original flavor hits different. You've perfected the basics and honestly? That's a skill. Not everyone can make simple feel this good.",
    shareText: "I'm VANILLA BEAN — classic never goes out of style. How freaky are you?",
    emoji: "🍦",
    color: "text-amber-100",
    yourPeople: ["the friend who leaves parties at 10", "your most normal coworker", "someone's wholesome aunt"],
  },
  spicy: {
    title: "SPICY CURIOUS",
    tagline: "one foot in comfort, one foot in chaos",
    description: "You're not vanilla, but you're not fully unhinged either. You like to keep things interesting without going off the deep end. You'll try something new if the vibe is right, but you also appreciate a good classic. The perfect blend of adventurous and sensible.",
    shareText: "I'm SPICY CURIOUS — adventurous with a safety net. How freaky are you?",
    emoji: "🌶️",
    color: "text-orange-400",
    yourPeople: ["the 'convince me' friend", "spicy margarita orderers", "people who say 'I'm not usually like this'"],
  },
  unhinged: {
    title: "CASUALLY UNHINGED",
    tagline: "you've seen things. you've done things.",
    description: "Your browser history would make your therapist take notes. You've got stories you'll only tell after the third drink. You're not trying to shock anyone — this is just how you're wired. Normal is a setting on a washing machine, and you don't do laundry.",
    shareText: "I'm CASUALLY UNHINGED — my therapist takes notes. How freaky are you?",
    emoji: "🔥",
    color: "text-red-500",
    yourPeople: ["the friend with concerning stories", "that one coworker", "main characters in HBO shows"],
  },
  feral: {
    title: "ABSOLUTELY FERAL",
    tagline: "you are the intrusive thought",
    description: "You don't have intrusive thoughts — you ARE the intrusive thought. Your friends come to you for advice they're too scared to Google. You've probably been banned from something. You exist in a space beyond judgment, and honestly? We respect it.",
    shareText: "I'm ABSOLUTELY FERAL — I AM the intrusive thought. How freaky are you?",
    emoji: "👹",
    color: "text-purple-500",
    yourPeople: ["cryptids", "people with alt accounts", "everyone's 'wild' phase personified"],
  },
  menace: {
    title: "CERTIFIED MENACE",
    tagline: "the devil takes notes from you",
    description: "You're not just freaky — you're a lifestyle. Your energy could power a small city. When you walk into a room, the vibe shifts permanently. You've transcended categories entirely. At this point, you're not participating in the quiz, the quiz is studying you.",
    shareText: "I'm a CERTIFIED MENACE — the devil takes notes from me. How freaky are you?",
    emoji: "😈",
    color: "text-fuchsia-600",
    yourPeople: ["the devil on your shoulder", "that friend you can't take anywhere", "chaos incarnate"],
  },
};

/**
 * Freak Level visual metadata for UI
 */
export const FREAK_VISUALS: Record<FreakLevel, { emoji: string; color: string; gradient: string }> = {
  vanilla: {
    emoji: "🍦",
    color: "text-amber-100",
    gradient: "from-amber-500/20 to-yellow-500/20",
  },
  spicy: {
    emoji: "🌶️",
    color: "text-orange-400",
    gradient: "from-orange-500/20 to-red-500/20",
  },
  unhinged: {
    emoji: "🔥",
    color: "text-red-500",
    gradient: "from-red-500/20 to-rose-500/20",
  },
  feral: {
    emoji: "👹",
    color: "text-purple-500",
    gradient: "from-purple-500/20 to-violet-500/20",
  },
  menace: {
    emoji: "😈",
    color: "text-fuchsia-600",
    gradient: "from-fuchsia-500/20 to-pink-500/20",
  },
};
