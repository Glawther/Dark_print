"""Monetization Funnel & Pinned Comment Engine.

Builds high-converting monetization packs for short-form video creators:
- ManyChat DM automation trigger comments ("Comente 'DOSSIE'...")
- YouTube Shorts / TikTok to Longform conversion bridge
- FTC and CONAR compliant affiliate disclosures
- Second-50 verbal script and visual hook overlays
- Multi-tier RPM revenue calculator (Tier 1 vs Brazil/Tier 3)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# ManyChat Trigger Words and Niched Defaults
# ---------------------------------------------------------------------------

NICHE_DEFAULTS = [
    {
        "keywords": ["espaço", "espaco", "buraco negro", "galáxia", "galaxy", "universo", "cosmos", "webb", "nasa", "estrela"],
        "trigger": "COSMOS",
        "lead_magnet": "Dossiê Secreto da Astrofísica & Dados Reclassificados em PDF",
        "affiliate_category": "livros_educacao",
    },
    {
        "keywords": ["oceano", "mar", "abismo", "marianas", "bloop", "profundo", "submarino", "fossa"],
        "trigger": "ABISMO",
        "lead_magnet": "Arquivo de Mistérios Oceânicos & Gravações Inéditas em PDF",
        "affiliate_category": "livros_educacao",
    },
    {
        "keywords": ["cérebro", "cerebro", "mente", "psicologia", "memória", "memoria", "viés", "vies", "dunning", "overton"],
        "trigger": "MENTE",
        "lead_magnet": "Guia Prático de Vieses Cognitivos & Hacks Mentais em PDF",
        "affiliate_category": "livros_educacao",
    },
    {
        "keywords": ["quântica", "quantica", "quantum", "física", "fisica", "átomo", "atomo", "relatividade", "einstein"],
        "trigger": "QUANTUM",
        "lead_magnet": "Guia Ilustrado dos Paradoxo da Física Quântica em PDF",
        "affiliate_category": "livros_educacao",
    },
    {
        "keywords": ["ia", "inteligência artificial", "inteligencia artificial", "chatgpt", "software", "tech", "computador", "código", "codigo"],
        "trigger": "FUTURO",
        "lead_magnet": "Mega Pack com 100+ Prompts Avançados e Ferramentas Secretas de IA",
        "affiliate_category": "softwares_ia",
    },
    {
        "keywords": ["dinheiro", "finanças", "financas", "riqueza", "rico", "renda", "cripto", "investimento", "lucro", "milionário", "milionario"],
        "trigger": "LUCRO",
        "lead_magnet": "Planilha de Gestão Financeira & Mapa de Fontes de Renda Passiva",
        "affiliate_category": "financas_investimentos",
    },
    {
        "keywords": ["história", "historia", "antigo", "antiga", "roma", "grécia", "grecia", "egito", "arqueologia", "ruínas"],
        "trigger": "SEGREDO",
        "lead_magnet": "Dossiê Histórico Censurado & Descobertas Arqueológicas em PDF",
        "affiliate_category": "livros_educacao",
    },
]

# Standard triggers based on lead magnet text
LEAD_MAGNET_KEYWORD_TRIGGERS = [
    ("dossie", "DOSSIE"),
    ("dossiê", "DOSSIE"),
    ("guia", "GUIA"),
    ("guide", "GUIA"),
    ("mapa", "MAPA"),
    ("planilha", "PLANILHA"),
    ("pdf", "PDF"),
    ("prompt", "PROMPT"),
    ("checklist", "CHECKLIST"),
    ("lista", "LISTA"),
    ("aula", "AULA"),
    ("livro", "LIVRO"),
    ("ebook", "EBOOK"),
    ("resumo", "RESUMO"),
    ("segredo", "SEGREDO"),
    ("pack", "PACK"),
]

# Affiliate product suggestions by category
AFFILIATE_CATALOG = {
    "livros_educacao": {
        "label": "Livros & Educação Científica (Amazon Associates)",
        "products": [
            {"name": "Livro: 'Cosmos' - Carl Sagan (Edição Especial)", "type": "Livro Físico / Kindle", "est_commission": "8% - 10%"},
            {"name": "Livro: 'O Universo Numa Casca de Noz' - Stephen Hawking", "type": "Livro Físico / Kindle", "est_commission": "8% - 10%"},
            {"name": "Livro: 'Rápido e Devagar: Duas Formas de Pensar' - Daniel Kahneman", "type": "Livro Físico / Kindle", "est_commission": "8% - 10%"},
            {"name": "Kindle Paperwhite 16GB com Luz Ajustável", "type": "Dispositivo Amazon", "est_commission": "7% - 9%"},
        ],
    },
    "tecnologia_gadgets": {
        "label": "Tecnologia & Equipamentos de Criação",
        "products": [
            {"name": "Microfone Sem Fio Lapela DJI Mic 2 / Boya", "type": "Áudio & Vídeo", "est_commission": "5% - 8%"},
            {"name": "Luminária de Mesa LED com Controle de Temperatura", "type": "Acessório Studio", "est_commission": "6% - 10%"},
            {"name": "Hub USB-C 8 em 1 de Alta Velocidade", "type": "Hardware", "est_commission": "7% - 10%"},
        ],
    },
    "softwares_ia": {
        "label": "Softwares, IA & SaaS de Produtividade",
        "products": [
            {"name": "Assinatura ElevenLabs / Ferramenta de Clonagem de Voz", "type": "SaaS Recorrente", "est_commission": "20% - 30% MRR"},
            {"name": "NordVPN / ExpressVPN Proteção de Dados", "type": "Software de Segurança", "est_commission": "35% - 50%"},
            {"name": "Hostinger Cloud Hosting para Criadores", "type": "Hospedagem Web", "est_commission": "40% - 60%"},
        ],
    },
    "financas_investimentos": {
        "label": "Finanças, Contas & Investimentos",
        "products": [
            {"name": "Hardware Wallet Ledger Nano S Plus (Cripto)", "type": "Segurança Financeira", "est_commission": "10% - 15%"},
            {"name": "Livro: 'A Psicologia Financeira' - Morgan Housel", "type": "Livro Físico / Kindle", "est_commission": "8% - 10%"},
            {"name": "Conta Global Internacional Nomad / Wise (Link de Indicação)", "type": "Fintech", "est_commission": "Bônus por ativação"},
        ],
    },
    "saude_biohacking": {
        "label": "Saúde, Sono & Biohacking",
        "products": [
            {"name": "Óculos Bloqueador de Luz Azul para Telas", "type": "Acessório de Sono", "est_commission": "8% - 12%"},
            {"name": "Suplemento Magnésio Treonato & Inositol", "type": "Nutracêuticos", "est_commission": "10% - 15%"},
            {"name": "Smartband Monitor Cardíaco & Sono", "type": "Wearable", "est_commission": "5% - 8%"},
        ],
    },
}


# ---------------------------------------------------------------------------
# Extraction & Inference Helpers
# ---------------------------------------------------------------------------

def _clean_text(text: str) -> str:
    """Strip extraneous quotes and whitespace."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def extract_trigger_word(lead_magnet: str = "", subject: str = "") -> str:
    """
    Extracts or infers a ManyChat trigger word in uppercase.
    Prioritizes explicit lead magnet keywords (by earliest occurrence in text), then subject niche defaults.
    """
    lm_clean = (lead_magnet or "").lower()
    matches = []
    for kw, trigger in LEAD_MAGNET_KEYWORD_TRIGGERS:
        idx = lm_clean.find(kw)
        if idx != -1:
            matches.append((idx, trigger))
    if matches:
        matches.sort(key=lambda x: x[0])
        return matches[0][1]

    combined = f"{subject} {lead_magnet}".lower()
    for niche in NICHE_DEFAULTS:
        for kw in niche["keywords"]:
            if kw in combined:
                return niche["trigger"]

    # Fallback: extract first substantial alphanumeric word from subject
    words = [w for w in re.findall(r"[A-Za-zÀ-ÿ]{4,}", subject) if len(w) <= 10]
    if words:
        cleaned = re.sub(r"[^A-Za-z]", "", words[0]).upper()
        if len(cleaned) >= 3:
            return cleaned

    return "DOSSIE"


