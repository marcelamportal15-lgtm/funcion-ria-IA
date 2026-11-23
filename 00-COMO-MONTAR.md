# Como montar a Funcionária no ChatGPT

## O que você precisa
- Conta do ChatGPT com **GPTs personalizados** e **Code Interpreter / análise de dados** (confira no seu plano; isso muda com o tempo).
- Os arquivos desta pasta.

## Passo a passo
1. No ChatGPT, vá em **Explorar GPTs > Criar** e abra a aba **Configurar**.
2. **Instruções:** cole todo o conteúdo de `01-instrucoes-do-gpt.md` (4,7 mil caracteres; o limite do campo é 8 mil).
3. **Conhecimento:** anexe estes arquivos:
   - `render_slides.py`
   - `modo-designer.md`
   - `modo-copywriter.md`
   - `modo-reels.md`
   - `modo-imagens.md`
   - `briefing-template.md`
   - `pedidos-prontos.md`
   - o briefing da marca (cliente: o dele; seu teste: `briefing-exemplo-pack-empreendedores.md`)
4. **Recursos:** ligue **Code Interpreter e análise de dados**. Sem isso, ela não gera arquivos.
5. Salve como "Só eu" (teste) ou "Qualquer pessoa com o link" (para o cliente).

## Teste obrigatório antes de vender
O ChatGPT muda sem aviso. Rode estes testes no seu plano e anote o resultado:
- [ ] Digitei "menu": a lista saiu certa?
- [ ] Opção 4: ela rodou o `render_slides.py` e entregou PNGs para baixar? Os arquivos têm 1080×1350?
- [ ] Ela achou o script em `/mnt/data/`? Se não achou, mude o caminho nas instruções e em `modo-designer.md`.
- [ ] O texto das artes está sem erro e os checks aparecem?
- [ ] Opção 1: o `calendario.csv` abre no Excel com acentos certos e uma coluna por campo?
- [ ] Opção 9: o roteiro de Reels saiu em tabela (Tempo | Fala | Texto na tela | Cena), com 2 ganchos A/B e capa?
- [ ] Opção 10: ela gerou a imagem SEM texto, pediu para anexar de volta e só então colocou o texto por cima?
- [ ] Opção 8: entregou calendário, posts e artes em uma só resposta?
- [ ] Ela avisou que não posta sozinha e mandou conferir horário nos insights?
- [ ] Testei no **celular** (app). Os links de download funcionam?
- [ ] Um cliente de teste montou sozinho. Onde travou?

Se algo falhar, ajuste primeiro as instruções, depois rode de novo.

## O que prometer na venda (só o que foi testado)
- "Deixa o calendário em planilha, os textos prontos e as artes de carrossel em PNG."
- **Não** prometa: postar sozinha, agendar sozinha, ver os números da conta, fotos e ilustrações perfeitas.
- Diga que o cliente precisa do plano do ChatGPT que inclui GPTs e Code Interpreter. Ele paga direto à OpenAI.
