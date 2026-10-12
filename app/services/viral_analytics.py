"""Viral Retention Analytics & Hook A/B Engine.

Provides deep retention curve simulation, algorithmic hook scoring,
sentence pacing variance evaluation, and neuro-targeted A/B hook variations
for short-form video creation (YouTube Shorts, TikTok, Instagram Reels).
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List


# Standard 1.15x neural cadence used by modern TTS engines (e.g. EdgeTTS, Azure, ElevenLabs)
# Average speaking rate: ~2.65 words per second (~159 words/minute).
NEURAL_CADENCE_WORDS_PER_SEC: float = 2.65

# Power words and shock triggers that maximize thumb-stop rate in the first 3-5 seconds
POWER_WORDS = {
    "chocante", "chocantes", "bizarro", "bizarra", "bizarros", "bizarras",
    "proibido", "proibida", "proibidos", "proibidas", "impossível", "impossíveis", "impossiveis",
    "segredo", "segredos", "mistério", "mistérios", "misterios", "misterio", "brutal", "brutais",
    "fatal", "fatais", "invisível", "invisíveis", "invisivel", "escondido", "escondida",
    "escondidos", "escondidas", "aniquilado", "aniquilada", "perigoso", "perigosa",
    "perigosos", "perigosas", "assustador", "assustadora", "estranho", "estranha",
    "estranhos", "estranhas", "verdade", "insano", "insana", "inacreditável", "inacreditavel",
    "abismo", "sombria", "sombrio", "sombrias", "sombrios", "espaguetificação", "espaguetificacao",
    "paradoxo", "sinistro", "sinistra", "farsa", "iludido", "erro", "erros",
    "surpreendente", "surpreendentes", "destruição", "destruicao", "extinção", "extincao",
    "apocalipse", "alerta", "urgente", "jamais", "nunca", "mortal", "mortais",
    "desconhecido", "desconhecida", "terror", "aterrorizante", "esmagador", "esmagadora",
    "revelado", "revelada", "mutação", "mutacao", "incurável", "incuravel", "silêncio",
    "silencio", "singularidade", "horizonte", "intensa", "intenso", "pulverizado",
    "pulverizada", "congelado", "congelada", "radiação", "radiacao", "colapso",
    "shocking", "bizarre", "forbidden", "impossible", "secret", "mystery",
    "deadly", "danger", "hidden", "insane", "unbelievable", "abyss", "dark",
    "paradox", "destruction", "lethal", "terrifying"
}

# Curiosity gap question and hypothetical openers
CURIOSITY_TRIGGERS = [
    "se você", "se voce", "se você caísse", "se voce caisse", "se você pudesse", "se voce pudesse",
    "você sabia", "voce sabia", "sabia que", "já se perguntou", "ja se perguntou",
    "já imaginou", "ja imaginou", "e se você", "e se voce", "e se",
    "por que o", "por que a", "por que os", "por que as", "por que", "por que razão",
    "como é possível", "como e possivel", "como pode", "o que acontece", "o que aconteceria",
    "o que a ciência", "o que a ciencia", "o que ninguém", "o que ninguem",
    "qual é o segredo", "qual e o segredo", "o mistério de", "o misterio de",
    "você não vai acreditar", "voce nao vai acreditar", "existe uma razão",
    "existe uma razao", "existem centenas", "existem bilhões", "existem bilhoes",
    "existem trilhões", "existem trilhoes", "a verdade sobre",
    "did you know", "have you ever", "what if", "why do", "how is it", "what happens",
    "what nobody tells you", "the reason why", "the hidden truth"
]

# Weak fluff / throat-clearing openers that cause immediate viewer swipe
FLUFF_OPENERS = [
    "olá a todos", "ola a todos", "olá pessoal", "ola pessoal", "e aí galera",
    "e ai galera", "fala pessoal", "fala galera", "bem-vindo", "bem vindo",
    "sejam bem-vindos", "sejam bem vindos", "neste vídeo", "neste video",
    "hoje eu vou", "hoje vamos", "no vídeo de hoje", "no video de hoje",
    "bom dia", "boa tarde", "boa noite", "hello guys", "welcome to",
    "in this video", "today we are going to", "hey everyone"
]

# High-stakes / survival / existential anchors
STAKES_WORDS = {
    "sobreviver", "sobrevivência", "sobrevivencia", "vida", "morte", "fim",
    "terra", "universo", "cosmos", "humanidade", "cérebro", "cerebro", "corpo",
    "pressão", "pressao", "tempo", "destruir", "congelar", "desaparecer",
    "aniquilar", "apagar", "física", "fisica", "ciência", "ciencia", "realidade",
    "gravidade", "planetas", "galáxias", "galaxias", "estrelas", "buraco",
    "survive", "survival", "death", "universe", "earth", "humanity", "body", "time"
}

# Transition / contrast connectors that prevent mid-video attention drop-off
TRANSITION_MARKERS = [
    "mas", "porém", "porem", "no entanto", "contudo", "todavia", "entretanto",
    "enquanto isso", "enquanto", "de repente", "ao mesmo tempo", "em vez disso",
    "por isso", "além disso", "alem disso", "na verdade", "o resultado",
    "embora", "o detalhe é que", "o detalhe e que", "a verdadeira surpresa",
    "a reviravolta", "o problema é", "o problema e", "curiosamente", "para você", "para voce",
    "but", "however", "meanwhile", "suddenly", "instead", "yet", "although", "interestingly"
]


def _extract_words(text: str) -> List[str]:
    """Tokenize words preserving accented letters and hyphens."""
    if not text:
        return []
    return re.findall(r"\b[\w'-]+\b", text, re.UNICODE)


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences cleanly based on punctuation or line breaks."""
    if not text or not text.strip():
        return []
    raw = re.split(r"(?<=[.!?…\n])\s+", text.strip())
    sentences = [s.strip() for s in raw if s and s.strip()]
    return sentences if sentences else [text.strip()]