def infer_lead_magnet(subject: str = "", script: str = "") -> Dict[str, str]:
    """
    Infers an irresistible lead magnet title and affiliate category
    if the creator did not explicitly provide one.
    """
    combined = f"{subject} {script}".lower()
    for niche in NICHE_DEFAULTS:
        for kw in niche["keywords"]:
            if kw in combined:
                return {
                    "lead_magnet": niche["lead_magnet"],
                    "affiliate_category": niche["affiliate_category"],
                    "trigger": niche["trigger"],
                }

    subj_label = subject.strip() or "este tema"
    subj_label = re.sub(r"[?!.,;]+$", "", subj_label)
    return {
        "lead_magnet": f"Dossiê Completo e Não Censurado sobre {subj_label} em PDF",
        "affiliate_category": "livros_educacao",
        "trigger": "DOSSIE",
    }


def get_affiliate_disclosures() -> Dict[str, str]:
    """
    Generates FTC (USA) and CONAR (Brazil) compliant disclosure texts.
    """
    conar = (
        "⚠️ Transparência (CONAR): Este conteúdo e os links nos comentários/descrição "
        "podem conter links de afiliados. Ao adquirir por meio deles, nosso canal recebe uma pequena "
        "comissão sem nenhum custo adicional para você."
    )
    ftc = (
        "⚠️ FTC Disclosure: This video and comments may contain affiliate links. "
        "If you purchase through these links, I may earn a qualifying commission at no additional cost to you."
    )
    tags = "#publi #afiliado #ad #transparencia"
    full_text = (
        f"{conar}\n\n"
        f"{ftc}\n"
        f"Tags de conformidade: {tags}"
    )

    return {
        "conar_br": conar,
        "ftc_us": ftc,
        "short_tags": tags,
        "full_text": full_text,
    }


