/**
 * eCitizen Voice Guidance Service
 * Helps visually impaired users navigate eCitizen by:
 * 1. Opening the correct eCitizen pages
 * 2. Reading form fields and requirements aloud
 * 3. Guiding users step-by-step through the application process
 * 4. Storing their spoken information for reference
 * 
 * NOTE: Due to eCitizen security, we cannot auto-fill forms.
 * Instead, we provide detailed voice guidance so users can fill forms themselves
 * or with the help of a sighted assistant.
 */

// eCitizen URL mappings
export const ECITIZEN_URLS = {
  home: 'https://accounts.ecitizen.go.ke',
  login: 'https://accounts.ecitizen.go.ke/en/login',
  register: 'https://accounts.ecitizen.go.ke/en/register',
  services: 'https://accounts.ecitizen.go.ke/en/services',
  passport: 'https://accounts.ecitizen.go.ke/en/services/passport',
  national_id: 'https://accounts.ecitizen.go.ke/en/services/id',
  driving_license: 'https://accounts.ecitizen.go.ke/en/services/dl',
  good_conduct: 'https://accounts.ecitizen.go.ke/en/services/goodconduct',
  birth_certificate: 'https://accounts.ecitizen.go.ke/en/services/birth',
  business_registration: 'https://accounts.ecitizen.go.ke/en/services/business',
  land_search: 'https://accounts.ecitizen.go.ke/en/services/land',
};