def _detect_subject_from_script(script: str) -> str:
    """Extract a likely subject from opening sentence or keywords if none was given."""
    sentences = _split_sentences(script)
    if not sentences:
        return "Fatos Extraordinários da Ciência"
    first = sentences[0].strip().rstrip(".!?")
    clean = re.sub(
        r"^(se você|se voce|você sabia que|voce sabia que|sabia que|o que acontece se você)\s+",
        "",
        first,
        flags=re.IGNORECASE,
    ).strip()
    words = _extract_words(clean)
    if 2 <= len(words) <= 7:
        return clean
    elif len(words) > 7:
        return " ".join(words[:6])
    return "Mistérios da Ciência"


def _format_subject_in_sentence(subject: str, case: str = "em") -> str:
    """Format subject grammatically in Portuguese with appropriate contraction."""
    s = subject.strip()
    if not s:
        return "este fenômeno"
    s_lower = s.lower()

    # Pre-existing articles
    if s_lower.startswith(("o ", "a ", "os ", "as ", "um ", "uma ", "uns ", "umas ")):
        if case == "em":
            if s_lower.startswith("o "):
                return f"no {s[2:]}"
            elif s_lower.startswith("a "):
                return f"na {s[2:]}"
            elif s_lower.startswith("os "):
                return f"nos {s[3:]}"
            elif s_lower.startswith("as "):
                return f"nas {s[3:]}"
            return f"em {s}"
        elif case == "de":
            if s_lower.startswith("o "):
                return f"do {s[2:]}"
            elif s_lower.startswith("a "):
                return f"da {s[2:]}"
            elif s_lower.startswith("os "):
                return f"dos {s[3:]}"
            elif s_lower.startswith("as "):
                return f"das {s[3:]}"
            return f"de {s}"
        elif case == "sobre":
            return f"sobre {s}"
        elif case == "perto":
            if s_lower.startswith("o "):
                return f"perto do {s[2:]}"
            elif s_lower.startswith("a "):
                return f"perto da {s[2:]}"
            elif s_lower.startswith("os "):
                return f"perto dos {s[3:]}"
            elif s_lower.startswith("as "):
                return f"perto das {s[3:]}"
            return f"perto de {s}"

    # Singular/plural detection without leading article
    is_plural = s_lower.endswith("s")
    is_feminine = s_lower.endswith(("a", "ção", "dade", "gem")) and not s_lower.endswith(("tema", "problema", "sistema"))

    if case == "em":
        if is_plural:
            return f"em {s}"
        return f"na {s}" if is_feminine else f"no {s}"
    elif case == "de":
        if is_plural:
            return f"de {s}"
        return f"da {s}" if is_feminine else f"do {s}"
    elif case == "perto":
        if is_plural:
            return f"perto de {s}"
        return f"perto da {s}" if is_feminine else f"perto do {s}"
    elif case == "com":
        if is_plural:
            return f"com {s}"
        return f"com a {s}" if is_feminine else f"com o {s}"
    return f"sobre {s}"


