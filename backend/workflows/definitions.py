"""
Workflow Definitions for Kenya Government Services

This module contains all the workflow definitions for:
- NTSA (Driving License Appointments)
- KRA (Nil Returns Filing, PIN Verification)
- DCI (Good Conduct Certificate)
- NRB (National ID)
- DCRS (Birth/Death Certificates)
- BRS (Business Registration)
- Huduma Centre Lookup
- Emergency Reporting
- Feedback Submission
"""

from typing import Dict, List, Optional, TYPE_CHECKING
from workflows.engine import (
    WorkflowDefinition, 
    StepDefinition, 
    StepType,
    WorkflowEngine
)

if TYPE_CHECKING:
    from workflows.engine import WorkflowEngine


def get_ntsa_driving_license_workflow() -> WorkflowDefinition:
    """NTSA Driving License Renewal/Appointment workflow."""
    return WorkflowDefinition(
        workflow_id="ntsa_driving_license",
        name_en="NTSA Driving License Appointment",
        name_sw="Miadi ya Leseni ya Kuendesha Gari NTSA",
        description_en="Book an appointment for driving license renewal or application",
        description_sw="Weka miadi ya kuhuisha au kuomba leseni ya kuendesha gari",
        agency="NTSA",
        initial_step="welcome",
        estimated_time_minutes=5,
        completion_message_en="Your appointment has been booked successfully! Booking ID: {booking_id}. You will receive an SMS confirmation at {phone_number}. Please arrive 15 minutes early with your National ID, medical certificate, and passport photos.",
        completion_message_sw="Miadi yako imewekwa kwa mafanikio! Nambari ya Miadi: {booking_id}. Utapokea ujumbe wa SMS kwa {phone_number}. Tafadhali fika dakika 15 mapema na kitambulisho chako, cheti cha matibabu, na picha za pasipoti.",
        steps=[
            StepDefinition(
                step_id="welcome",
                step_type=StepType.INFO,
                prompt_en="Welcome to the NTSA Driving License service. I'll help you book an appointment for your driving license.",
                prompt_sw="Karibu kwa huduma ya Leseni ya Kuendesha Gari ya NTSA. Nitakusaidia kuweka miadi ya leseni yako.",
                next_step="license_type"
            ),
            StepDefinition(
                step_id="license_type",
                step_type=StepType.PROMPT,
                prompt_en="Is this for a NEW driving license or RENEWAL of an existing license?",
                prompt_sw="Hii ni kwa leseni MPYA au KUHUISHA leseni iliyopo?",
                entity_name="license_type",
                next_step="full_name"
            ),
            StepDefinition(
                step_id="full_name",
                step_type=StepType.PROMPT,
                prompt_en="Please provide your full name as it appears on your National ID.",
                prompt_sw="Tafadhali toa jina lako kamili kama linavyoonekana kwenye kitambulisho chako.",
                entity_name="full_name",
                validator="name",
                retry_prompt_en="Please enter a valid name (letters only, 2-100 characters).",
                retry_prompt_sw="Tafadhali ingiza jina halali (herufi tu, vibambo 2-100).",
                next_step="national_id"
            ),
            StepDefinition(
                step_id="national_id",
                step_type=StepType.PROMPT,
                prompt_en="Please provide your National ID number.",
                prompt_sw="Tafadhali toa nambari yako ya kitambulisho.",
                entity_name="national_id",
                validator="national_id",
                retry_prompt_en="Invalid ID number. Please enter your 7 or 8 digit National ID number.",
                retry_prompt_sw="Nambari ya kitambulisho si sahihi. Tafadhali ingiza nambari ya tarakimu 7 au 8.",
                next_step="phone_number"
            ),
            StepDefinition(
                step_id="phone_number",
                step_type=StepType.PROMPT,
                prompt_en="Please provide your phone number for SMS confirmation (e.g., 0712345678).",
                prompt_sw="Tafadhali toa nambari yako ya simu kwa uthibitisho wa SMS (mfano, 0712345678).",
                entity_name="phone_number",
                validator="phone_ke",
                retry_prompt_en="Invalid phone number. Please enter a valid Kenyan phone number.",
                retry_prompt_sw="Nambari ya simu si sahihi. Tafadhali ingiza nambari sahihi ya simu ya Kenya.",
                next_step="time_slot"
            ),
            StepDefinition(
                step_id="time_slot",
                step_type=StepType.PROMPT,
                prompt_en="Would you prefer a MORNING (8am-12pm) or AFTERNOON (2pm-5pm) appointment?",
                prompt_sw="Ungependa miadi ya ASUBUHI (8am-12pm) au MCHANA (2pm-5pm)?",
                entity_name="time_slot",
                next_step="confirm_details"
            ),
            StepDefinition(
                step_id="confirm_details",
                step_type=StepType.CONFIRM,
                prompt_en="Please confirm these details:\n• Name: {full_name}\n• National ID: {national_id}\n• Phone: {phone_number}\n• Time Preference: {time_slot}\n\nIs this correct? (Yes/No)",
                prompt_sw="Tafadhali thibitisha maelezo haya:\n• Jina: {full_name}\n• Kitambulisho: {national_id}\n• Simu: {phone_number}\n• Muda Unaopendelea: {time_slot}\n\nHii ni sahihi? (Ndio/Hapana)",
                next_step="create_booking",
                branches={"no": "full_name"}
            ),
            StepDefinition(
                step_id="create_booking",
                step_type=StepType.ACTION,
                prompt_en="Creating your booking...",
                prompt_sw="Inaunda miadi yako...",
                action_handler="create_ntsa_booking",
                next_step="send_confirmation"
            ),
            StepDefinition(
                step_id="send_confirmation",
                step_type=StepType.ACTION,
                prompt_en="Sending SMS confirmation...",
                prompt_sw="Inatuma uthibitisho wa SMS...",
                action_handler="send_sms_confirmation",
                next_step=None  # Workflow complete
            )
        ]
    )


