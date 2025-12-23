/**
 * Quiz Mode Data v3.0
 *
 * Two distinct quiz types optimized for different viral mechanics:
 *
 * 1. Dating Personality Test (romantic_trope)
 *    - Primary mechanic: Identity validation ("this is so me")
 *    - Reveals patterns, not preferences
 *    - Tone: Therapist who said something uncomfortable
 *
 * 2. The Unhinged Test (freak_level)
 *    - Primary mechanic: Social comparison ("what did you get?")
 *    - Pure entertainment, spectrum ranking
 *    - Tone: Chaotic friend with no filter
 */

import type { QuizQuestion, RomanticTrope } from "@/types";

// =============================================================================
// DATING PERSONALITY TEST - Identity Validation
// "What's Your Dating Pattern?"
// =============================================================================

export const QUIZ_QUESTIONS: QuizQuestion[] = [
  {
    id: 1,
    question: "You pull away when things get good because:",
    options: [
      { text: "If I don't expect much, I can't be disappointed", trope: "slow_burn" },
      { text: "What if this isn't as good as what I had before?", trope: "second_chance" },
      { text: "I'd rather leave than be left", trope: "all_in" },
      { text: "I need to know they'll chase me", trope: "push_pull" },
      { text: "They don't really know me yet — what if they won't like what they find?", trope: "slow_reveal" },
    ],
  },
  {
    id: 2,
    question: "When someone says 'I love you' first, your honest reaction is:",
    options: [
      { text: "Finally. I've been waiting to say it too.", trope: "all_in" },
      { text: "I need to think about what this means", trope: "slow_burn" },
      { text: "Do they mean it the way my ex meant it?", trope: "second_chance" },
      { text: "Now I feel like I have to say it back and I hate that", trope: "push_pull" },
      { text: "Do they even know who they're saying it to?", trope: "slow_reveal" },
    ],
  },
  {
    id: 3,
    question: "You've sabotaged something good because:",
    options: [
      { text: "I got scared of how much I wanted it", trope: "slow_burn" },
      { text: "I kept comparing them to someone from my past", trope: "second_chance" },
      { text: "I showed too much too fast and it felt unsafe", trope: "all_in" },
      { text: "It was getting too predictable", trope: "push_pull" },
      { text: "They started asking questions I wasn't ready to answer", trope: "slow_reveal" },
    ],
  },
  {
    id: 4,
    question: "The real reason you're single (be honest):",
    options: [
      { text: "I'd rather be alone than settle for less than the real thing", trope: "slow_burn" },
      { text: "I'm not over someone I probably should be over by now", trope: "second_chance" },
      { text: "My 'all or nothing' approach scares people off", trope: "all_in" },
      { text: "I lose interest once someone actually likes me back", trope: "push_pull" },
      { text: "I haven't met someone I trust enough to really let in", trope: "slow_reveal" },
    ],
  },
  {
    id: 5,
    question: "What you want people to think vs. what's actually true:",
    options: [
      { text: "They think I'm patient. Actually, I'm terrified of wanting something I might not get.", trope: "slow_burn" },
      { text: "They think I'm romantic. Actually, I'm stuck on someone who wasn't right.", trope: "second_chance" },
      { text: "They think I'm intense. Actually, I'm just tired of pretending I don't care.", trope: "all_in" },
      { text: "They think I'm playing games. Actually, I'm testing if they'll stay.", trope: "push_pull" },
      { text: "They think I'm mysterious. Actually, I'm scared of being fully known.", trope: "slow_reveal" },
    ],
  },
  {
    id: 6,
    question: "The pattern you keep repeating even though you know better:",
    options: [
      { text: "Waiting until I'm 'sure' — and by then, they've moved on", trope: "slow_burn" },
      { text: "Reaching out to exes when I'm lonely", trope: "second_chance" },
      { text: "Going all in before I know if they're worth it", trope: "all_in" },
      { text: "Creating problems when things get too comfortable", trope: "push_pull" },
      { text: "Shutting down whenever someone gets too close", trope: "slow_reveal" },
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

  const maxScore = Math.max(...Object.values(scores));
  const winners = Object.entries(scores)
    .filter(([, score]) => score === maxScore)
    .map(([trope]) => trope as RomanticTrope);

  if (winners.length === 1) {
    return winners[0];
  }

  if (winners.includes(lastAnswered)) {
    return lastAnswered;
  }

  return winners[Math.floor(Math.random() * winners.length)];
}

/**
 * Dating Personality Test - v3.0 Content
 * Focus: Identity validation, psychological insight
 * Tone: Therapist who said something uncomfortable
 */
export const TROPE_CONTENT: Record<RomanticTrope, {
  title: string;
  tagline: string;
  pattern: string;
  theTruth: string;
  youTellYourself: string;
  butActually: string;
  whatYouNeed: string;
  shareText: string;
}> = {
  slow_burn: {
    title: "SLOW BURN",
    tagline: "you use patience as protection",
    pattern: "You've made waiting into an art form — but it's not patience. It's armor.",
    theTruth: "You're not 'taking it slow' because you value the buildup. You're taking it slow because wanting something terrifies you. Every time you say 'I just want to be sure,' what you mean is 'I can't handle being the one who wanted it more.' You've convinced yourself that hesitation is wisdom. It's not. It's fear dressed up as standards.",
    youTellYourself: "I just like when things develop naturally.",
    butActually: "You're terrified of wanting something you might not get. So you've made 'patience' your whole personality.",
    whatYouNeed: "To risk wanting something before you know if it's safe.",
    shareText: "I'm a SLOW BURN — apparently I use patience as protection. What's your dating pattern?",
  },
  second_chance: {
    title: "SECOND CHANCE",
    tagline: "you romanticize potential over reality",
    pattern: "You're not holding out for the right person — you're holding onto the wrong one.",
    theTruth: "You say you 'believe in timing' but what you actually believe in is avoiding closure. The person you keep thinking about? They're not unfinished business — they're a safe place to put your feelings so you never have to risk them on someone new. You're not romantic. You're stuck. And you're using the past as an excuse to not show up for the present.",
    youTellYourself: "Some love stories just take time to get right.",
    butActually: "You'd rather stay loyal to a memory than risk being disappointed by reality.",
    whatYouNeed: "To grieve it properly so you can actually move on.",
    shareText: "I'm a SECOND CHANCE — I romanticize potential over reality. What's your dating pattern?",
  },
  all_in: {
    title: "ALL IN",
    tagline: "you use vulnerability as armor",
    pattern: "You show everything upfront — not because you're brave, but because rejection early hurts less than rejection later.",
    theTruth: "You call it 'being authentic' but it's actually a defense mechanism. By going all in immediately, you control the rejection. If they leave, at least it was on your terms. If they stay, they can't say they didn't know what they were getting into. You've weaponized honesty so you never have to feel blindsided. That's not intimacy — it's a preemptive strike.",
    youTellYourself: "I just don't believe in playing games.",
    butActually: "You go all in early because if they reject you, you can tell yourself they never had a chance to really hurt you.",
    whatYouNeed: "To let someone earn your vulnerability instead of handing it over like a test.",
    shareText: "I'm ALL IN — I use vulnerability as armor. What's your dating pattern?",
  },
  push_pull: {
    title: "PUSH & PULL",
    tagline: "you create distance to test closeness",
    pattern: "You call it 'keeping things interesting.' It's actually a loyalty test nobody signed up for.",
    theTruth: "Every time you pull away, you're checking if they'll follow. Every time you push, you're seeing if they'll stay. You've turned relationships into an obstacle course and you're keeping score. The problem? Even when they pass your tests, you don't trust it. You just design a harder one. You're not afraid of boredom — you're afraid of what happens when there's nothing left to hide behind.",
    youTellYourself: "I need someone who can handle me.",
    butActually: "You create chaos because stability feels like a trap — or worse, like they've stopped caring.",
    whatYouNeed: "To learn that someone staying without drama doesn't mean they're not trying.",
    shareText: "I'm PUSH & PULL — I create distance to test closeness. What's your dating pattern?",
  },
  slow_reveal: {
    title: "SLOW REVEAL",
    tagline: "you make people earn access as a defense",
    pattern: "You're not mysterious. You're scared of what happens when someone actually sees you.",
    theTruth: "You tell yourself that you're 'selective' about who gets the real you. But the truth is, you've decided that being fully known is the same as being fully vulnerable — and vulnerability feels like handing someone a weapon. So you parcel yourself out in pieces, testing each time to see if they'll use it against you. By the time someone finally 'earns' the real you, you've already exhausted them.",
    youTellYourself: "The right person will be patient enough to wait.",
    butActually: "You withhold yourself because you've decided that being truly known means being truly rejected.",
    whatYouNeed: "To risk being seen before you're sure it's safe.",
    shareText: "I'm a SLOW REVEAL — I make people earn access as a defense. What's your dating pattern?",
  },
};


// =============================================================================
// THE UNHINGED TEST - Social Comparison
// "How Unhinged Are You?"
// =============================================================================

export type FreakLevel = "vanilla" | "spicy" | "unhinged" | "feral" | "menace";

export interface FreakQuizQuestion {
  id: number;
  question: string;
  options: { text: string; level: FreakLevel }[];
}

export const FREAK_QUIZ_QUESTIONS: FreakQuizQuestion[] = [
  {
    id: 1,
    question: "It's 2am and you can't sleep. You:",
    options: [
      { text: "Read a book until you're tired", level: "vanilla" },
      { text: "Scroll through your ex's LinkedIn", level: "spicy" },
      { text: "Send a risky text you'll regret", level: "unhinged" },
      { text: "Reorganize your entire room then order food", level: "feral" },
      { text: "Start a group chat argument about nothing", level: "menace" },
    ],
  },
  {
    id: 2,
    question: "Your ex's new partner follows you. You:",
    options: [
      { text: "Ignore it and move on", level: "vanilla" },
      { text: "Check their profile once (okay, twice)", level: "spicy" },
      { text: "Follow them back and like a strategic post", level: "unhinged" },
      { text: "Screenshot and send to the group chat immediately", level: "feral" },
      { text: "Post your best content for the next 72 hours straight", level: "menace" },
    ],
  },
  {
    id: 3,
    question: "The group chat has been quiet for 3 hours. You:",
    options: [
      { text: "Enjoy the peace", level: "vanilla" },
      { text: "Send a meme to test the waters", level: "spicy" },
      { text: "Drop a controversial take to start chaos", level: "unhinged" },
      { text: "Send 'we need to talk' with no context", level: "feral" },
      { text: "Create a poll ranking everyone in the chat", level: "menace" },
    ],
  },
  {
    id: 4,
    question: "You're slightly tipsy and have your phone. You:",
    options: [
      { text: "Put it away to avoid mistakes", level: "vanilla" },
      { text: "Text your crush something flirty", level: "spicy" },
      { text: "Post a story you'll delete by morning", level: "unhinged" },
      { text: "Send voice notes to everyone you know", level: "feral" },
      { text: "Start planning a trip nobody asked for", level: "menace" },
    ],
  },
  {
    id: 5,
    question: "Someone says 'I have tea.' You:",
    options: [
      { text: "Wait for them to share when ready", level: "vanilla" },
      { text: "Ask 'who is it about' immediately", level: "spicy" },
      { text: "Guess every possible scenario out loud", level: "unhinged" },
      { text: "Demand voice note evidence NOW", level: "feral" },
      { text: "Already have more tea than they do somehow", level: "menace" },
    ],
  },
  {
    id: 6,
    question: "Your screen time report comes in. You:",
    options: [
      { text: "Feel good about your balance", level: "vanilla" },
      { text: "Hide it and pretend you didn't see it", level: "spicy" },
      { text: "Screenshot it for content", level: "unhinged" },
      { text: "Get competitive about how high it is", level: "feral" },
      { text: "Your phone is scared to send it", level: "menace" },
    ],
  },
  {
    id: 7,
    question: "Your Notes app contains:",
    options: [
      { text: "Grocery lists and passwords", level: "vanilla" },
      { text: "A few unsent texts to exes", level: "spicy" },
      { text: "Unhinged drafts and hot takes saved for later", level: "unhinged" },
      { text: "Full investigation dossiers on people", level: "feral" },
      { text: "Things that could end friendships if leaked", level: "menace" },
    ],
  },
];

/**
 * The Unhinged Test - v3.0 Content
 * Focus: Social comparison, quotable roasts, screenshot-worthy
 * Tone: Chaotic friend with no filter
 */
export const FREAK_CONTENT: Record<FreakLevel, {
  title: string;
  tagline: string;
  description: string;
  shareText: string;
  emoji: string;
  color: string;
  levelNumber: number;
}> = {
  vanilla: {
    title: "VANILLA BEAN",
    tagline: "you read terms and conditions for fun",
    description: "You're the friend who leaves parties at 10pm and actually means it when you say 'let me know you got home safe.' Your screen time is reasonable. Your Notes app is just grocery lists. Honestly? We need you to balance out the chaos.",
    shareText: "I'm VANILLA BEAN — I read terms and conditions for fun. How unhinged are you?",
    emoji: "🍦",
    color: "text-amber-200",
    levelNumber: 1,
  },
  spicy: {
    title: "SPICY CURIOUS",
    tagline: "one foot in, one foot ready to run",
    description: "You'll do something unhinged but you'll think about it for three days first. You've drafted texts you never sent. You've stalked but felt guilty about it. You're chaos-adjacent. Chaos-curious. The training wheels are still on but you're wobbling.",
    shareText: "I'm SPICY CURIOUS — chaos-adjacent and wobbling. How unhinged are you?",
    emoji: "🌶️",
    color: "text-orange-400",
    levelNumber: 2,
  },
  unhinged: {
    title: "CASUALLY UNHINGED",
    tagline: "you've got stories you only tell after drink three",
    description: "Your browser history is a liability. Your screen time report is a crime scene. You've done things that would concern your mother and texted things that would concern a therapist. But somehow you're functional. That's the scariest part.",
    shareText: "I'm CASUALLY UNHINGED — functional but concerning. How unhinged are you?",
    emoji: "🔥",
    color: "text-red-500",
    levelNumber: 3,
  },
  feral: {
    title: "ABSOLUTELY FERAL",
    tagline: "you don't have intrusive thoughts — you ARE the intrusive thought",
    description: "You've been banned from something. You have at least one story that starts with 'legally I can't say much but...' Your group chat fears your notification sound. You're the reason someone has trust issues and you might not even know who.",
    shareText: "I'm ABSOLUTELY FERAL — I AM the intrusive thought. How unhinged are you?",
    emoji: "👹",
    color: "text-purple-500",
    levelNumber: 4,
  },
  menace: {
    title: "CERTIFIED MENACE",
    tagline: "the devil takes notes from you",
    description: "You're not participating in this quiz. This quiz is studying you. Your energy has caused at least one international incident. Your presence in a room changes the WiFi. Scientists should be monitoring you. You're not unhinged — you're the hinge everyone else swings from.",
    shareText: "I'm a CERTIFIED MENACE — the devil takes notes from me. How unhinged are you?",
    emoji: "😈",
    color: "text-fuchsia-500",
    levelNumber: 5,
  },
};

/**
 * Freak Level visual metadata for UI
 */
export const FREAK_VISUALS: Record<FreakLevel, { emoji: string; color: string; gradient: string }> = {
  vanilla: {
    emoji: "🍦",
    color: "text-amber-200",
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
    color: "text-fuchsia-500",
    gradient: "from-fuchsia-500/20 to-pink-500/20",
  },
};
