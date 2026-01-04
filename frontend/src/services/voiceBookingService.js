/**
 * Voice Booking Automation Service
 * Handles voice-to-booking flow for eCitizen services
 */

// eCitizen service URLs
const ECITIZEN_URLS = {
  passport: 'https://accounts.ecitizen.go.ke/en/register/passport',
  national_id: 'https://accounts.ecitizen.go.ke/en/register/id',
  driving_license: 'https://accounts.ecitizen.go.ke/en/register/ntsa',
  good_conduct: 'https://www.ecitizen.go.ke/service/DCICGC',
  birth_certificate: 'https://www.ecitizen.go.ke/service/CRSOnlineBirth',
  business_registration: 'https://www.ecitizen.go.ke/service/BRS',
  home: 'https://www.ecitizen.go.ke',
};

// Service requirements
const SERVICE_INFO = {
  passport: {
    name: 'Passport Application',
    nameSwahili: 'Maombi ya Pasipoti',
    requirements: ['National ID', 'Birth Certificate', '2 Passport Photos', 'KES 4,550'],
    fields: ['first_name', 'last_name', 'id_number', 'phone', 'email', 'date_of_birth'],
  },
  national_id: {
    name: 'National ID Application',
    nameSwahili: 'Maombi ya Kitambulisho',
    requirements: ['Birth Certificate', 'School Leaving Certificate', 'Parent ID'],
    fields: ['first_name', 'last_name', 'date_of_birth', 'phone'],
  },
  driving_license: {
    name: 'Driving License',
    nameSwahili: 'Leseni ya Udereva',
    requirements: ['National ID', 'Medical Certificate', 'Driving School Certificate', 'KES 3,050'],
    fields: ['first_name', 'last_name', 'id_number', 'phone', 'email'],
  },
  good_conduct: {
    name: 'Certificate of Good Conduct',
    nameSwahili: 'Cheti cha Mwenendo Mwema',
    requirements: ['National ID', 'Passport Photo', 'KES 1,050'],
    fields: ['first_name', 'last_name', 'id_number', 'phone', 'email'],
  },
};

class VoiceBookingService {
  constructor() {
    this.collectedData = {};
    this.currentService = null;
    this.bookingStep = 0;
    this.language = 'en';
    this.onStepComplete = null;
    this.onBookingReady = null;
  }

  setLanguage(lang) {
    this.language = lang === 'sw' ? 'sw' : 'en';
  }

  t(en, sw) {
    return this.language === 'sw' ? sw : en;
  }

  /**
   * Parse user speech for booking intent and data
   */
  parseUserSpeech(text) {
    const lower = text.toLowerCase();
    const result = {
      intent: null,
      service: null,
      data: {},
    };

    // Detect service type
    if (lower.includes('passport') || lower.includes('pasipoti')) {
      result.service = 'passport';
    } else if (lower.includes('national id') || lower.includes('kitambulisho') || lower.includes('id card')) {
      result.service = 'national_id';
    } else if (lower.includes('driving') || lower.includes('license') || lower.includes('leseni')) {
      result.service = 'driving_license';
    } else if (lower.includes('good conduct') || lower.includes('police') || lower.includes('mwenendo')) {
      result.service = 'good_conduct';
    }

    // Detect intent
    if (lower.includes('book') || lower.includes('apply') || lower.includes('weka') || lower.includes('omba')) {
      result.intent = 'book';
    } else if (lower.includes('check') || lower.includes('status') || lower.includes('hali')) {
      result.intent = 'check_status';
    } else if (lower.includes('require') || lower.includes('need') || lower.includes('hitaji')) {
      result.intent = 'requirements';
    }

    // Extract personal data
    // Name patterns
    const namePatterns = [
      /my name is (\w+\s*\w*)/i,
      /i am (\w+\s*\w*)/i,
      /jina langu ni (\w+\s*\w*)/i,
      /called (\w+\s*\w*)/i,
    ];
    for (const pattern of namePatterns) {
      const match = text.match(pattern);
      if (match) {
        const names = match[1].trim().split(/\s+/);
        result.data.first_name = names[0];
        if (names[1]) result.data.last_name = names[1];
        break;
      }
    }

    // ID number (8 digits)
    const idMatch = text.match(/\b(\d{8})\b/);
    if (idMatch) {
      result.data.id_number = idMatch[1];
    }

    // Phone number (Kenyan format)
    const phoneMatch = text.match(/(?:0|\+?254)?([17]\d{8})/);
    if (phoneMatch) {
      result.data.phone = '0' + phoneMatch[1];
    }

    // Email
    const emailMatch = text.match(/[\w.-]+@[\w.-]+\.\w+/);
    if (emailMatch) {
      result.data.email = emailMatch[0];
    }

    return result;
  }

  /**
   * Start a booking flow
   */
  startBooking(serviceType) {
    if (!SERVICE_INFO[serviceType]) {
      return {
        success: false,
        message: this.t(
          `Unknown service. Available: passport, national ID, driving license, good conduct.`,
          `Huduma haijulikani. Zinazopatikana: pasipoti, kitambulisho, leseni, mwenendo mwema.`
        ),
      };
    }

    this.currentService = serviceType;
    this.collectedData = {};
    this.bookingStep = 0;

    const info = SERVICE_INFO[serviceType];
    const name = this.language === 'sw' ? info.nameSwahili : info.name;

    return {
      success: true,
      service: serviceType,
      message: this.t(
        `Starting ${name} booking. You'll need: ${info.requirements.join(', ')}. Let's collect your information. What is your full name?`,
        `Tunaanza maombi ya ${name}. Utahitaji: ${info.requirements.join(', ')}. Hebu tukusanye taarifa zako. Jina lako kamili ni nani?`
      ),
      nextField: 'name',
    };
  }