def get_affiliate_recommendations(category: str = "") -> List[Dict[str, str]]:
    """Returns curated affiliate product ideas for a given category."""
    cat_key = (category or "").lower().strip()
    if cat_key in AFFILIATE_CATALOG:
        return AFFILIATE_CATALOG[cat_key]["products"]

    # Fuzzy match category
    for key, data in AFFILIATE_CATALOG.items():
        if cat_key in key or any(p in cat_key for p in ["livro", "book", "ia", "tech", "gadget", "financ", "saude"]):
            return data["products"]

    return AFFILIATE_CATALOG["livros_educacao"]["products"]


# ---------------------------------------------------------------------------
# Projected RPM Revenue Calculator
# ---------------------------------------------------------------------------

def calculate_projected_earnings(views: int, tier: str = "tier_1") -> Dict[str, Any]:
    """
    Calculates projected AdSense Shorts RPM revenue for a given view count.
    
    Tiers:
    - tier_1: $0.15 - $0.35 per 1,000 views (USA, UK, Canada, Australia, Germany)
    - brazil_tier_3: $0.03 - $0.07 per 1,000 views (approx R$ 0,15 - R$ 0,35 / mil views)
    """
    views_k = max(0, views) / 1000.0

    if tier.lower() in ("tier_1", "tier1", "us", "usa", "global"):
        min_rpm = 0.15
        max_rpm = 0.35
        min_usd = round(views_k * min_rpm, 2)
        max_usd = round(views_k * max_rpm, 2)
        return {
            "views": views,
            "tier": "tier_1",
            "rpm_range_usd": [min_rpm, max_rpm],
            "min_usd": min_usd,
            "max_usd": max_usd,
            "formatted": f"${min_usd:,.2f} - ${max_usd:,.2f}",
        }
    else:
        # Brazil / Latin America (Tier 3)
        min_rpm_usd = 0.03
        max_rpm_usd = 0.07
        usd_to_brl = 5.20
        min_usd = round(views_k * min_rpm_usd, 2)
        max_usd = round(views_k * max_rpm_usd, 2)
        min_brl = round(min_usd * usd_to_brl, 2)
        max_brl = round(max_usd * usd_to_brl, 2)
        return {
            "views": views,
            "tier": "brazil_tier_3",
            "rpm_range_usd": [min_rpm_usd, max_rpm_usd],
            "min_usd": min_usd,
            "max_usd": max_usd,
            "min_brl": min_brl,
            "max_brl": max_brl,
            "formatted_usd": f"${min_usd:,.2f} - ${max_usd:,.2f}",
            "formatted_brl": f"R$ {min_brl:,.2f} - R$ {max_brl:,.2f}".replace(".", "_").replace(",", ".").replace("_", ","),
            "formatted": f"R$ {min_brl:,.2f} - R$ {max_brl:,.2f} (${min_usd:,.2f} - ${max_usd:,.2f})".replace(".", "_").replace(",", ".").replace("_", ","),
        }