def _generate_ab_hook_variations(subject: str) -> List[Dict[str, Any]]:
    """
    Generate 3 distinct high-converting viral hook variations:
    1. Curiosity Gap (Lacuna de Curiosidade)
    2. Shock & High Stakes (Choque & Urgência)
    3. Counter-Intuitive Fact (Verdade Contraintuitiva)
    """
    s_clean = (subject or "Mistérios da Ciência").strip().rstrip(".?!:")
    s_lower = s_clean.lower()

    # Detect theme keywords for domain-specific neuro-hooks
    is_space = any(w in s_lower for w in ["buraco negro", "universo", "galáxia", "estrela", "telescópio", "espaço", "marte", "planeta", "james webb", "fermi", "alien", "cosmos", "lua", "solar", "astrofísica"])
    is_ocean = any(w in s_lower for w in ["oceano", "mar", "marinas", "abismo", "bloop", "fossa", "tubarão", "águas", "submarino", "fundo do mar"])
    is_neuro = any(w in s_lower for w in ["cérebro", "cerebro", "mente", "memória", "memoria", "sono", "psicologia", "sonho", "ilusão", "ilusao", "consciência"])
    is_tech = any(w in s_lower for w in ["inteligência artificial", "ia", "robô", "robo", "algoritmo", "computador", "tecnologia"])

    s_em = _format_subject_in_sentence(s_clean, "em")
    s_de = _format_subject_in_sentence(s_clean, "de")
    s_perto = _format_subject_in_sentence(s_clean, "perto")
    s_com = _format_subject_in_sentence(s_clean, "com")

    # Hook 1: Curiosity Gap (Lacuna de Curiosidade)
    if is_space:
        hook_1_text = f"Existe uma razão perturbadora pela qual a física tenta esconder o que acontece {s_em}."
    elif is_ocean:
        hook_1_text = f"O que os radares militares detectaram no fundo {s_de} foi mantido sob sigilo até hoje."
    elif is_neuro:
        hook_1_text = f"Seu cérebro esconde uma anomalia sinistra {s_de} que você experimenta todos os dias sem perceber."
    elif is_tech:
        hook_1_text = f"O que os engenheiros acabaram de registrar por trás {s_de} não deveria ter vindo a público."
    else:
        hook_1_text = f"Existe um detalhe perturbador sobre {s_clean} que a maioria das pessoas nunca vai descobrir."

    # Hook 2: Shock & High Stakes (Choque & Urgência)
    if is_space:
        hook_2_text = f"Se você chegasse {s_perto} por apenas 1 segundo, seu corpo seria pulverizado antes de você piscar."
    elif is_ocean:
        hook_2_text = f"A pressão brutal {s_em} esmagaria cinquenta aviões comerciais em questão de milissegundos."
    elif is_neuro:
        hook_2_text = "Se essa função do seu cérebro falhar por 3 segundos, toda a sua percepção da realidade simplesmente acaba."
    elif is_tech:
        hook_2_text = f"O novo avanço {s_em} acabou de cruzar o limite exato que os cientistas prometeram nunca ultrapassar."
    else:
        hook_2_text = f"Se isso acontecesse {s_com} hoje, noventa e nove por cento das pessoas não teriam como escapar."

    # Hook 3: Counter-Intuitive Fact (Verdade Contraintuitiva)
    if is_space:
        hook_3_text = f"Parece impossível, mas o tempo passa em uma velocidade completamente diferente {s_perto}."
    elif is_ocean:
        hook_3_text = f"Nós temos mapas muito mais nítidos da superfície da Lua do que do que realmente vive {s_em}."
    elif is_neuro:
        hook_3_text = "Tudo o que você acha que sabe sobre a sua própria mente é na verdade uma ilusão calculada pelo cérebro."
    elif is_tech:
        hook_3_text = f"Ao contrário do que todo mundo pensa, o verdadeiro perigo {s_de} não é a consciência artificial, mas sim isso."
    else:
        hook_3_text = f"Tudo o que você aprendeu na escola sobre {s_clean} está completamente ao contrário da realidade."

    return [
        {
            "id": "hook_curiosity_gap",
            "type": "Curiosity Gap",
            "type_pt": "Lacuna de Curiosidade",
            "hook": hook_1_text,
            "retention_lift": "+18% de retenção aos 15s",
            "retention_lift_pct": 18,
            "psychological_trigger": "Ativa o viés cognitivo de informação incompleta. O cérebro humano odeia perguntas em aberto e se recusa a deslizar o feed.",
            "best_for": "Mistérios, curiosidades científicas e narrativas documentais de suspense.",
        },
        {
            "id": "hook_shock_stakes",
            "type": "Shock & High Stakes",
            "type_pt": "Choque & Urgência",
            "hook": hook_2_text,
            "retention_lift": "+24% de retenção aos 15s",
            "retention_lift_pct": 24,
            "psychological_trigger": "Dispara o reflexo de preservação e urgência extrema. Força retenção visual imediata por choque biológico/físico.",
            "best_for": "Astrofísica extrema, catástrofes, fatos brutais da natureza e perigos ocultos.",
        },
        {
            "id": "hook_counter_intuitive",
            "type": "Counter-Intuitive Fact",
            "type_pt": "Verdade Contraintuitiva",
            "hook": hook_3_text,
            "retention_lift": "+21% de retenção aos 15s",
            "retention_lift_pct": 21,
            "psychological_trigger": "Quebra de padrão neurológico. Desafia o senso comum e faz o espectador questionar o próprio conhecimento.",
            "best_for": "Desmistificação de crenças populares, neurociência, física teórica e paradoxos.",
        },
    ]


