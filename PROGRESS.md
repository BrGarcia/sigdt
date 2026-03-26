# PROGRESSO DO PROJETO SIGDT

## Versão 3.0.0-dev

### Status Atual: Implementação de Exportação Filtrada Concluída

#### 📅 26/03/2026
- [x] Refatoração da lógica de filtragem para reuso (`apply_filters`).
- [x] Atualização da rota `/export/xlsx` para aceitar parâmetros de busca e especialidade.
- [x] Sincronização em tempo real do link de exportação no frontend via JavaScript.
- [x] Implementação de nomes de arquivos dinâmicos baseados no termo de busca.
- [x] Adição da coluna `OBJETIVO` (descrição técnica) no relatório exportado.

---
**Nota:** Seguindo para as próximas etapas de Segurança (CSRF) e Rate Limiting conforme `doc/08_NEXT.md`.
**Referência:** Paramos no Passo 7 do ajuste fino (Projeto FAB).