def get_kra_nil_returns_workflow() -> WorkflowDefinition:
    """KRA Nil Returns Filing guidance workflow."""
    return WorkflowDefinition(
        workflow_id="kra_nil_returns",
        name_en="KRA Nil Returns Filing",
        name_sw="Kuwasilisha Nil Returns KRA",
        description_en="Step-by-step guidance for filing nil returns on iTax",
        description_sw="Mwongozo wa hatua kwa hatua wa kuwasilisha nil returns kwenye iTax",
        agency="KRA",
        initial_step="welcome",
        estimated_time_minutes=10,
        requires_auth=False,
        completion_message_en="You have completed the nil returns filing guidance! Remember to keep your acknowledgment receipt safe. If you need help navigating iTax, I can guide you through the website step by step.",
        completion_message_sw="Umekamilisha mwongozo wa kuwasilisha nil returns! Kumbuka kuhifadhi risiti yako ya uthibitisho. Ukihitaji msaada wa kutumia iTax, naweza kukuongoza kupitia tovuti hatua kwa hatua.",
        steps=[
            StepDefinition(
                step_id="welcome",
                step_type=StepType.INFO,
                prompt_en="I'll guide you through filing nil returns on KRA iTax. Nil returns are filed when you have no income to report for the tax year.",
                prompt_sw="Nitakuongoza kupitia kuwasilisha nil returns kwenye KRA iTax. Nil returns zinawasilishwa unapokuwa huna mapato ya kuripoti kwa mwaka wa kodi.",
                next_step="check_pin"
            ),
            StepDefinition(
                step_id="check_pin",
                step_type=StepType.PROMPT,
                prompt_en="Do you have your KRA PIN ready? Please enter it (format: A123456789B) or say 'no' if you need help getting it.",
                prompt_sw="Una PIN yako ya KRA tayari? Tafadhali iingize (muundo: A123456789B) au sema 'hapana' ukihitaji msaada kupata.",
                entity_name="kra_pin",
                next_step="verify_pin"
            ),
            StepDefinition(
                step_id="verify_pin",
                step_type=StepType.BRANCH,
                prompt_en="Checking your PIN...",
                prompt_sw="Inakagua PIN yako...",
                branches={
                    "no": "pin_recovery_info",
                    "hapana": "pin_recovery_info",
                    "default": "itax_login_guide"
                },
                next_step="itax_login_guide"
            ),
            StepDefinition(
                step_id="pin_recovery_info",
                step_type=StepType.INFO,
                prompt_en="To recover your KRA PIN:\n1. Visit https://itax.kra.go.ke\n2. Click 'Forgot PIN?'\n3. Enter your National ID number\n4. Follow the instructions sent to your registered email/phone\n\nOnce you have your PIN, we can continue.",
                prompt_sw="Kupata PIN yako ya KRA:\n1. Tembelea https://itax.kra.go.ke\n2. Bonyeza 'Forgot PIN?'\n3. Ingiza nambari yako ya kitambulisho\n4. Fuata maelekezo yaliyotumwa kwa barua pepe/simu yako iliyosajiliwa\n\nUkipata PIN yako, tunaweza kuendelea.",
                next_step="check_pin"
            ),
            StepDefinition(
                step_id="itax_login_guide",
                step_type=StepType.INFO,
                prompt_en="Step 1: Login to iTax\n• Go to https://itax.kra.go.ke\n• Enter your KRA PIN: {kra_pin}\n• Enter your password\n• Click 'Login'\n\nAre you logged in?",
                prompt_sw="Hatua ya 1: Ingia iTax\n• Nenda https://itax.kra.go.ke\n• Ingiza PIN yako ya KRA: {kra_pin}\n• Ingiza nenosiri lako\n• Bonyeza 'Login'\n\nUmeingia?",
                next_step="navigate_returns"
            ),
            StepDefinition(
                step_id="navigate_returns",
                step_type=StepType.PROMPT,
                prompt_en="Step 2: Navigate to Returns\n• Click 'Returns' in the top menu\n• Select 'File Returns'\n• Choose 'Income Tax - Resident Individual'\n\nAre you on the returns page? (Yes/No)",
                prompt_sw="Hatua ya 2: Nenda Returns\n• Bonyeza 'Returns' kwenye menyu ya juu\n• Chagua 'File Returns'\n• Chagua 'Income Tax - Resident Individual'\n\nUko kwenye ukurasa wa returns? (Ndio/Hapana)",
                entity_name="on_returns_page",
                validator="yes_no",
                next_step="fill_nil_return"
            ),
            StepDefinition(
                step_id="fill_nil_return",
                step_type=StepType.INFO,
                prompt_en="Step 3: Fill the Nil Return\n• Select the tax year (e.g., 2024)\n• For 'Employment Income': Enter 0\n• For 'Business Income': Enter 0\n• For 'Other Income': Enter 0\n• Scroll down and click 'Submit'\n\nHave you filled in zeros and submitted?",
                prompt_sw="Hatua ya 3: Jaza Nil Return\n• Chagua mwaka wa kodi (mfano, 2024)\n• Kwa 'Employment Income': Ingiza 0\n• Kwa 'Business Income': Ingiza 0\n• Kwa 'Other Income': Ingiza 0\n• Sogeza chini na bonyeza 'Submit'\n\nUmejaza sufuri na kuwasilisha?",
                next_step="download_receipt"
            ),
            StepDefinition(
                step_id="download_receipt",
                step_type=StepType.PROMPT,
                prompt_en="Step 4: Download Acknowledgment Receipt\n• After submission, click 'Download Acknowledgment Receipt'\n• Save this PDF - it's your proof of filing!\n\nDid you successfully download your receipt? (Yes/No)",
                prompt_sw="Hatua ya 4: Pakua Risiti ya Uthibitisho\n• Baada ya kuwasilisha, bonyeza 'Download Acknowledgment Receipt'\n• Hifadhi PDF hii - ni uthibitisho wako wa kuwasilisha!\n\nUmefanikiwa kupakua risiti yako? (Ndio/Hapana)",
                entity_name="receipt_downloaded",
                validator="yes_no",
                next_step="completion_check"
            ),
            StepDefinition(
                step_id="completion_check",
                step_type=StepType.BRANCH,
                prompt_en="Checking completion...",
                prompt_sw="Inakagua ukamilifu...",
                branches={
                    "yes": None,  # Complete
                    "no": "troubleshoot"
                },
                next_step=None
            ),
            StepDefinition(
                step_id="troubleshoot",
                step_type=StepType.INFO,
                prompt_en="If you're having trouble:\n• Check your internet connection\n• Try refreshing the page\n• If the error persists, call KRA helpline: 0800 724 253\n\nWould you like to try again from the beginning?",
                prompt_sw="Ukipata shida:\n• Kagua muunganisho wako wa mtandao\n• Jaribu kuburudisha ukurasa\n• Hitilafu ikiendelea, piga simu kwa msaada wa KRA: 0800 724 253\n\nUngependa kujaribu tena kutoka mwanzo?",
                next_step="navigate_returns"
            )
        ]
    )


