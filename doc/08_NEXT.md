# Próximos Passos e Bugs (V4.0.0 - Em Desenvolvimento)

Este documento consolida as metas para a Versão 4.0.0, focando na estabilidade do novo modelo relacional e expansão de funcionalidades.

---

## 🎯 Sprint B (Atual)
- [x] **Relational Refactoring:** Migração completa para o modelo de 4 níveis (Aeronave > Snapshot > DT > Item).
- [x] **Simplified PKs:** Identificação de diretivas via código sanitizado (alfanumérico puro).
- [x] **Audit Trail:** Registro de Snapshot por importação.
- [ ] **UI Refresh:** Atualizar o Dashboard para agrupar visualmente itens por Diretiva Mestra (evitar lista flat excessivamente longa).
- [ ] **Filtros por Snapshot:** Permitir visualizar o estado do banco em uma data específica no passado.

## 🚀 Sprint C (Futuro Próximo)
- [ ] **PDF Parser Avançado:** Melhorar a extração de dados das Fichas AT para preencher campos automaticamente (PN, SN, Data).
- [ ] **Importação Multi-Aeronave:** Otimizar o parser de CSV para processar arquivos com múltiplas matrículas em uma única transação (atualmente processa linha a linha).
- [ ] **Dashboard de Conformidade:** Visão executiva (gráficos) da porcentagem de conclusão por aeronave e por especialidade.
- [ ] **Gestão de Anexos:** Galeria de anexos por diretiva (atualmente limitado a um único PDF).

## 🐛 Bugs Conhecidos / Débitos Técnicos
- [ ] **Consistência de GUT:** Recalcular GUT de todos os itens quando a Classe/Categoria da Diretiva Mestra for alterada (parcialmente implementado).
- [ ] **Performance:** Implementar paginação real no banco (SQL) para filtros de especialidade (atualmente filtra no Python em alguns pontos).
- [ ] **Token Expiring:** Melhorar feedback visual quando o cookie do Gatekeeper expira.

---

## ✅ Concluído (V3.5.0 & Início V4.0)
- [x] Proteção Anti-CSRF Global.
- [x] Mapeamento de Carreiras (BMA, BET, etc) vs Especialidades Técnicas.
- [x] Sanitização de fórmulas em exportação Excel.
- [x] Remoção completa de modelos legados.
