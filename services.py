import os
from typing import List

from xhtml2pdf import pisa


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

    with open(caminho, "w+b") as f:
        pisa.CreatePDF(html_final, dest=f)

    return caminho


def obter_prompt(canal: str, empresa: str, cargo: str) -> str:
    """Retorna o prompt estruturado para a IA"""
    instr_email = (
        '"email_corpo": "texto para o e-mail"' if "E-mail" in canal else ""
    )

    prompt_lines = [
        "Atue como Especialista em Recrutamento. Analise o PDF e a vaga "
        f"para {cargo} na {empresa}.",
        "Retorne RIGOROSAMENTE um JSON com:",
        "{",
        '  "nome": "Denis Bolfarini",',
        '  "contato": "denis.bolfarini@gmail.com | 11948103499 | '
        'São Paulo, SP",',
        '  "resumo": "Resumo focado em dados",',
        '  "habilidades": ["item1", "item2"],',
        '  "experiencias": [',
        '    { "cargo": "título", "empresa": "nome", '
        '"periodo": "datas", "conquistas": ["ponto1"] }',
        "  ],",
        '  "formacao": ["graduação"],',
    ]

    if instr_email:
        prompt_lines.append(f"  {instr_email}")

    prompt_lines += [
        "}",
        "Mantenha os dados reais do PDF e use KPIs.",
    ]

    return "\n".join(prompt_lines)


def obter_prompt_gupy(
    experiencia: str,
    descricao_vaga: str,
    comando_final: str = "",
) -> str:
    """Constrói o prompt para a geração do texto 'Apresente-se' pela Alia IA.

    Observação: a experiência do candidato será extraída do arquivo PDF
    enviado (`linkedin.pdf`). Não é necessário que o usuário cole a
    experiência; a função orienta o modelo a analisar o PDF e usar os pontos
    relevantes para conectar à vaga.
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
        "ATENÇÃO: Analise o PDF do candidato que eu irei fornecer e extraia os "
        "principais pontos da experiência profissional (responsabilidades, "
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
        "- NÃO faça perguntas ao final, nem inclua CTAs ou solicitações de confirmação.\n\n"
        "RETORNE APENAS O TEXTO DA CARTA DE APRESENTAÇÃO: NÃO inclua saudações da assistente, explicações, instruções, metadados, ou qualquer texto adicional. Comece diretamente com o texto que deve ser colado no campo 'Apresente-se'.\n\n"
        "TEXTO A GERAR:\n"
        f"{final_instruction}\n"
    )

    return prompt