def get_dci_good_conduct_workflow() -> WorkflowDefinition:
    """DCI Certificate of Good Conduct application workflow."""
    return WorkflowDefinition(
        workflow_id="dci_good_conduct",
        name_en="DCI Good Conduct Certificate",
        name_sw="Cheti cha Tabia Njema DCI",
        description_en="Apply for a Certificate of Good Conduct (Police Clearance)",
        description_sw="Omba Cheti cha Tabia Njema (Police Clearance)",
        agency="DCI",
        initial_step="welcome",
        estimated_time_minutes=7,
        completion_message_en="Your good conduct certificate application information has been recorded. Next steps:\n1. Visit any DCI office or Huduma Centre with your documents\n2. Pay the application fee (Ksh 1,050)\n3. Have your fingerprints captured\n4. Certificate processing takes 2-3 weeks\n\nYou will receive updates at {phone_number}.",
        completion_message_sw="Maelezo ya maombi yako ya cheti cha tabia njema yamerekodiwa. Hatua zifuatazo:\n1. Tembelea ofisi yoyote ya DCI au Huduma Centre na nyaraka zako\n2. Lipa ada ya maombi (Ksh 1,050)\n3. Alama za vidole zitanaswa\n4. Uchakataji wa cheti unachukua wiki 2-3\n\nUtapokea sasisho kwa {phone_number}.",
        steps=[
            StepDefinition(
                step_id="welcome",
                step_type=StepType.INFO,
                prompt_en="I'll help you apply for a Certificate of Good Conduct from the DCI. This certificate is required for employment, travel, and other official purposes.",
                prompt_sw="Nitakusaidia kuomba Cheti cha Tabia Njema kutoka DCI. Cheti hiki kinahitajika kwa ajira, kusafiri, na madhumuni mengine rasmi.",
                next_step="purpose"
            ),
            StepDefinition(
                step_id="purpose",
                step_type=StepType.PROMPT,
                prompt_en="What is the purpose of this certificate?\n1. Employment\n2. Travel/Immigration\n3. Education\n4. Other",
                prompt_sw="Cheti hiki ni kwa madhumuni gani?\n1. Ajira\n2. Kusafiri/Uhamiaji\n3. Elimu\n4. Mengine",
                entity_name="purpose",
                next_step="full_name"
            ),
            StepDefinition(
                step_id="full_name",
                step_type=StepType.PROMPT,
                prompt_en="Please provide your full name as it appears on your National ID.",
                prompt_sw="Tafadhali toa jina lako kamili kama linavyoonekana kwenye kitambulisho chako.",
                entity_name="full_name",
                validator="name",
                next_step="national_id"
            ),
            StepDefinition(
                step_id="national_id",
                step_type=StepType.PROMPT,
                prompt_en="Please provide your National ID number.",
                prompt_sw="Tafadhali toa nambari yako ya kitambulisho.",
                entity_name="national_id",
                validator="national_id",
                next_step="phone_number"
            ),
            StepDefinition(
                step_id="phone_number",
                step_type=StepType.PROMPT,
                prompt_en="Please provide your phone number for notifications.",
                prompt_sw="Tafadhali toa nambari yako ya simu kwa arifa.",
                entity_name="phone_number",
                validator="phone_ke",
                next_step="requirements_info"
            ),
            StepDefinition(
                step_id="requirements_info",
                step_type=StepType.INFO,
                prompt_en="📋 Required Documents:\n• Original National ID (and copy)\n• 2 passport-size photos\n• Application fee: Ksh 1,050\n• For travel: Passport copy and invitation letter\n\n📍 Where to Apply:\n• Any DCI headquarters\n• Huduma Centres nationwide\n• Processing time: 2-3 weeks",
                prompt_sw="📋 Nyaraka Zinazohitajika:\n• Kitambulisho cha Asili (na nakala)\n• Picha 2 za pasipoti\n• Ada ya maombi: Ksh 1,050\n• Kwa kusafiri: Nakala ya pasipoti na barua ya mwaliko\n\n📍 Wapi Kuomba:\n• Makao makuu yoyote ya DCI\n• Huduma Centres nchini kote\n• Muda wa uchakataji: Wiki 2-3",
                next_step="confirm_details"
            ),
            StepDefinition(
                step_id="confirm_details",
                step_type=StepType.CONFIRM,
                prompt_en="I have recorded your details:\n• Name: {full_name}\n• ID: {national_id}\n• Phone: {phone_number}\n• Purpose: {purpose}\n\nWould you like me to save this and send you a reminder? (Yes/No)",
                prompt_sw="Nimehifadhi maelezo yako:\n• Jina: {full_name}\n• Kitambulisho: {national_id}\n• Simu: {phone_number}\n• Madhumuni: {purpose}\n\nUngependa nihifadhi hii na kukutumia ukumbusho? (Ndio/Hapana)",
                next_step="send_reminder",
                branches={"no": None}
            ),
            StepDefinition(
                step_id="send_reminder",
                step_type=StepType.ACTION,
                prompt_en="Saving your information...",
                prompt_sw="Inahifadhi maelezo yako...",
                action_handler="log_audit",
                next_step=None
            )
        ]
    )