def build_revenue_estimator_summary() -> Dict[str, Any]:
    """
    Builds the standard views milestones revenue table (100k, 500k, 1M).
    Covers both Tier 1 and Brazil/Tier 3, plus Longform Bridge & Lead Magnet multiplier.
    """
    t1_100k = calculate_projected_earnings(100_000, "tier_1")
    t1_500k = calculate_projected_earnings(500_000, "tier_1")
    t1_1m = calculate_projected_earnings(1_000_000, "tier_1")

    br_100k = calculate_projected_earnings(100_000, "brazil_tier_3")
    br_500k = calculate_projected_earnings(500_000, "brazil_tier_3")
    br_1m = calculate_projected_earnings(1_000_000, "brazil_tier_3")

    return {
        "tier_1": {
            "country_group": "Tier 1 (EUA, Reino Unido, Canadá, Austrália, Alemanha)",
            "rpm_range_usd": [0.15, 0.35],
            "rpm_display": "$0.15 - $0.35 por 1k visualizações",
            "projections": {
                "100k": t1_100k,
                "500k": t1_500k,
                "1m": t1_1m,
            },
            "views_100k": t1_100k["formatted"],
            "views_500k": t1_500k["formatted"],
            "views_1m": t1_1m["formatted"],
        },
        "brazil_tier_3": {
            "country_group": "Brasil & América Latina (Tier 3)",
            "rpm_range_usd": [0.03, 0.07],
            "rpm_display": "$0.03 - $0.07 (R$ 0,15 - R$ 0,35) por 1k visualizações",
            "projections": {
                "100k": br_100k,
                "500k": br_500k,
                "1m": br_1m,
            },
            "views_100k": br_100k["formatted"],
            "views_500k": br_500k["formatted"],
            "views_1m": br_1m["formatted"],
        },
        "longform_bridge_extra": {
            "concept": "Ponte do Shorts para Vídeo Longo no Comentário Fixado (RPM 20x maior)",
            "ctr_estimate": "1.0% - 2.5%",
            "extra_100k_views": "+$6.00 - $18.00 adicionais (1.000 a 2.500 cliques no vídeo de 20min)",
            "extra_500k_views": "+$30.00 - $90.00 adicionais",
            "extra_1m_views": "+$60.00 - $180.00 adicionais",
        },
        "lead_capture_potential": {
            "concept": "Leads capturados via automação no Direct (ManyChat / Instagram / TikTok)",
            "comment_conversion_rate": "1.5% - 3.0%",
            "leads_100k_views": "1.500 - 3.000 leads automáticos gerados",
            "leads_500k_views": "7.500 - 15.000 leads",
            "leads_1m_views": "15.000 - 30.000 leads qualificados na base",
        },
    }


# ---------------------------------------------------------------------------
# Main Monetization Generator
# ---------------------------------------------------------------------------

