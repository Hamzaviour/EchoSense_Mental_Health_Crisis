export type Language = 'en' | 'ur'

export const LANGUAGE_STORAGE_KEY = 'echo_language'

type TranslationTree = {
  nav: {
    chat: string
    journal: string
    sessionRequest: string
    therapyPlan: string
    copingTools: string
    logout: string
  }
  lang: {
    english: string
    romanUrdu: string
    label: string
  }
  chat: {
    title: string
    placeholder: string
    crisisAlert: string
    sendFailed: string
    voiceFailed: string
    dailyCalm: string
    tickerLabel: string
  }
  consent: {
    title: string
    p1: string
    p2: string
    crisis: string
    consentCheck: string
    privacyCheck: string
    continue: string
  }
  assessment: {
    yesContinue: string
    maybeLater: string
  }
  therapyPlan: {
    title: string
    subtitle: string
    downloadPdf: string
    generateTitle: string
    generateDesc: string
    focusPlaceholder: string
    generating: string
    regenerate: string
    generate: string
    loadError: string
    generateError: string
    pdfError: string
    aiGenerated: string
    weeklyGoals: string
    copingTasks: string
    behavioralSuggestions: string
    disclaimer: string
    emptyTitle: string
    emptyHint: string
  }
  coping: {
    title: string
    subtitle: string
    breathing: string
    grounding: string
    sleep: string
    anxiety: string
    mindfulness: string
    breathingDesc: string
    groundingDesc: string
    sleepDesc: string
    anxietyDesc: string
    mindfulnessDesc: string
  }
  journal: {
    title: string
    subtitle: string
    writeTitle: string
    writeDesc: string
    placeholder: string
    saveReflection: string
    voiceLabel: string
    voiceBadge: string
    textBadge: string
    pastEntries: string
    noEntries: string
    aiInsights: string
    aiInsightsDesc: string
    summary: string
    emotions: string
    copingStrategies: string
    fullEntry: string
    selectOrSave: string
    loadError: string
    saveError: string
    voiceError: string
    minLength: string
    consentRequired: string
    exportPdf: string
    exportEntryPdf: string
    exportError: string
  }
  sessionRequest: {
    title: string
    subtitle: string
    formTitle: string
    formDesc: string
    chooseCounselor: string
    anyCounselor: string
    offDuty: string
    requestType: string
    chatSession: string
    chatDesc: string
    callback: string
    callbackDesc: string
    contact: string
    contactPlaceholder: string
    messageOptional: string
    messagePlaceholder: string
    submit: string
    submitting: string
    success: string
    submitError: string
    loadError: string
    history: string
    noRequests: string
    counselor: string
  }
  common: {
    loading: string
    start: string
    pause: string
    reset: string
    next: string
    back: string
    stop: string
    begin: string
  }
  quotes: string[]
}