def get_huduma_centre_workflow() -> WorkflowDefinition:
    """Huduma Centre location lookup workflow."""
    return WorkflowDefinition(
        workflow_id="huduma_centre_lookup",
        name_en="Find Nearest Huduma Centre",
        name_sw="Tafuta Huduma Centre Karibu Nawe",
        description_en="Find the nearest Huduma Centre and get directions",
        description_sw="Tafuta Huduma Centre karibu nawe na upate maelekezo",
        agency="Huduma Kenya",
        initial_step="welcome",
        estimated_time_minutes=3,
        completion_message_en="I found Huduma Centres near {location}. The nearest is {nearest_centre} which is {distance} away. Operating hours: {hours}. Would you like directions?",
        completion_message_sw="Nimepata Huduma Centres karibu na {location}. Karibu zaidi ni {nearest_centre} ambayo iko {distance} mbali. Masaa ya kufanya kazi: {hours}. Ungependa maelekezo?",
        steps=[
            StepDefinition(
                step_id="welcome",
                step_type=StepType.INFO,
                prompt_en="I'll help you find the nearest Huduma Centre where you can access government services.",
                prompt_sw="Nitakusaidia kupata Huduma Centre karibu zaidi ambapo unaweza kupata huduma za serikali.",
                next_step="get_location"
            ),
            StepDefinition(
                step_id="get_location",
                step_type=StepType.PROMPT,
                prompt_en="Please tell me your location. You can say the city/town name or area (e.g., 'Juja', 'Westlands', 'Mombasa CBD').",
                prompt_sw="Tafadhali niambie eneo lako. Unaweza sema jina la mji au eneo (mfano, 'Juja', 'Westlands', 'Mombasa CBD').",
                entity_name="location",
                next_step="service_needed"
            ),
            StepDefinition(
                step_id="service_needed",
                step_type=StepType.PROMPT,
                prompt_en="What service do you need at the Huduma Centre?\n1. National ID\n2. KRA PIN\n3. Passport\n4. NHIF/NSSF\n5. Business Registration\n6. Other/Not sure",
                prompt_sw="Unahitaji huduma gani kwenye Huduma Centre?\n1. Kitambulisho\n2. KRA PIN\n3. Pasipoti\n4. NHIF/NSSF\n5. Usajili wa Biashara\n6. Nyingine/Sijui",
                entity_name="service_needed",
                next_step="transport_mode"
            ),
            StepDefinition(
                step_id="transport_mode",
                step_type=StepType.PROMPT,
                prompt_en="How will you travel to the Huduma Centre?\n1. Walking\n2. Matatu/PSV\n3. Private vehicle\n4. Boda boda/Motorcycle",
                prompt_sw="Utasafiri vipi kwenda Huduma Centre?\n1. Kutembea\n2. Matatu/PSV\n3. Gari binafsi\n4. Boda boda",
                entity_name="transport_mode",
                next_step="find_centres"
            ),
            StepDefinition(
                step_id="find_centres",
                step_type=StepType.ACTION,
                prompt_en="Searching for nearby Huduma Centres...",
                prompt_sw="Inatafuta Huduma Centres karibu...",
                action_handler="lookup_huduma_centres",
                next_step=None
            )
        ]
    )