// Comprehensive service information for voice guidance
export const SERVICE_GUIDANCE = {
  passport: {
    name: 'Passport Application',
    nameSwahili: 'Maombi ya Pasipoti',
    requirements: [
      'Original National ID card',
      'Original Birth Certificate', 
      '2 recent passport-size photos with white background',
      'Old passport if renewing',
    ],
    requirementsSwahili: [
      'Kitambulisho cha Taifa asili',
      'Cheti cha Kuzaliwa asili',
      'Picha 2 za pasipoti na mandhari nyeupe',
      'Pasipoti ya zamani ikiwa unahuisha',
    ],
    fees: {
      ordinary_32: 'KES 4,550 for 32 pages',
      ordinary_48: 'KES 6,050 for 48 pages', 
      east_african: 'KES 4,550 for East African passport',
      diplomatic: 'KES 0 for diplomatic passport',
    },
    processingTime: '10 working days',
    steps: [
      'First, you need to create an eCitizen account or log in if you have one',
      'Go to the passport services section',
      'Select "Apply for New Passport" or "Renew Passport"',
      'Fill in your personal details: Full name, ID number, date of birth',
      'Upload your passport photo',
      'Select your preferred collection center',
      'Pay the application fee via M-Pesa or card',
      'Book an appointment for biometric capture',
      'Visit the immigration office on your appointment date with original documents',
    ],
    stepsSwahili: [
      'Kwanza, tengeneza akaunti ya eCitizen au ingia ukiwa nayo',
      'Nenda sehemu ya huduma za pasipoti',
      'Chagua "Omba Pasipoti Mpya" au "Huisha Pasipoti"',
      'Jaza taarifa zako: Jina kamili, nambari ya kitambulisho, tarehe ya kuzaliwa',
      'Pakia picha yako ya pasipoti',
      'Chagua kituo unachopenda kuchukua pasipoti',
      'Lipa ada kupitia M-Pesa au kadi',
      'Weka miadi ya kupigwa picha za biometric',
      'Tembelea ofisi ya uhamiaji siku ya miadi yako na hati asili',
    ],
    formFields: [
      { name: 'Full Name', description: 'Your name as it appears on your ID' },
      { name: 'ID Number', description: '8 digits from your National ID' },
      { name: 'Date of Birth', description: 'Day, month, and year you were born' },
      { name: 'Phone Number', description: 'Your mobile number starting with 07 or 01' },
      { name: 'Email Address', description: 'Your email for notifications' },
      { name: 'County of Residence', description: 'Where you currently live' },
    ],
  },
  national_id: {
    name: 'National ID Application',
    nameSwahili: 'Maombi ya Kitambulisho cha Taifa',
    requirements: [
      'Original Birth Certificate',
      'School Leaving Certificate or letter from chief',
      'Parent or Guardian National ID (copy)',
      'Must be 18 years or older',
    ],
    requirementsSwahili: [
      'Cheti cha Kuzaliwa asili',
      'Cheti cha kumaliza shule au barua ya chifu',
      'Nakala ya Kitambulisho cha mzazi au mlezi',
      'Lazima uwe na miaka 18 au zaidi',
    ],
    fees: {
      first_id: 'Free for first application',
      replacement: 'KES 100 for replacement',
    },
    processingTime: '30 to 60 days',
    steps: [
      'Register on eCitizen if you do not have an account',
      'Go to National Registration services',
      'Fill the application form with your details',
      'Select your registration center - usually the DC office in your sub-county',
      'Book an appointment',
      'Visit the registration center with your original documents',
      'Your fingerprints and photo will be captured',
      'Wait for SMS notification when ID is ready',
      'Collect from your chosen center',
    ],
    formFields: [
      { name: 'Full Name', description: 'As it appears on your birth certificate' },
      { name: 'Birth Certificate Number', description: 'Number on your birth certificate' },
      { name: 'Date of Birth', description: 'Your date of birth' },
      { name: 'Place of Birth', description: 'Hospital or location where you were born' },
      { name: 'Father\'s Name', description: 'Your father\'s full name' },
      { name: 'Mother\'s Name', description: 'Your mother\'s full name' },
    ],
  },
  driving_license: {
    name: 'Driving License Application',
    nameSwahili: 'Maombi ya Leseni ya Udereva',
    requirements: [
      'National ID',
      'Certificate from approved driving school',
      'Medical examination certificate',
      'Passport photo',
      'Must be 18 years or older',
    ],
    fees: {
      class_BCE: 'KES 600 for Class B, C, E',
      class_ADFGH: 'KES 600 for Class A, D, F, G, H',
      psv: 'KES 1,000 for PSV license',
    },
    processingTime: '14 working days',
    steps: [
      'Complete driving school training first',
      'Get a medical certificate from an approved doctor',
      'Create or log into your eCitizen account',
      'Go to NTSA driving license services',
      'Apply for interim license first',
      'Book and pass the driving test',
      'Apply for the permanent license',
      'Pay the fees',
      'Collect your license',
    ],
    formFields: [
      { name: 'Full Name', description: 'Your name as on your ID' },
      { name: 'ID Number', description: 'Your 8-digit National ID number' },
      { name: 'Driving School', description: 'Name of your driving school' },
      { name: 'License Class', description: 'Type of vehicle - Class B for cars' },
      { name: 'Blood Group', description: 'Your blood type from medical certificate' },
    ],
  },
  good_conduct: {
    name: 'Certificate of Good Conduct',
    nameSwahili: 'Cheti cha Mwenendo Mwema',
    requirements: [
      'National ID',
      'Recent passport photo',
      'Application fee',
    ],
    fees: {
      local: 'KES 1,050 for local use',
      foreign: 'KES 1,050 for foreign use',
    },
    processingTime: '7 to 14 working days',
    steps: [
      'Log into eCitizen',
      'Go to Police Clearance Certificate services',
      'Select purpose - local employment, foreign travel, etc.',
      'Fill in your personal details',
      'Pay the application fee',
      'Book an appointment for fingerprint capture',
      'Visit CID headquarters or a Huduma Center on your appointment',
      'Wait for SMS when certificate is ready',
      'Download from eCitizen or collect physical copy',
    ],
    formFields: [
      { name: 'Full Name', description: 'Your name as on your ID' },
      { name: 'ID Number', description: 'Your National ID number' },
      { name: 'Purpose', description: 'Why you need the certificate - employment, visa, etc.' },
      { name: 'Phone Number', description: 'For SMS notifications' },
    ],
  },
};

class ECitizenGuidanceService {
  constructor() {
    this.eCitizenWindow = null;
    this.userInfo = {};
    this.currentService = null;
    this.currentStep = 0;
    this.language = 'en';
  }