  /**
   * Process collected data and determine next step
   */
  processInput(text) {
    if (!this.currentService) {
      const parsed = this.parseUserSpeech(text);
      
      if (parsed.service && parsed.intent === 'book') {
        return this.startBooking(parsed.service);
      }
      
      if (parsed.intent === 'requirements' && parsed.service) {
        const info = SERVICE_INFO[parsed.service];
        return {
          success: true,
          message: this.t(
            `For ${info.name}, you need: ${info.requirements.join(', ')}. Would you like to start the application?`,
            `Kwa ${info.nameSwahili}, unahitaji: ${info.requirements.join(', ')}. Ungependa kuanza maombi?`
          ),
        };
      }

      return {
        success: true,
        message: this.t(
          `What service would you like? Say "Book passport", "Apply for ID", "Get driving license", or "Good conduct certificate".`,
          `Unahitaji huduma gani? Sema "Omba pasipoti", "Omba kitambulisho", "Pata leseni", au "Cheti cha mwenendo".`
        ),
      };
    }

    // Collect data based on current step
    const parsed = this.parseUserSpeech(text);
    const info = SERVICE_INFO[this.currentService];
    const fields = info.fields;

    // Merge any extracted data
    this.collectedData = { ...this.collectedData, ...parsed.data };

    // Check what we still need
    const missing = fields.filter(f => {
      if (f === 'first_name') return !this.collectedData.first_name;
      if (f === 'last_name') return !this.collectedData.last_name;
      return !this.collectedData[f];
    });

    if (missing.length === 0) {
      return this.completeBooking();
    }

    // Ask for next missing field
    const nextField = missing[0];
    const prompts = {
      first_name: this.t('What is your first name?', 'Jina lako la kwanza ni nani?'),
      last_name: this.t('What is your last name?', 'Jina lako la ukoo ni nani?'),
      id_number: this.t('What is your ID number? Please say each digit clearly.', 'Nambari yako ya kitambulisho ni ipi? Sema kila tarakimu wazi.'),
      phone: this.t('What is your phone number?', 'Nambari yako ya simu ni ipi?'),
      email: this.t('What is your email address?', 'Barua pepe yako ni ipi?'),
      date_of_birth: this.t('What is your date of birth?', 'Tarehe yako ya kuzaliwa ni ipi?'),
    };

    // Confirm what we have so far
    const collected = Object.entries(this.collectedData)
      .filter(([k, v]) => v)
      .map(([k, v]) => `${k}: ${v}`)
      .join(', ');

    return {
      success: true,
      message: collected 
        ? this.t(`Got it. ${collected}. ${prompts[nextField]}`, `Sawa. ${collected}. ${prompts[nextField]}`)
        : prompts[nextField],
      nextField,
      collectedData: this.collectedData,
    };
  }

  /**
   * Complete the booking - open eCitizen with data
   */
  completeBooking() {
    const info = SERVICE_INFO[this.currentService];
    const url = ECITIZEN_URLS[this.currentService];
    const data = this.collectedData;

    // Generate summary
    const summary = this.t(
      `Perfect! I have all your information:\n` +
      `Name: ${data.first_name} ${data.last_name}\n` +
      `ID: ${data.id_number}\n` +
      `Phone: ${data.phone}\n` +
      `Email: ${data.email || 'Not provided'}\n\n` +
      `I'm opening the eCitizen ${info.name} page now. Use this information to fill the form.`,
      
      `Vizuri! Nina taarifa zako zote:\n` +
      `Jina: ${data.first_name} ${data.last_name}\n` +
      `Kitambulisho: ${data.id_number}\n` +
      `Simu: ${data.phone}\n` +
      `Barua pepe: ${data.email || 'Haijatolewa'}\n\n` +
      `Ninafungua ukurasa wa eCitizen wa ${info.nameSwahili} sasa. Tumia taarifa hizi kujaza fomu.`
    );

    // Open eCitizen page
    const win = window.open(url, '_blank');
    
    // Store data for potential clipboard copy
    this.lastBookingData = data;

    // Reset for next booking
    const completedData = { ...this.collectedData };
    this.collectedData = {};
    this.currentService = null;
    this.bookingStep = 0;

    return {
      success: true,
      complete: true,
      message: summary,
      data: completedData,
      url,
      window: win,
    };
  }

  /**
   * Get current booking status
   */
  getStatus() {
    return {
      service: this.currentService,
      data: this.collectedData,
      step: this.bookingStep,
    };
  }

  /**
   * Cancel current booking
   */
  cancel() {
    this.collectedData = {};
    this.currentService = null;
    this.bookingStep = 0;
    return {
      success: true,
      message: this.t('Booking cancelled.', 'Maombi yamefutwa.'),
    };
  }

  /**
   * Copy data to clipboard for easy paste
   */
  async copyDataToClipboard() {
    if (!this.lastBookingData) return false;
    
    const text = Object.entries(this.lastBookingData)
      .map(([k, v]) => `${k}: ${v}`)
      .join('\n');
    
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      return false;
    }
  }
}

// Singleton instance
const voiceBookingService = new VoiceBookingService();
export default voiceBookingService;