def get_constitution_query_workflow() -> WorkflowDefinition:
    """Constitutional knowledge query workflow."""
    return WorkflowDefinition(
        workflow_id="constitution_query",
        name_en="Constitutional Knowledge",
        name_sw="Maarifa ya Katiba",
        description_en="Learn about the Kenya Constitution 2010",
        description_sw="Jifunze kuhusu Katiba ya Kenya 2010",
        agency="Judiciary",
        initial_step="welcome",
        estimated_time_minutes=5,
        completion_message_en="I hope this information was helpful! The Constitution of Kenya 2010 is available at http://kenyalaw.org. Feel free to ask more questions about your rights.",
        completion_message_sw="Natumaini maelezo haya yalikuwa ya msaada! Katiba ya Kenya 2010 inapatikana kwa http://kenyalaw.org. Jisikie huru kuuliza maswali zaidi kuhusu haki zako.",
        steps=[
            StepDefinition(
                step_id="welcome",
                step_type=StepType.INFO,
                prompt_en="I can answer questions about the Constitution of Kenya 2010. You can ask about:\n• Bill of Rights\n• Citizenship\n• Government Structure\n• Land and Environment\n• Public Finance\n• Any chapter or article",
                prompt_sw="Naweza kujibu maswali kuhusu Katiba ya Kenya 2010. Unaweza kuuliza kuhusu:\n• Haki za Binadamu\n• Uraia\n• Muundo wa Serikali\n• Ardhi na Mazingira\n• Fedha za Umma\n• Sura au kifungu chochote",
                next_step="question"
            ),
            StepDefinition(
                step_id="question",
                step_type=StepType.PROMPT,
                prompt_en="What would you like to know about the Constitution?",
                prompt_sw="Ungependa kujua nini kuhusu Katiba?",
                entity_name="query",
                next_step="search_constitution"
            ),
            StepDefinition(
                step_id="search_constitution",
                step_type=StepType.ACTION,
                prompt_en="Searching the Constitution...",
                prompt_sw="Inatafuta katika Katiba...",
                action_handler="search_rag",
                next_step="follow_up"
            ),
            StepDefinition(
                step_id="follow_up",
                step_type=StepType.PROMPT,
                prompt_en="Would you like to ask another question about the Constitution? (Yes/No)",
                prompt_sw="Ungependa kuuliza swali lingine kuhusu Katiba? (Ndio/Hapana)",
                entity_name="continue",
                validator="yes_no",
                branches={
                    "yes": "question",
                    "no": None
                },
                next_step=None
            )
        ]
    )