  /**
   * Set the language for guidance
   */
  setLanguage(lang) {
    this.language = lang === 'sw' ? 'sw' : 'en';
  }

  /**
   * Store user information spoken during conversation
   */
  setUserInfo(info) {
    this.userInfo = { ...this.userInfo, ...info };
    console.log('User info stored:', this.userInfo);
  }

  /**
   * Get stored user information
   */
  getUserInfo() {
    return this.userInfo;
  }

  /**
   * Clear stored information
   */
  clearUserInfo() {
    this.userInfo = {};
    this.currentService = null;
    this.currentStep = 0;
  }

  /**
   * Get comprehensive guidance for a service
   * This is what Habari speaks to guide the user
   */
  getServiceGuidance(serviceType, language = 'en') {
    const service = SERVICE_GUIDANCE[serviceType];
    if (!service) {
      return {
        success: false,
        message: language === 'sw' 
          ? 'Samahani, sijui huduma hiyo. Huduma zinazopatikana ni: pasipoti, kitambulisho, leseni ya udereva, na cheti cha mwenendo mwema.'
          : 'Sorry, I don\'t recognize that service. Available services are: passport, national ID, driving license, and certificate of good conduct.',
      };
    }

    const name = language === 'sw' ? service.nameSwahili : service.name;
    const requirements = language === 'sw' ? service.requirementsSwahili : service.requirements;
    
    // Build spoken guidance
    let guidance = '';
    
    if (language === 'sw') {
      guidance = `Sawa, nitakusaidia na ${name}. `;
      guidance += `Utahitaji vitu hivi: ${requirements.join(', ')}. `;
      guidance += `Ada ni ${Object.values(service.fees)[0]}. `;
      guidance += `Muda wa kupata ni ${service.processingTime}. `;
      guidance += `Je, ungependa nifungue ukurasa wa eCitizen sasa?`;
    } else {
      guidance = `Alright, I'll help you with ${name}. `;
      guidance += `You will need: ${requirements.join(', ')}. `;
      guidance += `The fee is ${Object.values(service.fees)[0]}. `;
      guidance += `Processing time is ${service.processingTime}. `;
      guidance += `Would you like me to open the eCitizen page now?`;
    }

    return {
      success: true,
      service: serviceType,
      message: guidance,
      requirements,
      fees: service.fees,
      processingTime: service.processingTime,
    };
  }

  /**
   * Get step-by-step instructions for a service
   */
  getStepByStepGuide(serviceType, language = 'en') {
    const service = SERVICE_GUIDANCE[serviceType];
    if (!service) return null;

    const steps = language === 'sw' ? service.stepsSwahili : service.steps;
    
    let guide = language === 'sw' 
      ? `Hizi ni hatua za kupata ${service.nameSwahili}:\n`
      : `Here are the steps for ${service.name}:\n`;
    
    steps.forEach((step, index) => {
      guide += `${language === 'sw' ? 'Hatua' : 'Step'} ${index + 1}: ${step}\n`;
    });

    return guide;
  }

  /**
   * Get the next step in the process
   */
  getNextStep(serviceType, language = 'en') {
    const service = SERVICE_GUIDANCE[serviceType];
    if (!service) return null;

    const steps = language === 'sw' ? service.stepsSwahili : service.steps;
    
    if (this.currentStep >= steps.length) {
      this.currentStep = 0;
      return language === 'sw'
        ? 'Umekamilisha hatua zote! Je, una swali lingine?'
        : 'You\'ve completed all steps! Do you have any questions?';
    }

    const step = steps[this.currentStep];
    this.currentStep++;
    
    return language === 'sw'
      ? `Hatua ${this.currentStep}: ${step}`
      : `Step ${this.currentStep}: ${step}`;
  }

