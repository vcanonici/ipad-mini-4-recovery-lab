# iPad mini 4 Recovery Lab

Documentação de uma investigação de recuperação do **iPad mini 4 Wi‑Fi — iPad5,1, j96ap, A8**, após um downgrade interrompido com surrealra1n.

[English](README.md) · [Histórico](docs/CASE-STUDY.md) · [Descobertas](docs/FINDINGS.md) · [Procedimento](docs/WORKFLOW.md) · [Logs](evidence/README.md)

**Se este trabalho ajudar você, deixe uma ⭐ no repositório!** Isso ajuda outras pessoas com o mesmo iPad a encontrar o material.

## Resultado comprovado

Em 30/10/2026, a restauração completa do iOS **15.8.8 / 19H422** terminou com verificação e selagem do sistema. Depois, os arquivos gravados foram lidos novamente:

- LLB, iBoot e SEP tinham payloads idênticos aos componentes oficiais do IPSW.
- Os tickets desses componentes, o ART e o Preboot ativo estavam alinhados.
- `SHA1(IM4R.BNCN) == IM4M.BNCH` passou no LLB e no iBoot gravados.

**O boot normal foi confirmado pelo proprietário:** “bootou e ta a funcionar”. A configuração foi deixada para depois de carregar. Isso confirma a inicialização observada, mas não representa um teste completo de hardware, ativação ou estabilidade de longo prazo.

## O que aprendemos

O envio USB retornar sucesso não prova que o carregador executou. O marcador `PWND` não garante que a CPU está executando o patch que aparece numa leitura de memória. E uma restauração que terminou com `DONE` pode ter gravado arquivos cujo nonce não corresponde ao ticket.

Também encontramos respostas antigas no buffer de `getenv`, uma restrição adicional de variável que o patcher local não alterava, e a necessidade de alinhar o manifesto do diagnóstico com o ticket usado na restauração. Dois panics foram provocados pelos próprios testes de diagnóstico e estão identificados como tal.

Os [logs selecionados completos](evidence/README.md), dados reais do aparelho, nonces, hashes e offsets foram preservados para permitir a análise técnica. Foram excluídas apenas credenciais/chaves de conta. Arquivos de firmware Apple, tickets completos e executáveis de terceiros não são redistribuídos.

## Como usar

Comece pelo [histórico do caso](docs/CASE-STUDY.md) e pelos [limites das descobertas](docs/FINDINGS.md). As ferramentas Python são locais e não escrevem no iPad:

```sh
python3 tools/inspect_img4.py LLB.img4 --require-nonce
python3 -m unittest discover -s tests -v
```

O analisador confere estrutura e relação entre nonces; ele **não valida assinatura Apple nem comprova que o aparelho vai iniciar**. Os offsets de RAM só foram conferidos para o hash exato registrado. O modelo celular `iPad5,2` não foi validado.

Contribuições com evidências reproduzíveis são bem-vindas. E, se o material foi útil, **deixe uma ⭐!**
