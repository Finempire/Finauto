"""
AI-powered ledger mapper — ported from the Streamlit monolith.
Provides multi-strategy matching: exact rules, learned mappings,
keyword overlap, ledger-name focus, and optional sentence-transformer
semantic matching.
"""

import re
import difflib
import pandas as pd

try:
    from sentence_transformers import SentenceTransformer, util
    import torch
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

_cached_model = None


def _get_model():
    global _cached_model
    if _cached_model is None and SENTENCE_TRANSFORMERS_AVAILABLE:
        _cached_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _cached_model


class EnhancedLedgerMapper:
    def __init__(self):
        self.model = None
        self.ledger_embeddings = None
        self.ledger_master = None
        self.ledger_keyword_index = None
        self.initialized = False

    def initialize_model(self):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return False
        try:
            self.model = _get_model()
            self.initialized = True
            return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f'Failed to load AI model: {e}')
            return False

    # --- Name extraction helpers ---

    def extract_name_from_end(self, narration):
        if pd.isna(narration):
            return ''
        narration_str = str(narration).upper().strip()
        if len(narration_str) <= 20:
            return narration_str
        start_index = len(narration_str) // 2
        focus_part = narration_str[start_index:]
        patterns_to_remove = [
            r'UPI[-]?', r'TXN[-]?', r'REF[-]?', r'IMPS', r'NEFT', r'RTGS',
            r'UTR?[\d]*', r'CHQ[\d]*', r'CHEQUE[\d]*', r'CREDIT\s*CARD',
            r'DEBIT\s*CARD', r'ATM', r'IB[\d]*', r'\/', r'\\', r'TRF',
            r'TRANSFER', r'PAYMENT', r'RECEIPT', r'DEPOSIT', r'WITHDRAWAL',
            r'TO\s+', r'FROM\s+', r'BY\s+', r'VIA\s+', r'THROUGH\s+',
            r'BILL\s+NO', r'INVOICE\s+NO', r'REF\s+NO', r'ID\s+', r'TDS\s+',
            r'SALARY', r'PAYROLL', r'VENDOR', r'SUPPLIER', r'CLIENT', r'CUSTOMER',
            r'\d{2,}', r'[\(\)\{\}\[\]]', r'#\w+', r'FOR\s+', r'TOWARD\s+'
        ]
        for pattern in patterns_to_remove:
            focus_part = re.sub(pattern, '', focus_part, flags=re.IGNORECASE)
        focus_part = re.sub(r'[^a-zA-Z0-9\s]', ' ', focus_part)
        focus_part = re.sub(r'\s+', ' ', focus_part).strip()
        words = focus_part.split()
        name_indicators = ['MR', 'MRS', 'MS', 'SHRI', 'SMT', 'SRI', 'TO', 'BY']
        potential_names = []
        transaction_words = ['BANK', 'ACCOUNT', 'CASH', 'CHEQUE', 'TRANSFER', 'PAYMENT']
        for i in range(len(words)):
            for length in [4, 3, 2]:
                if i + length <= len(words):
                    sequence = ' '.join(words[i:i + length])
                    if (len(sequence) >= 3 and
                            not any(tx_word in sequence for tx_word in transaction_words) and
                            any(word in name_indicators for word in words[i:i + length] if length > 1)):
                        potential_names.append(sequence)
        if potential_names:
            return max(potential_names, key=len)
        if len(words) >= 3:
            return ' '.join(words[-3:])
        elif words:
            return ' '.join(words)
        return focus_part

    def identify_person_or_company_name(self, narration):
        narration_str = str(narration).upper()
        person_indicators = [
            'SALARY', 'PAYROLL', 'EMPLOYEE', 'STAFF', 'PAYMENT TO', 'PAID TO',
            'VENDOR', 'SUPPLIER', 'CONTRACTOR', 'SERVICE PROVIDER',
            'CLIENT', 'CUSTOMER', 'RECEIVED FROM', 'RECEIPT FROM',
            'MR ', 'MRS ', 'MS ', 'SHRI ', 'SMT ', 'SRI '
        ]
        extracted_name = self.extract_name_from_end(narration)
        is_person = any(ind in narration_str for ind in person_indicators)
        return extracted_name, is_person

    def categorize_transaction(self, narration):
        narration_lower = str(narration).lower()
        expense_keywords = {
            'salary': ['salary', 'payroll', 'wage', 'employee', 'staff', 'pay slip'],
            'food': ['zomato', 'swiggy', 'food', 'restaurant', 'cafe', 'pizza', 'burger', 'meal', 'dining'],
            'travel': ['uber', 'ola', 'rapido', 'travel', 'taxi', 'auto', 'fuel', 'petrol', 'diesel', 'transport'],
            'shopping': ['amazon', 'flipkart', 'myntra', 'shopping', 'store', 'market', 'purchase'],
            'utilities': ['electricity', 'water', 'gas', 'bill', 'mobile', 'phone', 'internet', 'broadband'],
            'entertainment': ['netflix', 'hotstar', 'movie', 'cinema', 'theatre', 'entertainment'],
            'healthcare': ['hospital', 'clinic', 'doctor', 'medical', 'pharmacy', 'medicine'],
            'education': ['school', 'college', 'tuition', 'course', 'book', 'education'],
            'vendor': ['vendor', 'supplier', 'contractor', 'service provider'],
            'client': ['client', 'customer', 'received from'],
        }
        for category, keywords in expense_keywords.items():
            for kw in keywords:
                if kw in narration_lower:
                    return category
        income_keywords = ['salary', 'refund', 'interest', 'dividend', 'commission', 'revenue', 'income']
        for kw in income_keywords:
            if kw in narration_lower:
                return 'income'
        return 'other'

    def calculate_string_similarity(self, str1, str2):
        str1, str2 = str1.lower(), str2.lower()
        if str1 == str2:
            return 1.0
        seq_matcher = difflib.SequenceMatcher(None, str1, str2)
        sequence_ratio = seq_matcher.ratio()
        words1 = set(str1.split())
        words2 = set(str2.split())
        if not words1 or not words2:
            return sequence_ratio
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        word_ratio = len(intersection) / len(union) if union else 0
        return (sequence_ratio * 0.7) + (word_ratio * 0.3)

    def preprocess_narration(self, narration):
        if pd.isna(narration):
            return ''
        narration_str = str(narration).upper()
        patterns_to_remove = [
            r'UPI[-]?', r'TXN[-]?', r'REF[-]?', r'IMPS', r'NEFT', r'RTGS',
            r'UTR?[\d]*', r'CHQ[\d]*', r'CHEQUE[\d]*', r'CREDIT\s*CARD',
            r'DEBIT\s*CARD', r'ATM', r'IB[\d]*', r'\/', r'\\', r'TRF',
            r'TRANSFER', r'PAYMENT', r'RECEIPT', r'DEPOSIT', r'WITHDRAWAL',
            r'TO\s+', r'FROM\s+', r'BY\s+', r'VIA\s+', r'THROUGH\s+',
            r'BILL\s+NO', r'INVOICE\s+NO', r'REF\s+NO', r'ID\s+', r'TDS\s+',
            r'\d{2,}', r'[\(\)\{\}\[\]]', r'#\w+'
        ]
        for pattern in patterns_to_remove:
            narration_str = re.sub(pattern, '', narration_str, flags=re.IGNORECASE)
        narration_str = re.sub(r'[^a-zA-Z0-9\s]', ' ', narration_str)
        narration_str = re.sub(r'\s+', ' ', narration_str).strip()
        return narration_str

    def build_ledger_keyword_index(self, ledger_master):
        noise_words = {'account', 'a/c', 'ac', 'ledger', 'bank', 'cash', 'general',
                        'misc', 'miscellaneous', 'expense', 'expenses', 'and', '&'}
        keyword_synonyms = {
            'fuel': {'petrol', 'diesel', 'gas', 'cng'},
            'petrol': {'fuel', 'diesel', 'gas', 'cng'},
            'diesel': {'fuel', 'petrol', 'gas', 'cng'},
            'rent': {'lease'},
            'salary': {'payroll', 'wages', 'wage'},
            'travel': {'transport', 'conveyance'},
            'vendor': {'supplier', 'contractor'},
            'client': {'customer', 'debtor'},
            'gst': {'tax'},
            'tds': {'tax'},
        }
        ledger_index = []
        for ledger in ledger_master:
            clean = self.preprocess_narration(ledger)
            words = [w for w in clean.lower().split() if w and w not in noise_words]
            expanded = set(words)
            for w in words:
                expanded.update(keyword_synonyms.get(w, set()))
            ledger_index.append({'ledger': ledger, 'clean': clean, 'keywords': expanded})
        return ledger_index

    def ensure_ledger_index(self, ledger_master):
        if not ledger_master:
            return None
        if self.ledger_master != ledger_master or self.ledger_keyword_index is None:
            self.ledger_keyword_index = self.build_ledger_keyword_index(ledger_master)
            self.ledger_master = ledger_master
        return self.ledger_keyword_index

    def ledger_name_focus_match(self, narration, ledger_master):
        clean_narration = self.preprocess_narration(narration)
        narration_words = set(clean_narration.lower().split()) if clean_narration else set()
        if not narration_words or not ledger_master:
            return None, 0
        ledger_index = self.ensure_ledger_index(ledger_master)
        if not ledger_index:
            return None, 0
        best_ledger, best_score = None, 0
        for entry in ledger_index:
            overlap = narration_words.intersection(entry['keywords'])
            overlap_score = len(overlap) * 22
            name_sim = self.calculate_string_similarity(clean_narration, entry['clean'])
            sim_score = name_sim * 60
            partial_bonus = 20 if entry['clean'] and entry['clean'] in clean_narration else 0
            combined = overlap_score + sim_score + partial_bonus
            if combined > best_score and (overlap or name_sim >= 0.55):
                best_score = combined
                best_ledger = entry['ledger']
        if best_ledger:
            return best_ledger, min(95, best_score)
        return None, 0

    def compute_ledger_embeddings(self, ledger_master):
        if not self.initialized or not ledger_master:
            return None
        try:
            processed = [self.preprocess_narration(l) for l in ledger_master]
            self.ledger_embeddings = self.model.encode(processed, convert_to_tensor=True)
            self.ledger_master = ledger_master
            self.ledger_keyword_index = self.build_ledger_keyword_index(ledger_master)
            return True
        except Exception as e:
            print(f'Error computing ledger embeddings: {e}')
            return False

    def semantic_similarity_match(self, narration, threshold=0.4):
        if not self.initialized or self.ledger_embeddings is None:
            return None, 0
        try:
            extracted_name, _ = self.identify_person_or_company_name(narration)
            clean = extracted_name if extracted_name else self.preprocess_narration(narration)
            if not clean:
                return None, 0
            emb = self.model.encode([clean], convert_to_tensor=True)
            scores = util.cos_sim(emb, self.ledger_embeddings)[0]
            best_score, best_idx = torch.max(scores, dim=0)
            best_score = best_score.item()
            if best_score >= threshold:
                return self.ledger_master[best_idx], best_score * 100
            return None, best_score * 100
        except Exception as e:
            print(f'Semantic matching error: {e}')
            return None, 0

    def keyword_based_match(self, narration, ledger_master):
        if not narration or not ledger_master:
            return None, 0
        narration_str = str(narration).upper()
        clean_narration = self.preprocess_narration(narration_str)
        extracted_name, is_person = self.identify_person_or_company_name(narration)
        category = self.categorize_transaction(narration)

        if extracted_name and is_person:
            for ledger in ledger_master:
                clean_ledger = self.preprocess_narration(ledger)
                sim = self.calculate_string_similarity(extracted_name, clean_ledger)
                if sim > 0.6:
                    return ledger, min(95, sim * 100)
                if extracted_name in clean_ledger or clean_ledger in extracted_name:
                    return ledger, 90

        category_keywords = {
            'salary': ['salary', 'employee', 'payroll', 'staff'],
            'food': ['food', 'meal', 'restaurant', 'cafe', 'dining'],
            'travel': ['travel', 'transport', 'taxi', 'uber', 'fuel', 'conveyance'],
            'shopping': ['shopping', 'store', 'market', 'purchase', 'supplies'],
            'utilities': ['electricity', 'water', 'gas', 'utility', 'bill', 'telephone'],
            'entertainment': ['entertainment', 'movie', 'cinema', 'recreation'],
            'healthcare': ['medical', 'hospital', 'clinic', 'health', 'medicine'],
            'education': ['education', 'school', 'college', 'tuition', 'books'],
            'vendor': ['vendor', 'supplier', 'contractor', 'service'],
            'client': ['client', 'customer', 'debtor'],
            'income': ['salary', 'income', 'revenue', 'commission', 'interest']
        }
        if category in category_keywords:
            for kw in category_keywords[category]:
                for ledger in ledger_master:
                    if kw in ledger.lower():
                        return ledger, 80

        for ledger in ledger_master:
            cl = self.preprocess_narration(ledger)
            if cl and cl in clean_narration:
                return ledger, 85

        narration_words = set(clean_narration.split())
        best_overlap, best_ledger = 0, None
        for ledger in ledger_master:
            cl = self.preprocess_narration(ledger)
            if not cl:
                continue
            lw = set(cl.split())
            overlap = narration_words.intersection(lw)
            if overlap and len(overlap) > best_overlap:
                best_overlap = len(overlap)
                best_ledger = ledger
        if best_ledger and best_overlap >= 1:
            return best_ledger, min(75, best_overlap * 30)

        close = difflib.get_close_matches(clean_narration, ledger_master, n=1, cutoff=0.5)
        if close:
            return close[0], 65
        return None, 0

    def multi_strategy_match(self, narration, ledger_master, rules_config, suspense_ledger, learned_mappings):
        narration_str = str(narration)
        extracted_name, is_person = self.identify_person_or_company_name(narration)

        if narration_str in learned_mappings:
            return learned_mappings[narration_str]['ledger'], 95, 'learned_exact'

        for rule in rules_config:
            keyword = rule.get('Narration Keyword', '').lower()
            if keyword and keyword in narration_str.lower():
                return rule.get('Mapped Ledger'), 90, 'rule'

        best_score, best_ledger = 0, None
        for ln, ld in learned_mappings.items():
            sim = self.calculate_string_similarity(narration_str, ln)
            boosted = sim * 100 + (ld.get('count', 1) * 2) + (ld.get('score', 0) * 0.1)
            if boosted > best_score and boosted >= 60:
                best_score = boosted
                best_ledger = ld['ledger']
        if best_ledger:
            return best_ledger, min(85, best_score), 'learned_similar'

        kw_match, kw_score = self.keyword_based_match(narration_str, ledger_master)
        if kw_match and kw_score >= 50:
            return kw_match, kw_score, 'keyword_match'

        lf_match, lf_score = self.ledger_name_focus_match(narration_str, ledger_master)
        if lf_match and lf_score >= 55:
            return lf_match, lf_score, 'ledger_name_focus'

        if self.initialized:
            sem_match, sem_score = self.semantic_similarity_match(narration_str, threshold=0.3)
            if sem_match and sem_score >= 35:
                return sem_match, sem_score, 'semantic_ai'

        category = self.categorize_transaction(narration_str)
        category_ledgers = {
            'salary': [l for l in ledger_master if any(w in l.lower() for w in ['salary', 'employee', 'staff'])],
            'food': [l for l in ledger_master if any(w in l.lower() for w in ['food', 'meal', 'restaurant'])],
            'travel': [l for l in ledger_master if any(w in l.lower() for w in ['travel', 'transport', 'fuel', 'conveyance'])],
            'shopping': [l for l in ledger_master if any(w in l.lower() for w in ['purchase', 'expense', 'general', 'supplies'])],
            'utilities': [l for l in ledger_master if any(w in l.lower() for w in ['electricity', 'water', 'utility', 'telephone'])],
            'vendor': [l for l in ledger_master if any(w in l.lower() for w in ['vendor', 'supplier', 'contractor'])],
            'client': [l for l in ledger_master if any(w in l.lower() for w in ['client', 'customer', 'debtor'])],
            'income': [l for l in ledger_master if any(w in l.lower() for w in ['salary', 'income', 'revenue'])],
        }
        if category in category_ledgers and category_ledgers[category]:
            return category_ledgers[category][0], 60, f'category_{category}'

        if extracted_name and is_person:
            for ledger in ledger_master:
                if extracted_name.lower() in ledger.lower():
                    return ledger, 55, 'name_fallback'

        return suspense_ledger, 0, 'default'