  /**
   * Read back stored user information
   */
  readBackUserInfo(language = 'en') {
    const info = this.userInfo;
    if (Object.keys(info).length === 0) {
      return language === 'sw'
        ? 'Bado sijarekodi taarifa zako. Tafadhali niambie jina lako, nambari ya kitambulisho, na nambari ya simu.'
        : 'I haven\'t recorded any of your information yet. Please tell me your name, ID number, and phone number.';
    }

    let readback = language === 'sw' ? 'Taarifa zako: ' : 'Your information: ';
    
    if (info.user_name || info.first_name) {
      const name = info.user_name || `${info.first_name} ${info.last_name || ''}`;
      readback += language === 'sw' ? `Jina: ${name}. ` : `Name: ${name}. `;
    }
    
    if (info.id_number) {
      // Spell out ID number for clarity
      const idSpelled = info.id_number.toString().split('').join(' ');
      readback += language === 'sw' 
        ? `Nambari ya kitambulisho: ${idSpelled}. `
        : `ID number: ${idSpelled}. `;
    }
    
    if (info.phone_number || info.phone) {
      const phone = info.phone_number || info.phone;
      const phoneSpelled = phone.toString().split('').join(' ');
      readback += language === 'sw'
        ? `Nambari ya simu: ${phoneSpelled}. `
        : `Phone number: ${phoneSpelled}. `;
    }
    
    if (info.email) {
      readback += language === 'sw' ? `Barua pepe: ${info.email}. ` : `Email: ${info.email}. `;
    }

    readback += language === 'sw'
      ? 'Je, taarifa hizi ni sahihi?'
      : 'Is this information correct?';

    return readback;
  }

  /**
   * Navigate to an eCitizen page
   */
  navigate(serviceType) {
    try {
      let url = ECITIZEN_URLS[serviceType];
      
      if (!url && serviceType.startsWith('http')) {
        url = serviceType;
      }
      
      if (!url) {
        return {
          success: false,
          error: `Unknown service: ${serviceType}`,
          message: this.language === 'sw'
            ? `Sijui huduma hiyo. Huduma zinazopatikana: pasipoti, kitambulisho, leseni, mwenendo mwema.`
            : `I don't recognize that service. Available: passport, national_id, driving_license, good_conduct.`,
        };
      }

      this.currentService = serviceType;
      
      // Open in a new window
      this.eCitizenWindow = window.open(url, 'eCitizenPortal', 'width=1200,height=800');
      
      if (this.eCitizenWindow) {
        this.eCitizenWindow.focus();
        
        const guidance = SERVICE_GUIDANCE[serviceType];
        const formFieldsGuide = guidance ? this.getFormFieldsGuide(serviceType) : '';
        
        return {
          success: true,
          url,
          message: this.language === 'sw'
            ? `Nimefungua ukurasa wa ${guidance?.nameSwahili || serviceType} kwenye dirisha jipya. ${formFieldsGuide}`
            : `I've opened the ${guidance?.name || serviceType} page in a new window. ${formFieldsGuide}`,
          window: this.eCitizenWindow,
        };
      } else {
        return {
          success: false,
          error: 'popup_blocked',
          message: this.language === 'sw'
            ? 'Dirisha limezuiwa. Tafadhali ruhusu popups kwa tovuti hii.'
            : 'The popup was blocked. Please allow popups for this site.',
          fallbackUrl: url,
        };
      }
    } catch (error) {
      console.error('Navigation error:', error);
      return {
        success: false,
        error: error.message,
        message: this.language === 'sw'
          ? 'Imeshindikana kufungua ukurasa. Tafadhali jaribu tena.'
          : 'Failed to open the page. Please try again.',
      };
    }
  }

  /**
   * Get voice guidance for form fields
   */
  getFormFieldsGuide(serviceType) {
    const service = SERVICE_GUIDANCE[serviceType];
    if (!service || !service.formFields) return '';

    if (this.language === 'sw') {
      return `Fomu ina sehemu hizi: ${service.formFields.map(f => f.name).join(', ')}. Niambie ukihitaji msaada na sehemu yoyote.`;
    }
    return `The form has these fields: ${service.formFields.map(f => f.name).join(', ')}. Let me know if you need help with any field.`;
  }