export const translations: Record<Language, TranslationTree> = {
  en: {
    nav: {
      chat: 'Chat',
      journal: 'Journal',
      sessionRequest: 'Request Session',
      therapyPlan: 'Therapy Plan',
      copingTools: 'Coping Tools',
      logout: 'Logout',
    },
    lang: {
      english: 'EN',
      romanUrdu: 'Roman Urdu',
      label: 'Language',
    },
    chat: {
      title: 'Echo Sense Assistant',
      placeholder: 'Share how you\'re feeling...',
      crisisAlert: 'A counselor has been notified to assist you. You are not alone. Umang: 0311-7786264',
      sendFailed: 'Failed to send',
      voiceFailed: 'Voice message failed',
      dailyCalm: 'Daily calm',
      tickerLabel: 'Motivational messages',
    },
    consent: {
      title: 'Welcome to Echo Sense',
      p1: 'Echo Sense provides AI-assisted emotional support. It is not a substitute for professional medical care.',
      p2: 'Your conversations may be reviewed by licensed counselors for your safety. Data is stored securely.',
      crisis: 'Crisis support — Umang: 0311-7786264 (24/7)',
      consentCheck: 'I consent to AI-assisted support sessions',
      privacyCheck: 'I accept the privacy policy',
      continue: 'Continue safely',
    },
    assessment: {
      yesContinue: 'Yes, Continue',
      maybeLater: 'Maybe Later',
    },
    therapyPlan: {
      title: 'Therapy Plan Generator',
      subtitle: 'AI creates a personalized weekly plan with goals, coping tasks, and behavioral suggestions.',
      downloadPdf: 'Download PDF',
      generateTitle: 'Generate your plan',
      generateDesc: 'Optional: share what you would like to focus on this week (e.g. sleep, anxiety, motivation).',
      focusPlaceholder: 'Focus area (optional)...',
      generating: 'Generating...',
      regenerate: 'Regenerate plan',
      generate: 'Generate plan',
      loadError: 'Could not load your therapy plan.',
      generateError: 'Failed to generate plan. Please try again.',
      pdfError: 'No PDF available. Generate a plan first.',
      aiGenerated: 'AI-generated',
      weeklyGoals: 'Weekly Goals',
      copingTasks: 'Coping Tasks',
      behavioralSuggestions: 'Behavioral Suggestions',
      disclaimer: 'This is wellness guidance, not medical advice. For crisis support: Umang 0311-7786264.',
      emptyTitle: 'No plan yet. Generate one to see your weekly goals and tasks.',
      emptyHint: 'Example tasks: "Walk 10 minutes daily", "Write 3 journal entries this week"',
    },
    coping: {
      title: 'Coping Tools Library',
      subtitle: 'Interactive exercises to help you feel grounded, calmer, and more in control.',
      breathing: 'Breathing',
      grounding: 'Grounding',
      sleep: 'Sleep',
      anxiety: 'Anxiety Relief',
      mindfulness: 'Mindfulness',
      breathingDesc: 'Box breathing with animated guide',
      groundingDesc: '5-4-3-2-1 sensory method',
      sleepDesc: 'Wind-down tips and timer',
      anxietyDesc: 'Step-by-step calming sequence',
      mindfulnessDesc: 'Guided session with voice option',
    },
    journal: {
      title: 'AI Journal',
      subtitle: 'Write or record your thoughts. AI reflects back with summary, emotions, and coping ideas.',
      writeTitle: 'New reflection',
      writeDesc: 'Your entries are private and stored securely.',
      placeholder: 'What is on your mind today? Challenges, wins, worries, gratitude...',
      saveReflection: 'Save & analyze',
      voiceLabel: 'Voice diary',
      voiceBadge: 'Voice',
      textBadge: 'Written',
      pastEntries: 'Past reflections',
      noEntries: 'No entries yet. Start writing above.',
      aiInsights: 'AI insights',
      aiInsightsDesc: 'Summary and gentle suggestions based on your reflection',
      summary: 'Summary',
      emotions: 'Detected emotions',
      copingStrategies: 'Suggested coping strategies',
      fullEntry: 'Your entry',
      selectOrSave: 'Save a reflection or select one from the list to see AI insights.',
      loadError: 'Could not load journal entries.',
      saveError: 'Could not save your reflection.',
      voiceError: 'Voice diary failed. Check microphone and try again.',
      minLength: 'Please write at least a few words.',
      consentRequired: 'Please complete consent on the Chat page before using the journal.',
      exportPdf: 'Export All (PDF)',
      exportEntryPdf: 'Export Entry (PDF)',
      exportError: 'Could not export journal PDF.',
    },
    sessionRequest: {
      title: 'Request Counselor Session',
      subtitle: 'Choose a counselor and request a live chat or phone callback.',
      formTitle: 'New request',
      formDesc: 'A counselor will review your request and respond when available.',
      chooseCounselor: 'Preferred counselor',
      anyCounselor: 'Any available counselor',
      offDuty: 'off duty',
      requestType: 'Session type',
      chatSession: 'Chat session',
      chatDesc: 'Live text chat with a licensed counselor',
      callback: 'Request callback',
      callbackDesc: 'Counselor calls you at your preferred number',
      contact: 'Phone or contact (optional)',
      contactPlaceholder: 'e.g. 03XX-XXXXXXX',
      messageOptional: 'Note for counselor (optional)',
      messagePlaceholder: 'Best times to reach you, what you would like to discuss...',
      submit: 'Submit request',
      submitting: 'Submitting...',
      success: 'Your request was sent. A counselor will respond soon.',
      submitError: 'Could not submit request. Try again.',
      loadError: 'Could not load counselors or requests.',
      history: 'Your requests',
      noRequests: 'No requests yet.',
      counselor: 'Counselor',
    },
    common: {
      loading: 'Loading...',
      start: 'Start',
      pause: 'Pause',
      reset: 'Reset',
      next: 'Next',
      back: 'Back',
      stop: 'Stop',
      begin: 'Begin',
    },
    quotes: [
      'You are allowed to take things one step at a time.',
      'Your feelings are valid, even when they are hard to explain.',
      'Healing is not linear — progress still counts.',
      'Asking for help is a sign of strength, not weakness.',
      'You deserve the same kindness you offer others.',
      'Small moments of calm can make a meaningful difference.',
      'It is okay to not be okay today.',
      'You have survived every difficult day so far.',
      'Rest is not giving up — it is part of recovery.',
      'Your story is still being written, and hope remains.',
      'Breathing slowly can remind your body that you are safe.',
      'You do not have to carry everything alone.',
    ],
  },
  ur: {
    nav: {
      chat: 'Chat',
      journal: 'Journal',
      sessionRequest: 'Session Request',
      therapyPlan: 'Therapy Plan',
      copingTools: 'Coping Tools',
      logout: 'Logout',
    },
    lang: {
      english: 'EN',
      romanUrdu: 'Roman Urdu',
      label: 'Zubaan',
    },
    chat: {
      title: 'Echo Sense Assistant',
      placeholder: 'Apna ehsaas share karein...',
      crisisAlert: 'Ek counselor ko inform kar diya gaya hai. Aap akelay nahi hain. Umang: 0311-7786264',
      sendFailed: 'Message bhejne mein masla',
      voiceFailed: 'Voice message fail ho gaya',
      dailyCalm: 'Rozana sukoon',
      tickerLabel: 'Motivational paigham',
    },
    consent: {
      title: 'Echo Sense mein khush amdeed',
      p1: 'Echo Sense AI-assisted emotional support deta hai. Yeh professional medical care ki jagah nahi hai.',
      p2: 'Aap ki conversations licensed counselors dekh sakte hain aap ki safety ke liye. Data mehfooz rakha jata hai.',
      crisis: 'Crisis support — Umang: 0311-7786264 (24/7)',
      consentCheck: 'Main AI-assisted support sessions ke liye consent deta/deti hoon',
      privacyCheck: 'Main privacy policy accept karta/karti hoon',
      continue: 'Mehfooz tareeqay se continue karein',
    },
    assessment: {
      yesContinue: 'Haan, Continue',
      maybeLater: 'Shayad Baad Mein',
    },
    therapyPlan: {
      title: 'Therapy Plan Generator',
      subtitle: 'AI aap ke liye haftay ka plan banata hai — goals, coping tasks, aur behavioral suggestions ke saath.',
      downloadPdf: 'PDF Download',
      generateTitle: 'Apna plan banayein',
      generateDesc: 'Optional: is hafte kis cheez par focus karna chahte hain (jaise neend, anxiety, motivation).',
      focusPlaceholder: 'Focus area (optional)...',
      generating: 'Ban raha hai...',
      regenerate: 'Plan dobara banayein',
      generate: 'Plan banayein',
      loadError: 'Therapy plan load nahi ho saka.',
      generateError: 'Plan banane mein masla. Dobara try karein.',
      pdfError: 'PDF available nahi. Pehle plan banayein.',
      aiGenerated: 'AI-generated',
      weeklyGoals: 'Haftay ke Goals',
      copingTasks: 'Coping Tasks',
      behavioralSuggestions: 'Behavioral Suggestions',
      disclaimer: 'Yeh wellness guidance hai, medical advice nahi. Crisis ke liye: Umang 0311-7786264.',
      emptyTitle: 'Abhi koi plan nahi. Generate karein apne haftay ke goals aur tasks dekhne ke liye.',
      emptyHint: 'Misal: "Roz 10 minute walk karein", "Is hafte 3 journal entries likhein"',
    },
    coping: {
      title: 'Coping Tools Library',
      subtitle: 'Interactive exercises jo aap ko grounded, calm aur control mein mehsoos karne mein madad karein.',
      breathing: 'Breathing',
      grounding: 'Grounding',
      sleep: 'Neend',
      anxiety: 'Anxiety Relief',
      mindfulness: 'Mindfulness',
      breathingDesc: 'Box breathing animated guide ke saath',
      groundingDesc: '5-4-3-2-1 sensory method',
      sleepDesc: 'Wind-down tips aur timer',
      anxietyDesc: 'Step-by-step calming sequence',
      mindfulnessDesc: 'Guided session voice option ke saath',
    },
    journal: {
      title: 'AI Journal',
      subtitle: 'Apne khayalat likhein ya record karein. AI summary, emotions aur coping ideas deta hai.',
      writeTitle: 'Nayi reflection',
      writeDesc: 'Aap ki entries private aur mehfooz hain.',
      placeholder: 'Aaj aap ke dil mein kya hai? Challenges, wins, worries, shukriya...',
      saveReflection: 'Save & analyze',
      voiceLabel: 'Voice diary',
      voiceBadge: 'Voice',
      textBadge: 'Written',
      pastEntries: 'Purani reflections',
      noEntries: 'Abhi koi entry nahi. Upar likhna shuru karein.',
      aiInsights: 'AI insights',
      aiInsightsDesc: 'Aap ki reflection par summary aur gentle suggestions',
      summary: 'Summary',
      emotions: 'Detected emotions',
      copingStrategies: 'Suggested coping strategies',
      fullEntry: 'Aap ki entry',
      selectOrSave: 'Reflection save karein ya list se select karein AI insights ke liye.',
      loadError: 'Journal entries load nahi ho sakin.',
      saveError: 'Reflection save nahi ho saki.',
      voiceError: 'Voice diary fail. Microphone check karein.',
      minLength: 'Kuch alfaaz likhein (kam az kam thori si reflection).',
      consentRequired: 'Journal se pehle Chat page par consent complete karein.',
      exportPdf: 'Sab Export (PDF)',
      exportEntryPdf: 'Entry Export (PDF)',
      exportError: 'Journal PDF export nahi ho saka.',
    },
    sessionRequest: {
      title: 'Counselor Session Request',
      subtitle: 'Counselor choose karein aur live chat ya phone callback request karein.',
      formTitle: 'Nayi request',
      formDesc: 'Counselor aap ki request review karega jab available ho.',
      chooseCounselor: 'Preferred counselor',
      anyCounselor: 'Koi bhi available counselor',
      offDuty: 'off duty',
      requestType: 'Session type',
      chatSession: 'Chat session',
      chatDesc: 'Licensed counselor ke saath live text chat',
      callback: 'Callback request',
      callbackDesc: 'Counselor aap ko call karega',
      contact: 'Phone / contact (optional)',
      contactPlaceholder: 'jaise 03XX-XXXXXXX',
      messageOptional: 'Counselor ke liye note (optional)',
      messagePlaceholder: 'Best time, kya discuss karna chahte hain...',
      submit: 'Request bhejein',
      submitting: 'Bhej rahe hain...',
      success: 'Request bhej di gayi. Counselor jald respond karega.',
      submitError: 'Request submit nahi ho saki.',
      loadError: 'Counselors ya requests load nahi ho sakin.',
      history: 'Aap ki requests',
      noRequests: 'Abhi koi request nahi.',
      counselor: 'Counselor',
    },
    common: {
      loading: 'Loading...',
      start: 'Start',
      pause: 'Pause',
      reset: 'Reset',
      next: 'Agla',
      back: 'Peeche',
      stop: 'Band',
      begin: 'Shuru',
    },
    quotes: [
      'Aap ek ek qadam le sakte hain — yeh bilkul theek hai.',
      'Aap ke feelings valid hain, chahe samjhana mushkil ho.',
      'Healing seedhi line mein nahi hoti — progress phir bhi count hoti hai.',
      'Madad maangna taqat ki nishani hai, kamzori ki nahi.',
      'Aap wohi meharbani deserve karte hain jo doosron ke liye karte hain.',
      'Sukoon ke chhote lamhe bhi farq la sakte hain.',
      'Aaj theek na hona bhi theek hai.',
      'Aap har mushkil din se guzar chuke hain.',
      'Aaram dena haar nahi — recovery ka hissa hai.',
      'Aap ki kahani abhi likhi ja rahi hai, aur umeed hai.',
      'Aahista saans lena body ko yaad dilata hai ke aap mehfooz hain.',
      'Aap ko sab kuch akela uthana nahi hai.',
    ],
  },
}

export function getStoredLanguage(): Language {
  const stored = localStorage.getItem(LANGUAGE_STORAGE_KEY)
  return stored === 'ur' ? 'ur' : 'en'
}
