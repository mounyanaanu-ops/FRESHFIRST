"""FreshFirst: perishable produce dispatch planner (hackathon prototype).
All sample data is synthetic. Run with:  python -m streamlit run app.py
"""
from collections import defaultdict

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="FreshFirst", page_icon="🥬", layout="wide")

# ---------------------------------------------------------------
# LOOK AND FEEL: one green "fresh" theme, bigger text
# ---------------------------------------------------------------
GREEN, DARK, SOFT = "#1B7F4C", "#14532D", "#EAF4EC"
st.markdown(f"""
<style>
html, body, [class*="css"] {{ font-size: 18px; }}
.block-container {{ padding-top: 2.2rem; max-width: 1100px; }}
h1, h2, h3 {{ color: {DARK}; }}
section[data-testid="stSidebar"] {{ background: {SOFT}; }}
[data-testid="stMetric"] {{ background: #FFFFFF; border: 1px solid #CFE3D3; border-radius: 16px; padding: 16px 18px; }}
[data-testid="stMetricValue"] {{ color: {DARK}; font-size: 2.3rem; }}
div[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 16px; }}
.stButton > button, .stDownloadButton > button {{ border-radius: 12px; font-weight: 600; padding: 0.55rem 1.3rem; }}
.stButton > button[kind="primary"] {{ background: {GREEN}; border-color: {GREEN}; color: #FFFFFF; }}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# SETTINGS that the user can change (kept between pages)
# ---------------------------------------------------------------
_defaults = {"lang": "en", "page": "data", "mode": "sample", "base": "fifo",
             "handling": 1.0, "disposal": 2.0, "disc_pct": 15, "uplift_pct": 30,
             "s_demand": 0, "s_shelf": 0, "s_delay": 0}
for _k, _v in _defaults.items():
    st.session_state.setdefault(_k, _v)
for _k in _defaults:                      # keep widget values when a page does not draw them
    st.session_state[_k] = st.session_state[_k]

HANDLING = float(st.session_state.handling)      # Rs per kg handling cost on every kg sent
DISPOSAL = float(st.session_state.disposal)      # Rs per kg cost of throwing away spoiled stock
DISC = st.session_state.disc_pct / 100           # discount rate
UPLIFT = st.session_state.uplift_pct / 100       # extra demand a discount creates (assumption)

# ---------------------------------------------------------------
# TEXT IN THREE LANGUAGES
# ---------------------------------------------------------------
TX = {}
TX["en"] = {
 "app_tagline": "Decide what to send where, so less food spoils and more money is earned.",
 "lang": "Language", "nav": "Go to page",
 "p_data": "1. Data", "p_plan": "2. Your plan", "p_results": "3. Results", "p_whatif": "4. What if?", "p_about": "5. About",
 "step_of": "Step {n} of 5",
 "badge_sample": "Using: sample data (synthetic)", "badge_user": "Using: your uploaded data",
 "synth_note": "The sample data is SYNTHETIC (made up by a program). Results show how the method behaves in a simulation, not real-world performance.",
 "need_data": "Please add your data first (Step 1).",
 "data_title": "Step 1: Choose your data",
 "data_intro": "FreshFirst needs three small tables: your stock, your shops, and what each shop wants and pays. You can try the sample data first.",
 "mode_label": "How do you want to give the data?", "mode_sample": "Use sample data", "mode_upload": "Upload my own files",
 "dl_templates": "Download an example of each file to see the format",
 "up_stock": "Stock file (stock.csv)", "up_markets": "Shops file (markets.csv)", "up_demand": "Demand and price file (demand.csv)",
 "upload_all": "Please upload all three files, or choose the sample data.",
 "data_ok": "Data is ready.",
 "rules_title": "Cost rules (you can change them)",
 "r_handling": "Handling cost (Rs per kg)", "r_disposal": "Cost of throwing away spoiled food (Rs per kg)",
 "r_disc": "Discount offered (%)", "r_uplift": "Extra demand a discount creates (%)",
 "tbl_stock": "Your stock", "tbl_markets": "Your shops", "tbl_demand": "What each shop wants and pays",
 "btn_make": "Make my plan →", "btn_back": "← Back", "btn_next": "Next →",
 "c_batch": "Batch", "c_item": "Produce", "c_shop": "Shop", "c_kg": "Quantity (kg)", "c_days_left": "Days of freshness left",
 "c_risk": "Urgency", "c_travel": "Travel days", "c_cost": "Transport cost (Rs/kg)", "c_cap": "Truck capacity (kg)",
 "c_demand": "Demand (kg)", "c_price": "Price (Rs/kg)", "c_disc": "Discount?", "c_why": "Why", "c_notsold": "Not sold fresh (kg)",
 "u_high": "SEND SOON", "u_ok": "OK", "yes": "Yes", "no": "No",
 "plan_title": "Step 2: Your dispatch plan", "plan_intro": "Here is what to send to each shop, and why.",
 "plan_summary": "FreshFirst plan: {sent} kg sent to {shops} shops, {disc} kg of it at a discount, and {spoil} kg could not be sold fresh.",
 "strategy_line": "Strategy chosen: {s}", "s_urgent": "urgent stock first", "s_value": "most profitable cargo first",
 "sec_by_shop": "What to send to each shop", "shop_nothing": "Nothing to send to this shop.",
 "sec_disc": "Discounts", "disc_none": "No discounts are needed.",
 "sec_left": "Stock that cannot be sold fresh", "left_none": "All stock can be sold.",
 "dl_plan": "Download the plan (CSV)",
 "res_title": "Step 3: How good is the plan?",
 "res_intro": "We compare FreshFirst with a simple method. Both use the same data and the same costs.",
 "cmp_with": "Compare FreshFirst with",
 "m_fifo": "Earliest expiry first (nearest feasible shop)", "m_price": "Price first (most expensive produce first)",
 "n_fifo": "Earliest-expiry baseline", "n_price": "Price first",
 "k_spoil": "Food spoiled (kg)", "k_demand": "Demand met", "k_money": "Money earned (Rs)",
 "h_spoil": "Lower is better.", "h_demand": "Share of what shops wanted that arrived fresh. Higher is better.",
 "h_money": "Sales minus transport, handling and waste costs. Higher is better.",
 "arrows_cap": "Small arrows compare FreshFirst with: {base}",
 "money_more": "FreshFirst earns Rs {x} MORE than {base}.", "money_less": "FreshFirst earns Rs {x} LESS than {base}.",
 "money_same": "FreshFirst earns about the same as {base}.",
 "spoil_less": "It spoils {x} kg LESS food.", "spoil_more": "It spoils {x} kg MORE food.", "spoil_same": "It spoils the same amount of food.",
 "rule_ok": "Rule check passed: nothing over-sent, no shop over-filled, no food arriving after it expires.",
 "rule_bad": "{n} rules were broken in the FreshFirst plan.",
 "tbl_all": "All methods side by side", "col_method": "Method", "col_rules": "Rules broken",
 "rules_help_title": "What are 'rules'?",
 "rules_help": "A plan breaks a rule if it sends more than we have, gives a shop more than it wants, overloads a truck, or sends food that expires before it arrives.",
 "see_base": "See the plans made by the simple methods", "rule_broken": "Rule broken: ",
 "chart_money": "Money earned (Rs)", "chart_spoil": "Food spoiled (kg)",
 "wi_title": "Step 4: What if things change?",
 "wi_intro": "Real life is not perfect. Move the sliders to see how the plan holds up.",
 "s_demand": "Shops want more or less (%)", "s_shelf": "Food lasts more or fewer days", "s_delay": "Trucks run late (extra days)",
 "wi_result": "Result with these changes",
 "stress_title": "Quick stress test", "stress_intro": "FreshFirst against the chosen simple method in five tough situations.",
 "sc_normal": "Normal day", "sc_demand": "Demand falls 20%", "sc_shelf": "Food lasts 1 day less",
 "sc_late": "Trucks run 1 day late", "sc_all": "All three together", "col_scn": "Situation",
 "col_ours_money": "FreshFirst money (Rs)", "col_base_money": "Simple method money (Rs)",
 "col_ours_spoil": "FreshFirst spoiled (kg)", "col_base_spoil": "Simple method spoiled (kg)",
 "about_title": "Step 5: About FreshFirst", "how_title": "How FreshFirst works",
 "how1": "It lists every batch of produce and how many days it will stay fresh.",
 "how2": "For each batch it checks which shops the produce can reach before it expires.",
 "how3": "It builds two plans: one handles the soonest-to-expire stock first, the other sends the most profitable produce first. It keeps the plan that earns more.",
 "how4": "If stock is about to expire and no shop will buy it at full price, it offers a discount, but only when that earns more than letting the food spoil.",
 "assump_title": "Assumptions",
 "as1": "The sample data is synthetic. Every method uses the same data and the same cost rules.",
 "as2": "A delivery is on time if the travel days are less than or equal to the days of freshness left.",
 "as3": "This is a single-round simulation: stock not sold fresh by the end of the round is counted as unsold/spoilage for scoring (disposal cost Rs {disp} per kg). This is a simplifying assumption, not a claim that all unsent stock expires immediately.",
 "as4": "Handling (Rs {hand} per kg) and transport costs are paid on every kg sent.",
 "as5": "Discount {disc}%: only for batches with 2 days or less left, only after full-price demand is used up, and only if it beats letting the food spoil. We assume a discount creates {up}% extra demand.",
 "limits_title": "Limits", "limits": "One dispatch round only. No demand forecasting. Capacity is the total available dispatch capacity per destination for this round. Unsent stock is treated as unsold/spoilage at the round boundary by assumption. The sample data is synthetic. Discount-driven extra demand is an assumption, not a measurement.",
 "r_fifo": "Earliest-expiry-first, nearest feasible shop", "r_price": "Highest-price shop it can reach in time",
 "r_sale": "Sent to {shop}: arrives in {days} day(s), {shelf} day(s) of freshness left, earns Rs {profit} per kg after costs",
 "r_disc": "{pct}% discount: only {shelf} day(s) left and full-price demand is finished. Selling at {shop} still earns Rs {gain} per kg more than letting it spoil",
 "err_read": "{f}: could not read this file. Please upload a CSV file.",
 "err_missing": "{f}: missing columns: {cols}",
 "err_cells": "{f}: some cells are empty, or have letters where numbers are needed.",
 "err_neg": "{f}: negative numbers are not allowed.",
 "err_dup": "{f}: the same row appears twice.",
 "err_dest": "demand.csv mentions a shop that is not in markets.csv: {x}",
}
TX["hi"] = {
 "app_tagline": "तय करें कि कौन-सा माल किस दुकान को भेजना है, ताकि कम खाना खराब हो और ज़्यादा कमाई हो।",
 "lang": "भाषा", "nav": "पेज चुनें",
 "p_data": "1. डेटा", "p_plan": "2. आपकी योजना", "p_results": "3. नतीजे", "p_whatif": "4. अगर ऐसा हो तो?", "p_about": "5. जानकारी",
 "step_of": "चरण {n} / 5",
 "badge_sample": "इस्तेमाल में: नमूना डेटा (बनावटी)", "badge_user": "इस्तेमाल में: आपका अपलोड किया डेटा",
 "synth_note": "नमूना डेटा बनावटी है (प्रोग्राम से बनाया गया)। नतीजे दिखाते हैं कि तरीका इस सिमुलेशन में कैसे काम करता है, असली दुनिया में नहीं।",
 "need_data": "कृपया पहले अपना डेटा जोड़ें (चरण 1)।",
 "data_title": "चरण 1: अपना डेटा चुनें",
 "data_intro": "FreshFirst को तीन छोटी तालिकाएँ चाहिए: आपका माल, आपकी दुकानें, और हर दुकान को क्या चाहिए और वह क्या दाम देती है। पहले नमूना डेटा आज़मा सकते हैं।",
 "mode_label": "डेटा कैसे देना है?", "mode_sample": "नमूना डेटा इस्तेमाल करें", "mode_upload": "अपनी फ़ाइलें अपलोड करें",
 "dl_templates": "फ़ॉर्मैट देखने के लिए हर फ़ाइल का नमूना डाउनलोड करें",
 "up_stock": "माल की फ़ाइल (stock.csv)", "up_markets": "दुकानों की फ़ाइल (markets.csv)", "up_demand": "माँग और दाम की फ़ाइल (demand.csv)",
 "upload_all": "कृपया तीनों फ़ाइलें अपलोड करें, या नमूना डेटा चुनें।",
 "data_ok": "डेटा तैयार है।",
 "rules_title": "खर्च के नियम (आप बदल सकते हैं)",
 "r_handling": "संभालने का खर्च (रु. प्रति किलो)", "r_disposal": "खराब माल फेंकने का खर्च (रु. प्रति किलो)",
 "r_disc": "छूट (%)", "r_uplift": "छूट से बढ़ने वाली माँग (%)",
 "tbl_stock": "आपका माल", "tbl_markets": "आपकी दुकानें", "tbl_demand": "हर दुकान को क्या चाहिए और दाम",
 "btn_make": "मेरी योजना बनाएँ →", "btn_back": "← पीछे", "btn_next": "आगे →",
 "c_batch": "खेप", "c_item": "सामान", "c_shop": "दुकान", "c_kg": "मात्रा (किलो)", "c_days_left": "ताज़ा रहने के बचे दिन",
 "c_risk": "जल्दी", "c_travel": "सफ़र के दिन", "c_cost": "ढुलाई (रु./किलो)", "c_cap": "ट्रक क्षमता (किलो)",
 "c_demand": "माँग (किलो)", "c_price": "दाम (रु./किलो)", "c_disc": "छूट?", "c_why": "कारण", "c_notsold": "ताज़ा न बिकने वाला (किलो)",
 "u_high": "जल्दी भेजें", "u_ok": "ठीक", "yes": "हाँ", "no": "नहीं",
 "plan_title": "चरण 2: आपकी भेजने की योजना", "plan_intro": "हर दुकान को क्या भेजना है और क्यों, यह यहाँ है।",
 "plan_summary": "FreshFirst योजना: {shops} दुकानों को {sent} किलो भेजा जाएगा, इसमें से {disc} किलो छूट पर, और {spoil} किलो ताज़ा नहीं बिक पाएगा।",
 "strategy_line": "चुनी गई रणनीति: {s}", "s_urgent": "जल्दी खराब होने वाला माल पहले", "s_value": "सबसे ज़्यादा मुनाफ़े वाला माल पहले",
 "sec_by_shop": "हर दुकान को क्या भेजें", "shop_nothing": "इस दुकान को कुछ नहीं भेजना।",
 "sec_disc": "छूट", "disc_none": "किसी छूट की ज़रूरत नहीं है।",
 "sec_left": "जो माल ताज़ा नहीं बिक सकता", "left_none": "सारा माल बिक सकता है।",
 "dl_plan": "योजना डाउनलोड करें (CSV)",
 "res_title": "चरण 3: योजना कितनी अच्छी है?",
 "res_intro": "हम FreshFirst की तुलना एक सीधे तरीके से करते हैं। दोनों में डेटा और खर्च एक जैसे हैं।",
 "cmp_with": "FreshFirst की तुलना किससे करें",
 "m_fifo": "पहले समाप्त होने वाला माल (सबसे नज़दीकी संभव दुकान)", "m_price": "दाम पहले (सबसे महँगा माल पहले)",
 "n_fifo": "Earliest-expiry baseline", "n_price": "दाम पहले",
 "k_spoil": "खराब खाना (किलो)", "k_demand": "पूरी हुई माँग", "k_money": "कमाई (रु.)",
 "h_spoil": "कम होना बेहतर है।", "h_demand": "दुकानों की जितनी माँग थी, उसमें से कितना ताज़ा पहुँचा। ज़्यादा बेहतर है।",
 "h_money": "बिक्री में से ढुलाई, संभाल और बर्बादी का खर्च घटाकर। ज़्यादा बेहतर है।",
 "arrows_cap": "छोटे तीर FreshFirst की तुलना इससे दिखाते हैं: {base}",
 "money_more": "FreshFirst, {base} से रु. {x} ज़्यादा कमाता है।", "money_less": "FreshFirst, {base} से रु. {x} कम कमाता है।",
 "money_same": "FreshFirst की कमाई {base} के लगभग बराबर है।",
 "spoil_less": "यह {x} किलो कम खाना खराब करता है।", "spoil_more": "यह {x} किलो ज़्यादा खाना खराब करता है।", "spoil_same": "यह उतना ही खाना खराब करता है।",
 "rule_ok": "नियम जाँच पास: कुछ भी ज़्यादा नहीं भेजा, कोई दुकान ज़्यादा नहीं भरी, कोई माल एक्सपायर होकर नहीं पहुँचा।",
 "rule_bad": "FreshFirst योजना में {n} नियम टूटे।",
 "tbl_all": "सभी तरीके साथ-साथ", "col_method": "तरीका", "col_rules": "टूटे नियम",
 "rules_help_title": "'नियम' क्या हैं?",
 "rules_help": "योजना तब नियम तोड़ती है जब वह जितना माल है उससे ज़्यादा भेजे, किसी दुकान को उसकी माँग से ज़्यादा दे, ट्रक की क्षमता से ज़्यादा लादे, या ऐसा माल भेजे जो पहुँचने से पहले एक्सपायर हो जाए।",
 "see_base": "सीधे तरीकों की योजनाएँ देखें", "rule_broken": "टूटा नियम: ",
 "chart_money": "कमाई (रु.)", "chart_spoil": "खराब खाना (किलो)",
 "wi_title": "चरण 4: अगर हालात बदल जाएँ तो?",
 "wi_intro": "असली ज़िंदगी परफ़ेक्ट नहीं होती। स्लाइडर हिलाकर देखें कि योजना कितनी टिकती है।",
 "s_demand": "दुकानों को ज़्यादा या कम चाहिए (%)", "s_shelf": "माल ज़्यादा या कम दिन टिकता है", "s_delay": "ट्रक देर से चलें (अतिरिक्त दिन)",
 "wi_result": "इन बदलावों के साथ नतीजा",
 "stress_title": "जल्दी वाली कठिन परीक्षा", "stress_intro": "पाँच मुश्किल हालात में FreshFirst और चुने हुए सीधे तरीके की तुलना।",
 "sc_normal": "सामान्य दिन", "sc_demand": "माँग 20% गिरी", "sc_shelf": "माल 1 दिन कम टिकता है",
 "sc_late": "ट्रक 1 दिन देर से", "sc_all": "तीनों एक साथ", "col_scn": "हालात",
 "col_ours_money": "FreshFirst कमाई (रु.)", "col_base_money": "सीधे तरीके की कमाई (रु.)",
 "col_ours_spoil": "FreshFirst खराब (किलो)", "col_base_spoil": "सीधे तरीके में खराब (किलो)",
 "about_title": "चरण 5: FreshFirst के बारे में", "how_title": "FreshFirst कैसे काम करता है",
 "how1": "यह हर खेप की सूची बनाता है और देखता है कि वह कितने दिन ताज़ा रहेगी।",
 "how2": "हर खेप के लिए देखता है कि एक्सपायर होने से पहले वह किन दुकानों तक पहुँच सकती है।",
 "how3": "यह दो योजनाएँ बनाता है: एक में जल्दी खराब होने वाला माल पहले जाता है, दूसरी में सबसे ज़्यादा मुनाफ़े वाला माल पहले। जो योजना ज़्यादा कमाती है, वही रखता है।",
 "how4": "अगर माल एक्सपायर होने वाला है और कोई दुकान पूरे दाम पर नहीं लेती, तो यह छूट देता है, लेकिन तभी जब इससे माल खराब होने देने से ज़्यादा कमाई हो।",
 "assump_title": "मान्यताएँ",
 "as1": "नमूना डेटा बनावटी है। हर तरीके में डेटा और खर्च के नियम एक जैसे हैं।",
 "as2": "डिलीवरी समय पर मानी जाती है अगर सफ़र के दिन, बचे ताज़ा दिनों से कम या बराबर हों।",
 "as3": "जो माल भेजा नहीं गया, या एक्सपायर होने के बाद पहुँचा, वह खराब गिना जाता है (फेंकने का खर्च रु. {disp} प्रति किलो)।",
 "as4": "भेजे गए हर किलो पर संभालने का (रु. {hand} प्रति किलो) और ढुलाई का खर्च लगता है।",
 "as5": "छूट {disc}%: सिर्फ़ उन खेपों पर जिनमें 2 दिन या कम बचे हों, पूरे दाम की माँग खत्म होने के बाद, और तभी जब यह माल खराब होने देने से बेहतर हो। हम मानते हैं कि छूट से {up}% ज़्यादा माँग बनती है।",
 "limits_title": "सीमाएँ", "limits": "सिर्फ़ एक भेजने का दौर। माँग का अनुमान नहीं। नमूना डेटा बनावटी है। छूट का असर नापा हुआ नहीं, एक मान्यता है।",
 "r_fifo": "पहले समाप्त होने वाला माल, सबसे नज़दीकी संभव दुकान", "r_price": "सबसे ऊँचे दाम वाली दुकान जहाँ समय पर पहुँचे",
 "r_sale": "{shop} को भेजा: {days} दिन में पहुँचेगा, {shelf} दिन ताज़गी बची, खर्च के बाद रु. {profit} प्रति किलो कमाई",
 "r_disc": "{pct}% छूट: सिर्फ़ {shelf} दिन बचे हैं और पूरे दाम की माँग खत्म है। {shop} में बेचना, माल खराब होने देने से रु. {gain} प्रति किलो ज़्यादा देता है",
 "err_read": "{f}: यह फ़ाइल पढ़ी नहीं जा सकी। कृपया CSV फ़ाइल अपलोड करें।",
 "err_missing": "{f}: ये कॉलम नहीं मिले: {cols}",
 "err_cells": "{f}: कुछ खाने खाली हैं, या जहाँ संख्या चाहिए वहाँ अक्षर हैं।",
 "err_neg": "{f}: ऋणात्मक संख्याएँ मान्य नहीं हैं।",
 "err_dup": "{f}: एक ही पंक्ति दो बार है।",
 "err_dest": "demand.csv में ऐसी दुकान है जो markets.csv में नहीं है: {x}",
}
TX["te"] = {
 "app_tagline": "ఏ సరుకు ఏ షాపుకు పంపాలో నిర్ణయించండి, దీనివల్ల తక్కువ ఆహారం పాడవుతుంది, ఎక్కువ ఆదాయం వస్తుంది.",
 "lang": "భాష", "nav": "పేజీని ఎంచుకోండి",
 "p_data": "1. డేటా", "p_plan": "2. మీ ప్లాన్", "p_results": "3. ఫలితాలు", "p_whatif": "4. ఒకవేళ ఇలా జరిగితే?", "p_about": "5. సమాచారం",
 "step_of": "దశ {n} / 5",
 "badge_sample": "వాడుతున్నది: నమూనా డేటా (కృత్రిమం)", "badge_user": "వాడుతున్నది: మీరు అప్‌లోడ్ చేసిన డేటా",
 "synth_note": "నమూనా డేటా కృత్రిమమైనది (ప్రోగ్రామ్ తయారు చేసింది). ఫలితాలు ఈ సిమ్యులేషన్‌లో పద్ధతి ఎలా పనిచేస్తుందో చూపుతాయి, నిజ జీవితంలో కాదు.",
 "need_data": "దయచేసి ముందు మీ డేటాను జోడించండి (దశ 1).",
 "data_title": "దశ 1: మీ డేటాను ఎంచుకోండి",
 "data_intro": "FreshFirst‌కు మూడు చిన్న పట్టికలు కావాలి: మీ సరుకు, మీ షాపులు, ప్రతి షాపుకు ఏమి కావాలి మరియు ఏ ధర ఇస్తుంది. ముందుగా నమూనా డేటాతో ప్రయత్నించవచ్చు.",
 "mode_label": "డేటా ఎలా ఇస్తారు?", "mode_sample": "నమూనా డేటా వాడండి", "mode_upload": "నా ఫైళ్లను అప్‌లోడ్ చేస్తా",
 "dl_templates": "ఫార్మాట్ చూడడానికి ప్రతి ఫైల్ నమూనాను డౌన్‌లోడ్ చేయండి",
 "up_stock": "సరుకు ఫైల్ (stock.csv)", "up_markets": "షాపుల ఫైల్ (markets.csv)", "up_demand": "డిమాండ్ మరియు ధర ఫైల్ (demand.csv)",
 "upload_all": "దయచేసి మూడు ఫైళ్లను అప్‌లోడ్ చేయండి, లేదా నమూనా డేటాను ఎంచుకోండి.",
 "data_ok": "డేటా సిద్ధంగా ఉంది.",
 "rules_title": "ఖర్చు నియమాలు (మీరు మార్చవచ్చు)",
 "r_handling": "నిర్వహణ ఖర్చు (రూ. కిలోకు)", "r_disposal": "పాడైన సరుకు పారవేసే ఖర్చు (రూ. కిలోకు)",
 "r_disc": "డిస్కౌంట్ (%)", "r_uplift": "డిస్కౌంట్ వల్ల పెరిగే డిమాండ్ (%)",
 "tbl_stock": "మీ సరుకు", "tbl_markets": "మీ షాపులు", "tbl_demand": "ప్రతి షాపుకు ఏమి కావాలి, ధర",
 "btn_make": "నా ప్లాన్ తయారు చేయి →", "btn_back": "← వెనక్కి", "btn_next": "తర్వాత →",
 "c_batch": "బ్యాచ్", "c_item": "సరుకు", "c_shop": "షాపు", "c_kg": "పరిమాణం (కిలోలు)", "c_days_left": "తాజాగా ఉండే మిగిలిన రోజులు",
 "c_risk": "అత్యవసరం", "c_travel": "ప్రయాణ రోజులు", "c_cost": "రవాణా (రూ./కిలో)", "c_cap": "ట్రక్ సామర్థ్యం (కిలోలు)",
 "c_demand": "డిమాండ్ (కిలోలు)", "c_price": "ధర (రూ./కిలో)", "c_disc": "డిస్కౌంట్?", "c_why": "కారణం", "c_notsold": "తాజాగా అమ్ముడుకానిది (కిలోలు)",
 "u_high": "త్వరగా పంపండి", "u_ok": "సరే", "yes": "అవును", "no": "కాదు",
 "plan_title": "దశ 2: మీ పంపిణీ ప్లాన్", "plan_intro": "ప్రతి షాపుకు ఏమి పంపాలో, ఎందుకో ఇక్కడ ఉంది.",
 "plan_summary": "FreshFirst ప్లాన్: {shops} షాపులకు {sent} కిలోలు పంపుతారు, వాటిలో {disc} కిలోలు డిస్కౌంట్‌తో, {spoil} కిలోలు తాజాగా అమ్మడం సాధ్యం కాదు.",
 "strategy_line": "ఎంచుకున్న వ్యూహం: {s}", "s_urgent": "త్వరగా గడువు ముగిసే సరుకు ముందు", "s_value": "ఎక్కువ లాభం ఇచ్చే సరుకు ముందు",
 "sec_by_shop": "ప్రతి షాపుకు ఏమి పంపాలి", "shop_nothing": "ఈ షాపుకు ఏమీ పంపక్కర్లేదు.",
 "sec_disc": "డిస్కౌంట్లు", "disc_none": "డిస్కౌంట్ అవసరం లేదు.",
 "sec_left": "తాజాగా అమ్మలేని సరుకు", "left_none": "మొత్తం సరుకు అమ్మవచ్చు.",
 "dl_plan": "ప్లాన్ డౌన్‌లోడ్ చేయండి (CSV)",
 "res_title": "దశ 3: ప్లాన్ ఎంత బాగుంది?",
 "res_intro": "FreshFirst‌ను ఒక సాధారణ పద్ధతితో పోలుస్తాము. రెండింటికీ డేటా, ఖర్చులు ఒకటే.",
 "cmp_with": "FreshFirst‌ను దేనితో పోల్చాలి",
 "m_fifo": "ముందుగా గడువు ముగిసేది (సాధ్యమైన దగ్గరి షాప్)", "m_price": "ధర ముందు (ఖరీదైన సరుకు ముందు)",
 "n_fifo": "Earliest-expiry baseline", "n_price": "ధర ముందు",
 "k_spoil": "పాడైన ఆహారం (కిలోలు)", "k_demand": "తీరిన డిమాండ్", "k_money": "ఆదాయం (రూ.)",
 "h_spoil": "తక్కువ ఉంటే మంచిది.", "h_demand": "షాపులు కోరిన దానిలో తాజాగా చేరిన వాటా. ఎక్కువ ఉంటే మంచిది.",
 "h_money": "అమ్మకాల నుండి రవాణా, నిర్వహణ, వృథా ఖర్చులు తీసివేసిన మొత్తం. ఎక్కువ ఉంటే మంచిది.",
 "arrows_cap": "చిన్న బాణాలు FreshFirst‌ను దీనితో పోలుస్తాయి: {base}",
 "money_more": "FreshFirst, {base} కంటే రూ. {x} ఎక్కువ సంపాదిస్తుంది.", "money_less": "FreshFirst, {base} కంటే రూ. {x} తక్కువ సంపాదిస్తుంది.",
 "money_same": "FreshFirst ఆదాయం {base}కు దాదాపు సమానం.",
 "spoil_less": "ఇది {x} కిలోల తక్కువ ఆహారాన్ని పాడుచేస్తుంది.", "spoil_more": "ఇది {x} కిలోల ఎక్కువ ఆహారాన్ని పాడుచేస్తుంది.", "spoil_same": "ఇది అంతే ఆహారాన్ని పాడుచేస్తుంది.",
 "rule_ok": "నియమాల తనిఖీ పాస్: ఏదీ ఎక్కువ పంపలేదు, ఏ షాపునూ ఎక్కువ నింపలేదు, గడువు ముగిసిన సరుకు చేరలేదు.",
 "rule_bad": "FreshFirst ప్లాన్‌లో {n} నియమాలు ఉల్లంఘించబడ్డాయి.",
 "tbl_all": "అన్ని పద్ధతులు పక్కపక్కన", "col_method": "పద్ధతి", "col_rules": "ఉల్లంఘించిన నియమాలు",
 "rules_help_title": "'నియమాలు' అంటే ఏమిటి?",
 "rules_help": "ప్లాన్ ఉన్న సరుకు కంటే ఎక్కువ పంపినా, షాపు కోరిన దానికంటే ఎక్కువ ఇచ్చినా, ట్రక్ సామర్థ్యం మించినా, లేదా చేరేలోపు గడువు ముగిసే సరుకు పంపినా నియమాన్ని ఉల్లంఘిస్తుంది.",
 "see_base": "సాధారణ పద్ధతుల ప్లాన్లు చూడండి", "rule_broken": "ఉల్లంఘన: ",
 "chart_money": "ఆదాయం (రూ.)", "chart_spoil": "పాడైన ఆహారం (కిలోలు)",
 "wi_title": "దశ 4: పరిస్థితులు మారితే?",
 "wi_intro": "నిజ జీవితం పరిపూర్ణంగా ఉండదు. స్లైడర్లను కదిపి ప్లాన్ ఎలా నిలుస్తుందో చూడండి.",
 "s_demand": "షాపులకు కావాల్సింది ఎక్కువ లేదా తక్కువ (%)", "s_shelf": "సరుకు ఎక్కువ లేదా తక్కువ రోజులు నిలుస్తుంది", "s_delay": "ట్రక్కులు ఆలస్యం (అదనపు రోజులు)",
 "wi_result": "ఈ మార్పులతో ఫలితం",
 "stress_title": "త్వరిత ఒత్తిడి పరీక్ష", "stress_intro": "ఐదు కష్టమైన పరిస్థితులలో FreshFirst‌ను ఎంచుకున్న సాధారణ పద్ధతితో పోలుస్తాము.",
 "sc_normal": "సాధారణ రోజు", "sc_demand": "డిమాండ్ 20% తగ్గింది", "sc_shelf": "సరుకు 1 రోజు తక్కువ నిలుస్తుంది",
 "sc_late": "ట్రక్కులు 1 రోజు ఆలస్యం", "sc_all": "మూడూ కలిసి", "col_scn": "పరిస్థితి",
 "col_ours_money": "FreshFirst ఆదాయం (రూ.)", "col_base_money": "సాధారణ పద్ధతి ఆదాయం (రూ.)",
 "col_ours_spoil": "FreshFirst పాడైనది (కిలోలు)", "col_base_spoil": "సాధారణ పద్ధతిలో పాడైనది (కిలోలు)",
 "about_title": "దశ 5: FreshFirst గురించి", "how_title": "FreshFirst ఎలా పనిచేస్తుంది",
 "how1": "ప్రతి బ్యాచ్ సరుకును, అది ఎన్ని రోజులు తాజాగా ఉంటుందో జాబితా చేస్తుంది.",
 "how2": "ప్రతి బ్యాచ్ గడువు ముగిసేలోపు ఏ షాపులకు చేరగలదో తనిఖీ చేస్తుంది.",
 "how3": "రెండు ప్లాన్లు తయారు చేస్తుంది: ఒకటి త్వరగా గడువు ముగిసే సరుకును ముందు చూస్తుంది, మరొకటి ఎక్కువ లాభం ఇచ్చే సరుకును ముందు పంపుతుంది. ఎక్కువ సంపాదించే ప్లాన్‌ను ఉంచుతుంది.",
 "how4": "సరుకు గడువు ముగియబోతూ, పూర్తి ధరకు ఏ షాపూ కొనకపోతే, డిస్కౌంట్ ఇస్తుంది. అది సరుకు పాడవనివ్వడం కంటే ఎక్కువ సంపాదిస్తేనే.",
 "assump_title": "ఊహలు",
 "as1": "నమూనా డేటా కృత్రిమమైనది. ప్రతి పద్ధతికి ఒకే డేటా, ఒకే ఖర్చు నియమాలు.",
 "as2": "ప్రయాణ రోజులు మిగిలిన తాజా రోజులకు సమానం లేదా తక్కువ ఉంటేనే డెలివరీ సమయానికి చేరినట్లు.",
 "as3": "పంపని సరుకు, లేదా గడువు ముగిశాక చేరిన సరుకు పాడైనట్లు లెక్క (పారవేసే ఖర్చు రూ. {disp}/కిలో).",
 "as4": "పంపిన ప్రతి కిలోకు నిర్వహణ (రూ. {hand}/కిలో) మరియు రవాణా ఖర్చు చెల్లించాలి.",
 "as5": "డిస్కౌంట్ {disc}%: 2 రోజులు లేదా తక్కువ మిగిలిన బ్యాచ్‌లకు మాత్రమే, పూర్తి ధర డిమాండ్ అయిపోయాకే, పాడవనివ్వడం కంటే లాభం ఇస్తేనే. డిస్కౌంట్ {up}% అదనపు డిమాండ్ తెస్తుందని ఊహిస్తున్నాం.",
 "limits_title": "పరిమితులు", "limits": "ఒక్క పంపిణీ రౌండ్ మాత్రమే. డిమాండ్ అంచనా లేదు. నమూనా డేటా కృత్రిమం. డిస్కౌంట్ ప్రభావం కొలిచింది కాదు, ఊహ మాత్రమే.",
 "r_fifo": "ముందుగా గడువు ముగిసే సరుకు, సాధ్యమైన దగ్గరి షాప్", "r_price": "గడువులోపు చేరగలిగే అత్యధిక ధర షాపు",
 "r_sale": "{shop}కు పంపుతున్నాం: {days} రోజుల్లో చేరుతుంది, {shelf} రోజులు తాజాగా ఉంటుంది, ఖర్చులు పోను కిలోకు రూ. {profit} లాభం",
 "r_disc": "{pct}% డిస్కౌంట్: {shelf} రోజులే మిగిలాయి, పూర్తి ధర డిమాండ్ అయిపోయింది. {shop}లో అమ్మడం పాడవనివ్వడం కంటే కిలోకు రూ. {gain} ఎక్కువ",
 "err_read": "{f}: ఫైల్ చదవలేకపోయాం. దయచేసి CSV ఫైల్ అప్‌లోడ్ చేయండి.",
 "err_missing": "{f}: ఈ నిలువు వరుసలు లేవు: {cols}",
 "err_cells": "{f}: కొన్ని గడులు ఖాళీగా ఉన్నాయి, లేదా సంఖ్యలు కావాల్సిన చోట అక్షరాలు ఉన్నాయి.",
 "err_neg": "{f}: రుణాత్మక సంఖ్యలు అనుమతించబడవు.",
 "err_dup": "{f}: ఒకే వరుస రెండుసార్లు ఉంది.",
 "err_dest": "demand.csv లో ఉన్న షాపు markets.csv లో లేదు: {x}",
}


def t(key, **kw):
    """Look up a text in the chosen language (falls back to English)."""
    text = TX.get(st.session_state.lang, {}).get(key) or TX["en"][key]
    return text.format(**kw) if kw else text


# ---------------------------------------------------------------
# SAMPLE DATA (synthetic; random but repeatable because the seed is fixed)
# ---------------------------------------------------------------
COMM = {"Tomato": (25, 6), "Banana": (40, 8), "Spinach": (30, 4), "Mango": (80, 7)}  # (price Rs/kg, max shelf days)


def make_data(seed=42):
    rng = np.random.default_rng(seed)
    names = list(COMM)
    batches = []
    for i in range(12):
        c = names[i % 4]
        batches.append({"batch_id": f"B{i+1:02d}", "commodity": c,
                        "quantity_kg": int(rng.integers(4, 17)) * 50,
                        "shelf_life_days": int(rng.integers(2, COMM[c][1] + 1))})
    batches = pd.DataFrame(batches)
    batches.loc[0, "shelf_life_days"] = 1  # deliberate test case: a nearly expired batch
    dest = pd.DataFrame([
        {"dest_id": "MarketA", "transport_days": 1, "cost_per_kg": 2.0, "capacity_kg": 1500},
        {"dest_id": "MarketB", "transport_days": 2, "cost_per_kg": 3.0, "capacity_kg": 1500},
        {"dest_id": "MarketC", "transport_days": 3, "cost_per_kg": 4.5, "capacity_kg": 1200},
        {"dest_id": "MarketD", "transport_days": 1, "cost_per_kg": 2.5, "capacity_kg": 800},
    ])
    rows = []
    for d in dest.dest_id:
        for c in names:
            rows.append({"dest_id": d, "commodity": c,
                         "demand_kg": int(rng.integers(2, 11)) * 50,
                         "price_per_kg": round(COMM[c][0] * float(rng.uniform(0.9, 1.2)), 1)})
    return batches, dest, pd.DataFrame(rows)


# ---------------------------------------------------------------
# READING AND CHECKING UPLOADED FILES
# ---------------------------------------------------------------
SCHEMA = {"stock": ["batch_id", "commodity", "quantity_kg", "shelf_life_days"],
          "markets": ["dest_id", "transport_days", "cost_per_kg", "capacity_kg"],
          "demand": ["dest_id", "commodity", "demand_kg", "price_per_kg"]}
NUMBERS = {"stock": ["quantity_kg", "shelf_life_days"],
           "markets": ["transport_days", "cost_per_kg", "capacity_kg"],
           "demand": ["demand_kg", "price_per_kg"]}
WHOLE = ["quantity_kg", "shelf_life_days", "transport_days", "capacity_kg", "demand_kg"]
KEYS = {"stock": ["batch_id"], "markets": ["dest_id"], "demand": ["dest_id", "commodity"]}


def read_table(file, kind):
    name = kind + ".csv"
    try:
        df = pd.read_csv(file)
    except Exception:
        return None, [t("err_read", f=name)]
    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = [c for c in SCHEMA[kind] if c not in df.columns]
    if missing:
        return None, [t("err_missing", f=name, cols=", ".join(missing))]
    df = df[SCHEMA[kind]].copy()
    for c in SCHEMA[kind]:
        if c not in NUMBERS[kind]:
            df[c] = df[c].astype(str).str.strip()
    for c in NUMBERS[kind]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if df.empty or df.isna().any().any():
        return None, [t("err_cells", f=name)]
    if (df[NUMBERS[kind]] < 0).any().any():
        return None, [t("err_neg", f=name)]
    if df.duplicated(KEYS[kind]).any():
        return None, [t("err_dup", f=name)]
    for c in [x for x in SCHEMA[kind] if x not in NUMBERS[kind]]:
        if df[c].str.strip().eq("").any() or df[c].str.lower().isin(["nan", "none"]).any():
            return None, [t("err_cells", f=name)]
    if kind == "markets" and (df["capacity_kg"] <= 0).any():
        return None, [t("err_cells", f=name)]
    if kind == "stock" and (df["shelf_life_days"] <= 0).any():
        return None, [t("err_cells", f=name)]
    for c in NUMBERS[kind]:
        if c in WHOLE:
            df[c] = df[c].round().astype(int)
    return df, []


def parse_uploads(files):
    tables, errors = {}, []
    for kind, f in files.items():
        df, errs = read_table(f, kind)
        errors += errs
        tables[kind] = df
    if not errors:
        unknown = sorted(set(tables["demand"].dest_id) - set(tables["markets"].dest_id))
        if unknown:
            errors.append(t("err_dest", x=", ".join(unknown)))
    if errors:
        return None, errors
    return (tables["stock"], tables["markets"], tables["demand"]), []


def active_data():
    if st.session_state.mode == "upload":
        return st.session_state.get("user_data")
    return make_data()


# ---------------------------------------------------------------
# PLAN HELPERS
# ---------------------------------------------------------------
COLS = ["batch_id", "commodity", "dest_id", "quantity_kg", "discount_applied",
        "kind", "profit", "days", "shelf", "gain"]


def row(b, d, room, discount, kind, profit=np.nan, gain=np.nan):
    return {"batch_id": b.batch_id, "commodity": b.commodity, "dest_id": d.dest_id, "quantity_kg": room,
            "discount_applied": discount, "kind": kind, "profit": profit,
            "days": d.transport_days, "shelf": b.shelf_life_days, "gain": gain}


def lookups(batches, dest, demand):
    price, dem = defaultdict(float), defaultdict(int)
    for r in demand.itertuples():
        price[(r.dest_id, r.commodity)] = r.price_per_kg
        dem[(r.dest_id, r.commodity)] = r.demand_kg
    extra = defaultdict(int, {k: int(round(v * UPLIFT)) for k, v in dem.items()})
    cap = dict(zip(dest.dest_id, dest.capacity_kg))
    left = dict(zip(batches.batch_id, batches.quantity_kg))
    return price, dem, extra, cap, left


# ---------------------------------------------------------------
# SIMPLE METHODS (the baselines we compare against)
# ---------------------------------------------------------------
def baseline(batches, dest, demand, mode):
    """Transparent comparison methods. Both respect shelf life and share the
    same discount policy as FreshFirst, so the allocation strategy is compared fairly.
       fifo  = earliest-expiry-first, then nearest feasible shop.
       price = higher average commodity price first, then best-price feasible shop."""
    price, dem, extra, cap, remaining = lookups(batches, dest, demand)
    if mode == "fifo":
        ordered = batches.sort_values(["shelf_life_days", "batch_id"])
    else:
        avg = demand.groupby("commodity").price_per_kg.mean()
        tmp = batches.assign(p=batches.commodity.map(avg).fillna(0))
        ordered = tmp.sort_values(["p", "shelf_life_days", "batch_id"], ascending=[False, True, True])
    rows = []
    for b in ordered.itertuples():
        left = int(remaining[b.batch_id])
        while left > 0:
            best = None
            for d in dest.itertuples():
                # All methods must reject deliveries that arrive after expiry.
                if d.transport_days > b.shelf_life_days:
                    continue
                room = int(min(left, dem[(d.dest_id, b.commodity)], cap[d.dest_id]))
                if room <= 0:
                    continue
                key = ((d.transport_days, d.cost_per_kg) if mode == "fifo"
                       else (-price[(d.dest_id, b.commodity)], d.transport_days, d.cost_per_kg))
                if best is None or key < best[0]:
                    best = (key, d, room)
            if best is None:
                break
            _, d, room = best
            left -= room
            remaining[b.batch_id] -= room
            dem[(d.dest_id, b.commodity)] -= room
            cap[d.dest_id] -= room
            rows.append(row(b, d, room, 0, mode))
    # Apply the exact same discount policy to the baseline after full-price allocation.
    rows += discount_pass(batches, dest, price, extra, cap, remaining)
    return pd.DataFrame(rows, columns=COLS)


# ---------------------------------------------------------------
# FRESHFIRST: two candidate plans, keep the better one
# ---------------------------------------------------------------
def discount_pass(batches, dest, price, extra, cap, left):
    """Stock with 2 days or less left that is still unsold: offer a discount,
    but only if that beats letting it spoil."""
    rows = []
    for b in batches.sort_values(["shelf_life_days", "batch_id"]).itertuples():
        if b.shelf_life_days > 2:
            continue
        while left[b.batch_id] > 0:
            best = None
            for d in dest.itertuples():
                if d.transport_days > b.shelf_life_days:
                    continue
                room = int(min(left[b.batch_id], extra[(d.dest_id, b.commodity)], cap[d.dest_id]))
                if room <= 0:
                    continue
                gain = price[(d.dest_id, b.commodity)] * (1 - DISC) - d.cost_per_kg - HANDLING + DISPOSAL
                if gain <= 0:
                    continue
                if best is None or gain > best[0]:
                    best = (gain, d, room)
            if best is None:
                break
            gain, d, room = best
            left[b.batch_id] -= room
            extra[(d.dest_id, b.commodity)] -= room
            cap[d.dest_id] -= room
            rows.append(row(b, d, room, 1, "discount", gain=gain))
    return rows


def urgency_first_plan(batches, dest, demand):
    """Candidate 1: handle the batches closest to expiry first."""
    price, dem, extra, cap, left = lookups(batches, dest, demand)
    rows = []
    for b in batches.sort_values(["shelf_life_days", "batch_id"]).itertuples():
        while left[b.batch_id] > 0:
            best = None
            for d in dest.itertuples():
                if d.transport_days > b.shelf_life_days:
                    continue
                room = int(min(left[b.batch_id], dem[(d.dest_id, b.commodity)], cap[d.dest_id]))
                if room <= 0:
                    continue
                margin = price[(d.dest_id, b.commodity)] - d.cost_per_kg - HANDLING
                if best is None or margin > best[0]:
                    best = (margin, d, room)
            if best is None:
                break
            margin, d, room = best
            left[b.batch_id] -= room
            dem[(d.dest_id, b.commodity)] -= room
            cap[d.dest_id] -= room
            rows.append(row(b, d, room, 0, "sale", profit=margin))
    rows += discount_pass(batches, dest, price, extra, cap, left)
    return pd.DataFrame(rows, columns=COLS)


def value_first_plan(batches, dest, demand):
    """Candidate 2: rank every possible delivery by profit per kg, so scarce truck
    space goes to the most valuable cargo."""
    price, dem, extra, cap, left = lookups(batches, dest, demand)
    pairs = []
    for b in batches.itertuples():
        for d in dest.itertuples():
            if d.transport_days <= b.shelf_life_days:  # must arrive before it expires
                margin = price[(d.dest_id, b.commodity)] - d.cost_per_kg - HANDLING
                pairs.append((margin, b.shelf_life_days - d.transport_days, b, d))
    pairs.sort(key=lambda p: (-p[0], p[1]))  # best profit first; tie: tighter freshness first
    rows = []
    for margin, slack, b, d in pairs:
        room = int(min(left[b.batch_id], dem[(d.dest_id, b.commodity)], cap[d.dest_id]))
        if room <= 0:
            continue
        left[b.batch_id] -= room
        dem[(d.dest_id, b.commodity)] -= room
        cap[d.dest_id] -= room
        rows.append(row(b, d, room, 0, "sale", profit=margin))
    rows += discount_pass(batches, dest, price, extra, cap, left)
    return pd.DataFrame(rows, columns=COLS)


def smart_plan(batches, dest, demand):
    """FreshFirst: build both candidate plans, drop any that break a rule,
    and keep the one with the higher net revenue (same cost rules for all)."""
    candidates = {"urgent": urgency_first_plan(batches, dest, demand),
                  "value": value_first_plan(batches, dest, demand)}
    best_name, best_plan, best_net = None, None, None
    for name, p in candidates.items():
        if validate(p, batches, dest, demand):
            continue
        net = evaluate(p, batches, dest, demand)["net_revenue"]
        if best_net is None or net > best_net:
            best_name, best_plan, best_net = name, p, net
    if best_plan is None:
        best_name, best_plan = "value", candidates["value"]
    best_plan = best_plan.copy()
    best_plan["strategy"] = best_name
    return best_plan


# ---------------------------------------------------------------
# SCORING AND RULE CHECKS (identical for every method)
# ---------------------------------------------------------------
def evaluate(plan, batches, dest, demand):
    total_stock = int(batches.quantity_kg.sum())
    if plan.empty:
        return {"spoiled_kg": total_stock, "fulfilled_pct": 0.0, "net_revenue": -DISPOSAL * total_stock}
    p = (plan[["batch_id", "commodity", "dest_id", "quantity_kg", "discount_applied"]]
         .merge(batches[["batch_id", "shelf_life_days"]], on="batch_id")
         .merge(dest[["dest_id", "transport_days", "cost_per_kg"]], on="dest_id")
         .merge(demand[["dest_id", "commodity", "price_per_kg"]], on=["dest_id", "commodity"]))
    p["fresh"] = p.transport_days <= p.shelf_life_days  # arrives before expiry?
    p["revenue"] = np.where(p.fresh, p.quantity_kg * p.price_per_kg * (1 - p.discount_applied * DISC), 0.0)
    p["cost"] = p.quantity_kg * (p.cost_per_kg + HANDLING)  # paid even if it arrives spoiled
    fresh_kg = int(p.loc[p.fresh, "quantity_kg"].sum())
    spoiled = total_stock - fresh_kg
    net = p.revenue.sum() - p.cost.sum() - spoiled * DISPOSAL
    f = (p[p.fresh].groupby(["dest_id", "commodity"]).quantity_kg.sum().reset_index()
           .merge(demand, on=["dest_id", "commodity"]))
    fulfilled = np.minimum(f.quantity_kg, f.demand_kg).sum()
    total_demand = max(int(demand.demand_kg.sum()), 1)
    return {"spoiled_kg": spoiled, "fulfilled_pct": 100 * fulfilled / total_demand, "net_revenue": float(net)}


def validate(plan, batches, dest, demand):
    """Returns a list of broken rules (an empty list means the plan is valid)."""
    v = []
    if plan.empty:
        return v
    stock = dict(zip(batches.batch_id, batches.quantity_kg))
    life = dict(zip(batches.batch_id, batches.shelf_life_days))
    cap = dict(zip(dest.dest_id, dest.capacity_kg))
    days = dict(zip(dest.dest_id, dest.transport_days))
    dem = defaultdict(int, {(r.dest_id, r.commodity): r.demand_kg for r in demand.itertuples()})
    for bid, q in plan.groupby("batch_id").quantity_kg.sum().items():
        if q > stock[bid]:
            v.append(f"{bid}: sends {q} kg but only {stock[bid]} kg in stock")
    for d, q in plan.groupby("dest_id").quantity_kg.sum().items():
        if q > cap[d]:
            v.append(f"{d}: {q} kg is more than the truck capacity {cap[d]} kg")
    for (d, c), g in plan.groupby(["dest_id", "commodity"]):
        normal = g.loc[g.discount_applied == 0, "quantity_kg"].sum()
        total = g.quantity_kg.sum()
        if normal > dem[(d, c)]:
            v.append(f"{d} {c}: {normal} kg at full price is more than the demand {dem[(d, c)]} kg")
        if total > dem[(d, c)] + int(round(dem[(d, c)] * UPLIFT)):
            v.append(f"{d} {c}: total {total} kg is more than demand even with a discount")
    for r in plan.itertuples():
        if days[r.dest_id] > life[r.batch_id]:
            v.append(f"{r.batch_id} to {r.dest_id}: arrives after it expires")
    return v


def scenario(batches, dest, demand, demand_pct, shelf_delta, delay):
    """Apply the what-if changes."""
    b = batches.copy()
    b["shelf_life_days"] = (b["shelf_life_days"] + shelf_delta).clip(lower=0)
    dm = demand.copy()
    dm["demand_kg"] = (dm["demand_kg"] * (1 + demand_pct / 100)).round().astype(int)
    ds = dest.copy()
    ds["transport_days"] = ds["transport_days"] + delay
    return b, ds, dm


def run_all(b, d, m):
    plans = {"fifo": baseline(b, d, m, "fifo"), "price": baseline(b, d, m, "price"), "ours": smart_plan(b, d, m)}
    results = {}
    for k, p in plans.items():
        r = evaluate(p, b, d, m)
        r["violations"] = len(validate(p, b, d, m))
        results[k] = r
    return plans, results


# ---------------------------------------------------------------
# SMALL DISPLAY HELPERS
# ---------------------------------------------------------------
PAGES = ["data", "plan", "results", "whatif", "about"]
LANGS = {"en": "English", "hi": "हिन्दी", "te": "తెలుగు"}


def go(p):
    st.session_state.page = p


def nav(prev=None, nxt=None):
    st.write("")
    c1, c2, _ = st.columns([1, 1, 3])
    if prev:
        c1.button(t("btn_back"), on_click=go, args=(prev,), key="back_" + prev)
    if nxt:
        c2.button(t("btn_next"), on_click=go, args=(nxt,), type="primary", key="next_" + nxt)


def method_name(k):
    return {"fifo": t("n_fifo"), "price": t("n_price"), "ours": "FreshFirst"}[k]


def reason_text(r):
    if r.kind == "fifo":
        return t("r_fifo")
    if r.kind == "price":
        return t("r_price")
    if r.kind == "discount":
        return t("r_disc", pct=f"{DISC*100:.0f}", shelf=int(r.shelf), shop=r.dest_id, gain=f"{r.gain:.1f}")
    return t("r_sale", shop=r.dest_id, days=int(r.days), shelf=int(r.shelf), profit=f"{r.profit:.1f}")


def plan_view(plan):
    return pd.DataFrame({
        t("c_batch"): plan.batch_id.values, t("c_item"): plan.commodity.values,
        t("c_shop"): plan.dest_id.values, t("c_kg"): plan.quantity_kg.values,
        t("c_disc"): np.where(plan.discount_applied.values == 1, t("yes"), t("no")),
        t("c_why"): [reason_text(r) for r in plan.itertuples()]})


def show_kpis(ours_r, base_r, bname):
    st.caption(t("arrows_cap", base=bname))
    c1, c2, c3 = st.columns(3)
    c1.metric(t("k_spoil"), f"{ours_r['spoiled_kg']:.0f}",
              delta=f"{ours_r['spoiled_kg'] - base_r['spoiled_kg']:.0f} kg", delta_color="inverse", help=t("h_spoil"))
    c2.metric(t("k_demand"), f"{ours_r['fulfilled_pct']:.1f}%",
              delta=f"{ours_r['fulfilled_pct'] - base_r['fulfilled_pct']:.1f} %", help=t("h_demand"))
    c3.metric(t("k_money"), f"{ours_r['net_revenue']:,.0f}",
              delta=f"{ours_r['net_revenue'] - base_r['net_revenue']:,.0f} Rs", help=t("h_money"))
    if ours_r["violations"] == 0:
        st.success(t("rule_ok"))
    else:
        st.error(t("rule_bad", n=ours_r["violations"]))


# ---------------------------------------------------------------
# SIDEBAR: language, pages, which data is in use
# ---------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🥬 FreshFirst")
    st.selectbox("Language / भाषा / భాష", list(LANGS), format_func=LANGS.get, key="lang")
    st.radio(t("nav"), PAGES, format_func=lambda p: t("p_" + p), key="page")
    st.divider()
    st.caption(t("badge_user") if st.session_state.mode == "upload" else t("badge_sample"))

page = st.session_state.page
step = PAGES.index(page) + 1
st.progress(step / 5, text=t("step_of", n=step))

# ---------------------------------------------------------------
# PAGE 1: DATA
# ---------------------------------------------------------------
if page == "data":
    st.title("🥬 FreshFirst")
    st.markdown(f"**{t('app_tagline')}**")
    st.header(t("data_title"))
    st.write(t("data_intro"))
    st.warning(t("synth_note"))
    st.radio(t("mode_label"), ["sample", "upload"], format_func=lambda m: t("mode_" + m),
             key="mode", horizontal=True)

    if st.session_state.mode == "upload":
        with st.expander(t("dl_templates")):
            cols = st.columns(3)
            for col, kind, df in zip(cols, ["stock", "markets", "demand"], make_data()):
                col.download_button(kind + ".csv", df.to_csv(index=False), file_name=kind + ".csv",
                                    mime="text/csv", key="dl_" + kind)
        files = {k: st.file_uploader(t("up_" + k), type="csv", key="file_" + k)
                 for k in ["stock", "markets", "demand"]}
        if all(files.values()):
            parsed, errs = parse_uploads(files)
            if errs:
                st.session_state.pop("user_data", None)
                for e in errs:
                    st.error(e)
            else:
                st.session_state.user_data = parsed
        elif "user_data" not in st.session_state:
            st.info(t("upload_all"))

    with st.expander(t("rules_title")):
        c1, c2 = st.columns(2)
        c1.number_input(t("r_handling"), min_value=0.0, max_value=50.0, step=0.5, key="handling")
        c1.number_input(t("r_disposal"), min_value=0.0, max_value=50.0, step=0.5, key="disposal")
        c2.number_input(t("r_disc"), min_value=0, max_value=90, step=5, key="disc_pct")
        c2.number_input(t("r_uplift"), min_value=0, max_value=200, step=5, key="uplift_pct")

    data = active_data()
    if data is not None:
        b0, d0, m0 = data
        st.success(t("data_ok"))
        sv = b0.copy()
        sv["urgency"] = np.where(sv.shelf_life_days <= 2, t("u_high"), t("u_ok"))
        sv = sv.sort_values("shelf_life_days").rename(columns={
            "batch_id": t("c_batch"), "commodity": t("c_item"), "quantity_kg": t("c_kg"),
            "shelf_life_days": t("c_days_left"), "urgency": t("c_risk")})
        st.subheader(t("tbl_stock"))
        st.dataframe(sv, hide_index=True)
        st.subheader(t("tbl_markets"))
        st.dataframe(d0.rename(columns={"dest_id": t("c_shop"), "transport_days": t("c_travel"),
                                        "cost_per_kg": t("c_cost"), "capacity_kg": t("c_cap")}), hide_index=True)
        st.subheader(t("tbl_demand"))
        st.dataframe(m0.rename(columns={"dest_id": t("c_shop"), "commodity": t("c_item"),
                                        "demand_kg": t("c_demand"), "price_per_kg": t("c_price")}), hide_index=True)
        st.write("")
        st.button(t("btn_make"), type="primary", on_click=go, args=("plan",))
    st.stop()

# the other pages need data
data = active_data()
if data is None:
    st.warning(t("need_data"))
    st.button(t("btn_back"), on_click=go, args=("data",))
    st.stop()
b0, d0, m0 = data

# ---------------------------------------------------------------
# PAGE 2: YOUR PLAN
# ---------------------------------------------------------------
if page == "plan":
    plans, results = run_all(b0, d0, m0)
    ours = plans["ours"]
    st.header(t("plan_title"))
    st.write(t("plan_intro"))
    sent = int(ours.quantity_kg.sum())
    disc_kg = int(ours.loc[ours.discount_applied == 1, "quantity_kg"].sum())
    shops = int(ours.dest_id.nunique())
    st.info(t("plan_summary", sent=f"{sent:,}", shops=shops, disc=f"{disc_kg:,}",
              spoil=f"{results['ours']['spoiled_kg']:,.0f}"))
    if not ours.empty:
        st.caption(t("strategy_line", s=t("s_" + ours.strategy.iloc[0])))

    st.subheader(t("sec_by_shop"))
    for shop in d0.dest_id:
        g = ours[ours.dest_id == shop].sort_values(["discount_applied", "batch_id"])
        with st.container(border=True):
            st.markdown(f"**{shop}**  ·  {int(g.quantity_kg.sum()):,} kg")
            if g.empty:
                st.caption(t("shop_nothing"))
            else:
                st.dataframe(plan_view(g), hide_index=True)

    st.subheader(t("sec_disc"))
    dd = ours[ours.discount_applied == 1]
    if dd.empty:
        st.info(t("disc_none"))
    else:
        st.dataframe(plan_view(dd), hide_index=True)

    st.subheader(t("sec_left"))
    sold = ours.groupby("batch_id").quantity_kg.sum()
    lf = b0[["batch_id", "commodity", "quantity_kg"]].copy()
    lf["left"] = lf.quantity_kg - lf.batch_id.map(sold).fillna(0).astype(int)
    lf = lf[lf.left > 0][["batch_id", "commodity", "left"]]
    if lf.empty:
        st.success(t("left_none"))
    else:
        st.dataframe(lf.rename(columns={"batch_id": t("c_batch"), "commodity": t("c_item"),
                                        "left": t("c_notsold")}), hide_index=True)
    if not ours.empty:
        st.download_button(t("dl_plan"), plan_view(ours).to_csv(index=False).encode("utf-8-sig"),
                           file_name="freshfirst_plan.csv", mime="text/csv")
    nav("data", "results")

# ---------------------------------------------------------------
# PAGE 3: RESULTS
# ---------------------------------------------------------------
elif page == "results":
    plans, results = run_all(b0, d0, m0)
    st.header(t("res_title"))
    st.write(t("res_intro"))
    st.radio(t("cmp_with"), ["fifo", "price"], format_func=lambda k: t("m_" + k), key="base", horizontal=True)
    bk = st.session_state.base
    ours_r, base_r, bname = results["ours"], results[bk], method_name(bk)
    show_kpis(ours_r, base_r, bname)

    dm_ = ours_r["net_revenue"] - base_r["net_revenue"]
    ds_ = ours_r["spoiled_kg"] - base_r["spoiled_kg"]
    line1 = (t("money_more", x=f"{abs(dm_):,.0f}", base=bname) if dm_ > 0.5 else
             t("money_less", x=f"{abs(dm_):,.0f}", base=bname) if dm_ < -0.5 else t("money_same", base=bname))
    line2 = (t("spoil_less", x=f"{abs(ds_):,.0f}") if ds_ < 0 else
             t("spoil_more", x=f"{abs(ds_):,.0f}") if ds_ > 0 else t("spoil_same"))
    st.markdown(f"**{line1}** {line2}")

    st.subheader(t("tbl_all"))
    st.dataframe(pd.DataFrame([{
        t("col_method"): method_name(k), t("k_spoil"): int(results[k]["spoiled_kg"]),
        t("k_demand"): round(results[k]["fulfilled_pct"], 1), t("k_money"): int(results[k]["net_revenue"]),
        t("col_rules"): results[k]["violations"]} for k in ["fifo", "price", "ours"]]), hide_index=True)
    c1, c2 = st.columns(2)
    order = ["fifo", "price", "ours"]
    c1.write(t("chart_money"))
    c1.bar_chart(pd.DataFrame({"v": [results[k]["net_revenue"] for k in order]},
                              index=[method_name(k) for k in order]), color=GREEN)
    c2.write(t("chart_spoil"))
    c2.bar_chart(pd.DataFrame({"v": [results[k]["spoiled_kg"] for k in order]},
                              index=[method_name(k) for k in order]), color="#C2410C")
    with st.expander(t("rules_help_title")):
        st.write(t("rules_help"))
    with st.expander(t("see_base")):
        for k in ["fifo", "price"]:
            st.markdown(f"**{method_name(k)}**")
            if not plans[k].empty:
                st.dataframe(plan_view(plans[k]), hide_index=True)
            for msg in validate(plans[k], b0, d0, m0)[:10]:
                st.caption(t("rule_broken") + msg)
    nav("plan", "whatif")

# ---------------------------------------------------------------
# PAGE 4: WHAT IF?
# ---------------------------------------------------------------
elif page == "whatif":
    st.header(t("wi_title"))
    st.write(t("wi_intro"))
    s1, s2, s3 = st.columns(3)
    s1.slider(t("s_demand"), -50, 50, step=10, key="s_demand")
    s2.slider(t("s_shelf"), -2, 2, key="s_shelf")
    s3.slider(t("s_delay"), 0, 2, key="s_delay")
    bk = st.session_state.base
    bname = method_name(bk)
    b, ds, dm = scenario(b0, d0, m0, st.session_state.s_demand, st.session_state.s_shelf, st.session_state.s_delay)
    plans, results = run_all(b, ds, dm)
    st.subheader(t("wi_result"))
    show_kpis(results["ours"], results[bk], bname)

    st.subheader(t("stress_title"))
    st.write(t("stress_intro"))
    rows = []
    for key, pct, sh, dl in [("sc_normal", 0, 0, 0), ("sc_demand", -20, 0, 0), ("sc_shelf", 0, -1, 0),
                             ("sc_late", 0, 0, 1), ("sc_all", -20, -1, 1)]:
        sb, sd, sm = scenario(b0, d0, m0, pct, sh, dl)
        _, rr = run_all(sb, sd, sm)
        rows.append({t("col_scn"): t(key),
                     t("col_ours_money"): int(rr["ours"]["net_revenue"]), t("col_base_money"): int(rr[bk]["net_revenue"]),
                     t("col_ours_spoil"): int(rr["ours"]["spoiled_kg"]), t("col_base_spoil"): int(rr[bk]["spoiled_kg"]),
                     t("col_rules"): rr["ours"]["violations"]})
    st.caption(t("arrows_cap", base=bname))
    st.dataframe(pd.DataFrame(rows), hide_index=True)
    nav("results", "about")

# ---------------------------------------------------------------
# PAGE 5: ABOUT
# ---------------------------------------------------------------
else:
    st.header(t("about_title"))
    st.subheader(t("how_title"))
    for i in range(1, 5):
        st.markdown(f"{i}. {t('how' + str(i))}")
    st.subheader(t("assump_title"))
    st.markdown("- " + t("as1"))
    st.markdown("- " + t("as2"))
    st.markdown("- " + t("as3", disp=f"{DISPOSAL:g}"))
    st.markdown("- " + t("as4", hand=f"{HANDLING:g}"))
    st.markdown("- " + t("as5", disc=f"{DISC*100:.0f}", up=f"{UPLIFT*100:.0f}"))
    st.subheader(t("limits_title"))
    st.write(t("limits"))
    nav("whatif")
