export const COPY = {
  en: {
    title: "Face verification consent",
    body:
      "Haulwise wants to verify your identity using a face scan each time you start a trip or if a mismatch is detected on camera. Your face data is shared with our verification partner only for this purpose.",
    grant: "I consent to face verification",
    withdraw: "Withdraw face verification",
    granted: "Consent granted",
    withdrawn: "Consent withdrawn",
    receipts: "Consent receipts",
    dpr: "Your data request",
  },
  hi: {
    title: "चेहरा सत्यापन सहमति",
    body:
      "Haulwise हर यात्रा की शुरुआत में या कैमरे पर बेमेल पाए जाने पर चेहरा स्कैन के ज़रिए आपकी पहचान सत्यापित करना चाहता है। आपका चेहरे का डेटा केवल इसी उद्देश्य के लिए हमारे सत्यापन साझेदार के साथ साझा किया जाता है।",
    grant: "मैं चेहरा सत्यापन के लिए सहमति देता/देती हूं",
    withdraw: "चेहरा सत्यापन वापस लें",
    granted: "सहमति दी गई",
    withdrawn: "सहमति वापस ली गई",
    receipts: "सहमति रसीदें",
    dpr: "आपका डेटा अनुरोध",
  },
} as const;

export type Lang = keyof typeof COPY;
