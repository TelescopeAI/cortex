<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'

const displayedText = ref('')
const isTyping = ref(false)
const typewriterSpeed = ref(50) // milliseconds per character

const greetings = computed(() => {
  const currentHour = new Date().getHours()

  // Morning (5am - 12pm)
  if (currentHour >= 5 && currentHour < 12) {
    const morningGreetings = [
      '☀️ Fresh start! Let\'s go climb that peak',
      '🌅 New day, new insights to uncover',
      '⚡ Kickstart your day with a new mindset',
      '☕ Coffee + Questions = Unstoppable you',
      '🧠 Sharpened mind, clean datasets. Let\'s go!',
      '✨ Good morning! Let\'s turn hunches into hard numbers',
      '🚀 Launch your day with a new thought!',
      '🎯 Let\'s go solve those bottlenecks today',
      '📈 Excited to see what you\'ll discover today'
    ]
    return morningGreetings[Math.floor(Math.random() * morningGreetings.length)]
  }

  // Afternoon (12pm - 5pm)
  if (currentHour >= 12 && currentHour < 17) {
    const afternoonGreetings = [
      '☀️ Good afternoon! Keep that exploration streak alive!',
      '💪 Let\'s close the loop with your discoveries',
      '📊 Stuck on something? Let\'s try a new approach',
      '🚀 Post Lunch boost activated. Let\'s explore',
      '🎯 Let\'s go get our next win!',
      '🍱 Lunch is done. Time for some data dessert',
      '⚡ Quick check-in: What changed since morning?',
      '📈 One more chart today, one less doubt tomorrow',
      '🧩 Let\'s put the pieces together and complete this puzzle',
      '🏃‍♂️ Sprint through your backlog with fresh insights'
    ]
    return afternoonGreetings[Math.floor(Math.random() * afternoonGreetings.length)]
  }

  // Evening (5pm - 9pm)
  if (currentHour >= 17 && currentHour < 21) {
    const eveningGreetings = [
      '🌆 Golden hour for crystal clear insights',
      '🌙 Time to wrap the day with one more discovery',
      '☕ Time for a fresh cup of coffee and a new approach',
      '✨ Turn today\'s noise into tomorrow\'s vision',
      '🎯 Learn from our wins and let\'s find the next one',
      '🧠 Let\'s drill down and find the root cause',
      '📈 Evening check-in: Are we on track to meet the deadlines?',
      '🍷 Unwind with a clean, simple overview',
      '🚦 Before you log off, let\'s quickly look at the key indicators',
      '🌌 Small insights tonight, big moves tomorrow'
    ]
    return eveningGreetings[Math.floor(Math.random() * eveningGreetings.length)]
  }

  // Night (9pm - 5am)
  const nightGreetings = [
    '🌙 Night Owl detected: It\'s just you, me and the data',
    '🚀 Midnight Mission: Discover one more insight',
    '💫 Late night focus, laser sharp dashboards',
    '🦉 Quiet hours, loud signals in your metrics',
    '⭐ Welcome to the Insomniac analytics club!',
    '📊 While others sleep, you\'re making new discoveries',
    '🔍 Deep Focus window unlocked: Explore freely',
    '🌌 Stargazing in your data universe',
    '🧠 Big thoughts, less distractions. Best time for new discoveries',
    '🔥 One last chart, then we call it a night'
  ]
  return nightGreetings[Math.floor(Math.random() * nightGreetings.length)]
})

const typewrite = async (text: string) => {
  displayedText.value = ''
  isTyping.value = true
  for (let i = 0; i < text.length; i++) {
    await new Promise(resolve => setTimeout(resolve, typewriterSpeed.value))
    displayedText.value += text[i]
  }
  isTyping.value = false
}

watch(greetings, (newGreeting) => {
  if (newGreeting) {
    typewrite(newGreeting)
  }
}, { immediate: true })
</script>

<template>
  <h1 class="text-4xl font-bold mb-2 min-h-16">{{ displayedText }}<span v-if="isTyping" class="animate-pulse">|</span></h1>
</template>