# Global singleton
ledger_mapper = EnhancedLedgerMapper()


def initialize_ai_model():
    if not ledger_mapper.initialized:
        return ledger_mapper.initialize_model()
    return ledger_mapper.initialized


def get_smart_suggestions(narrations_list, ledger_master, rules_config, suspense_ledger, learned_mappings):
    best_matches, confidence_scores, match_types = {}, {}, {}
    initialize_ai_model()
    if ledger_mapper.initialized and (ledger_mapper.ledger_master != ledger_master or ledger_mapper.ledger_embeddings is None):
        ledger_mapper.compute_ledger_embeddings(ledger_master)
    valid = [n for n in narrations_list if pd.notna(n)]
    for narration in valid:
        ns = str(narration)
        suggested, conf, mt = ledger_mapper.multi_strategy_match(ns, ledger_master, rules_config, suspense_ledger, learned_mappings)
        best_matches[ns] = suggested
        confidence_scores[ns] = conf
        match_types[ns] = mt
    if len(valid) < len(narrations_list):
        best_matches['__NaN__'] = suspense_ledger
        confidence_scores['__NaN__'] = 0
        match_types['__NaN__'] = 'default'
    return best_matches, confidence_scores, match_types


def auto_map_ledgers_based_on_rules(narrations_list, ledger_master, rules_config, suspense_ledger, learned_mappings):
    auto_mappings = {}
    initialize_ai_model()
    if ledger_mapper.initialized and (ledger_mapper.ledger_master != ledger_master or ledger_mapper.ledger_embeddings is None):
        ledger_mapper.compute_ledger_embeddings(ledger_master)
    valid = [n for n in narrations_list if pd.notna(n)]
    for narration in valid:
        ns = str(narration)
        if ns in learned_mappings:
            auto_mappings[ns] = learned_mappings[ns]['ledger']
            continue
        matched = False
        for rule in rules_config:
            kw = rule.get('Narration Keyword', '').lower()
            if kw and kw in ns.lower():
                auto_mappings[ns] = rule.get('Mapped Ledger')
                matched = True
                break
        if matched:
            continue
        best_sim, best_ll = 0, None
        for ln, ld in learned_mappings.items():
            sim = ledger_mapper.calculate_string_similarity(ns, ln)
            if sim > best_sim and sim >= 0.7:
                best_sim = sim
                best_ll = ld['ledger']
        if best_ll:
            auto_mappings[ns] = best_ll
            continue
        if ledger_mapper.initialized and ledger_master:
            try:
                ai_l, conf, _ = ledger_mapper.multi_strategy_match(ns, ledger_master, rules_config, suspense_ledger, learned_mappings)
                if ai_l and ai_l != suspense_ledger:
                    auto_mappings[ns] = ai_l
                    continue
            except Exception:
                pass
        auto_mappings[ns] = suspense_ledger
    return auto_mappings
