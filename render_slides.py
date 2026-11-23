#!/usr/bin/env python3
"""Gera artes (PNG) a partir de um JSON, só com Pillow. Roda no Code Interpreter do ChatGPT.

Uso:  python render_slides.py entrada.json [pasta_saida] [--so-primeiro]
JSON: { "imagem_fundo": "foto.jpg" (opcional), "imagem_em": "capa"|"todos", "escurecer": 0.55,
        "estilo": "clinico" | "bold" | "elegante", "formato": "4:5" | "1:1" | "9:16",
        "marca": {"cores": {...}}, "slides": [ {"titulo","apoio","lista","botao","tag","tipo"} ] }
Saída: slide-01.png, slide-02.png... (1080x1350, 1080x1080 ou 1080x1920)

Estilos:
  clinico   limpo, círculos suaves, ideal para saúde e serviços
  bold      forte, título em caixa alta, número gigante ao fundo
  elegante  fonte com serifa, centralizado, moldura fina
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

TAMANHOS = {"4:5": (1080, 1350), "1:1": (1080, 1080), "9:16": (1080, 1920)}
S = 2  # supersampling das formas (bordas suaves)

SANS_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
SANS_REG = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/Library/Fonts/Arial.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
SERIF_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "/Library/Fonts/Georgia Bold.ttf",
    "C:/Windows/Fonts/georgiab.ttf",
    "C:/Windows/Fonts/timesbd.ttf",
]
SERIF_REG = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "/Library/Fonts/Georgia.ttf",
    "C:/Windows/Fonts/georgia.ttf",
    "C:/Windows/Fonts/times.ttf",
]


def acha_fonte(lista, extra=None, obrigatoria=True):
    for p in ([extra] if extra else []) + lista:
        if p and os.path.exists(p):
            return p
    if obrigatoria:
        raise SystemExit("ERRO: nenhuma fonte encontrada. Informe marca.fonte_bold e marca.fonte com o caminho de um .ttf")
    return None


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mistura(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def quebra(draw, texto, fonte, largura, balanceado=False):
    """Quebra o texto em linhas. balanceado=True evita palavra sozinha na última linha."""
    palavras = texto.split()

    def guloso(lg):
        linhas, atual = [], ""
        for p in palavras:
            teste = (atual + " " + p).strip()
            if draw.textlength(teste, font=fonte) <= lg:
                atual = teste
            else:
                if atual:
                    linhas.append(atual)
                atual = p
        if atual:
            linhas.append(atual)
        return linhas

    linhas = guloso(largura)
    if balanceado and len(linhas) > 1:
        n = len(linhas)
        lo = max(draw.textlength(p, font=fonte) for p in palavras)
        hi = largura
        for _ in range(16):
            mid = (lo + hi) / 2
            if len(guloso(mid)) <= n:
                hi = mid
            else:
                lo = mid
        # distribui as palavras em n linhas o mais parecidas possível (sem estourar hi)
        W_ = [[0.0] * (len(palavras) + 1) for _ in range(len(palavras) + 1)]
        for i in range(len(palavras)):
            for j in range(i + 1, len(palavras) + 1):
                W_[i][j] = draw.textlength(" ".join(palavras[i:j]), font=fonte)
        INF = float("inf")
        m = len(palavras)
        custo = [[INF] * (m + 1) for _ in range(n + 1)]
        volta = [[0] * (m + 1) for _ in range(n + 1)]
        custo[0][0] = 0.0
        for k in range(1, n + 1):
            for j in range(k, m + 1):
                for i in range(k - 1, j):
                    if W_[i][j] <= hi * 1.0001 and custo[k - 1][i] < INF:
                        c = custo[k - 1][i] + (hi - W_[i][j]) ** 2
                        if c < custo[k][j]:
                            custo[k][j], volta[k][j] = c, i
        if custo[n][m] < INF:
            cortes, j = [], m
            for k in range(n, 0, -1):
                i = volta[k][j]
                cortes.append(" ".join(palavras[i:j]))
                j = i
            return cortes[::-1]
        linhas = guloso(hi)
    return linhas


# ---------- fundos e decoração ----------

def gradiente(W, H, topo, base):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        d.line([(0, y), (W, y)], fill=mistura(topo, base, y / max(1, H - 1)))
    return img


def com_formas(img, desenhar):
    """desenhar(draw, k) desenha em coordenadas já multiplicadas por k=S, com cores RGBA."""
    W, H = img.size
    ov = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    desenhar(ImageDraw.Draw(ov), S)
    ov = ov.resize((W, H), Image.LANCZOS)
    base = img.convert("RGBA")
    base.alpha_composite(ov)
    return base.convert("RGB")


def fundo(estilo, tipo, escuro, cores, W, H, idx):
    prim, fund, dest = rgb(cores["primaria"]), rgb(cores["fundo"]), rgb(cores["destaque"])
    if estilo == "clinico":
        if escuro:
            img = gradiente(W, H, prim, mistura(prim, dest, 0.28))

            def f(d, k):
                d.ellipse([(W - 480) * k, -220 * k, (W + 280) * k, 540 * k], fill=dest + (60,))
                d.ellipse([-260 * k, (H - 420) * k, 420 * k, (H + 260) * k], fill=dest + (40,))
                d.ellipse([(W - 350) * k, (H - 470) * k, (W - 110) * k, (H - 230) * k], outline=dest + (110,), width=6 * k)
        else:
            img = Image.new("RGB", (W, H), fund)

            def f(d, k):
                d.ellipse([(W - 420) * k, -200 * k, (W + 240) * k, 460 * k], fill=dest + (46,))
                d.ellipse([-220 * k, (H - 380) * k, 380 * k, (H + 220) * k], fill=dest + (28,))
                d.rectangle([0, 0, W * k, 18 * k], fill=dest + (255,))
        return com_formas(img, f)

    if estilo == "bold":
        if escuro:
            img = Image.new("RGB", (W, H), prim)

            def f(d, k):
                d.polygon([(0, H * k), (W * k, H * k), (W * k, (H - 330) * k), (0, (H - 110) * k)], fill=dest + (255,))
                d.polygon([(0, (H - 110) * k), (W * k, (H - 330) * k), (W * k, (H - 380) * k), (0, (H - 170) * k)],
                          fill=dest + (90,))
                d.rectangle([90 * k, 150 * k, 250 * k, 164 * k], fill=dest + (255,))
        else:
            img = Image.new("RGB", (W, H), fund)

            def f(d, k):
                d.rectangle([0, 0, 34 * k, H * k], fill=dest + (255,))
                d.rectangle([0, (H - 26) * k, W * k, H * k], fill=prim + (255,))

        img = com_formas(img, f)
        if not escuro:  # número gigante ao fundo
            fonte = ImageFont.truetype(acha_fonte(SANS_BOLD), 330)
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(ov).text((W - 70, 0), f"{idx + 1:02d}", font=fonte, fill=dest + (46,), anchor="ra")
            base = img.convert("RGBA")
            base.alpha_composite(ov)
            img = base.convert("RGB")
        return img

    # elegante
    img = Image.new("RGB", (W, H), prim if escuro else fund)
    linha = dest if escuro else mistura(dest, prim, 0.25)

    def f(d, k):
        d.rectangle([44 * k, 44 * k, (W - 44) * k, (H - 44) * k], outline=linha + (255,), width=3 * k)
        d.rectangle([62 * k, 62 * k, (W - 62) * k, (H - 62) * k], outline=linha + (140,), width=1 * k)
        cx, cy, r = (W // 2) * k, 128 * k, 12 * k
        d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=linha + (255,))
        d.line([(cx - 130 * k, cy), (cx - 30 * k, cy)], fill=linha + (255,), width=2 * k)
        d.line([(cx + 30 * k, cy), (cx + 130 * k, cy)], fill=linha + (255,), width=2 * k)

    return com_formas(img, f)


def prepara_fundo_imagem(caminho, W, H, cor, escurecer):
    """Corta a imagem para preencher W x H e escurece para o texto ficar legível."""
    im = Image.open(caminho).convert("RGB")
    k = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * k) + 1, int(im.height * k) + 1), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H))
    return Image.blend(im, Image.new("RGB", (W, H), cor), max(0.0, min(0.9, escurecer)))


def decora_sobre_imagem(img, estilo, cores, W, H):
    dest = rgb(cores["destaque"])

    def f(d, k):
        if estilo == "bold":
            d.rectangle([90 * k, 150 * k, 250 * k, 164 * k], fill=dest + (255,))
        elif estilo == "elegante":
            d.rectangle([44 * k, 44 * k, (W - 44) * k, (H - 44) * k], outline=dest + (255,), width=3 * k)
            d.rectangle([62 * k, 62 * k, (W - 62) * k, (H - 62) * k], outline=dest + (140,), width=1 * k)
        else:
            d.rectangle([0, 0, W * k, 18 * k], fill=dest + (255,))

    return com_formas(img, f)


# ---------- texto ----------

def marcador(d, estilo, x, y, t, cor):
    if estilo == "clinico":
        larg = max(6, t // 5)
        d.line([(x, y + t * 0.55), (x + t * 0.38, y + t * 0.95)], fill=cor, width=larg)
        d.line([(x + t * 0.38, y + t * 0.95), (x + t * 1.0, y + t * 0.1)], fill=cor, width=larg)
    elif estilo == "bold":
        d.rectangle([x, y + t * 0.2, x + t * 0.7, y + t * 0.9], fill=cor)
    else:
        cx, cy, r = x + t * 0.35, y + t * 0.58, t * 0.3
        d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=cor)


def desenha_slide(s, i, total, W, H, cores, fontes, estilo, logo, fundo_img=None):
    tipo = s.get("tipo") or ("capa" if i == 0 else "cta" if i == total - 1 else "conteudo")
    escuro = tipo in ("capa", "cta") or fundo_img is not None
    centro = estilo == "elegante"
    caixa_alta = estilo == "bold"
    prim, fund, dest = rgb(cores["primaria"]), rgb(cores["fundo"]), rgb(cores["destaque"])
    fg = rgb(cores["textoClaro"] if escuro else cores["texto"])
    cor_dest = dest if (escuro or estilo != "elegante") else mistura(dest, prim, 0.35)
    f_bold, f_reg = fontes

    if fundo_img is not None:
        img = decora_sobre_imagem(fundo_img.copy(), estilo, cores, W, H)
    else:
        img = fundo(estilo, tipo, escuro, cores, W, H, i)
    d = ImageDraw.Draw(img)

    seguro = 130 if H >= 1900 else 0  # Stories/Reels: topo e rodapé cobertos pelo app
    mx = 150 if centro else 90
    larg = W - 2 * mx
    topo = (200 if centro else 170) + seguro
    reserva = 210 + seguro + (230 if (estilo == "bold" and escuro) else 0)
    area_h = H - topo - reserva

    t_tam = (96 if centro else 108) if tipo == "capa" else 84
    a_tam = 44
    gap = 36
    titulo = s["titulo"].upper() if caixa_alta else s["titulo"]
    while True:
        blocos, altura = [], 0
        if s.get("tag"):
            blocos.append(("tag", ImageFont.truetype(f_bold, 30), [s["tag"].upper()], 40))
            altura += 40 + gap
        ft = ImageFont.truetype(f_bold, t_tam)
        lt = quebra(d, titulo, ft, larg, True)
        blocos.append(("titulo", ft, lt, int(t_tam * 1.1)))
        altura += int(len(lt) * t_tam * 1.1) + 16
        if estilo == "clinico":
            blocos.append(("barra", None, None, 10))
            altura += gap + 20
        if s.get("apoio"):
            fa = ImageFont.truetype(f_reg, a_tam)
            la = quebra(d, s["apoio"], fa, larg, True)
            blocos.append(("apoio", fa, la, int(a_tam * 1.35)))
            altura += gap + int(len(la) * a_tam * 1.35)
        if s.get("lista"):
            fl = ImageFont.truetype(f_reg, a_tam)
            itens = [quebra(d, x, fl, larg - 70) for x in s["lista"]]
            blocos.append(("lista", fl, itens, int(a_tam * 1.3)))
            altura += gap + sum(int(len(l) * a_tam * 1.3) + 22 for l in itens)
        if s.get("botao") and tipo == "cta":
            altura += gap + 110
        if altura <= area_h or t_tam <= 40:
            break
        t_tam = int(t_tam * 0.95)
        a_tam = max(24, int(a_tam * 0.95))

    y = topo + max(0, (area_h - altura) // 2)

    def linha(txt, fonte, cor, yy):
        w = d.textlength(txt, font=fonte)
        d.text(((W - w) / 2 if centro else mx, yy), txt, font=fonte, fill=cor)

    for nome, fonte, conteudo, lh in blocos:
        if nome == "tag":
            linha(conteudo[0], fonte, cor_dest, y)
            y += lh + gap
        elif nome == "titulo":
            for ln in conteudo:
                linha(ln, fonte, fg, y)
                y += lh
            y += gap + 8
        elif nome == "barra":
            x0 = (W - 110) / 2 if centro else mx
            d.rounded_rectangle([x0, y + 10, x0 + 110, y + 10 + lh], radius=5, fill=dest)
            y += lh + gap + 10
        elif nome == "apoio":
            for ln in conteudo:
                linha(ln, fonte, fg, y)
                y += lh
            y += gap - 8
        elif nome == "lista":
            for linhas in conteudo:
                for k, ln in enumerate(linhas):
                    w = d.textlength(ln, font=fonte)
                    x = (W - w) / 2 if centro else mx + 70
                    if k == 0:
                        marcador(d, estilo, (x - 62) if centro else mx, y + int(lh * 0.2), int(lh * 0.5), cor_dest)
                    d.text((x, y), ln, font=fonte, fill=fg)
                    y += lh
                y += 22
    if s.get("botao") and tipo == "cta":
        fb = ImageFont.truetype(f_bold, 46)
        tw = d.textlength(s["botao"], font=fb)
        x0 = (W - tw - 108) / 2 if centro else mx
        d.rounded_rectangle([x0, y, x0 + tw + 108, y + 110], radius=(55 if estilo == "clinico" else 14 if estilo == "bold" else 4),
                            fill=dest)
        d.text((x0 + 54, y + 28), s["botao"], font=fb, fill=prim if sum(dest) > 380 else (255, 255, 255))

    # contador e logo
    fc = ImageFont.truetype(f_reg, 30)
    txt = f"{i + 1}/{total}"
    cw = d.textlength(txt, font=fc)
    cx = (W - cw) / 2 if centro else W - mx - cw
    d.text((cx, H - 105 - seguro // 2), txt, font=fc, fill=fg)
    if logo is not None:
        lg = logo.copy()
        lg.thumbnail((260, 70))
        img.paste(lg, (mx, H - 115 - seguro // 2), lg if lg.mode == "RGBA" else None)
    return img


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    so_primeiro = "--so-primeiro" in sys.argv
    if not args:
        raise SystemExit(__doc__)
    cfg = json.load(open(args[0], encoding="utf-8"))
    pasta = args[1] if len(args) > 1 else cfg.get("saida", "artes")
    os.makedirs(pasta, exist_ok=True)

    estilo = cfg.get("estilo", "clinico")
    if estilo not in ("clinico", "bold", "elegante"):
        raise SystemExit("ERRO: estilo deve ser clinico, bold ou elegante")
    marca = cfg.get("marca", {})
    cores = {"fundo": "#FFFFFF", "primaria": "#0B2A5B", "destaque": "#4DA3FF",
             "texto": "#0B2A5B", "textoClaro": "#FFFFFF"}
    if estilo == "elegante":
        cores["fundo"] = "#FBF7F0"
    cores.update(marca.get("cores", {}))
    W, H = TAMANHOS.get(cfg.get("formato", "4:5"), TAMANHOS["4:5"])

    if estilo == "elegante":
        fb = acha_fonte(SERIF_BOLD, marca.get("fonte_bold"), obrigatoria=False) or acha_fonte(SANS_BOLD)
        fr = acha_fonte(SERIF_REG, marca.get("fonte"), obrigatoria=False) or acha_fonte(SANS_REG)
    else:
        fb = acha_fonte(SANS_BOLD, marca.get("fonte_bold"))
        fr = acha_fonte(SANS_REG, marca.get("fonte"))
    logo = Image.open(marca["logo"]).convert("RGBA") if marca.get("logo") and os.path.exists(marca["logo"]) else None

    slides = cfg["slides"]
    alvo = slides[:1] if so_primeiro else slides
    problemas = 0
    for i, s in enumerate(alvo):
        caminho_img = s.get("imagem") or (cfg.get("imagem_fundo") if (cfg.get("imagem_em", "capa") == "todos" or i == 0) else None)
        fundo_img = None
        if caminho_img:
            junto_do_json = os.path.join(os.path.dirname(os.path.abspath(args[0])), caminho_img)
            if not os.path.exists(caminho_img) and os.path.exists(junto_do_json):
                caminho_img = junto_do_json
            if not os.path.exists(caminho_img):
                print("AVISO: imagem não encontrada, usando fundo liso:", caminho_img)
            else:
                fundo_img = prepara_fundo_imagem(caminho_img, W, H, rgb(cores["primaria"]), cfg.get("escurecer", 0.55))
        img = desenha_slide(s, i, len(slides), W, H, cores, (fb, fr), estilo, logo, fundo_img)
        caminho = os.path.join(pasta, f"slide-{i + 1:02d}.png")
        img.save(caminho)
        ok = Image.open(caminho).size == (W, H)
        problemas += 0 if ok else 1
        print(("OK " if ok else "TAMANHO ERRADO ") + caminho, Image.open(caminho).size)
    sys.exit(1 if problemas else 0)


if __name__ == "__main__":
    main()
