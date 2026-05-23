import os
import re
from typing import List

import requests
from bs4 import BeautifulSoup
from weasyprint import HTML, CSS


def extrair_texto_url(url: str) -> str:
    """Extrai o texto visível de uma página web."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    session = requests.Session()
    session.headers.update(headers)
    resp = session.get(url, timeout=15, allow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Remover scripts, styles, nav, footer
    for tag in soup(
        ["script", "style", "nav", "footer", "header", "noscript"]
    ):
        tag.decompose()

    texto = soup.get_text(separator="\n", strip=True)
    # Limitar tamanho para não estourar o prompt
    return texto[:8000]


def obter_prompt_extrair_vaga(texto_pagina: str) -> str:
    """Prompt para Gemini extrair dados estruturados da vaga."""
    return (
        "Analise o texto abaixo, extraído de uma página de vaga "
        "de emprego, e retorne APENAS um JSON com:\n"
        "{\n"
        '  "empresa": "Nome da empresa",\n'
        '  "cargo": "Título da vaga/cargo",\n'
        '  "descricao": "Descrição completa da vaga '
        '(responsabilidades, atividades, etc.)",\n'
        '  "requisitos": ["skill 1", "skill 2", '
        '"conhecimento 1", ...],\n'
        '  "beneficios": ["benefício 1", '
        '"benefício 2", ...]\n'
        "}\n\n"
        "REGRAS:\n"
        "- Extraia apenas informações reais do texto\n"
        "- Em 'requisitos', liste TODAS as skills, "
        "tecnologias e conhecimentos pedidos\n"
        "- Em 'beneficios', liste os benefícios "
        "oferecidos (VR, VT, plano de saúde, etc.)\n"
        "- Se não encontrar algum campo, use [] ou "
        "string vazia\n"
        "- Retorne SOMENTE o JSON, sem explicações\n\n"
        f"TEXTO DA PÁGINA:\n{texto_pagina}"
    )


def clean_ai_response(text: str) -> str:
    """Remove artefatos de IA (code fences, saudações, CTAs) do texto."""
    # remove code fences
    t = re.sub(r"```[\s\S]*?```", "", text)
    # remove markdown fences or leading/trailing dashes
    t = t.strip().lstrip("-\n ")

    # remove common assistant-opening lines
    lines = t.splitlines()
    skip_prefixes = (
        "Olá",
        "Oi",
        "Perfeito",
        "Excelente",
        "Com certeza",
        "Claro",
        "Certo",
        "Posso",
        "Vou",
        "Pronto",
    )
    i = 0
    for i, ln in enumerate(lines):
        lstr = ln.strip()
        if not lstr:
            continue
        if any(
            lstr.lower().startswith(p.lower())
            for p in skip_prefixes
        ):
            continue
        # if line contains obvious assistant verbs, skip
        assistant_verbs = (
            "vamos", "analis", "vou", "posso", "ajudar"
        )
        if any(w in lstr.lower() for w in assistant_verbs):
            continue
        # otherwise, stop skipping
        break

    cleaned_lines = lines[i:]

    # remove trailing assistant questions/CTAs
    trailing_patterns = [
        r"^(.*\?)$",
        (
            r"^(deseja|quer|gostaria|posso|"
            r"precisa|querer|queria)\b"
        ),
        r"^(se quiser|se desejar)\b",
    ]

    # drop lines from end while they match trailing patterns
    while cleaned_lines:
        last = cleaned_lines[-1].strip()
        if not last:
            cleaned_lines.pop()
            continue
        matched = False
        for pat in trailing_patterns:
            if re.search(pat, last, re.IGNORECASE):
                matched = True
                break
        if matched:
            cleaned_lines.pop()
        else:
            break

    cleaned = "\n".join(cleaned_lines).strip()
    return cleaned


def gerar_pdf(dados: dict, empresa: str) -> str:
    """Gera o currículo completo no padrão visual SempreIT"""
    nome = dados.get("nome", "Denis Bolfarini")
    contato = dados.get(
        "contato",
        "denis.bolfarini@gmail.com | 11948103499 | São Paulo, SP",
    )
    resumo = dados.get("resumo", "")
    habilidades: List[str] = dados.get("habilidades", [])
    experiencias: List[dict] = dados.get("experiencias", [])
    formacao: List[str] = dados.get("formacao", [])

    html_style = "".join(
        [
            "<style>",
            "@page { size: A4; margin: 1.2cm; }",
            "body { font-family: Helvetica, Arial, sans-serif; ",
            "font-size: 9pt; color: #333; line-height: 1.4; }",
            ".header { border-bottom: 2px solid #1a3a5a; ",
            "padding-bottom: 5px; margin-bottom: 10px; }",
            "h1 { color: #1a3a5a; font-size: 18pt; margin: 0; ",
            "text-transform: uppercase; font-weight: bold; }",
            ".contato { font-size: 9pt; color: #666; margin-top: 2px; }",
            ".section-title { color: #1a3a5a; font-weight: bold; ",
            "font-size: 11pt; border-bottom: 1px solid #ddd; ",
            "text-transform: uppercase; margin-top: 15px; ",
            "margin-bottom: 5px; }",
            ".exp-item { margin-bottom: 10px; }",
            ".exp-header { font-weight: bold; color: #222; ",
            "font-size: 10pt; }",
            "li { margin-bottom: 2px; text-align: justify; }",
            "ul { margin-top: 3px; }",
            "</style>",
        ]
    )

    exp_html = ""
    for exp in experiencias:
        cargo_exp = exp.get("cargo", "Cargo")
        emp = exp.get("empresa", "Empresa")
        per = exp.get("periodo", "Período")
        conquistas = exp.get("conquistas", [])
        bullets = "".join([f"<li>{c}</li>" for c in conquistas])
        exp_html += (
            "<div class='exp-item'>"
            f"<div class='exp-header'>{cargo_exp} | {emp} ({per})</div>"
            f"<ul>{bullets}</ul></div>"
        )

    hab_html = ", ".join(habilidades)
    form_html = "".join([f"<li>{f}</li>" for f in formacao])

    html_final = "".join(
        [
            "<html><head>",
            html_style,
            "</head><body>",
            "<div class='header'>",
            f"<h1>{nome}</h1>",
            f"<div class='contato'>{contato}</div></div>",
            "<div class='section-title'>Resumo Profissional</div>",
            f"<p>{resumo}</p>",
            "<div class='section-title'>Habilidades Técnicas</div>",
            f"<p>{hab_html}</p>",
            "<div class='section-title'>Experiência Profissional</div>",
            exp_html,
            "<div class='section-title'>Formação e Certificações</div>",
            f"<ul>{form_html}</ul>",
            "</body></html>",
        ]
    )

    os.makedirs("curriculos_gerados", exist_ok=True)
    nome_arquivo = f"CV_Denis_{empresa.replace(' ', '_')}.pdf"
    caminho = os.path.join("curriculos_gerados", nome_arquivo)

    # Usar weasyprint para converter HTML em PDF
    HTML(string=html_final).write_pdf(caminho)

    return caminho


def obter_prompt(canal: str, empresa: str, cargo: str) -> str:
    """Retorna prompt estruturado para a IA de acordo com o canal escolhido"""

    prompt_lines = [
        f"Você é um assistente de carreira ajudando Denis Bolfarini "
        f"a se candidatar para a vaga de {cargo} na {empresa}.",
        "Analise o PDF do currículo original fornecido e a descrição da vaga.",
        "Sua tarefa é extrair e adaptar as informações do currículo "
        "para que fiquem perfeitamente alinhadas com a vaga.",
        "Retorne RIGOROSAMENTE um JSON com a seguinte estrutura:",
        "{",
        '  "nome": "Denis Bolfarini",',
        '  "contato": "denis.bolfarini@gmail.com | 11948103499 | '
        'São Paulo, SP",',
        '  "resumo": "Resumo profissional adaptado focando nas '
        'exigências da vaga.",',
        '  "habilidades": ["habilidade 1", "habilidade 2"],',
        '  "experiencias": [',
        '    { "cargo": "Título", "empresa": "Nome", "periodo": "datas", '
        '"conquistas": ["resultado 1", "resultado 2"] }',
        '  ],',
        '  "formacao": ["Sua Graduação / Curso"]'
    ]

    # Se a opção for E-mail, instruímos a IA a criar a estrutura completa
    if "E-mail" in canal:
        prompt_lines[-1] += ","
        prompt_lines.append(
            '  "email_destinatario": "Recrutamento [Empresa] '
            '<recrutamento@empresa.com.br> (preencha com o e-mail '
            'real do recrutador, se não souber use este placeholder)",'
        )
        prompt_lines.append(
            '  "email_assunto": "Crie um assunto curto e direto '
            'para o e-mail de candidatura à vaga de [Cargo] na '
            '[Empresa]. Exemplo: Candidatura – [Cargo] | Denis '
            'Bolfarini",'
        )
        prompt_lines.append(
            '  "email_corpo": "Redija o e-mail COMPLETO em PRIMEIRA '
            'PESSOA com TOM INFORMAL e AMIGÁVEL, como se estivesse '
            'conversando com alguém de forma natural. EVITE '
            'formalidades excessivas como Prezado(a), Venho por meio '
            'desta, Atenciosamente etc. Obrigatório: 1) Saudação '
            'leve e simpática (ex: Oi, tudo bem? / Olá, equipe da '
            '[Empresa]!); 2) Uma breve apresentação pessoal '
            'conectando sua experiência à vaga de forma genuína e '
            'direta; 3) Encerramento casual e positivo '
            '(ex: Fico à disposição pra bater um papo! / Adoraria '
            'conversar mais sobre isso!); 4) Assinatura com o nome '
            'Denis Bolfarini e contatos (telefone e e-mail) '
            'extraídos do currículo."'
        )

    prompt_lines += [
        "}",
        "ATENÇÃO: Mantenha os dados reais do PDF, use KPIs onde existirem "
        "e não invente experiências."
    ]

    return "\n".join(prompt_lines)


def obter_prompt_gupy(
    experiencia: str,
    descricao_vaga: str,
    comando_final: str = "",
) -> str:
    """Constrói o prompt para a geração do texto 'Apresente-se'.

    A experiência do candidato será extraída do arquivo PDF enviado.
    """

    final_instruction = (
        comando_final
        if comando_final and comando_final.strip()
        else (
            "Escreva um texto de apresentação em primeira pessoa, "
            "conectando a experiência extraída do PDF aos desafios da vaga. "
            "Máximo 1500 caracteres, tom persuasivo e profissional. "
        )
    )

    prompt = (
        "Você é Alia IA, uma especialista em carreira e coach de "
        "recolocação profissional. "
        "Seu tom é encorajador, prático e voltado para destacar o candidato."
        "\n\n"
        "ATENÇÃO: Analise o PDF do candidato que eu irei fornecer e extraia "
        "os principais pontos da experiência profissional (responsabilidades, "
        "resultados e skills) para que sejam relacionados à vaga abaixo.\n\n"
        "Contexto da vaga (descrição):\n"
        f"{descricao_vaga}\n\n"
        "Instruções para produção (siga RIGOROSAMENTE):\n"
        "- Extraia e use informações do PDF fornecido.\n"
        "- Escreva o texto em primeira pessoa.\n"
        "- Conecte diretamente a experiência do candidato com os principais "
        "desafios/atividades da vaga.\n"
        "- Seja persuasivo, objetivo e profissional.\n"
        "- Máximo 1500 caracteres.\n"
        "- NÃO faça perguntas ao final, nem inclua CTAs ou solicitações "
        "de confirmação.\n\n"
        "RETORNE APENAS O TEXTO DA CARTA DE APRESENTAÇÃO: NÃO inclua "
        "saudações da assistente, explicações, instruções, metadados, "
        "ou qualquer texto adicional. Comece diretamente com o texto "
        "que deve ser colado no campo 'Apresente-se'.\n\n"
        "TEXTO A GERAR:\n"
        f"{final_instruction}\n"
    )

    return prompt


def obter_prompt_followup(empresa: str, cargo: str, dias: int) -> str:
    """Gera prompt para e-mail de follow-up de candidatura sem resposta."""

    return (
        "Você é um assistente de carreira ajudando Denis Bolfarini.\n\n"
        f"Ele se candidatou para a vaga de {cargo} na {empresa} "
        f"há {dias} dias e ainda não recebeu resposta.\n\n"
        "Redija um e-mail CURTO de follow-up em PRIMEIRA PESSOA com "
        "TOM INFORMAL e AMIGÁVEL. O e-mail deve:\n"
        "1) Lembrar brevemente da candidatura enviada\n"
        "2) Reforçar o interesse na vaga de forma genuína\n"
        "3) Pedir gentilmente um retorno sobre o processo\n"
        "4) Ter no máximo 500 caracteres\n"
        "5) Assinatura: Denis Bolfarini\n\n"
        "RETORNE APENAS o corpo do e-mail, sem assunto, "
        "sem metadados, sem explicações."
    )