def get_feedback_workflow() -> WorkflowDefinition:
    """Citizen feedback submission workflow."""
    return WorkflowDefinition(
        workflow_id="feedback_submission",
        name_en="Submit Feedback",
        name_sw="Toa Maoni",
        description_en="Submit feedback about government services",
        description_sw="Toa maoni kuhusu huduma za serikali",
        agency="Citizen Services",
        initial_step="welcome",
        estimated_time_minutes=3,
        completion_message_en="Thank you for your feedback! Your reference number is {reference_id}. Your voice matters and helps improve government services.",
        completion_message_sw="Asante kwa maoni yako! Nambari yako ya kumbukumbu ni {reference_id}. Sauti yako ni muhimu na husaidia kuboresha huduma za serikali.",
        steps=[
            StepDefinition(
                step_id="welcome",
                step_type=StepType.INFO,
                prompt_en="Your feedback helps improve government services. You can submit feedback anonymously if you prefer.",
                prompt_sw="Maoni yako husaidia kuboresha huduma za serikali. Unaweza kutoa maoni bila kutoa jina lako ukipenda.",
                next_step="anonymous_check"
            ),
            StepDefinition(
                step_id="anonymous_check",
                step_type=StepType.PROMPT,
                prompt_en="Would you like to submit feedback anonymously? Your privacy is protected either way. (Yes/No)",
                prompt_sw="Ungependa kutoa maoni bila kutoa jina lako? Faragha yako inalindwa kwa vyovyote. (Ndio/Hapana)",
                entity_name="is_anonymous",
                validator="yes_no",
                branches={
                    "yes": "feedback_category",
                    "no": "get_contact"
                },
                next_step="feedback_category"
            ),
            StepDefinition(
                step_id="get_contact",
                step_type=StepType.PROMPT,
                prompt_en="Please provide your phone number or email for follow-up (optional).",
                prompt_sw="Tafadhali toa nambari yako ya simu au barua pepe kwa ufuatiliaji (si lazima).",
                entity_name="contact_info",
                required=False,
                next_step="feedback_category"
            ),
            StepDefinition(
                step_id="feedback_category",
                step_type=StepType.PROMPT,
                prompt_en="What type of feedback is this?\n1. Suggestion\n2. Complaint\n3. Praise\n4. Question\n5. Other",
                prompt_sw="Hii ni maoni ya aina gani?\n1. Pendekezo\n2. Malalamiko\n3. Sifa\n4. Swali\n5. Nyingine",
                entity_name="category",
                next_step="service_or_centre"
            ),
            StepDefinition(
                step_id="service_or_centre",
                step_type=StepType.PROMPT,
                prompt_en="Which service or Huduma Centre is this feedback about?",
                prompt_sw="Maoni haya ni kuhusu huduma gani au Huduma Centre ipi?",
                entity_name="subject",
                next_step="feedback_message"
            ),
            StepDefinition(
                step_id="feedback_message",
                step_type=StepType.PROMPT,
                prompt_en="Please share your feedback. Be as specific as possible.",
                prompt_sw="Tafadhali toa maoni yako. Kuwa maalum iwezekanavyo.",
                entity_name="message",
                next_step="submit_feedback"
            ),
            StepDefinition(
                step_id="submit_feedback",
                step_type=StepType.ACTION,
                prompt_en="Submitting your feedback...",
                prompt_sw="Inawasilisha maoni yako...",
                action_handler="submit_feedback",
                next_step=None
            )
        ]
    )