def analyze_script_virality(script: str, subject: str = "") -> Dict[str, Any]:
    """
    Comprehensive viral retention analysis and hook scoring engine for video scripts.

    Evaluates:
    - Word count, character count, and 1.15x neural audio duration (~2.65 wps).
    - Hook Score (0-100): opening power words, curiosity gaps, questions, stakes, brevity.
    - Pacing Score (0-100): rhythm cadence, sentence variance, transition pivots.
    - Retention Simulation: milestone decay projection [0s, 15s, 30s, 45s, 60s].
    - Recommendations: 2-4 actionable, prioritized optimization tips.
    - 3 Viral Hook A/B Variations for the given subject.
    """
    cleaned_script = (script or "").strip()
    words = _extract_words(cleaned_script)
    word_count = len(words)
    character_count = len(cleaned_script)

    # 1. Estimated duration calculation
    estimated_duration_seconds = (
        round(word_count / NEURAL_CADENCE_WORDS_PER_SEC, 1) if word_count > 0 else 0.0
    )

    resolved_subject = (subject or "").strip()
    if not resolved_subject:
        resolved_subject = _detect_subject_from_script(cleaned_script)

    # Handle completely empty script gracefully
    if word_count == 0:
        variations = _generate_ab_hook_variations(resolved_subject)
        return {
            "word_count": 0,
            "character_count": 0,
            "estimated_duration_seconds": 0.0,
            "cadence_words_per_second": NEURAL_CADENCE_WORDS_PER_SEC,
            "hook_score": 0,
            "pacing_score": 0,
            "overall_score": 0,
            "hook_analysis": {
                "opening_sentence": "",
                "word_count": 0,
                "power_words_detected": [],
                "has_question": False,
                "has_curiosity_gap": False,
                "has_high_stakes": False,
                "rating": "Vazio",
            },
            "pacing_analysis": {
                "sentence_count": 0,
                "avg_words_per_sentence": 0.0,
                "sentence_variance": 0.0,
                "transition_markers_count": 0,
                "transition_markers": [],
                "rating": "Vazio",
            },
            "retention_simulation": [
                {"second": 0, "retention_rate": 100.0, "benchmark": 100.0, "dropoff_risk": "Mínimo"},
                {"second": 15, "retention_rate": 0.0, "benchmark": 70.0, "dropoff_risk": "Crítico"},
                {"second": 30, "retention_rate": 0.0, "benchmark": 52.0, "dropoff_risk": "Crítico"},
                {"second": 45, "retention_rate": 0.0, "benchmark": 39.0, "dropoff_risk": "Crítico"},
                {"second": 60, "retention_rate": 0.0, "benchmark": 28.0, "dropoff_risk": "Crítico"},
            ],
            "recommendations": [
                "Insira ou gere um roteiro com pelo menos 130 a 170 palavras para preencher 60 segundos.",
                "Inicie com uma pergunta intrigante ou fato contraintuitivo para prender a atenção nos primeiros 3 segundos.",
            ],
            "hook_variations": variations,
        }

    sentences = _split_sentences(cleaned_script)
    opening_sentence = sentences[0] if sentences else cleaned_script
    opening_words = _extract_words(opening_sentence)
    opening_word_count = len(opening_words)
    opening_lower = opening_sentence.lower()

    # In short-form videos, the opening hook phase comprises the first ~32 words or the first 2 sentences
    opening_phase_sentences = sentences[:2] if len(sentences) >= 2 else sentences
    opening_phase_text = " ".join(opening_phase_sentences).lower()
    first_chunk_text = " ".join(words[:35]).lower()
    hook_evaluation_text = opening_phase_text if len(opening_phase_text) > len(first_chunk_text) else first_chunk_text
    hook_evaluation_words = set(_extract_words(hook_evaluation_text))

    # --- 2. HOOK SCORE EVALUATION (0 - 100) ---
    # A. Curiosity Gap & Questions (0-25 pts)
    has_question = "?" in opening_sentence or (len(sentences) > 1 and "?" in sentences[1] and opening_word_count <= 18)
    has_curiosity_starter = any(trig in hook_evaluation_text for trig in CURIOSITY_TRIGGERS)

    if has_question and has_curiosity_starter:
        curiosity_pts = 25
    elif has_curiosity_starter:
        curiosity_pts = 21
    elif has_question:
        curiosity_pts = 19
    elif any(trig in hook_evaluation_text for trig in ["segredo", "mistério", "misterio", "descobriu", "acontece", "revelou"]):
        curiosity_pts = 14
    else:
        curiosity_pts = 4

    # B. Power Words & Shock Factor (0-25 pts)
    detected_power_words = [w for w in hook_evaluation_words if w in POWER_WORDS]
    power_words_count = len(detected_power_words)
    if power_words_count >= 3:
        power_pts = 25
    elif power_words_count == 2:
        power_pts = 20
    elif power_words_count == 1:
        power_pts = 14
    else:
        power_pts = 4

    # C. High Stakes, Concrete Anchors & Numbers (0-25 pts)
    has_numbers = bool(
        re.search(
            r"\b(\d+|cem|mil|milhões|milhoes|bilhões|bilhoes|trilhões|trilhoes|vezes|graus|metros|quilômetros|quilometros|segundos)\b",
            hook_evaluation_text,
            re.IGNORECASE,
        )
    )
    has_stakes = any(w in hook_evaluation_words for w in STAKES_WORDS)
    if has_numbers and has_stakes:
        stakes_pts = 25
    elif has_numbers:
        stakes_pts = 18
    elif has_stakes:
        stakes_pts = 16
    else:
        stakes_pts = 6

    # D. Cadence, Length & Throat-Clearing Penalty (0-25 pts)
    if 6 <= opening_word_count <= 18:
        cadence_pts = 25
    elif 19 <= opening_word_count <= 25:
        cadence_pts = 18
    elif 4 <= opening_word_count < 6:
        cadence_pts = 15
    elif opening_word_count > 25:
        cadence_pts = 10
    else:
        cadence_pts = 6

    # Penalty for throat clearing / greeting fluff
    penalty_fluff = 0
    if any(fluff in opening_lower for fluff in FLUFF_OPENERS):
        penalty_fluff = 25
    elif opening_lower.startswith(("bom,", "então,", "entao,", "basicamete", "well,")):
        penalty_fluff = 12

    hook_raw = curiosity_pts + power_pts + stakes_pts + cadence_pts - penalty_fluff
    hook_score = max(5, min(100, int(round(hook_raw))))

    if hook_score >= 82:
        hook_rating = "Excepcional (Alto Potencial Viral)"
    elif hook_score >= 68:
        hook_rating = "Forte (Boa Retenção Inicial)"
    elif hook_score >= 48:
        hook_rating = "Médio (Risco de Drop-off nos primeiros 3s)"
    else:
        hook_rating = "Fraco (Necessita de Reescrita Urgente)"

    # --- 3. PACING SCORE EVALUATION (0 - 100) ---
    sentence_word_counts = [_extract_words(s) for s in sentences]
    sentence_lengths = [len(sw) for sw in sentence_word_counts if len(sw) > 0]
    if not sentence_lengths:
        sentence_lengths = [word_count]

    sentence_count = len(sentence_lengths)
    avg_words = sum(sentence_lengths) / sentence_count

    # Variance (Standard deviation of sentence lengths)
    if sentence_count > 1:
        variance = sum((length - avg_words) ** 2 for length in sentence_lengths) / sentence_count
        std_dev = round(math.sqrt(variance), 2)
    else:
        std_dev = 0.0

    # A. Variance Score (0-35 pts)
    # Healthy variation: 3.5 to 9.5 indicates dynamic rhythm
    if 3.5 <= std_dev <= 9.5:
        variance_pts = 35
    elif 2.0 <= std_dev < 3.5 or 9.5 < std_dev <= 13.0:
        variance_pts = 25
    elif std_dev < 2.0:
        variance_pts = 10  # Monotonous
    else:
        variance_pts = 16  # Excessive disparity

    # B. Optimal Average Sentence Length (0-35 pts)
    # Ideal average length: 9 to 16.5 words
    if 9.0 <= avg_words <= 16.5:
        length_pts = 35
    elif 6.5 <= avg_words < 9.0 or 16.5 < avg_words <= 22.0:
        length_pts = 26
    elif 22.0 < avg_words <= 28.0:
        length_pts = 15
    elif avg_words > 28.0:
        length_pts = 6   # Dense walls of text
    else:
        length_pts = 16  # Overly fragmented

    # C. Cognitive Flow & Contrast Markers (0-30 pts)
    script_lower = cleaned_script.lower()
    found_transitions = [m for m in TRANSITION_MARKERS if re.search(r"\b" + re.escape(m) + r"\b", script_lower)]
    transitions_count = len(found_transitions)
    if transitions_count >= 3:
        flow_pts = 30
    elif transitions_count == 2:
        flow_pts = 22
    elif transitions_count == 1:
        flow_pts = 15
    else:
        flow_pts = 6

    pacing_raw = variance_pts + length_pts + flow_pts
    pacing_score = max(10, min(100, int(round(pacing_raw))))

    if pacing_score >= 82:
        pacing_rating = "Hipnótico & Dinâmico"
    elif pacing_score >= 68:
        pacing_rating = "Fluido & Bem Cadenciado"
    elif pacing_score >= 48:
        pacing_rating = "Moderado (Cadência Linear)"
    else:
        pacing_rating = "Monótono (Difícil Digestão Sonora)"

    # Overall virality score (Weighted: Hook 55%, Pacing 45%)
    overall_score = int(round(hook_score * 0.55 + pacing_score * 0.45))

    # --- 4. RETENTION SIMULATION ([0s, 15s, 30s, 45s, 60s]) ---
    ret_0 = 100.0
    hook_factor = (hook_score - 50.0) * 0.32
    ret_15 = max(42.0, min(88.0, 70.0 + hook_factor))

    # 30s retention is driven by 15s retention + Pacing Score + mid-script pivots
    pacing_factor_30 = 0.65 + (pacing_score / 100.0) * 0.22
    ret_30 = max(26.0, min(75.0, ret_15 * pacing_factor_30))

    # 45s retention
    pacing_factor_45 = 0.70 + (pacing_score / 100.0) * 0.16
    ret_45 = max(18.0, min(65.0, ret_30 * pacing_factor_45))

    # 60s retention
    pacing_factor_60 = 0.68 + (pacing_score / 100.0) * 0.18
    ret_60 = max(12.0, min(55.0, ret_45 * pacing_factor_60))

    def _risk_level(rate: float, benchmark: float) -> str:
        diff = rate - benchmark
        if diff >= 5:
            return "Baixo"
        elif diff >= -4:
            return "Médio"
        elif diff >= -12:
            return "Alto"
        return "Crítico"

    retention_simulation = [
        {
            "second": 0,
            "retention_rate": round(ret_0, 1),
            "benchmark": 100.0,
            "dropoff_risk": "Mínimo",
        },
        {
            "second": 15,
            "retention_rate": round(ret_15, 1),
            "benchmark": 70.0,
            "dropoff_risk": _risk_level(ret_15, 70.0),
        },
        {
            "second": 30,
            "retention_rate": round(ret_30, 1),
            "benchmark": 52.0,
            "dropoff_risk": _risk_level(ret_30, 52.0),
        },
        {
            "second": 45,
            "retention_rate": round(ret_45, 1),
            "benchmark": 39.0,
            "dropoff_risk": _risk_level(ret_45, 39.0),
        },
        {
            "second": 60,
            "retention_rate": round(ret_60, 1),
            "benchmark": 28.0,
            "dropoff_risk": _risk_level(ret_60, 28.0),
        },
    ]

    # --- 5. ACTIONABLE RECOMMENDATIONS (2-4 prioritized tips) ---
    recommendations: List[str] = []

    # Check 1: Opening sentence brevity / drop-off prevention
    if opening_word_count > 22:
        excess_seconds = max(2, int(round((opening_word_count - 14) / NEURAL_CADENCE_WORDS_PER_SEC)))
        recommendations.append(
            f"Encurte a introdução em cerca de {excess_seconds} segundos (menos de 15 palavras) para evitar drop-off antes do segundo 3."
        )
    elif opening_word_count < 5:
        recommendations.append(
            "O gancho inicial está muito curto; adicione uma pergunta provocativa ou paradoxo para segurar o espectador."
        )

    # Check 2: Throat-clearing fluff
    if penalty_fluff > 0:
        recommendations.append(
            "Elimine saudações ou introduções convencionais ('olá', 'neste vídeo'). Comece imediatamente no ponto mais dramático."
        )

    # Check 3: Hook power words / curiosity triggers
    if power_words_count == 0 or hook_score < 70:
        recommendations.append(
            "Adicione palavras de alto impacto sensorial (ex: 'segredo', 'chocante', 'impossível') ou formule uma pergunta direta nos primeiros 5 segundos."
        )

    # Check 4: Mid-video retention / plot twist around second 30
    if transitions_count < 2:
        recommendations.append(
            "Adicione uma quebra de expectativa ou contraste no segundo 30 (ex: 'Mas o que ninguém esperava...') para reengajar quem estava prestes a deslizar."
        )

    # Check 5: Sentence rhythm & variance
    if std_dev < 3.0 and sentence_count >= 3:
        recommendations.append(
            "Varie o ritmo das frases: alterne frases curtas e diretas de 4 a 6 palavras com períodos explicativos para criar uma cadência hipnótica."
        )

    # Check 6: Duration zone
    if estimated_duration_seconds < 35.0:
        recommendations.append(
            f"Roteiro curto ({int(estimated_duration_seconds)}s): expanda a revelação central para atingir a zona de monetização ideal (50s a 65s)."
        )
    elif estimated_duration_seconds > 75.0:
        recommendations.append(
            f"Roteiro longo ({int(estimated_duration_seconds)}s): corte 15 a 20 palavras secundárias para manter a taxa de conclusão acima de 40%."
        )

    # High performance fallback recommendations if script is already stellar
    if len(recommendations) < 2:
        recommendations.append(
            "Excelente retenção prevista! Sincronize cortes de B-roll e zoom a cada 2,5 segundos nos primeiros 15s para potencializar o algoritmo."
        )
    if len(recommendations) < 2:
        recommendations.append(
            "Destaque em amarelo ou ciano a palavra-chave de impacto na legenda durante os 3 primeiros segundos."
        )

    # Guarantee between 2 and 4 recommendations
    final_recommendations = recommendations[:4]

    # --- 6. 3 VIRAL HOOK A/B VARIATIONS ---
    hook_variations = _generate_ab_hook_variations(resolved_subject)

    return {
        "word_count": word_count,
        "character_count": character_count,
        "estimated_duration_seconds": estimated_duration_seconds,
        "cadence_words_per_second": NEURAL_CADENCE_WORDS_PER_SEC,
        "hook_score": hook_score,
        "pacing_score": pacing_score,
        "overall_score": overall_score,
        "hook_analysis": {
            "opening_sentence": opening_sentence,
            "word_count": opening_word_count,
            "power_words_detected": detected_power_words,
            "has_question": has_question,
            "has_curiosity_gap": has_curiosity_starter,
            "has_high_stakes": has_stakes or has_numbers,
            "rating": hook_rating,
        },
        "pacing_analysis": {
            "sentence_count": sentence_count,
            "avg_words_per_sentence": round(avg_words, 1),
            "sentence_variance": std_dev,
            "transition_markers_count": transitions_count,
            "transition_markers": found_transitions,
            "rating": pacing_rating,
        },
        "retention_simulation": retention_simulation,
        "recommendations": final_recommendations,
        "hook_variations": hook_variations,
    }