  /**
   * Get help for a specific form field
   */
  getFieldHelp(serviceType, fieldName) {
    const service = SERVICE_GUIDANCE[serviceType];
    if (!service) return null;

    const field = service.formFields?.find(
      f => f.name.toLowerCase().includes(fieldName.toLowerCase())
    );

    if (!field) {
      return this.language === 'sw'
        ? `Sijui sehemu hiyo. Sehemu zinazopatikana: ${service.formFields?.map(f => f.name).join(', ')}`
        : `I don't recognize that field. Available fields: ${service.formFields?.map(f => f.name).join(', ')}`;
    }

    return this.language === 'sw'
      ? `Sehemu ya ${field.name}: ${field.description}`
      : `${field.name} field: ${field.description}`;
  }

  /**
   * Generate spoken instructions based on collected info
   * This helps the user or their assistant fill the form
   */
  generateFillInstructions(data) {
    const instructions = [];
    const lang = this.language;
    
    if (data.first_name || data.user_name) {
      const name = data.first_name || data.user_name.split(' ')[0];
      instructions.push(lang === 'sw' 
        ? `Kwa jina la kwanza, andika: ${name}`
        : `For first name, enter: ${name}`);
    }
    
    if (data.last_name || (data.user_name && data.user_name.split(' ').length > 1)) {
      const lastName = data.last_name || data.user_name.split(' ').slice(1).join(' ');
      instructions.push(lang === 'sw'
        ? `Kwa jina la ukoo, andika: ${lastName}`
        : `For last name, enter: ${lastName}`);
    }
    
    if (data.id_number) {
      const spelled = data.id_number.split('').join(', ');
      instructions.push(lang === 'sw'
        ? `Kwa nambari ya kitambulisho, andika: ${spelled}`
        : `For ID number, enter: ${spelled}`);
    }
    
    if (data.phone_number || data.phone) {
      const phone = data.phone_number || data.phone;
      const spelled = phone.split('').join(', ');
      instructions.push(lang === 'sw'
        ? `Kwa nambari ya simu, andika: ${spelled}`
        : `For phone number, enter: ${spelled}`);
    }
    
    if (data.email) {
      instructions.push(lang === 'sw'
        ? `Kwa barua pepe, andika: ${data.email}`
        : `For email, enter: ${data.email}`);
    }

    if (instructions.length === 0) {
      return lang === 'sw'
        ? 'Tafadhali niambie taarifa zako ili nikisaidie kujaza fomu.'
        : 'Please tell me your details so I can help you fill the form.';
    }

    const intro = lang === 'sw'
      ? 'Hizi ni taarifa za kujaza kwenye fomu: '
      : 'Here is the information to fill in the form: ';
    
    const outro = lang === 'sw'
      ? ' Je, ungependa nirudie taarifa yoyote?'
      : ' Would you like me to repeat any of these?';

    return intro + instructions.join('. ') + '.' + outro;
  }

  /**
   * Execute an automation action from Gemini
   */
  async executeAutomation(automation) {
    if (!automation || automation.action === 'none') {
      return { success: true, message: '', noAction: true };
    }

    switch (automation.action) {
      case 'navigate':
        if (automation.target_url) {
          const serviceType = Object.keys(ECITIZEN_URLS).find(
            key => ECITIZEN_URLS[key] === automation.target_url
          );
          return this.navigate(serviceType || automation.target_url);
        }
        break;

      case 'guide':
        // Provide voice guidance instead of autofill
        if (automation.service_type) {
          return this.getServiceGuidance(automation.service_type, this.language);
        }
        break;

      case 'read_info':
        // Read back user's stored information
        return {
          success: true,
          message: this.readBackUserInfo(this.language),
        };

      case 'next_step':
        // Get next step in the process
        if (this.currentService) {
          return {
            success: true,
            message: this.getNextStep(this.currentService, this.language),
          };
        }
        break;

      case 'fill_instructions':
        // Generate spoken instructions for filling the form
        return {
          success: true,
          message: this.generateFillInstructions(this.userInfo),
        };

      default:
        return { success: true, message: '', noAction: true };
    }

    return { success: true, message: '', noAction: true };
  }

  /**
   * Get service information for voice announcement
   */
  getServiceDetails(serviceType) {
    return SERVICE_GUIDANCE[serviceType] || null;
  }
}

// Export singleton instance
const eCitizenGuidance = new ECitizenGuidanceService();
export default eCitizenGuidance;