def get_emergency_report_workflow() -> WorkflowDefinition:
    """Emergency reporting workflow."""
    return WorkflowDefinition(
        workflow_id="emergency_report",
        name_en="Report Emergency",
        name_sw="Ripoti Dharura",
        description_en="Report an emergency situation",
        description_sw="Ripoti hali ya dharura",
        agency="Emergency Services",
        initial_step="safety_first",
        estimated_time_minutes=2,
        completion_message_en="Your emergency report (Ref: {reference_id}) has been logged. For immediate help, call 999 (Police/Fire/Ambulance) or 112 (National Emergency). Stay safe!",
        completion_message_sw="Ripoti yako ya dharura (Kumb: {reference_id}) imerekodiwa. Kwa msaada wa haraka, piga 999 (Polisi/Moto/Ambulensi) au 112 (Dharura ya Kitaifa). Kaa salama!",
        steps=[
            StepDefinition(
                step_id="safety_first",
                step_type=StepType.INFO,
                prompt_en="🚨 SAFETY FIRST!\n\nIf you are in immediate danger, call:\n• 999 - Police, Fire, Ambulance\n• 112 - National Emergency\n• 1199 - Kenya Red Cross\n\nAre you safe to continue reporting?",
                prompt_sw="🚨 USALAMA KWANZA!\n\nUkiwa hatarini sasa hivi, piga:\n• 999 - Polisi, Moto, Ambulensi\n• 112 - Dharura ya Kitaifa\n• 1199 - Msalaba Mwekundu Kenya\n\nUko salama kuendelea kuripoti?",
                next_step="emergency_type"
            ),
            StepDefinition(
                step_id="emergency_type",
                step_type=StepType.PROMPT,
                prompt_en="What type of emergency is this?\n1. Fire\n2. Medical\n3. Crime/Security\n4. Accident\n5. Natural Disaster\n6. Other",
                prompt_sw="Hii ni dharura ya aina gani?\n1. Moto\n2. Kiafya\n3. Uhalifu/Usalama\n4. Ajali\n5. Janga la Asili\n6. Nyingine",
                entity_name="emergency_type",
                next_step="location"
            ),
            StepDefinition(
                step_id="location",
                step_type=StepType.PROMPT,
                prompt_en="Please describe the location as precisely as possible (landmark, building name, street, area).",
                prompt_sw="Tafadhali elezea eneo kwa usahihi iwezekanavyo (alama, jina la jengo, barabara, eneo).",
                entity_name="location",
                next_step="description"
            ),
            StepDefinition(
                step_id="description",
                step_type=StepType.PROMPT,
                prompt_en="Briefly describe what is happening.",
                prompt_sw="Elezea kwa ufupi kinachoendelea.",
                entity_name="description",
                next_step="log_emergency"
            ),
            StepDefinition(
                step_id="log_emergency",
                step_type=StepType.ACTION,
                prompt_en="Logging emergency report...",
                prompt_sw="Inarekodi ripoti ya dharura...",
                action_handler="log_emergency",
                next_step=None
            )
        ]
    )


