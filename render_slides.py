#!/usr/bin/env python3
"""Gera artes (PNG) a partir de um JSON, só com Pillow. Roda no Code Interpreter do ChatGPT.

Uso:  python render_slides.py entrada.json [pasta_saida] [--so-primeiro]
Saída: slide-01.png, slide-02.png... (1080x1350, 1080x1080 ou 1080x1920)
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

TAMANHOS = {"4:5": (1080, 1350), "1:1": (1080, 1080), "9:16": (1080, 1920)}

FONTES_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
FONTES_REG = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/Library/Fonts/Arial.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def acha_fonte(lista, extra=None):
    for p in ([extra] if extra else []) + lista:
        if p and os.path.exists(p):
            return p
    raise SystemExit("ERRO: nenhuma fonte encontrada. Informe marca.fonte_bold e marca.fonte com o caminho de um .ttf")


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def quebra(draw, texto, fonte, largura):
    palavras, linhas, atual = texto.split(), [], ""
    for p in palavras:
        teste = (atual + " " + p).strip()
        if draw.textlength(teste, font=fonte) <= largura:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def bloco(draw, texto, caminho, tam, largura, espaco=1.15):
    """Retorna (fonte, linhas, altura)."""
    f = ImageFont.truetype(caminho, tam)
    linhas = quebra(draw, texto, f, largura)
    return f, linhas, int(len(linhas) * tam * espaco)


def desenha_slide(s, i, total, W, H, cores, f_bold, f_reg, logo):
    tipo = s.get("tipo") or ("capa" if i == 0 else "cta" if i == total - 1 else "conteudo")
    escuro = tipo in ("capa", "cta")
    bg = hex_rgb(cores["primaria"] if escuro else cores["fundo"])
    fg = hex_rgb(cores["textoClaro"] if escuro else cores["texto"])
    dest = hex_rgb(cores["destaque"])

    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 18], fill=dest)

    mx = 90
    larg = W - 2 * mx
    area_h = H - 170 - 200

    # tamanhos iniciais; reduz até caber
    t_tam = 112 if tipo == "capa" else 86
    a_tam = 44
    gap = 36
    while True:
        blocos = []
        altura = 0
        if s.get("tag"):
            ft = ImageFont.truetype(f_bold, 30)
            blocos.append(("tag", ft, [s["tag"].upper()], 40))
            altura += 40 + gap
        ft, lt, ht = bloco(d, s["titulo"], f_bold, t_tam, larg, 1.1)
        blocos.append(("titulo", ft, lt, int(t_tam * 1.1)))
        altura += ht
        if s.get("apoio"):
            fa, la, ha = bloco(d, s["apoio"], f_reg, a_tam, larg, 1.35)
            blocos.append(("apoio", fa, la, int(a_tam * 1.35)))
            altura += gap + ha
        if s.get("lista"):
            fl = ImageFont.truetype(f_reg, a_tam)
            itens = [quebra(d, x, fl, larg - 70) for x in s["lista"]]
            hl = sum(int(len(l) * a_tam * 1.3) + 22 for l in itens)
            blocos.append(("lista", fl, itens, int(a_tam * 1.3)))
            altura += gap + hl
        if s.get("botao") and tipo == "cta":
            altura += gap + 110
        if altura <= area_h or t_tam <= 40:
            break
        t_tam = int(t_tam * 0.95)
        a_tam = max(24, int(a_tam * 0.95))

    y = 170 + max(0, (area_h - altura) // 2)
    for nome, fonte, conteudo, lh in blocos:
        if nome == "tag":
            d.text((mx, y), conteudo[0], font=fonte, fill=dest)
            y += lh + gap
        elif nome == "titulo":
            for ln in conteudo:
                d.text((mx, y), ln, font=fonte, fill=fg)
                y += lh
            y += gap - 8
        elif nome == "apoio":
            for ln in conteudo:
                d.text((mx, y), ln, font=fonte, fill=fg)
                y += lh
            y += gap - 8
        elif nome == "lista":
            for linhas in conteudo:
                _check(d, mx, y + int(lh * 0.22), int(lh * 0.5), dest)
                for ln in linhas:
                    d.text((mx + 70, y), ln, font=fonte, fill=fg)
                    y += lh
                y += 22
    if s.get("botao") and tipo == "cta":
        fb = ImageFont.truetype(f_bold, 46)
        tw = d.textlength(s["botao"], font=fb)
        d.rounded_rectangle([mx, y, mx + tw + 108, y + 110], radius=18, fill=dest)
        d.text((mx + 54, y + 28), s["botao"], font=fb, fill=hex_rgb(cores["primaria"]))

    # rodapé: contador e espaço de logo
    fc = ImageFont.truetype(f_reg, 30)
    txt = f"{i + 1}/{total}"
    d.text((W - mx - d.textlength(txt, font=fc), H - 100), txt, font=fc, fill=fg)
    if logo is not None:
        lg = logo.copy()
        lg.thumbnail((260, 70))
        img.paste(lg, (mx, H - 110), lg if lg.mode == "RGBA" else None)
    return img


def _check(d, x, y, t, cor):
    """Desenha um ✔ como forma (não depende de a fonte ter o símbolo)."""
    larg = max(6, t // 5)
    d.line([(x, y + t * 0.55), (x + t * 0.38, y + t * 0.95)], fill=cor, width=larg)
    d.line([(x + t * 0.38, y + t * 0.95), (x + t * 1.0, y + t * 0.1)], fill=cor, width=larg)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    so_primeiro = "--so-primeiro" in sys.argv
    if not args:
        raise SystemExit(__doc__)
    cfg = json.load(open(args[0], encoding="utf-8"))
    pasta = args[1] if len(args) > 1 else cfg.get("saida", "artes")
    os.makedirs(pasta, exist_ok=True)

    marca = cfg.get("marca", {})
    cores = {"fundo": "#FFFFFF", "primaria": "#0B2A5B", "destaque": "#4DA3FF",
             "texto": "#0B2A5B", "textoClaro": "#FFFFFF"}
    cores.update(marca.get("cores", {}))
    W, H = TAMANHOS.get(cfg.get("formato", "4:5"), TAMANHOS["4:5"])
    f_bold = acha_fonte(FONTES_BOLD, marca.get("fonte_bold"))
    f_reg = acha_fonte(FONTES_REG, marca.get("fonte"))
    logo = None
    if marca.get("logo") and os.path.exists(marca["logo"]):
        logo = Image.open(marca["logo"]).convert("RGBA")

    slides = cfg["slides"]
    alvo = slides[:1] if so_primeiro else slides
    problemas = 0
    for i, s in enumerate(alvo):
        img = desenha_slide(s, i, len(slides), W, H, cores, f_bold, f_reg, logo)
        caminho = os.path.join(pasta, f"slide-{i + 1:02d}.png")
        img.save(caminho)
        ok = Image.open(caminho).size == (W, H)
        problemas += 0 if ok else 1
        print(("OK " if ok else "TAMANHO ERRADO ") + caminho, Image.open(caminho).size)
    sys.exit(1 if problemas else 0)


if __name__ == "__main__":
    main()