def generate_monetization_pack(
    subject: str,
    script: str = "",
    lead_magnet: str = "",
    affiliate_category: str = "",
) -> Dict[str, Any]:
    """
    Builds a complete, conversion-optimized monetization kit for a short-form video.

    Args:
        subject: Topic or title of the video.
        script: Narrative script text (optional).
        lead_magnet: Custom lead magnet title or description (optional).
        affiliate_category: Affiliate niche (optional).

    Returns:
        Dict containing:
        - pinned_comment_dm_trigger: High-converting ManyChat comment copy.
        - pinned_comment_longform_bridge: YouTube Shorts / TikTok to longform bridge.
        - affiliate_disclosures: FTC and CONAR compliant disclosure dict.
        - lead_magnet_callouts: Verbal 50s script and visual overlay banner.
        - estimated_earnings: Multi-tier RPM earnings calculator.
        - revenue_estimator: Mirror alias of estimated_earnings.
        - trigger_word: Uppercase trigger word for ManyChat.
        - lead_magnet: Chosen lead magnet title.
        - affiliate_recommendations: Selected product hooks.
        - clipboard_comment: Full unified pinned comment ready for copy-pasting.
    """
    clean_sub = _clean_text(subject)
    clean_scr = _clean_text(script)
    clean_lm = _clean_text(lead_magnet)
    clean_cat = _clean_text(affiliate_category)

    # If lead magnet or affiliate category not specified, infer intelligently
    inferred = infer_lead_magnet(clean_sub, clean_scr)
    effective_lead_magnet = clean_lm if clean_lm else inferred["lead_magnet"]
    effective_category = clean_cat if clean_cat else inferred["affiliate_category"]

    # Extract or infer ManyChat trigger word
    trigger_word = extract_trigger_word(lead_magnet=effective_lead_magnet, subject=clean_sub)

    # 1. Pinned comment DM trigger (High converting ManyChat copy)
    pinned_comment_dm_trigger = (
        f"Comente \"{trigger_word}\" para receber o {effective_lead_magnet} no seu direct agora mesmo! 📩👇 "
        f"(O robô envia o link direto em menos de 5 segundos)."
    )

    # 2. Pinned comment Longform bridge (Shorts to Longform conversion)
    pinned_comment_longform_bridge = (
        "🎬 Assista à investigação completa de 20min no primeiro link fixado: "
        "[LINK DO VÍDEO COMPLETO NO YOUTUBE]. Descubra todos os fatos que não couberam neste vídeo curto!"
    )

    # 3. Affiliate disclosures (FTC & CONAR compliant)
    affiliate_disclosures = get_affiliate_disclosures()

    # 4. Lead magnet callouts (50-second hook overlay and verbal callout)
    verbal_script_50s = (
        f"O link para baixar {effective_lead_magnet} tá no comentário fixado. "
        f"Comente \"{trigger_word}\" aqui embaixo que eu te envio direto no direct!"
    )
    visual_overlay_text = "📌 BAIXE O MATERIAL NO COMENTÁRIO FIXADO"

    lead_magnet_callouts = {
        "verbal_script_50s": verbal_script_50s,
        "visual_overlay_text": visual_overlay_text,
        "trigger_word": trigger_word,
        "second": 50,
        "callout_timestamp_window": "00:48 - 00:58",
        "call_to_action": f"Comente '{trigger_word}' para receber o material exclusivo no direct",
    }

    # 5. Estimated earnings / Revenue estimator
    revenue_data = build_revenue_estimator_summary()

    # Recommended affiliate products
    affiliate_recommendations = get_affiliate_recommendations(effective_category)

    # Unified clipboard comment that creators can copy and pin with 1 click
    clipboard_comment = (
        f"📩 MATERIAL COMPLETO GRATUITO:\n"
        f"Comente \"{trigger_word}\" para receber o {effective_lead_magnet} no seu direct agora mesmo! 🚀👇\n\n"
        f"🎬 VÍDEO COMPLETO E DETALHADO (20min):\n"
        f"Assista à investigação completa no link fixado: [LINK DO VÍDEO COMPLETO NO YOUTUBE]\n\n"
        f"⚖️ {affiliate_disclosures['conar_br']}"
    )

    return {
        "pinned_comment_dm_trigger": pinned_comment_dm_trigger,
        "pinned_comment_longform_bridge": pinned_comment_longform_bridge,
        "affiliate_disclosures": affiliate_disclosures,
        "lead_magnet_callouts": lead_magnet_callouts,
        "estimated_earnings": revenue_data,
        "revenue_estimator": revenue_data,  # Alias for strict compatibility
        "trigger_word": trigger_word,
        "lead_magnet": effective_lead_magnet,
        "affiliate_category": effective_category,
        "affiliate_recommendations": affiliate_recommendations,
        "clipboard_comment": clipboard_comment,
    }