# Workflow registry
ALL_WORKFLOWS = {
    "ntsa_driving_license": get_ntsa_driving_license_workflow,
    "kra_nil_returns": get_kra_nil_returns_workflow,
    "dci_good_conduct": get_dci_good_conduct_workflow,
    "huduma_centre_lookup": get_huduma_centre_workflow,
    "constitution_query": get_constitution_query_workflow,
    "feedback_submission": get_feedback_workflow,
    "emergency_report": get_emergency_report_workflow,
}


def get_workflow(workflow_id: str) -> Optional[WorkflowDefinition]:
    """Get a workflow definition by ID."""
    factory = ALL_WORKFLOWS.get(workflow_id)
    if factory:
        return factory()
    return None


def list_workflows() -> Dict[str, Dict[str, str]]:
    """List all available workflows."""
    result = {}
    for workflow_id, factory in ALL_WORKFLOWS.items():
        workflow = factory()
        result[workflow_id] = {
            "name_en": workflow.name_en,
            "name_sw": workflow.name_sw,
            "description_en": workflow.description_en,
            "description_sw": workflow.description_sw,
            "agency": workflow.agency,
            "estimated_time": f"{workflow.estimated_time_minutes} minutes"
        }
    return result


def register_all_workflows(engine: "WorkflowEngine"):
    """Register all workflows with the engine."""
    for workflow_id, factory in ALL_WORKFLOWS.items():
        engine.register_workflow(factory())
